import os
import pathspec
import pyperclip

# Safe mode constants
SAFE_MODE_MAX_FILES = 30
SAFE_MODE_MAX_LENGTH = 100_000  # ~25K tokens, reasonable for most LLMs

# Global list of obvious files and directories to ignore
DEFAULT_IGNORES = {".git", ".vscode", "__pycache__", ".DS_Store", ".idea", ".gitignore"}


def create_pattern_spec(patterns):
    """Create a pathspec object from a list of glob patterns."""
    if not patterns or patterns == ["*"]:
        return None
    return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, patterns)


def matches_patterns(file_path, root_dir, pattern_spec):
    """Check if a file matches the given pattern spec."""
    if pattern_spec is None:
        return True  # No patterns means match all
    
    # Get relative path from root directory
    relative_path = os.path.relpath(file_path, root_dir)
    # Normalize path separators for cross-platform compatibility
    relative_path = relative_path.replace(os.sep, '/')
    
    return pattern_spec.match_file(relative_path)


def generate_tree_structure(root_dir, gitignore_spec, show_ignored=False, show_default_ignored=False, include_patterns=None, exclude_patterns=None):
    """Generate a tree-like directory structure, mimicking the 'tree' command output
       with correct characters, indentation, and alphabetical ordering."""
    tree_lines = ['.']  # Start with the root directory indicator
    file_list = []

    # Create pattern specs for include/exclude filtering
    include_spec = create_pattern_spec(include_patterns)
    exclude_spec = create_pattern_spec(exclude_patterns)

    def _generate_tree(dir_path, indent_prefix):
        items = sorted(os.listdir(dir_path))
        
        # Filter items based on ignore settings and patterns
        if not show_ignored:
            if show_default_ignored:
                # Only filter out gitignore items, but show default ignored items
                items = [item for item in items if not (gitignore_spec and 
                          gitignore_spec.match_file(os.path.relpath(os.path.join(dir_path, item), root_dir)))]
            else:
                # Filter out all ignored items
                items = [item for item in items
                       if not is_ignored(os.path.join(dir_path, item), gitignore_spec, root_dir)]
        
        # Apply include/exclude pattern filtering
        if include_spec or exclude_spec:
            filtered_items = []
            for item in items:
                item_path = os.path.join(dir_path, item)
                
                # Check include patterns (if specified, file must match at least one)
                if include_spec is not None:
                    if not matches_patterns(item_path, root_dir, include_spec):
                        # For directories, check if any child might match
                        if os.path.isdir(item_path):
                            # Check if any pattern could potentially match files in this directory
                            dir_relative = os.path.relpath(item_path, root_dir).replace(os.sep, '/')
                            # If any include pattern starts with this directory path, include it
                            should_include_dir = any(
                                pattern.startswith(dir_relative + '/') or 
                                pattern.startswith('**/') or
                                '**' in pattern
                                for pattern in include_patterns or []
                            )
                            if not should_include_dir:
                                continue
                        else:
                            continue
                
                # Check exclude patterns (if file matches any, exclude it)
                if exclude_spec is not None and matches_patterns(item_path, root_dir, exclude_spec):
                    continue
                
                filtered_items.append(item)
            items = filtered_items
        
        num_items = len(items)

        for index, item in enumerate(items):
            is_last_item = (index == num_items - 1)
            item_path = os.path.join(dir_path, item)
            is_directory = os.path.isdir(item_path)

            # Connector: └── for last item, ├── otherwise
            connector = '└── ' if is_last_item else '├── '
            line_prefix = indent_prefix + connector
            item_display_name = item + "/" if is_directory else item # Append "/" for directories

            tree_lines.append(line_prefix + item_display_name) # No prepended "|"

            if is_directory:
                # Indentation for subdirectories: '    ' if last item, '│   ' otherwise
                new_indent_prefix = indent_prefix + ('    ' if is_last_item else '│   ')
                _generate_tree(item_path, new_indent_prefix)
            elif os.path.isfile(item_path):
                file_list.append(item_path)

    _generate_tree(root_dir, '')

    return "\n".join(tree_lines), file_list


def load_gitignore(start_dir):
    """Load patterns from .gitignore by searching in the start directory and its parents,
       using os.path.abspath for path handling."""
    current_dir = os.path.abspath(start_dir) # Convert start_dir to absolute path

    while current_dir != os.path.dirname(current_dir):  # Stop at the root directory
        gitignore_path = os.path.join(current_dir, ".gitignore")
        if os.path.exists(gitignore_path):
            print(f"Found .gitignore in: {current_dir}")
            with open(gitignore_path, "r", encoding="utf-8") as f:
                return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, f)
        current_dir = os.path.dirname(current_dir) # Move to parent directory (still absolute path)

    # Check for .gitignore in the root directory as a last resort
    root_gitignore_path = os.path.join(current_dir, ".gitignore") # current_dir is now root path
    if os.path.exists(root_gitignore_path):
        print(f"Found .gitignore in root directory: {current_dir}")
        with open(root_gitignore_path, "r", encoding="utf-8") as f:
            return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, f)

    return None  # No .gitignore found


def is_ignored(file_or_dir_path, gitignore_spec, root_dir):
    """Check if a file or directory is ignored by .gitignore or default ignores."""
    # Normalize the path relative to the root directory
    relative_path = os.path.relpath(file_or_dir_path, root_dir)

    # Check if it's in the default ignore list (e.g., ".git", "__pycache__")
    if any(segment in DEFAULT_IGNORES for segment in relative_path.split(os.sep)):
        return True

    # Check against .gitignore if a spec is provided
    if gitignore_spec and gitignore_spec.match_file(relative_path):
        return True
    elif gitignore_spec and gitignore_spec.match_file(file_or_dir_path):
        return True

    return False


def add_line_numbers(content):
    """Add line numbers to the content."""
    lines = content.splitlines()
    if not lines and content == "":
        # Handle empty content - splitlines() returns [] for empty string
        return "   1 | "
    numbered_lines = [f"{i + 1:4d} | {line}" for i, line in enumerate(lines)]
    return "\n".join(numbered_lines)


def combine_files_with_structure(root_dir, use_git_ignore, interactive=False, previous_files=None, 
                          safe_mode=True, line_numbers=False, show_ignored_in_tree=False, 
                          show_default_ignored_in_tree=False, include_patterns=None, exclude_patterns=None):
    """Combine file contents with directory structure."""
    combined_content = []

    gitignore_spec = load_gitignore(root_dir) if use_git_ignore else None
    tree_structure, file_list = generate_tree_structure(
        root_dir, 
        gitignore_spec, 
        show_ignored=show_ignored_in_tree,
        show_default_ignored=show_default_ignored_in_tree,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns
    )

    combined_content.append("# Project Directory Structure:")
    combined_content.append(tree_structure)
    combined_content.append("\n# BEGIN FILE CONTENTS")

    if previous_files:
        # Convert relative paths to absolute paths and verify they exist
        selected_files = set()
        for rel_path in previous_files:
            abs_path = os.path.abspath(os.path.join(root_dir, rel_path))
            if os.path.exists(abs_path) and os.path.isfile(abs_path):
                selected_files.add(abs_path)
            else:
                print(f"Warning: Previously selected file not found: {rel_path}")
        
        if not selected_files:
            raise SystemExit("No valid files found from previous selection")
    elif interactive:
        # Import interactive function only when needed to avoid circular imports
        from .interactive import interactive_file_selector
        selected_files = interactive_file_selector(file_list)
    else:
        selected_files = set(file_list)

    # Add safe mode checks
    if safe_mode:
        if len(selected_files) > SAFE_MODE_MAX_FILES:
            raise SystemExit(
                f"Safe mode: Too many files selected ({len(selected_files)} > {SAFE_MODE_MAX_FILES})\n"
                "To override this limit, run the command again with --disable-safe-mode or -dsm"
            )
        
        total_size = 0
        for file_path in selected_files:
            total_size += os.path.getsize(file_path)
            if total_size > SAFE_MODE_MAX_LENGTH:
                raise SystemExit(
                    f"Safe mode: Combined file size too large (> {SAFE_MODE_MAX_LENGTH:,} bytes)\n"
                    "To override this limit, run the command again with --disable-safe-mode or -dsm"
                )

    # Combine contents of selected files
    for file_path in selected_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Add line numbers if requested
            if line_numbers:
                content = add_line_numbers(content)

            # Convert absolute path to relative path for display
            rel_path = os.path.relpath(file_path, root_dir)
            combined_content.append(f"\n# File: {rel_path}\n")
            combined_content.append(content)
            combined_content.append("\n# END FILE CONTENTS\n")
        except (UnicodeDecodeError, OSError) as e:
            print(f"Warning: Could not read file {file_path}: {e}")
            continue

    return "\n".join(combined_content), selected_files


def save_to_file(output_path, content):
    """Save the combined content to a file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def copy_to_clipboard(content):
    """Copy the provided content to the clipboard."""
    try:
        pyperclip.copy(content)
        print("Output copied to clipboard!")
    except pyperclip.PyperclipException as e:
        print(f"Failed to copy to clipboard: {e}")


def estimate_tokens(text):
    """Provide a rough estimate of tokens in the text (using ~4 chars per token)."""
    return len(text) // 4 