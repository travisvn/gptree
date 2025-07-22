import os
import tempfile
import pytest
import pathspec
from unittest.mock import patch, mock_open, MagicMock

from cli_tool_gptree.builder import (
    generate_tree_structure, load_gitignore, is_ignored, add_line_numbers,
    combine_files_with_structure, save_to_file, copy_to_clipboard, estimate_tokens,
    create_pattern_spec, matches_patterns, DEFAULT_IGNORES, SAFE_MODE_MAX_FILES, SAFE_MODE_MAX_LENGTH
)


class TestCreatePatternSpec:
    """Test pathspec creation from glob patterns."""

    def test_create_pattern_spec_none_patterns(self):
        """Test pattern spec creation with None patterns."""
        result = create_pattern_spec(None)
        assert result is None

    def test_create_pattern_spec_asterisk_pattern(self):
        """Test pattern spec creation with asterisk pattern."""
        result = create_pattern_spec(["*"])
        assert result is None

    def test_create_pattern_spec_valid_patterns(self):
        """Test pattern spec creation with valid patterns."""
        patterns = ["src/**/*.py", "**/*.js"]
        result = create_pattern_spec(patterns)
        assert result is not None
        assert isinstance(result, pathspec.PathSpec)

    def test_create_pattern_spec_empty_list(self):
        """Test pattern spec creation with empty list."""
        result = create_pattern_spec([])
        assert result is None


class TestMatchesPatterns:
    """Test pattern matching functionality."""

    def test_matches_patterns_none_spec(self):
        """Test pattern matching with None spec (should match all)."""
        result = matches_patterns("/path/to/file.py", "/project", None)
        assert result is True

    def test_matches_patterns_valid_match(self):
        """Test pattern matching with valid match."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "src", "main.py")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern, ["src/**/*.py"]
            )
            
            result = matches_patterns(file_path, temp_dir, spec)
            assert result is True

    def test_matches_patterns_no_match(self):
        """Test pattern matching with no match."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "src", "main.js")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern, ["**/*.py"]
            )
            
            result = matches_patterns(file_path, temp_dir, spec)
            assert result is False


class TestGenerateTreeStructure:
    """Test tree structure generation functionality."""

    def test_generate_tree_structure_simple(self):
        """Test tree generation with a simple directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test structure
            os.makedirs(os.path.join(temp_dir, "subdir"))
            with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
                f.write("content1")
            with open(os.path.join(temp_dir, "subdir", "file2.txt"), "w") as f:
                f.write("content2")
            
            tree, files = generate_tree_structure(temp_dir, None)
            
            assert "." in tree
            assert "├── file1.txt" in tree
            assert "└── subdir/" in tree
            assert "    └── file2.txt" in tree
            assert len(files) == 2

    def test_generate_tree_structure_with_gitignore(self):
        """Test tree generation respecting gitignore patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test structure
            with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
                f.write("content1")
            with open(os.path.join(temp_dir, "ignored.log"), "w") as f:
                f.write("ignored content")
            
            # Create mock gitignore spec
            gitignore_spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern, ["*.log"]
            )
            
            tree, files = generate_tree_structure(temp_dir, gitignore_spec)
            
            assert "file1.txt" in tree
            assert "ignored.log" not in tree
            assert len(files) == 1

    def test_generate_tree_structure_with_include_patterns(self):
        """Test tree generation with include patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test structure
            with open(os.path.join(temp_dir, "file1.py"), "w") as f:
                f.write("python content")
            with open(os.path.join(temp_dir, "file2.js"), "w") as f:
                f.write("javascript content")
            with open(os.path.join(temp_dir, "file3.txt"), "w") as f:
                f.write("text content")
            
            # Only include Python files
            include_patterns = ["**/*.py"]
            tree, files = generate_tree_structure(
                temp_dir, None, include_patterns=include_patterns
            )
            
            assert "file1.py" in tree
            assert "file2.js" not in tree
            assert "file3.txt" not in tree
            assert len(files) == 1

    def test_generate_tree_structure_with_exclude_patterns(self):
        """Test tree generation with exclude patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test structure
            with open(os.path.join(temp_dir, "file1.py"), "w") as f:
                f.write("python content")
            with open(os.path.join(temp_dir, "file2.js"), "w") as f:
                f.write("javascript content")
            with open(os.path.join(temp_dir, "test.log"), "w") as f:
                f.write("log content")
            
            # Exclude log files
            exclude_patterns = ["**/*.log"]
            tree, files = generate_tree_structure(
                temp_dir, None, exclude_patterns=exclude_patterns
            )
            
            assert "file1.py" in tree
            assert "file2.js" in tree
            assert "test.log" not in tree
            assert len(files) == 2

    def test_generate_tree_structure_with_complex_patterns(self):
        """Test tree generation with complex include/exclude patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test structure
            src_dir = os.path.join(temp_dir, "src")
            tests_dir = os.path.join(temp_dir, "tests")
            os.makedirs(src_dir)
            os.makedirs(tests_dir)
            
            with open(os.path.join(src_dir, "main.py"), "w") as f:
                f.write("main python")
            with open(os.path.join(tests_dir, "test_main.py"), "w") as f:
                f.write("test python")
            with open(os.path.join(temp_dir, "README.md"), "w") as f:
                f.write("readme")
            
            # Include all Python files but exclude tests
            include_patterns = ["**/*.py"]
            exclude_patterns = ["**/tests/**"]
            
            tree, files = generate_tree_structure(
                temp_dir, None, 
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns
            )
            
            assert "src/" in tree
            assert "main.py" in tree
            assert "tests/" not in tree or "test_main.py" not in tree
            assert "README.md" not in tree
            assert len(files) == 1

    def test_generate_tree_structure_show_ignored(self):
        """Test tree generation showing ignored files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test structure including default ignored
            os.makedirs(os.path.join(temp_dir, ".git"))
            with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
                f.write("content1")
            with open(os.path.join(temp_dir, ".git", "config"), "w") as f:
                f.write("git config")
            
            tree, files = generate_tree_structure(temp_dir, None, show_ignored=True)
            
            assert "file1.txt" in tree
            assert ".git/" in tree
            assert "config" in tree


class TestLoadGitignore:
    """Test gitignore loading functionality."""

    def test_load_gitignore_exists(self):
        """Test loading an existing .gitignore file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gitignore_path = os.path.join(temp_dir, ".gitignore")
            with open(gitignore_path, "w") as f:
                f.write("*.log\n__pycache__/\n")
            
            with patch('builtins.print'):  # Suppress print output
                spec = load_gitignore(temp_dir)
            
            assert spec is not None
            assert spec.match_file("test.log")
            assert spec.match_file("__pycache__/")
            assert not spec.match_file("test.txt")

    def test_load_gitignore_not_exists(self):
        """Test behavior when .gitignore doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            spec = load_gitignore(temp_dir)
            assert spec is None

    def test_load_gitignore_parent_directory(self):
        """Test loading .gitignore from parent directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create .gitignore in parent
            gitignore_path = os.path.join(temp_dir, ".gitignore")
            with open(gitignore_path, "w") as f:
                f.write("*.log\n")
            
            # Create subdirectory
            subdir = os.path.join(temp_dir, "subdir")
            os.makedirs(subdir)
            
            with patch('builtins.print'):  # Suppress print output
                spec = load_gitignore(subdir)
            
            assert spec is not None
            assert spec.match_file("test.log")


class TestIsIgnored:
    """Test file/directory ignore checking functionality."""

    def test_is_ignored_default_ignores(self):
        """Test that default ignored items are detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            git_path = os.path.join(temp_dir, ".git")
            cache_path = os.path.join(temp_dir, "__pycache__")
            
            assert is_ignored(git_path, None, temp_dir)
            assert is_ignored(cache_path, None, temp_dir)

    def test_is_ignored_gitignore_spec(self):
        """Test that gitignore patterns are respected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.log")
            
            gitignore_spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern, ["*.log"]
            )
            
            assert is_ignored(file_path, gitignore_spec, temp_dir)

    def test_is_ignored_not_ignored(self):
        """Test that non-ignored files are not flagged."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            
            gitignore_spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern, ["*.log"]
            )
            
            assert not is_ignored(file_path, gitignore_spec, temp_dir)


class TestAddLineNumbers:
    """Test line number addition functionality."""

    def test_add_line_numbers_simple(self):
        """Test adding line numbers to simple content."""
        content = "line 1\nline 2\nline 3"
        result = add_line_numbers(content)
        
        lines = result.split('\n')
        assert "   1 | line 1" in lines[0]
        assert "   2 | line 2" in lines[1]
        assert "   3 | line 3" in lines[2]

    def test_add_line_numbers_empty(self):
        """Test adding line numbers to empty content."""
        content = ""
        result = add_line_numbers(content)
        assert "   1 | " in result

    def test_add_line_numbers_single_line(self):
        """Test adding line numbers to single line."""
        content = "single line"
        result = add_line_numbers(content)
        assert "   1 | single line" in result


class TestCombineFilesWithStructure:
    """Test file combination functionality."""

    def test_combine_files_with_structure_basic(self):
        """Test basic file combination."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1_path = os.path.join(temp_dir, "file1.txt")
            file2_path = os.path.join(temp_dir, "file2.txt")
            
            with open(file1_path, "w") as f:
                f.write("content of file 1")
            with open(file2_path, "w") as f:
                f.write("content of file 2")
            
            content, selected_files = combine_files_with_structure(
                temp_dir, use_git_ignore=False, interactive=False
            )
            
            assert "# Project Directory Structure:" in content
            assert "# File: file1.txt" in content
            assert "content of file 1" in content
            assert "# File: file2.txt" in content
            assert "content of file 2" in content
            assert len(selected_files) == 2

    def test_combine_files_with_structure_with_patterns(self):
        """Test file combination with include/exclude patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            with open(os.path.join(temp_dir, "script.py"), "w") as f:
                f.write("python code")
            with open(os.path.join(temp_dir, "style.css"), "w") as f:
                f.write("css code")
            with open(os.path.join(temp_dir, "data.log"), "w") as f:
                f.write("log data")
            
            # Include only Python files, exclude log files
            include_patterns = ["**/*.py"]
            exclude_patterns = ["**/*.log"]
            
            content, selected_files = combine_files_with_structure(
                temp_dir, use_git_ignore=False, 
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns
            )
            
            assert "script.py" in content
            assert "python code" in content
            assert "style.css" not in content
            assert "data.log" not in content
            assert len(selected_files) == 1

    def test_combine_files_with_structure_safe_mode_files(self):
        """Test safe mode file count limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create more files than safe mode allows
            for i in range(SAFE_MODE_MAX_FILES + 1):
                with open(os.path.join(temp_dir, f"file{i}.txt"), "w") as f:
                    f.write(f"content {i}")
            
            with pytest.raises(SystemExit) as excinfo:
                combine_files_with_structure(
                    temp_dir, use_git_ignore=False, safe_mode=True
                )
            
            assert "Safe mode: Too many files selected" in str(excinfo.value)

    def test_combine_files_with_structure_safe_mode_size(self):
        """Test safe mode file size limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a large file that exceeds safe mode limit
            large_file_path = os.path.join(temp_dir, "large_file.txt")
            with open(large_file_path, "w") as f:
                f.write("x" * (SAFE_MODE_MAX_LENGTH + 1))
            
            with pytest.raises(SystemExit) as excinfo:
                combine_files_with_structure(
                    temp_dir, use_git_ignore=False, safe_mode=True
                )
            
            assert "Safe mode: Combined file size too large" in str(excinfo.value)

    def test_combine_files_with_structure_line_numbers(self):
        """Test file combination with line numbers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "file.txt")
            with open(file_path, "w") as f:
                f.write("line 1\nline 2")
            
            content, _ = combine_files_with_structure(
                temp_dir, use_git_ignore=False, line_numbers=True
            )
            
            assert "   1 | line 1" in content
            assert "   2 | line 2" in content

    def test_combine_files_with_structure_previous_files(self):
        """Test file combination with previous file selection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1_path = os.path.join(temp_dir, "file1.txt")
            file2_path = os.path.join(temp_dir, "file2.txt")
            
            with open(file1_path, "w") as f:
                f.write("content 1")
            with open(file2_path, "w") as f:
                f.write("content 2")
            
            # Use only file1 from previous selection
            previous_files = ["file1.txt"]
            
            content, selected_files = combine_files_with_structure(
                temp_dir, use_git_ignore=False, previous_files=previous_files
            )
            
            assert "content 1" in content
            assert "content 2" not in content
            assert len(selected_files) == 1

    def test_combine_files_with_structure_invalid_previous_files(self):
        """Test behavior with invalid previous files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            previous_files = ["nonexistent.txt"]
            
            with pytest.raises(SystemExit) as excinfo:
                combine_files_with_structure(
                    temp_dir, use_git_ignore=False, previous_files=previous_files
                )
            
            assert "No valid files found from previous selection" in str(excinfo.value)


class TestSaveToFile:
    """Test file saving functionality."""

    def test_save_to_file(self):
        """Test saving content to a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            os.unlink(temp_path)  # Remove the file so we can test creation
            content = "test content\nmultiple lines"
            
            save_to_file(temp_path, content)
            
            assert os.path.exists(temp_path)
            with open(temp_path, 'r') as f:
                saved_content = f.read()
            assert saved_content == content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestCopyToClipboard:
    """Test clipboard functionality."""

    @patch('cli_tool_gptree.builder.pyperclip.copy')
    @patch('builtins.print')
    def test_copy_to_clipboard_success(self, mock_print, mock_copy):
        """Test successful clipboard copy."""
        content = "test content"
        copy_to_clipboard(content)
        
        mock_copy.assert_called_once_with(content)
        mock_print.assert_called_once_with("Output copied to clipboard!")

    @patch('cli_tool_gptree.builder.pyperclip.copy')
    @patch('builtins.print')
    def test_copy_to_clipboard_failure(self, mock_print, mock_copy):
        """Test clipboard copy failure."""
        from cli_tool_gptree.builder import pyperclip
        mock_copy.side_effect = pyperclip.PyperclipException("Test error")
        
        content = "test content"
        copy_to_clipboard(content)
        
        mock_copy.assert_called_once_with(content)
        mock_print.assert_called_once_with("Failed to copy to clipboard: Test error")


class TestEstimateTokens:
    """Test token estimation functionality."""

    def test_estimate_tokens_simple(self):
        """Test token estimation with simple text."""
        text = "hello world test"  # 16 characters
        tokens = estimate_tokens(text)
        assert tokens == 4  # 16 / 4

    def test_estimate_tokens_empty(self):
        """Test token estimation with empty text."""
        text = ""
        tokens = estimate_tokens(text)
        assert tokens == 0

    def test_estimate_tokens_large(self):
        """Test token estimation with larger text."""
        text = "x" * 1000  # 1000 characters
        tokens = estimate_tokens(text)
        assert tokens == 250  # 1000 / 4 