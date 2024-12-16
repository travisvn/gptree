import os
import argparse
import readline
import pathspec
import curses

# Global list of obvious files and directories to ignore
DEFAULT_IGNORES = {".git", ".vscode", "__pycache__", ".DS_Store", ".idea"}

def generate_tree_structure(root_dir, gitignore_spec):
    """Generate a tree-like directory structure, excluding ignored files and directories."""
    tree_lines = []
    file_list = []

    for root, dirs, files in os.walk(root_dir):
        # Filter directories to skip ignored ones
        dirs[:] = [
            d for d in dirs
            if not is_ignored(os.path.join(root, d), gitignore_spec, root_dir)
        ]

        # Add the current directory to the tree
        level = root.replace(root_dir, '').count(os.sep)
        indent = '    ' * level
        tree_lines.append(f"{indent}├── {os.path.basename(root)}/")
        sub_indent = '    ' * (level + 1)

        # Filter files and add them to the tree
        for file in files:
            file_path = os.path.join(root, file)
            if is_ignored(file_path, gitignore_spec, root_dir):
                continue
            tree_lines.append(f"{sub_indent}├── {file}")
            file_list.append(file_path)

    return "\n".join(tree_lines), file_list

def load_gitignore(root_dir):
    """Load patterns from .gitignore if it exists."""
    gitignore_path = os.path.join(root_dir, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, f)
    return None

def is_ignored(file_or_dir_path, gitignore_spec, root_dir):
    """Check if a file or directory is ignored by .gitignore or default ignores."""
    # Check if it's in the default ignore list
    if any(segment in DEFAULT_IGNORES for segment in file_or_dir_path.split(os.sep)):
        return True

    # Check against .gitignore
    if gitignore_spec:
        relative_path = os.path.relpath(file_or_dir_path, root_dir)
        if gitignore_spec.match_file(relative_path):
            return True

    return False

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
            stdscr.addstr(0, 0, "Use ↑/↓ to scroll, SPACE to toggle selection, 'a' to select all, ENTER to confirm, ESC to quit")
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
            if key == curses.KEY_DOWN:
                if current_row < max_rows - 1:
                    current_row += 1
                    if current_row >= offset + display_limit:
                        offset += 1
            elif key == curses.KEY_UP:
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

def combine_files_with_structure(root_dir, use_git_ignore, interactive=False):
    """Combine file contents with directory structure."""
    combined_content = []

    # Load .gitignore spec if enabled
    gitignore_spec = load_gitignore(root_dir) if use_git_ignore else None

    # Generate tree structure and initial file list
    tree_structure, file_list = generate_tree_structure(root_dir, gitignore_spec)

    # Add the tree structure at the top
    combined_content.append("# Project Directory Structure:")
    combined_content.append(tree_structure)
    combined_content.append("\n# BEGIN FILE CONTENTS")

    # Interactive file selection
    if interactive:
        selected_files = interactive_file_selector(file_list)
    else:
        selected_files = set(file_list)

    # Combine contents of selected files
    for file_path in selected_files:
        # Ensure file is readable in utf-8
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, OSError):
            continue

        combined_content.append(f"\n# File: {file_path}\n")
        combined_content.append(content)
        combined_content.append(f"\n# END FILE CONTENTS\n")

    return "\n".join(combined_content)

def save_to_file(output_path, content):
    """Save the combined content to a file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

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

def load_or_create_config(root_dir):
    """Load or create a configuration file in the root directory."""
    config_path = os.path.join(root_dir, ".combine_config")
    if not os.path.exists(config_path):
        print("Configuration file not found. Creating default config file...")
        with open(config_path, "w", encoding="utf-8") as config_file:
            config_file.write("# Combine Config\n")
            config_file.write("# Whether to use .gitignore\n")
            config_file.write("useGitIgnore: true\n")
            config_file.write("# File types to include (e.g., .py,.js)\n")
            config_file.write("includeFileTypes: *\n")
            config_file.write("# File types to exclude when includeFileTypes is '*'\n")
            config_file.write("excludeFileTypes: \n")
            config_file.write("# Output file name\n")
            config_file.write("outputFile: combined_code.txt\n")
            config_file.write("# Whether to output the file locally or relative to the project directory\n")
            config_file.write("outputFileLocally: true\n")
        print(f"Default config file created at {config_path}")
    return config_path

def normalize_file_types(file_types):
    """Normalize file types to ensure they have a leading dot and are valid."""
    if file_types == "*":
        return "*"
    return [
        f".{ft.strip().lstrip('.')}" for ft in file_types.split(",") if ft.strip()
    ]

def parse_config(config_path):
    """Parse the configuration file for options and patterns."""
    config = {
        "useGitIgnore": True,
        "includeFileTypes": "*",
        "excludeFileTypes": [],
        "outputFile": "combined_code.txt",
        "outputFileLocally": True
    }

    with open(config_path, "r", encoding="utf-8") as config_file:
        for line in config_file:
            line = line.strip()
            if line.startswith("useGitIgnore:"):
                config["useGitIgnore"] = line.split(":", 1)[1].strip().lower() == "true"
            elif line.startswith("includeFileTypes:"):
                config["includeFileTypes"] = normalize_file_types(line.split(":", 1)[1].strip())
            elif line.startswith("excludeFileTypes:"):
                config["excludeFileTypes"] = normalize_file_types(line.split(":", 1)[1].strip())
            elif line.startswith("outputFile:"):
                config["outputFile"] = line.split(":", 1)[1].strip()
            elif line.startswith("outputFileLocally:"):
                config["outputFileLocally"] = line.split(":", 1)[1].strip().lower() == "true"

    return config

def load_global_config():
    """Load global configuration from ~/.gptreerc, or create it with defaults if it doesn't exist."""
    global_config_path = os.path.expanduser("~/.gptreerc")

    # If the global config file doesn't exist, create it with defaults
    if not os.path.exists(global_config_path):
        print("Global configuration file not found. Creating default global config file...")
        with open(global_config_path, "w", encoding="utf-8") as global_config_file:
            global_config_file.write("# GPTree Global Config\n")
            global_config_file.write("# File types to include (e.g., .py,.js)\n")
            global_config_file.write("includeFileTypes: *\n")
            global_config_file.write("# File types to exclude\n")
            global_config_file.write("excludeFileTypes: \n")
            global_config_file.write("# Output file name\n")
            global_config_file.write("outputFile: combined_code.txt\n")
            global_config_file.write("# Whether to output the file locally\n")
            global_config_file.write("outputFileLocally: true\n")
            global_config_file.write("# Whether to use .gitignore\n")
            global_config_file.write("useGitIgnore: true\n")
        print(f"Default global config file created at {global_config_path}")

    # Parse the global config file
    return parse_config(global_config_path)

def main():
    setup_autocomplete()
    parser = argparse.ArgumentParser(description="Combine project files into a single text file with directory structure.")
    parser.add_argument("path", nargs="?", default=".", help="Root directory of the project.")
    parser.add_argument("-i", "--interactive", action="store_true", help="Select files interactively.")
    parser.add_argument("--ignore-gitignore", action="store_true", help="Ignore .gitignore patterns.")
    parser.add_argument("--include-file-types", help="Comma-separated list of file types to include, e.g., '.py,.js' or 'py,js'. Use '*' for all types.")
    parser.add_argument("--exclude-file-types", help="Comma-separated list of file types to exclude, e.g., '.log,.tmp' or 'log,tmp'.")
    parser.add_argument("--output-file", help="Name of the output file.")
    parser.add_argument("--output-file-locally", action="store_true", help="Save the output file in the current working directory.")
    parser.add_argument("--no-config", "-nc", action="store_true", help="Disable creation or use of a configuration file.")

    args = parser.parse_args()

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

    # Determine output file path
    output_file = config["outputFile"]
    if not config["outputFileLocally"]:
        output_file = os.path.join(path, output_file)

    # Determine whether to use .gitignore based on config and CLI arguments
    use_gitignore = not args.ignore_gitignore and config["useGitIgnore"]

    try:
        print(f"Combining files in {path} into {output_file}...")
        combined_content = combine_files_with_structure(path, use_gitignore, interactive=args.interactive)
    except SystemExit as e:
        print(str(e))
        return  # Exit without saving

    save_to_file(output_file, combined_content)
    print(f"Done! Combined content saved to {output_file}.")

if __name__ == "__main__":
    main()
