import os
import tempfile
import pytest
from unittest.mock import patch, mock_open

from cli_tool_gptree.config import (
    normalize_file_types, normalize_patterns, file_types_to_patterns,
    migrate_config, write_config, parse_config,
    load_global_config, save_files_to_config, CONFIG_VERSION, DEFAULT_CONFIG
)


class TestNormalizeFileTypes:
    """Test file type normalization functionality."""

    def test_normalize_file_types_with_asterisk(self):
        """Test that asterisk is returned as is."""
        result = normalize_file_types("*")
        assert result == "*"

    def test_normalize_file_types_with_dots(self):
        """Test normalization of file types with dots."""
        result = normalize_file_types(".py,.js,.txt")
        assert result == [".py", ".js", ".txt"]

    def test_normalize_file_types_without_dots(self):
        """Test normalization of file types without dots."""
        result = normalize_file_types("py,js,txt")
        assert result == [".py", ".js", ".txt"]

    def test_normalize_file_types_mixed(self):
        """Test normalization of mixed file types."""
        result = normalize_file_types(".py,js,.txt,md")
        assert result == [".py", ".js", ".txt", ".md"]

    def test_normalize_file_types_with_spaces(self):
        """Test normalization with spaces around file types."""
        result = normalize_file_types(" .py , js , .txt ")
        assert result == [".py", ".js", ".txt"]

    def test_normalize_file_types_empty_values(self):
        """Test normalization with empty values."""
        result = normalize_file_types(".py,,js,,.txt")
        assert result == [".py", ".js", ".txt"]


class TestNormalizePatterns:
    """Test glob pattern normalization functionality."""

    def test_normalize_patterns_with_comma_separated(self):
        """Test normalization of comma-separated patterns."""
        result = normalize_patterns("src/**/*.py,**/*.js,tests/**/*.txt")
        assert result == ["src/**/*.py", "**/*.js", "tests/**/*.txt"]

    def test_normalize_patterns_list_input(self):
        """Test normalization with list input."""
        result = normalize_patterns(["src/**/*.py", "**/*.js"])
        assert result == ["src/**/*.py", "**/*.js"]

    def test_normalize_patterns_with_spaces(self):
        """Test normalization with spaces around patterns."""
        result = normalize_patterns(" src/**/*.py , **/*.js , tests/**/*.txt ")
        assert result == ["src/**/*.py", "**/*.js", "tests/**/*.txt"]

    def test_normalize_patterns_empty_values(self):
        """Test normalization with empty values."""
        result = normalize_patterns("src/**/*.py,,**/*.js,,tests/**/*.txt")
        assert result == ["src/**/*.py", "**/*.js", "tests/**/*.txt"]

    def test_normalize_patterns_invalid_input(self):
        """Test normalization with invalid input."""
        result = normalize_patterns(123)  # Invalid type
        assert result == []

    def test_normalize_patterns_empty_string(self):
        """Test normalization with empty string."""
        result = normalize_patterns("")
        assert result == []


class TestFileTypesToPatterns:
    """Test file type to pattern conversion functionality."""

    def test_file_types_to_patterns_asterisk(self):
        """Test conversion of asterisk."""
        result = file_types_to_patterns("*")
        assert result == ["*"]

    def test_file_types_to_patterns_list_with_dots(self):
        """Test conversion of file types list with dots."""
        result = file_types_to_patterns([".py", ".js"])
        assert result == ["**/*.py", "**/*.js"]

    def test_file_types_to_patterns_list_without_dots(self):
        """Test conversion of file types list without dots."""
        result = file_types_to_patterns(["py", "js"])
        assert result == ["**/*.py", "**/*.js"]

    def test_file_types_to_patterns_string(self):
        """Test conversion of file types string."""
        result = file_types_to_patterns(".py,.js")
        assert result == ["**/*.py", "**/*.js"]

    def test_file_types_to_patterns_empty(self):
        """Test conversion of empty file types."""
        result = file_types_to_patterns("")
        assert result == ["*"]

    def test_file_types_to_patterns_invalid(self):
        """Test conversion of invalid file types."""
        result = file_types_to_patterns(123)
        assert result == ["*"]


class TestMigrateConfig:
    """Test configuration migration functionality."""

    def test_migrate_config_no_version(self):
        """Test migration when config has no version."""
        config = {"useGitIgnore": True}
        result = migrate_config(config, CONFIG_VERSION)
        assert result["version"] == CONFIG_VERSION
        assert "previousFiles" in result

    def test_migrate_config_version_0_to_current(self):
        """Test migration from version 0 to current."""
        config = {"version": "0", "useGitIgnore": True}
        result = migrate_config(config, CONFIG_VERSION)
        assert result["version"] == CONFIG_VERSION
        assert "previousFiles" in result
        assert "showIgnoredInTree" in result
        assert "showDefaultIgnoredInTree" in result

    def test_migrate_config_version_2_to_3_adds_patterns(self):
        """Test migration from version 2 to 3 adds pattern support without converting file types."""
        config = {
            "version": "2", 
            "useGitIgnore": True,
            "includeFileTypes": ".py,.js",
            "excludeFileTypes": ".log,.tmp"
        }
        result = migrate_config(config, CONFIG_VERSION)
        assert result["version"] == CONFIG_VERSION
        # File types should be preserved, not converted
        assert result["includeFileTypes"] == ".py,.js"
        assert result["excludeFileTypes"] == ".log,.tmp"
        # Patterns should be added as empty
        assert result["includePatterns"] == []
        assert result["excludePatterns"] == []

    def test_migrate_config_global(self):
        """Test migration for global config (no previousFiles)."""
        config = {"version": "0", "useGitIgnore": True}
        result = migrate_config(config, CONFIG_VERSION, is_global=True)
        assert result["version"] == CONFIG_VERSION
        assert "previousFiles" not in result

    def test_migrate_config_invalid_version(self):
        """Test migration with invalid version string."""
        config = {"version": "invalid", "useGitIgnore": True}
        result = migrate_config(config, CONFIG_VERSION)
        assert result["version"] == CONFIG_VERSION

    def test_migrate_config_already_current(self):
        """Test migration when config is already current version."""
        config = {"version": CONFIG_VERSION, "useGitIgnore": True}
        result = migrate_config(config, CONFIG_VERSION)
        assert result["version"] == CONFIG_VERSION


class TestWriteConfig:
    """Test configuration file writing functionality."""

    def test_write_config_new_file(self):
        """Test writing a new config file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as temp_file:
            temp_path = temp_file.name

        try:
            # Remove the file so we can test creating a new one
            os.unlink(temp_path)
            
            result_path = write_config(temp_path, isGlobal=False)
            assert result_path == temp_path
            assert os.path.exists(temp_path)
            
            # Verify the file contains expected content
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "# GPTree Local Config" in content
                assert f"version: {CONFIG_VERSION}" in content
                assert "useGitIgnore: true" in content
                assert "includeFileTypes: *" in content
                assert "excludeFileTypes:" in content
                assert "includePatterns:" in content
                assert "excludePatterns:" in content
                assert "previousFiles:" in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_config_global_file(self):
        """Test writing a global config file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as temp_file:
            temp_path = temp_file.name

        try:
            # Remove the file so we can test creating a new one
            os.unlink(temp_path)
            
            result_path = write_config(temp_path, isGlobal=True)
            assert result_path == temp_path
            
            # Verify the file contains expected content
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "# GPTree Global Config" in content
                assert "previousFiles:" not in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_write_config_existing_file(self):
        """Test updating an existing config file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as temp_file:
            temp_file.write("version: 0\nuseGitIgnore: false\n")
            temp_path = temp_file.name

        try:
            result_path = write_config(temp_path, isGlobal=False)
            assert result_path == temp_path
            
            # Verify the file was updated
            with open(temp_path, 'r') as f:
                content = f.read()
                assert f"version: {CONFIG_VERSION}" in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestParseConfig:
    """Test configuration file parsing functionality."""

    def test_parse_config_hybrid_file_types_and_patterns(self):
        """Test parsing a config file with both file types and patterns."""
        config_content = """# GPTree Config
version: 3
useGitIgnore: true
includeFileTypes: .py,.js
excludeFileTypes: .log,.tmp
includePatterns: src/**/*.ts
excludePatterns: **/tests/**
outputFile: test_output.txt
outputFileLocally: false
copyToClipboard: true
safeMode: false
storeFilesChosen: true
lineNumbers: true
showIgnoredInTree: true
showDefaultIgnoredInTree: false
previousFiles: file1.py,file2.js
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as temp_file:
            temp_file.write(config_content)
            temp_path = temp_file.name

        try:
            config = parse_config(temp_path)
            assert config["version"] == 3
            assert config["useGitIgnore"] is True
            assert config["includeFileTypes"] == [".py", ".js"]
            assert config["excludeFileTypes"] == [".log", ".tmp"]
            assert config["includePatterns"] == ["src/**/*.ts"]
            assert config["excludePatterns"] == ["**/tests/**"]
            assert config["outputFile"] == "test_output.txt"
            assert config["outputFileLocally"] is False
            assert config["copyToClipboard"] is True
            assert config["safeMode"] is False
            assert config["storeFilesChosen"] is True
            assert config["lineNumbers"] is True
            assert config["showIgnoredInTree"] is True
            assert config["showDefaultIgnoredInTree"] is False
            assert config["previousFiles"] == ["file1.py", "file2.js"]
        finally:
            os.unlink(temp_path)

    def test_parse_config_file_types_only(self):
        """Test parsing config with only file types (primary interface)."""
        config_content = """# GPTree Config
version: 3
includeFileTypes: .py,.js
excludeFileTypes: .log,.tmp
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as temp_file:
            temp_file.write(config_content)
            temp_path = temp_file.name

        try:
            config = parse_config(temp_path)
            assert config["includeFileTypes"] == [".py", ".js"]
            assert config["excludeFileTypes"] == [".log", ".tmp"]
            assert config["includePatterns"] == []  # Should be empty
            assert config["excludePatterns"] == []  # Should be empty
        finally:
            os.unlink(temp_path)

    def test_parse_config_patterns_only(self):
        """Test parsing config with only patterns (advanced interface)."""
        config_content = """# GPTree Config
version: 3
includePatterns: src/**/*.py,**/*.js
excludePatterns: **/tests/**,**/*.log
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as temp_file:
            temp_file.write(config_content)
            temp_path = temp_file.name

        try:
            config = parse_config(temp_path)
            assert config["includeFileTypes"] == "*"  # Should be default
            assert config["excludeFileTypes"] == []  # Should be default
            assert config["includePatterns"] == ["src/**/*.py", "**/*.js"]
            assert config["excludePatterns"] == ["**/tests/**", "**/*.log"]
        finally:
            os.unlink(temp_path)

    def test_parse_config_empty_patterns(self):
        """Test parsing config with empty patterns."""
        config_content = """# GPTree Config
version: 3
includeFileTypes: .py
excludeFileTypes: .log
includePatterns: 
excludePatterns:
previousFiles:
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as temp_file:
            temp_file.write(config_content)
            temp_path = temp_file.name

        try:
            config = parse_config(temp_path)
            assert config["includeFileTypes"] == [".py"]
            assert config["excludeFileTypes"] == [".log"]
            assert config["includePatterns"] == []  # Empty patterns should be empty list
            assert config["excludePatterns"] == []  # Empty patterns should be empty list
            assert config["previousFiles"] == []
        finally:
            os.unlink(temp_path)

    def test_parse_config_with_comments(self):
        """Test parsing config file with comments."""
        config_content = """# GPTree Config
# This is a comment
version: 3
# Another comment
useGitIgnore: true
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as temp_file:
            temp_file.write(config_content)
            temp_path = temp_file.name

        try:
            config = parse_config(temp_path)
            assert config["version"] == 3
            assert config["useGitIgnore"] is True
        finally:
            os.unlink(temp_path)


class TestLoadGlobalConfig:
    """Test global configuration loading functionality."""

    @patch('cli_tool_gptree.config.write_config')
    @patch('cli_tool_gptree.config.parse_config')
    @patch('os.path.expanduser')
    def test_load_global_config(self, mock_expanduser, mock_parse_config, mock_write_config):
        """Test loading global configuration."""
        mock_expanduser.return_value = "/home/user/.gptreerc"
        mock_write_config.return_value = "/home/user/.gptreerc"
        mock_parse_config.return_value = {"version": CONFIG_VERSION, "useGitIgnore": True}
        
        result = load_global_config()
        
        mock_expanduser.assert_called_once_with("~/.gptreerc")
        mock_write_config.assert_called_once_with("/home/user/.gptreerc", isGlobal=True)
        mock_parse_config.assert_called_once_with("/home/user/.gptreerc")
        assert result["version"] == CONFIG_VERSION


class TestSaveFilesToConfig:
    """Test saving selected files to config functionality."""

    def test_save_files_to_config_new_entry(self):
        """Test saving files to config when previousFiles doesn't exist."""
        config_content = """# GPTree Config
version: 3
useGitIgnore: true
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as temp_file:
            temp_file.write(config_content)
            temp_path = temp_file.name

        try:
            selected_files = ["/project/file1.py", "/project/subdir/file2.js"]
            root_dir = "/project"
            
            save_files_to_config(temp_path, selected_files, root_dir)
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "previousFiles: file1.py,subdir/file2.js" in content
        finally:
            os.unlink(temp_path)

    def test_save_files_to_config_update_existing(self):
        """Test updating existing previousFiles in config."""
        config_content = """# GPTree Config
version: 3
useGitIgnore: true
previousFiles: old_file.py
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as temp_file:
            temp_file.write(config_content)
            temp_path = temp_file.name

        try:
            selected_files = ["/project/new_file1.py", "/project/new_file2.js"]
            root_dir = "/project"
            
            save_files_to_config(temp_path, selected_files, root_dir)
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "previousFiles: new_file1.py,new_file2.js" in content
                assert "old_file.py" not in content
        finally:
            os.unlink(temp_path) 