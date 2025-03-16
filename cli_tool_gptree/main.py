import os
import argparse
import readline
import pathspec
import curses
import pyperclip
import copy

CURRENT_VERSION = 'v1.4.0'

SAFE_MODE_MAX_FILES = 30
SAFE_MODE_MAX_LENGTH = 100_000  # ~25K tokens, reasonable for most LLMs

# Global list of obvious files and directories to ignore
DEFAULT_IGNORES = {".git", ".vscode", "__pycache__", ".DS_Store", ".idea", ".gitignore"}
PROJECT_CONFIG_FILE = '.gptree_config'
OUTPUT_FILE = 'gptree_output.txt'

CONFIG_VERSION = 2  # Increment this when config structure changes
DEFAULT_CONFIG = {
    "version": CONFIG_VERSION,  # Add version to default config
    "useGitIgnore": True,
    "includeFileTypes": "*",
    "excludeFileTypes": [],
    "outputFile": OUTPUT_FILE,
    "outputFileLocally": True,
    "copyToClipboard": False,
    "safeMode": True,
    "storeFilesChosen": True,
    "lineNumbers": False,
    "showIgnoredInTree": False,
    "showDefaultIgnoredInTree": False,
}

def generate_tree_structure(root_dir, gitignore_spec, show_ignored=False, show_default_ignored=False):
    """Generate a tree-like directory structure, mimicking the 'tree' command output
       with correct characters, indentation, and alphabetical ordering."""
    tree_lines = ['.']  # Start with the root directory indicator
    file_list = []

    def _generate_tree(dir_path, indent_prefix):
        items = sorted(os.listdir(dir_path))
        
        # Filter items based on ignore settings
        if not show_ignored:
            if show_default_ignored:
                # Only filter out gitignore items, but show default ignored items
                items = [item for item in items if not (gitignore_spec and 
                          gitignore_spec.match_file(os.path.relpath(os.path.join(dir_path, item), root_dir)))]
            else:
                # Filter out all ignored items
                items = [item for item in items
                       if not is_ignored(os.path.join(dir_path, item), gitignore_spec, root_dir)]
        
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
    numbered_lines = [f"{i + 1:4d} | {line}" for i, line in enumerate(lines)]
    return "\n".join(numbered_lines)

def interactive_file_selector(file_list):
    """Interactive file selector with a scrollable list using curses."""
    selected_files = set()
    display_limit = 15  # Number of files shown at a time

    def draw_menu(stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight color
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default color

        current_row = 0
        offset = 0  # For scrolling
        max_rows = len(file_list)

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Use ↑/↓/j/k to scroll, SPACE to toggle selection, 'a' to select all, ENTER to confirm, ESC to quit")
            stdscr.addstr(1, 0, "-" * 80)

            for idx in range(display_limit):
                file_idx = offset + idx
                if file_idx >= max_rows:
                    break
                file = file_list[file_idx]
                prefix = "[X]" if file in selected_files else "[ ]"

                if file_idx == current_row:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(idx + 2, 0, f"{prefix} {file[:70]}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.attron(curses.color_pair(2))
                    stdscr.addstr(idx + 2, 0, f"{prefix} {file[:70]}")
                    stdscr.attroff(curses.color_pair(2))

            # Add ellipsis indicators if there are more files above or below
            if offset > 0:
                stdscr.addstr(2, 78, "↑")
            if offset + display_limit < max_rows:
                stdscr.addstr(display_limit + 1, 78, "↓")

            stdscr.addstr(display_limit + 3, 0, "-" * 80)
            stdscr.addstr(display_limit + 4, 0, f"Selected: {len(selected_files)} / {len(file_list)}")

            key = stdscr.getch()
            if key in (curses.KEY_DOWN, ord('j')):
                if current_row < max_rows - 1:
                    current_row += 1
                    if current_row >= offset + display_limit:
                        offset += 1
            elif key in (curses.KEY_UP, ord('k')):
                if current_row > 0:
                    current_row -= 1
                    if current_row < offset:
                        offset -= 1
            elif key == ord(' '):
                file = file_list[current_row]
                if file in selected_files:
                    selected_files.remove(file)
                else:
                    selected_files.add(file)
            elif key == ord('a'):
                if len(selected_files) < len(file_list):
                    selected_files.update(file_list)
                else:
                    selected_files.clear()
            elif key == 27:  # ESC key
                raise SystemExit("Interactive mode canceled by user.")
            elif key == 10:  # ENTER key
                break

    curses.wrapper(draw_menu)
    return selected_files

def combine_files_with_structure(root_dir, use_git_ignore, interactive=False, previous_files=None, 
                          safe_mode=True, line_numbers=False, show_ignored_in_tree=False, 
                          show_default_ignored_in_tree=False):
    """Combine file contents with directory structure."""
    combined_content = []

    gitignore_spec = load_gitignore(root_dir) if use_git_ignore else None
    tree_structure, file_list = generate_tree_structure(
        root_dir, 
        gitignore_spec, 
        show_ignored=show_ignored_in_tree,
        show_default_ignored=show_default_ignored_in_tree
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

def setup_autocomplete():
    """Enable tab-completion for input prompts."""
    def complete_path(text, state):
        line = readline.get_line_buffer()
        path = os.path.expanduser(line)
        options = [x for x in os.listdir(path or '.') if x.startswith(text)]
        if state < len(options):
            return options[state]
        return None

    readline.set_completer(complete_path)
    readline.parse_and_bind("tab: complete")

def prompt_user_input(prompt, default):
    """Prompt user for input with a default value."""
    user_input = input(f"{prompt} [{default}]: ").strip()
    return user_input if user_input else default

def migrate_config(config, current_version, is_global=False):
    """Migrate config from older versions to current version."""
    if "version" not in config:
        config["version"] = 0
    else:
        try:
            config["version"] = int(config["version"])
        except ValueError:
            config["version"] = 0  # If version can't be parsed, assume oldest version

    while config["version"] < current_version:
        if config["version"] == 0:
            # Migrate from version 0 to 1
            if not is_global:
                config["previousFiles"] = config.get("previousFiles", [])
            config["version"] = 1
            print(f"Migrated {'global' if is_global else 'local'} config from version 0 to 1")
        elif config["version"] == 1:
            # Migrate from version 1 to 2
            config["showIgnoredInTree"] = False
            config["showDefaultIgnoredInTree"] = False
            config["version"] = 2
            print(f"Migrated {'global' if is_global else 'local'} config from version 1 to 2")
        # Add more elif blocks here for future versions
        # elif config["version"] == 2:
        #     # Migrate from version 2 to 3
        #     config["newSetting"] = "default"
        #     config["version"] = 3

    return config

def write_config(file_path, isGlobal=False):
    """Write or update configuration file."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    if not isGlobal:
        config["previousFiles"] = []

    if os.path.exists(file_path):
        # Read existing config
        existing_config = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and ":" in line:
                    key, value = line.split(":", 1)
                    existing_config[key.strip()] = value.strip()
        
        # Migrate if necessary
        existing_config = migrate_config(existing_config, CONFIG_VERSION, isGlobal)
        config.update(existing_config)

    # Write updated config
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# GPTree {'Global' if isGlobal else 'Local'} Config\n")
        f.write(f"version: {config['version']}\n\n")
        f.write("# Whether to use .gitignore\n")
        f.write(f"useGitIgnore: {str(config['useGitIgnore']).lower()}\n")
        f.write("# File types to include (e.g., .py,.js)\n")
        f.write(f"includeFileTypes: {config['includeFileTypes']}\n")
        f.write("# File types to exclude when includeFileTypes is '*'\n")
        f.write(f"excludeFileTypes: {','.join(config['excludeFileTypes']) if isinstance(config['excludeFileTypes'], list) else config['excludeFileTypes']}\n")
        f.write("# Output file name\n")
        f.write(f"outputFile: {config['outputFile']}\n")
        f.write("# Whether to output the file locally or relative to the project directory\n")
        f.write(f"outputFileLocally: {str(config['outputFileLocally']).lower()}\n")
        f.write("# Whether to copy the output to the clipboard\n")
        f.write(f"copyToClipboard: {str(config['copyToClipboard']).lower()}\n")
        f.write('# Whether to use safe mode (prevent overly large files from being combined)\n')
        f.write(f"safeMode: {str(config['safeMode']).lower()}\n")
        f.write("# Whether to store the files chosen in the config file (--save, -s)\n")
        f.write(f"storeFilesChosen: {str(config['storeFilesChosen']).lower()}\n")
        f.write("# Whether to include line numbers in the output (--line-numbers, -n)\n")
        f.write(f"lineNumbers: {str(config['lineNumbers']).lower()}\n")
        f.write("# Whether to show ignored files in the directory tree\n")
        f.write(f"showIgnoredInTree: {str(config['showIgnoredInTree']).lower()}\n")
        f.write("# Whether to show only default ignored files in the directory tree while still respecting gitignore\n")
        f.write(f"showDefaultIgnoredInTree: {str(config['showDefaultIgnoredInTree']).lower()}\n")
        if not isGlobal:
            f.write("# Previously selected files (when using the -s or --save flag previously)\n")

            current_previous_files = config.get('previousFiles', [])
            if isinstance(current_previous_files, list):
                # Convert the list to a comma-separated string
                current_previous_files = ','.join(current_previous_files)
            elif not isinstance(current_previous_files, str):
                # If it's not a list or a string, raise an error
                raise ValueError("Invalid type for 'previousFiles'. Expected a string or list.")

            # Now safely split the string
            split_previous_files = [f.strip() for f in current_previous_files.split(',')]

            f.write(f"previousFiles: {','.join(split_previous_files)}\n")

    if not os.path.exists(file_path):
        print(f"Created new {'global' if isGlobal else 'local'} config file at {file_path}")
    return file_path

def load_or_create_config(root_dir):
    """Load or create a configuration file in the root directory."""
    config_path = os.path.join(root_dir, PROJECT_CONFIG_FILE)
    return write_config(config_path, False)

def normalize_file_types(file_types):
    """Normalize file types to ensure they have a leading dot and are valid."""
    if file_types == "*":
        return "*"
    return [
        f".{ft.strip().lstrip('.')}" for ft in file_types.split(",") if ft.strip()
    ]

def parse_config(config_path):
    """Parse the configuration file for options and patterns."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["previousFiles"] = []

    with open(config_path, "r", encoding="utf-8") as config_file:
        for line in config_file:
            line = line.strip()
            if line and not line.startswith("#") and ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                
                if key == "previousFiles":
                    if value:  # Only split if there's a value
                        # Split on comma and filter out empty strings
                        files = [f.strip() for f in value.split(",")]
                        config["previousFiles"] = [f for f in files if f]
                elif key == "useGitIgnore":
                    config["useGitIgnore"] = value.lower() == "true"
                elif key == "includeFileTypes":
                    config["includeFileTypes"] = normalize_file_types(value)
                elif key == "excludeFileTypes":
                    config["excludeFileTypes"] = normalize_file_types(value)
                elif key == "outputFile":
                    config["outputFile"] = value
                elif key == "outputFileLocally":
                    config["outputFileLocally"] = value.lower() == "true"
                elif key == "copyToClipboard":
                    config["copyToClipboard"] = value.lower() == "true"
                elif key == "safeMode":
                    config["safeMode"] = value.lower() == "true"
                elif key == "storeFilesChosen":
                    config["storeFilesChosen"] = value.lower() == "true"
                elif key == "lineNumbers":
                    config["lineNumbers"] = value.lower() == "true"
                elif key == "showIgnoredInTree":
                    config["showIgnoredInTree"] = value.lower() == "true"
                elif key == "showDefaultIgnoredInTree":
                    config["showDefaultIgnoredInTree"] = value.lower() == "true"

    return config

def load_global_config():
    """Load global configuration from ~/.gptreerc, or create it with defaults if it doesn't exist."""
    global_config_path = os.path.expanduser("~/.gptreerc")

    result_config_path = write_config(global_config_path, isGlobal=True)
    return parse_config(result_config_path)

def save_files_to_config(config_path, selected_files, root_dir):
    """Save selected files to config file."""
    # Convert absolute paths to relative paths and ensure they're properly quoted
    relative_paths = [os.path.relpath(f, root_dir) for f in selected_files]
    
    # Read existing config
    with open(config_path, 'r') as f:
        lines = f.readlines()
    
    # Update or add previousFiles line - join with single comma, no spaces
    previous_files_line = f"previousFiles: {','.join(relative_paths)}\n"
    previous_files_found = False
    
    for i, line in enumerate(lines):
        if line.startswith("previousFiles:"):
            lines[i] = previous_files_line
            previous_files_found = True
            break
    
    if not previous_files_found:
        lines.append(previous_files_line)
    
    # Write back to config file
    with open(config_path, 'w') as f:
        f.writelines(lines)

def estimate_tokens(text):
    """Provide a rough estimate of tokens in the text (using ~4 chars per token)."""
    return len(text) // 4

def main():
    setup_autocomplete()
    parser = argparse.ArgumentParser(description="Provide LLM context for coding projects by combining project files into a single text file (or clipboard text) with directory tree structure")
    parser.add_argument("path", nargs="?", default=".", help="Root directory of the project")
    parser.add_argument("-i", "--interactive", action="store_true", help="Select files interactively")
    parser.add_argument("--ignore-gitignore", action="store_true", help="Ignore .gitignore patterns")
    parser.add_argument("--include-file-types", help="Comma-separated list of file types to include, e.g., '.py,.js' or 'py,js'. Use '*' for all types")
    parser.add_argument("--exclude-file-types", help="Comma-separated list of file types to exclude, e.g., '.log,.tmp' or 'log,tmp'")
    parser.add_argument("--output-file", help="Name of the output file")
    parser.add_argument("--output-file-locally", action="store_true", help="Save the output file in the current working directory")
    parser.add_argument("--no-config", "-nc", action="store_true", help="Disable creation or use of a configuration file")
    parser.add_argument("-c", "--copy", action="store_true", help="Copy the output to the clipboard")
    parser.add_argument("-p", "--previous", action="store_true", help="Use the previous file selection")
    parser.add_argument("-s", "--save", action="store_true", help="Save selected files to config")
    parser.add_argument("-n", "--line-numbers", action="store_true", help="Add line numbers to the output")
    parser.add_argument("--version", action="store_true", help="Returns the version of GPTree")
    parser.add_argument("--disable-safe-mode", "-dsm", action="store_true", help="Disable safe mode")
    parser.add_argument("--show-ignored-in-tree", action="store_true", help="Show ignored files in the directory tree")
    parser.add_argument("--show-default-ignored-in-tree", action="store_true", help="Show default ignored files in the directory tree (still respects gitignore)")

    args = parser.parse_args()

    if args.version:
        print(f"{CURRENT_VERSION}")
        return

    # If arguments are not provided, prompt the user for input
    path = args.path if args.path != "." else prompt_user_input("Enter the root directory of the project", ".")

    # Load global configuration first
    config = load_global_config()

    # Load directory-level configuration unless --no-config is specified
    if not args.no_config:
        config_path = load_or_create_config(path)
        directory_config = parse_config(config_path)
        config.update(directory_config)

    # Override with CLI arguments if provided
    if args.include_file_types:
        config["includeFileTypes"] = normalize_file_types(args.include_file_types)
    if args.exclude_file_types:
        config["excludeFileTypes"] = normalize_file_types(args.exclude_file_types)
    if args.output_file:
        config["outputFile"] = args.output_file
    if args.output_file_locally:
        config["outputFileLocally"] = True
    if args.save:
        config["storeFilesChosen"] = True
    if args.line_numbers:
        config["lineNumbers"] = True
    if args.disable_safe_mode:
        config["safeMode"] = False
    if args.show_ignored_in_tree:
        config["showIgnoredInTree"] = True
    if args.show_default_ignored_in_tree:
        config["showDefaultIgnoredInTree"] = True

    # Determine output file path
    output_file = config["outputFile"]
    if not config["outputFileLocally"]:
        output_file = os.path.join(path, output_file)

    # Determine whether to use .gitignore based on config and CLI arguments
    use_gitignore = not args.ignore_gitignore and config["useGitIgnore"]

    try:
        print(f"Combining files in {path} into {output_file}...")
        
        previous_files = None
        if args.previous and not args.no_config:
            previous_files = config.get("previousFiles", [])
            if not previous_files:
                print("No previous file selection found.")
                return
        
        combined_content, selected_files = combine_files_with_structure(
            path,
            use_gitignore,
            interactive=args.interactive,
            previous_files=previous_files,
            safe_mode=config["safeMode"],
            line_numbers=config["lineNumbers"],
            show_ignored_in_tree=config["showIgnoredInTree"], 
            show_default_ignored_in_tree=config["showDefaultIgnoredInTree"]
        )

        # Add token estimation
        estimated_tokens = estimate_tokens(combined_content)
        print(f"Estimated tokens: {estimated_tokens:,}")
        
    except SystemExit as e:
        print(str(e))
        return

    # Save to file
    save_to_file(output_file, combined_content)

    # Copy to clipboard if requested
    if args.copy or config.get("copyToClipboard", False):
        copy_to_clipboard(combined_content)

    # Save selected files if requested
    if config["storeFilesChosen"] and not args.no_config and not args.previous:
        config_path = os.path.join(path, PROJECT_CONFIG_FILE)
        save_files_to_config(config_path, selected_files, path)

    print(f"Done! Combined content saved to {output_file}.")

if __name__ == "__main__":
    main()
