import os
import argparse
import readline

from .config import (
    load_global_config, load_or_create_config, parse_config, 
    save_files_to_config, normalize_file_types, normalize_patterns, 
    file_types_to_patterns, PROJECT_CONFIG_FILE
)
from .builder import combine_files_with_structure, save_to_file, copy_to_clipboard, estimate_tokens

CURRENT_VERSION = 'v1.6.0'


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


def main():
    setup_autocomplete()
    parser = argparse.ArgumentParser(description="Provide LLM context for coding projects by combining project files into a single text file (or clipboard text) with directory tree structure. Check out the new GUI version at https://gptree.dev!")
    parser.add_argument("path", nargs="?", default=None, help="Root directory of the project")
    parser.add_argument("-i", "--interactive", action="store_true", help="Select files interactively")
    parser.add_argument("--ignore-gitignore", action="store_true", help="Ignore .gitignore patterns")
    parser.add_argument("--include-file-types", help="Comma-separated list of file types to include (e.g., '.py,.js' or 'py,js'). Use '*' for all types")
    parser.add_argument("--exclude-file-types", help="Comma-separated list of file types to exclude (e.g., '.log,.tmp' or 'log,tmp')")
    parser.add_argument("--include-patterns", help="Advanced: Comma-separated list of glob patterns to include (e.g., 'src/**/*.py,**/*.js'). Overrides include-file-types if specified")
    parser.add_argument("--exclude-patterns", help="Advanced: Comma-separated list of glob patterns to exclude (e.g., '**/tests/**,**/*.log'). Combined with exclude-file-types")
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

    # Use the provided path, or prompt if no path was given
    if args.path is None:
        path = prompt_user_input("Enter the root directory of the project", ".")
    else:
        path = args.path

    # Load global configuration first
    config = load_global_config()

    # Load directory-level configuration unless --no-config is specified
    if not args.no_config:
        config_path = load_or_create_config(path)
        directory_config = parse_config(config_path)
        config.update(directory_config)

    # Override with CLI arguments if provided
    # File types (primary interface)
    if args.include_file_types:
        config["includeFileTypes"] = normalize_file_types(args.include_file_types)
    if args.exclude_file_types:
        config["excludeFileTypes"] = normalize_file_types(args.exclude_file_types)
    
    # Patterns (advanced interface) - these override file types if specified
    if args.include_patterns:
        config["includePatterns"] = normalize_patterns(args.include_patterns)
    if args.exclude_patterns:
        config["excludePatterns"] = normalize_patterns(args.exclude_patterns)
    
    # Determine final patterns to use
    # Priority: patterns > file types
    if config.get("includePatterns") and len(config["includePatterns"]) > 0:
        # Use patterns directly
        final_include_patterns = config["includePatterns"]
    else:
        # Convert file types to patterns
        final_include_patterns = file_types_to_patterns(config["includeFileTypes"])
    
    # For exclude patterns, combine both file types and patterns
    final_exclude_patterns = []
    
    # Add patterns from excludeFileTypes (converted to patterns)
    if config["excludeFileTypes"] and config["excludeFileTypes"] != []:
        final_exclude_patterns.extend(file_types_to_patterns(config["excludeFileTypes"]))
    
    # Add explicit exclude patterns
    if config.get("excludePatterns") and len(config["excludePatterns"]) > 0:
        final_exclude_patterns.extend(config["excludePatterns"])
    
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
            show_default_ignored_in_tree=config["showDefaultIgnoredInTree"],
            include_patterns=final_include_patterns,
            exclude_patterns=final_exclude_patterns
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