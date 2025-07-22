import os
import copy

# Configuration constants
CONFIG_VERSION = 3  # Increment this when config structure changes
PROJECT_CONFIG_FILE = '.gptree_config'
OUTPUT_FILE = 'gptree_output.txt'

DEFAULT_CONFIG = {
    "version": CONFIG_VERSION,
    "useGitIgnore": True,
    "includeFileTypes": "*",        # Primary: simple file extensions
    "excludeFileTypes": [],         # Primary: simple file extensions  
    "includePatterns": [],          # Advanced: glob patterns (optional)
    "excludePatterns": [],          # Advanced: glob patterns (optional)
    "outputFile": OUTPUT_FILE,
    "outputFileLocally": True,
    "copyToClipboard": False,
    "safeMode": True,
    "storeFilesChosen": True,
    "lineNumbers": False,
    "showIgnoredInTree": False,
    "showDefaultIgnoredInTree": False,
}


def normalize_file_types(file_types):
    """Normalize file types to ensure they have a leading dot and are valid."""
    if file_types == "*":
        return "*"
    return [
        f".{ft.strip().lstrip('.')}" for ft in file_types.split(",") if ft.strip()
    ]


def normalize_patterns(patterns):
    """Normalize glob patterns to ensure they are properly formatted."""
    if isinstance(patterns, str):
        if not patterns.strip():  # Empty string
            return []
        # Split comma-separated patterns and strip whitespace
        patterns = [p.strip() for p in patterns.split(",") if p.strip()]
    
    if not isinstance(patterns, list):
        return []
    
    # Remove empty patterns
    return [p for p in patterns if p.strip()]


def file_types_to_patterns(file_types):
    """Convert file types to glob patterns."""
    if file_types == "*":
        return ["*"]
    if isinstance(file_types, str):
        if not file_types.strip():
            return ["*"]
        file_types = [ft.strip() for ft in file_types.split(",") if ft.strip()]
    if isinstance(file_types, list):
        return [f"**/*{ft}" if ft.startswith('.') else f"**/*.{ft}" for ft in file_types]
    return ["*"]


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
        elif config["version"] == 2:
            # Migrate from version 2 to 3 - Add patterns as advanced feature
            # Keep existing file types as-is (don't auto-convert)
            config["includePatterns"] = []
            config["excludePatterns"] = []
            config["version"] = 3
            print(f"Migrated {'global' if is_global else 'local'} config from version 2 to 3 (added pattern support)")
        # Add more elif blocks here for future versions

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
        f.write("# File types to include (e.g., .py,.js) - use * for all types\n")
        f.write(f"includeFileTypes: {config['includeFileTypes']}\n")
        f.write("# File types to exclude (e.g., .log,.tmp)\n")
        f.write(f"excludeFileTypes: {','.join(config['excludeFileTypes']) if isinstance(config['excludeFileTypes'], list) else config['excludeFileTypes']}\n")
        f.write("# Advanced: Glob patterns to include (e.g., src/**/*.py,**/*.js) - overrides includeFileTypes if specified\n")
        f.write(f"includePatterns: {','.join(config['includePatterns']) if isinstance(config['includePatterns'], list) else config['includePatterns']}\n")
        f.write("# Advanced: Glob patterns to exclude (e.g., **/tests/**,**/*.log) - combined with excludeFileTypes\n")
        f.write(f"excludePatterns: {','.join(config['excludePatterns']) if isinstance(config['excludePatterns'], list) else config['excludePatterns']}\n")
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
                elif key == "includePatterns":
                    config["includePatterns"] = normalize_patterns(value)
                elif key == "excludePatterns":
                    config["excludePatterns"] = normalize_patterns(value)
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