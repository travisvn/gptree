# gptree 🌳

**A CLI tool to provide LLM context for coding projects by combining project files into a single text file with a directory tree structure.**

![GitHub stars](https://img.shields.io/github/stars/travisvn/gptree?style=social)
![PyPI - Version](https://img.shields.io/pypi/v/gptree-cli)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/travisvn/gptree/.github%2Fworkflows%2Fbuild.yml)
![GitHub Release](https://img.shields.io/github/v/release/travisvn/gptree)
![GitHub last commit](https://img.shields.io/github/last-commit/travisvn/gptree?color=red)
[![PyPI Downloads](https://static.pepy.tech/badge/gptree-cli)](https://pepy.tech/projects/gptree-cli)

## What is gptree?

When working with Large Language Models (LLMs) to continue or debug your coding projects, providing the right context is key. `gptree` simplifies this by:

1. Generating a clear **directory tree structure** of your project.
2. Combining the **contents of relevant files** into a single output text file.
3. Allowing you to **select files interactively** to fine-tune which files are included.
4. Supporting both **simple file type filtering** and **advanced glob patterns** for maximum flexibility.

The resulting file can easily be copied and pasted into LLM prompts to provide the model with the necessary context to assist you effectively.

![GPTree Demo](./demo.gif)

## Features

- 🗂 **Tree Structure**: Includes a visual directory tree of your project.
- ✅ **Smart File Selection**: Automatically excludes ignored files using `.gitignore` and common directories like `.git`, `__pycache__`, and `.vscode`.
- 📁 **Simple File Types**: Easy filtering by file extensions (e.g., `.py,.js`) for quick setup.
- 🎯 **Advanced Patterns**: Optional glob patterns for complex filtering (e.g., `src/**/*.py`, `!**/tests/**`).
- 🎛 **Interactive Mode**: Select or deselect files interactively using arrow keys, with the ability to quit immediately by pressing `ESC`.
- 🌍 **Global Config Support**: Define default settings in a `~/.gptreerc` file.
- 🔧 **Directory-Specific Config**: Customize behavior for each project via a `.gptree_config` file.
- 🎛 **CLI Overrides**: Fine-tune settings directly in the CLI for maximum control.
- 📜 **Safe Mode**: Prevent overly large files from being combined by limiting file count and total size.
- 📋 **Clipboard Support**: Automatically copy output to clipboard if desired.
- 🛠 **Custom Configuration Management**: Define configurations that are auto-detected per project or globally.

## 🆕 GPTree GUI - Now Available! 🎉

Experience gptree with a beautiful and efficient graphical interface!

- **Lightweight & Fast**: Built with Rust for optimal performance.
- **Cross-Platform**: Available on macOS, Windows, and Linux
- **Learn More & Download**: Visit [gptree.dev](https://gptree.dev)
- **Open Source**: Check out the code on [GitHub](https://github.com/travisvn/gptree-gui)

## Installation

### Install via `pipx` 📦 (Recommended)

```bash
pipx install gptree-cli
```

[How to setup pipx](https://pipx.pypa.io/)

### Install via Homebrew 🍺

```bash
brew tap travisvn/tap
brew install gptree
```

Homebrew will attempt to install `gptree` using `pip3` and will fall back to binary installation otherwise

### Install via pip 🐍

Alternatively, install `gptree` (`gptree-cli`) directly via [pip](https://pypi.org/project/gptree-cli/):

```bash
pip install gptree-cli
```

> [!NOTE]
> Performance is better when installing directly with Python (`pipx` or `pip`)
>
> The binary installation might take a second or two longer to start up (not a huge deal — just something to note)

## Usage

Run `gptree` in your project directory:

```bash
gptree
```

Or run it anywhere and define the relative path to your project

### Options

| Flag                             | Description                                                                                             |
| -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `--interactive`, `-i`            | Enable interactive file selection                                                                       |
| `--copy`, `-c`                   | Copy result directly to clipboard                                                                       |
| `--include-file-types`           | Comma-separated list of file types to include (e.g., `.py,.js` or `py,js`). Use `*` for all types       |
| `--exclude-file-types`           | Comma-separated list of file types to exclude (e.g., `.log,.tmp` or `log,tmp`)                          |
| `--include-patterns`             | **Advanced**: Glob patterns to include (e.g., `src/**/*.py,**/*.js`). Overrides include-file-types      |
| `--exclude-patterns`             | **Advanced**: Glob patterns to exclude (e.g., `**/tests/**,**/*.log`). Combined with exclude-file-types |
| `--output-file`                  | Specify the name of the output file                                                                     |
| `--output-file-locally`          | Save the output file in the current working directory                                                   |
| `--no-config`, `-nc`             | Disable creation or use of configuration files                                                          |
| `--ignore-gitignore`             | Ignore `.gitignore` patterns                                                                            |
| `--disable-safe-mode`, `-dsm`    | Disable safe mode checks for file count or size                                                         |
| `--line-numbers`, `-n`           | Add line numbers to the output                                                                          |
| `--previous`, `-p`               | Use the previously saved file selection                                                                 |
| `--save`, `-s`                   | Save the selected files to the configuration                                                            |
| `--show-ignored-in-tree`         | Show all ignored files in the directory tree                                                            |
| `--show-default-ignored-in-tree` | Show default ignored files in the tree while still respecting gitignore                                 |
| `--version`                      | Display the current version of GPTree                                                                   |
| `path`                           | (Optional) Root directory of your project. Defaults to `.`                                              |

### Examples

#### Simple File Type Filtering (Recommended for Most Users)

Include only Python and JavaScript files:

```bash
gptree --include-file-types .py,.js
```

Exclude log and temporary files:

```bash
gptree --exclude-file-types .log,.tmp,.cache
```

Include specific types while excluding others:

```bash
gptree --include-file-types .py,.js,.ts --exclude-file-types .test.py,.spec.js
```

<details>
<summary>

### Advanced Pattern Filtering (For Power Users)

</summary>

Include Python files from src directory but exclude test files:

```bash
gptree --include-patterns "src/**/*.py" --exclude-patterns "**/test_*.py"
```

Complex filtering for a web project:

```bash
gptree --include-patterns "src/**/*.{js,ts,jsx,tsx},styles/**/*.{css,scss}" --exclude-patterns "**/tests/**,**/*.test.*,**/*.spec.*"
```

Include all files except those in specific directories:

```bash
gptree --exclude-patterns "node_modules/**,venv/**,.git/**"
```

#### Hybrid Approach (Best of Both Worlds)

Use file types as primary filter with additional pattern exclusions:

```bash
gptree --include-file-types .py,.js --exclude-patterns "**/tests/**,**/node_modules/**"
```

> **Note**: When both file types and patterns are specified for includes, patterns take precedence. For excludes, both file types and patterns are combined.

#### Interactive Mode and Configuration

Interactive file selection with pre-filtered files:

```bash
gptree --interactive --include-file-types .py,.js
```

Save current selection to config:

```bash
gptree --interactive --save
```

Re-use previously saved file selections and copy to clipboard:

```bash
gptree --previous --copy
```

## File Filtering: Simple vs Advanced

GPTree offers two approaches for file filtering to accommodate different user needs:

### 🎯 Simple File Types (Recommended)

**Use when**: You want to include/exclude files by extension quickly and easily.

```bash
# Quick and easy - include Python and JavaScript files
gptree --include-file-types .py,.js

# Exclude common unwanted files
gptree --exclude-file-types .log,.tmp,.pyc
```

**Config Example**:

```yaml
includeFileTypes: .py,.js,.ts
excludeFileTypes: .log,.tmp
```

### 🚀 Advanced Glob Patterns

**Use when**: You need precise control over directory structure and complex filtering.

```bash
# Advanced - include specific directory patterns
gptree --include-patterns "src/**/*.py,tests/**/*.py" --exclude-patterns "**/conftest.py"
```

**Config Example**:

```yaml
includePatterns: src/**/*.py,**/*.js
excludePatterns: **/tests/**,**/*.log
```

### 🔄 Hybrid Usage

You can combine both approaches! File types provide the base filter, while patterns add advanced rules:

```bash
# Use file types as base, patterns for advanced exclusions
gptree --include-file-types .py,.js --exclude-patterns "**/node_modules/**,**/tests/**"
```

### Pattern Syntax Reference

| Pattern        | Description                                           |
| -------------- | ----------------------------------------------------- |
| `*.py`         | Files ending in `.py` in current directory            |
| `**/*.py`      | All `.py` files recursively                           |
| `src/**/*.js`  | All `.js` files in `src` directory tree               |
| `**/tests/**`  | All files in any `tests` directory                    |
| `**/*.{js,ts}` | All JavaScript and TypeScript files                   |
| `!**/tests/**` | Exclude any `tests` directories (in exclude patterns) |

</details>

## Configuration

### Global Config (`~/.gptreerc`)

Define your global defaults in `~/.gptreerc` to avoid repetitive setup across projects. Example:

```yaml
# ~/.gptreerc
version: 3
useGitIgnore: true
includeFileTypes: .py,.js # Simple file types for quick filtering
excludeFileTypes: .log,.tmp # Exclude unwanted file types
includePatterns: # Advanced patterns (empty = use file types)
excludePatterns: **/node_modules/**,**/__pycache__/** # Advanced exclusions
outputFile: gptree_output.txt
outputFileLocally: true
copyToClipboard: false
safeMode: true
lineNumbers: false
storeFilesChosen: true
showIgnoredInTree: false
showDefaultIgnoredInTree: false
```

This file is automatically created with default settings if it doesn't exist.

### Directory Config (`.gptree_config`)

Customize settings for a specific project by adding a `.gptree_config` file to your project root. Example:

```yaml
# .gptree_config
version: 3
useGitIgnore: false
includeFileTypes: .py,.js # Primary file type filtering
excludeFileTypes: .pyc,.log # Exclude file types
includePatterns: # Empty = use file types above
excludePatterns: **/tests/**,**/node_modules/** # Additional pattern exclusions
outputFile: project_context.txt
outputFileLocally: false
copyToClipboard: true
safeMode: false
lineNumbers: false
storeFilesChosen: false
showIgnoredInTree: false
showDefaultIgnoredInTree: true
```

### Configuration Precedence

Settings are applied in the following order (highest to lowest precedence):

1. **CLI Arguments**: Always override other settings.
2. **Directory Config**: Project-specific settings in `.gptree_config`.
3. **Global Config**: User-defined defaults in `~/.gptreerc`.
4. **Programmed Defaults**: Built-in defaults used if no other settings are provided.

### How File Types and Patterns Work Together

1. **Include Logic**: If `includePatterns` is specified and non-empty, it overrides `includeFileTypes`. Otherwise, `includeFileTypes` is converted to patterns internally.

2. **Exclude Logic**: Both `excludeFileTypes` and `excludePatterns` are combined - files matching either will be excluded.

3. **Migration**: Existing configurations are automatically preserved - no forced conversion from file types to patterns.

## Safe Mode

To prevent overly large files from being combined, Safe Mode restricts:

- The **total number of files** (default: 30).
- The **combined file size** (default: ~25k tokens, ~100,000 bytes).

Override Safe Mode with `--disable-safe-mode`.

## Interactive Mode

In interactive mode, use the following controls:

| Key       | Action                               |
| --------- | ------------------------------------ |
| `↑/↓/j/k` | Navigate the file list               |
| `SPACE`   | Toggle selection of the current file |
| `a`       | Select or deselect all files         |
| `ENTER`   | Confirm the selection and proceed    |
| `ESC`     | Quit the process immediately         |

## Contributing

Contributions are welcome! Please fork the repository and create a pull request for any improvements.

## License

This project is licensed under GNU General Public License v3.0 (GPL-3.0).
