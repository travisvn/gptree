# gptree

**A CLI tool to provide LLM context for coding projects by combining project files into a single text file with a directory tree structure.**

![GitHub stars](https://img.shields.io/github/stars/travisvn/gptree?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/travisvn/gptree)
![GitHub language count](https://img.shields.io/github/languages/count/travisvn/gptree)
![GitHub top language](https://img.shields.io/github/languages/top/travisvn/gptree)
![GitHub last commit](https://img.shields.io/github/last-commit/travisvn/gptree?color=red)
![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Ftravisvn%2Fgptree&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)

## What is gptree?

When working with Large Language Models (LLMs) to continue or debug your coding projects, providing the right context is key. `gptree` simplifies this by:

1. Generating a clear **directory tree structure** of your project.
2. Combining the **contents of relevant files** into a single output text file.
3. Allowing you to **select files interactively** to fine-tune which files are included.

The resulting file can easily be copied and pasted into LLM prompts to provide the model with the necessary context to assist you effectively.

![GPTree Demo](./demo.gif)

## Features

- 🗂 **Tree Structure**: Includes a visual directory tree of your project.
- ✅ **Smart File Selection**: Automatically excludes ignored files using `.gitignore` and common directories like `.git`, `__pycache__`, and `.vscode`.
- 🎛 **Interactive Mode**: Select or deselect files interactively using arrow keys, with the ability to quit immediately by pressing `ESC`.
- 🌍 **Global Config Support**: Define default settings in a `~/.gptreerc` file.
- 🔧 **Directory-Specific Config**: Customize behavior for each project via a `.combine_config` file.
- 🎛 **CLI Overrides**: Fine-tune settings directly in the CLI for maximum control.
- 📜 **Easy Output**: Combines all selected files into a single text file, ready to paste into an LLM prompt _or_ have the output automatically copied to clipboard.

## Installation

### Install via Homebrew (recommended)
Once the Homebrew tap is ready, install `gptree` with:
```bash
brew tap travisvn/gptree
brew install gptree
```

### Install via pip
Alternatively, install `gptree` (`gptree-cli`) directly via pip:
```bash
pip install gptree-cli
```

## Usage

Run `gptree` in your project directory:

```bash
gptree
```

### Options:

| Flag                        | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| `--interactive`, `-i`       | Enable interactive file selection.                                          |
| `--copy`, `-c`              | Copy result directly to clipboard.                                          |
| `--include-file-types`      | Comma-separated list of file types to include (e.g., `.py,.js` or `py,js`). Use `*` for all types. |
| `--exclude-file-types`      | Comma-separated list of file types to exclude (e.g., `.log,.tmp` or `log,tmp`). |
| `--output-file`             | Specify the name of the output file.                                        |
| `--output-file-locally`     | Save the output file in the current working directory.                      |
| `--no-config`, `-nc`        | Disable creation or use of configuration files.                            |
| `--ignore-gitignore`        | Ignore `.gitignore` patterns.                                               |
| `path`                      | (Optional) Root directory of your project. Defaults to `.`.                |

### Example:

Interactive file selection with custom file types:
```bash
gptree --interactive --include-file-types '.py,.js'
```

Disable configuration files:
```bash
gptree --no-config
```

## Example Output

Running `gptree` generates a file like this:

```text
# Project Directory Structure:
├── src/
    ├── main.py
    ├── utils.py
├── .gitignore
├── README.md
├── requirements.txt

# BEGIN FILE CONTENTS

# File: src/main.py
def main():
    print("Hello, world!")

# File: src/utils.py
def add(a, b):
    return a + b

# END FILE CONTENTS
```

## Configuration

### Global Config (`~/.gptreerc`)

Define your global defaults in `~/.gptreerc` to avoid repetitive setup across projects. Example:

```yaml
# ~/.gptreerc
useGitIgnore: true
includeFileTypes: .py,.js  # Include only Python and JavaScript files
excludeFileTypes: .log,.tmp  # Exclude log and temporary files
outputFile: default_combined.txt
outputFileLocally: true
copyToClipboard: false
```

This file is automatically created with default settings if it doesn't exist.

### Directory Config (`.combine_config`)

Customize settings for a specific project by adding a `.combine_config` file to your project root. Example:

```yaml
# .combine_config
useGitIgnore: false
includeFileTypes: *  # Include all file types
excludeFileTypes: .test  # Exclude test files
outputFile: project_combined.txt
outputFileLocally: false
copyToClipboard: true
```

### Configuration Precedence

Settings are applied in the following order (highest to lowest precedence):
1. **CLI Arguments**: Always override other settings.
2. **Directory Config**: Project-specific settings in `.combine_config`.
3. **Global Config**: User-defined defaults in `~/.gptreerc`.
4. **Programmed Defaults**: Built-in defaults used if no other settings are provided.

## Interactive Mode

In interactive mode, use the following controls:

| Key         | Action                              |
|-------------|-------------------------------------|
| `↑/↓`       | Navigate the file list.            |
| `SPACE`     | Toggle selection of the current file. |
| `a`         | Select or deselect all files.      |
| `ENTER`     | Confirm the selection and proceed. |
| `ESC`       | Quit the process immediately.      |

## Contributing

1. Fork this repository.
2. Clone your fork and create a new branch:
   ```bash
   git clone https://github.com/travisvn/gptree.git
   cd gptree
   git checkout -b feature-name
   ```
3. Submit a pull request with your changes.

---

### License

This project is licensed under the MIT License.
