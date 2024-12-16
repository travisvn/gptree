## gptree

**A CLI tool to provide LLM context for coding projects by combining project files into a single text file with a directory tree structure.**

---

### What is gptree?

When working with Large Language Models (LLMs) to continue or debug your coding projects, providing the right context is key. `gptree` simplifies this by:

1. Generating a clear **directory tree structure** of your project.
2. Combining the **contents of relevant files** into a single output text file.
3. Allowing you to **select files interactively** to fine-tune which files are included.

The resulting file can easily be copied and pasted into LLM prompts to provide the model with the necessary context to assist you effectively.

---

### Features

- 🗂 **Tree Structure**: Includes a visual directory tree of your project.
- ✅ **Smart File Selection**: Automatically excludes ignored files using `.gitignore` and common directories like `.git`, `__pycache__`, and `.vscode`.
- 🎛 **Interactive Mode**: Select or deselect files interactively using arrow keys.
- 🔧 **Configurable**: Customizable behavior via a `.combine_config` file.
- 📜 **Easy Output**: Combines all selected files into a single text file, ready to paste into an LLM prompt.

---

### Installation

#### Install via Homebrew (recommended)
Once the Homebrew tap is ready, install `gptree` with:
```bash
brew tap travisvn/gptree
brew install gptree
```

#### Install via pip
Alternatively, install `gptree` (`gptree-cli`) directly via pip:
```bash
pip install gptree-cli
```

---

### Usage

Run `gptree` in your project directory:

```bash
gptree
```

#### Options:

| Flag                    | Description                                       |
|-------------------------|---------------------------------------------------|
| `--interactive`, `-i`   | Enable interactive file selection.                |
| `path`                  | (Optional) Root directory of your project. Defaults to `.`. |

#### Example:

To interactively choose files:
```bash
gptree --interactive
```

---

### Example Output

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

---

### Configuration

You can customize `gptree` behavior using a `.combine_config` file in your project root. Example:

```yaml
# .combine_config
useGitIgnore: true
includeFileTypes: .py,.js  # Include only Python and JavaScript files
excludeFileTypes: .test    # Exclude files with .test extensions
outputFile: gptree_output.txt
outputFileLocally: true
```

---

### Contributing

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