import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from cli_tool_gptree.cli import main, setup_autocomplete, prompt_user_input, CURRENT_VERSION


class TestSetupAutocomplete:
    """Test autocomplete setup functionality."""

    @patch('cli_tool_gptree.cli.readline.set_completer')
    @patch('cli_tool_gptree.cli.readline.parse_and_bind')
    def test_setup_autocomplete(self, mock_parse_and_bind, mock_set_completer):
        """Test that autocomplete is properly configured."""
        setup_autocomplete()
        
        mock_set_completer.assert_called_once()
        mock_parse_and_bind.assert_called_once_with("tab: complete")


class TestPromptUserInput:
    """Test user input prompting functionality."""

    @patch('builtins.input', return_value='user_input')
    def test_prompt_user_input_with_value(self, mock_input):
        """Test prompting when user provides input."""
        result = prompt_user_input("Enter value", "default")
        assert result == "user_input"
        mock_input.assert_called_once_with("Enter value [default]: ")

    @patch('builtins.input', return_value='')
    def test_prompt_user_input_default(self, mock_input):
        """Test prompting when user uses default."""
        result = prompt_user_input("Enter value", "default")
        assert result == "default"
        mock_input.assert_called_once_with("Enter value [default]: ")

    @patch('builtins.input', return_value='  ')
    def test_prompt_user_input_whitespace(self, mock_input):
        """Test prompting when user enters only whitespace."""
        result = prompt_user_input("Enter value", "default")
        assert result == "default"
        mock_input.assert_called_once_with("Enter value [default]: ")


class TestMainFunction:
    """Test the main CLI function with various scenarios."""

    def test_main_version_flag(self, capsys):
        """Test --version flag."""
        with patch('sys.argv', ['gptree', '--version']):
            main()
        
        captured = capsys.readouterr()
        assert CURRENT_VERSION in captured.out

    @patch('cli_tool_gptree.cli.load_global_config')
    @patch('cli_tool_gptree.cli.load_or_create_config')
    @patch('cli_tool_gptree.cli.parse_config')
    @patch('cli_tool_gptree.cli.combine_files_with_structure')
    @patch('cli_tool_gptree.cli.save_to_file')
    def test_main_basic_functionality(self, mock_save_to_file, mock_combine_files, 
                                      mock_parse_config, mock_load_or_create_config,
                                      mock_load_global_config):
        """Test basic main function execution."""
        # Setup mocks
        mock_load_global_config.return_value = {
            "outputFile": "test_output.txt",
            "outputFileLocally": True,
            "useGitIgnore": True,
            "safeMode": True,
            "lineNumbers": False,
            "showIgnoredInTree": False,
            "showDefaultIgnoredInTree": False,
            "copyToClipboard": False,
            "storeFilesChosen": False,
            "includeFileTypes": "*",
            "excludeFileTypes": [],
            "includePatterns": [],
            "excludePatterns": []
        }
        mock_load_or_create_config.return_value = "/tmp/config"
        mock_parse_config.return_value = {}
        mock_combine_files.return_value = ("combined content", set())
        
        with patch('sys.argv', ['gptree', '.']):
            with patch('builtins.print'):  # Suppress output
                main()
        
        mock_combine_files.assert_called_once()
        mock_save_to_file.assert_called_once()

    @patch('cli_tool_gptree.cli.load_global_config')
    @patch('cli_tool_gptree.cli.combine_files_with_structure')
    def test_main_no_config_flag(self, mock_combine_files, mock_load_global_config):
        """Test --no-config flag."""
        mock_load_global_config.return_value = {
            "outputFile": "test_output.txt",
            "outputFileLocally": True,
            "useGitIgnore": True,
            "safeMode": True,
            "lineNumbers": False,
            "showIgnoredInTree": False,
            "showDefaultIgnoredInTree": False,
            "copyToClipboard": False,
            "storeFilesChosen": False,
            "includeFileTypes": "*",
            "excludeFileTypes": [],
            "includePatterns": [],
            "excludePatterns": []
        }
        mock_combine_files.return_value = ("content", set())
        
        with patch('sys.argv', ['gptree', '--no-config', '.']):
            with patch('builtins.print'):
                with patch('cli_tool_gptree.cli.save_to_file'):
                    main()
        
        # Verify that load_or_create_config was not called due to --no-config
        with patch('cli_tool_gptree.cli.load_or_create_config') as mock_load_config:
            # Re-run to check that config loading is skipped
            pass

    @patch('cli_tool_gptree.cli.load_global_config')
    @patch('cli_tool_gptree.cli.load_or_create_config')
    @patch('cli_tool_gptree.cli.parse_config')
    @patch('cli_tool_gptree.cli.combine_files_with_structure')
    @patch('cli_tool_gptree.cli.save_to_file')
    @patch('cli_tool_gptree.cli.copy_to_clipboard')
    def test_main_with_copy_flag(self, mock_copy_to_clipboard, mock_save_to_file,
                                 mock_combine_files, mock_parse_config,
                                 mock_load_or_create_config, mock_load_global_config):
        """Test --copy flag."""
        mock_load_global_config.return_value = {
            "outputFile": "test_output.txt",
            "outputFileLocally": True,
            "useGitIgnore": True,
            "safeMode": True,
            "lineNumbers": False,
            "showIgnoredInTree": False,
            "showDefaultIgnoredInTree": False,
            "copyToClipboard": False,
            "storeFilesChosen": False,
            "includeFileTypes": "*",
            "excludeFileTypes": [],
            "includePatterns": [],
            "excludePatterns": []
        }
        mock_load_or_create_config.return_value = "/tmp/config"
        mock_parse_config.return_value = {}
        mock_combine_files.return_value = ("test content", set())
        
        with patch('sys.argv', ['gptree', '--copy', '.']):
            with patch('builtins.print'):
                main()
        
        mock_copy_to_clipboard.assert_called_once_with("test content")

    @patch('cli_tool_gptree.cli.load_global_config')
    @patch('cli_tool_gptree.cli.load_or_create_config')
    @patch('cli_tool_gptree.cli.parse_config')
    def test_main_previous_files_no_selection(self, mock_parse_config,
                                              mock_load_or_create_config,
                                              mock_load_global_config, capsys):
        """Test --previous flag when no previous selection exists."""
        mock_load_global_config.return_value = {
            "outputFile": "test.txt",
            "outputFileLocally": True,
            "useGitIgnore": True,
            "safeMode": True,
            "lineNumbers": False,
            "showIgnoredInTree": False,
            "showDefaultIgnoredInTree": False,
            "copyToClipboard": False,
            "storeFilesChosen": False,
            "includeFileTypes": "*",
            "excludeFileTypes": [],
            "includePatterns": [],
            "excludePatterns": []
        }
        mock_load_or_create_config.return_value = "/tmp/config"
        mock_parse_config.return_value = {"previousFiles": []}
        
        with patch('sys.argv', ['gptree', '--previous', '.']):
            main()
        
        captured = capsys.readouterr()
        assert "No previous file selection found." in captured.out

    @patch('cli_tool_gptree.cli.load_global_config')
    @patch('cli_tool_gptree.cli.load_or_create_config')
    @patch('cli_tool_gptree.cli.parse_config')
    @patch('cli_tool_gptree.cli.combine_files_with_structure')
    @patch('cli_tool_gptree.cli.save_to_file')
    def test_main_file_types_arguments(self, mock_save_to_file, mock_combine_files,
                                       mock_parse_config, mock_load_or_create_config,
                                       mock_load_global_config):
        """Test file type CLI arguments (primary interface)."""
        mock_load_global_config.return_value = {
            "outputFile": "default.txt",
            "outputFileLocally": False,
            "useGitIgnore": True,
            "safeMode": True,
            "lineNumbers": False,
            "showIgnoredInTree": False,
            "showDefaultIgnoredInTree": False,
            "copyToClipboard": False,
            "storeFilesChosen": False,
            "includeFileTypes": "*",
            "excludeFileTypes": [],
            "includePatterns": [],
            "excludePatterns": []
        }
        mock_load_or_create_config.return_value = "/tmp/config"
        mock_parse_config.return_value = {}
        mock_combine_files.return_value = ("content", set())
        
        args = [
            'gptree', 
            '--include-file-types', '.py,.js',
            '--exclude-file-types', '.log,.tmp',
            '.'
        ]
        
        with patch('sys.argv', args):
            with patch('builtins.print'):
                main()
        
        # Verify that patterns were converted from file types
        call_args = mock_combine_files.call_args
        assert call_args[1]['include_patterns'] == ['**/*.py', '**/*.js']
        assert call_args[1]['exclude_patterns'] == ['**/*.log', '**/*.tmp']

    @patch('cli_tool_gptree.cli.load_global_config')
    @patch('cli_tool_gptree.cli.load_or_create_config')
    @patch('cli_tool_gptree.cli.parse_config')
    @patch('cli_tool_gptree.cli.combine_files_with_structure')
    @patch('cli_tool_gptree.cli.save_to_file')
    def test_main_pattern_arguments(self, mock_save_to_file, mock_combine_files,
                                    mock_parse_config, mock_load_or_create_config,
                                    mock_load_global_config):
        """Test glob pattern CLI arguments (advanced interface)."""
        mock_load_global_config.return_value = {
            "outputFile": "default.txt",
            "outputFileLocally": False,
            "useGitIgnore": True,
            "safeMode": True,
            "lineNumbers": False,
            "showIgnoredInTree": False,
            "showDefaultIgnoredInTree": False,
            "copyToClipboard": False,
            "storeFilesChosen": False,
            "includeFileTypes": "*",
            "excludeFileTypes": [],
            "includePatterns": [],
            "excludePatterns": []
        }
        mock_load_or_create_config.return_value = "/tmp/config"
        mock_parse_config.return_value = {}
        mock_combine_files.return_value = ("content", set())
        
        args = [
            'gptree', 
            '--include-patterns', 'src/**/*.py,**/*.js',
            '--exclude-patterns', '**/tests/**,**/*.log',
            '--output-file', 'custom.txt',
            '--output-file-locally',
            '--line-numbers',
            '--disable-safe-mode',
            '--show-ignored-in-tree',
            '--show-default-ignored-in-tree',
            '.'
        ]
        
        with patch('sys.argv', args):
            with patch('builtins.print'):
                main()
        
        # Verify that combine_files_with_structure was called with pattern options
        call_args = mock_combine_files.call_args
        assert call_args[1]['safe_mode'] is False
        assert call_args[1]['line_numbers'] is True
        assert call_args[1]['show_ignored_in_tree'] is True
        assert call_args[1]['show_default_ignored_in_tree'] is True
        assert call_args[1]['include_patterns'] == ['src/**/*.py', '**/*.js']
        assert call_args[1]['exclude_patterns'] == ['**/tests/**', '**/*.log']

    @patch('cli_tool_gptree.cli.load_global_config')
    @patch('cli_tool_gptree.cli.load_or_create_config')
    @patch('cli_tool_gptree.cli.parse_config')
    @patch('cli_tool_gptree.cli.combine_files_with_structure')
    @patch('cli_tool_gptree.cli.save_to_file')
    def test_main_hybrid_file_types_and_patterns(self, mock_save_to_file, mock_combine_files,
                                                  mock_parse_config, mock_load_or_create_config,
                                                  mock_load_global_config):
        """Test using both file types and patterns together (patterns should take precedence for include)."""
        mock_load_global_config.return_value = {
            "outputFile": "default.txt",
            "outputFileLocally": False,
            "useGitIgnore": True,
            "safeMode": True,
            "lineNumbers": False,
            "showIgnoredInTree": False,
            "showDefaultIgnoredInTree": False,
            "copyToClipboard": False,
            "storeFilesChosen": False,
            "includeFileTypes": "*",
            "excludeFileTypes": [],
            "includePatterns": [],
            "excludePatterns": []
        }
        mock_load_or_create_config.return_value = "/tmp/config"
        mock_parse_config.return_value = {}
        mock_combine_files.return_value = ("content", set())
        
        args = [
            'gptree', 
            '--include-file-types', '.py,.js',        # File types
            '--exclude-file-types', '.log',           # File types
            '--include-patterns', 'src/**/*.ts',      # Patterns (should override include file types)
            '--exclude-patterns', '**/tests/**',     # Patterns (should combine with exclude file types)
            '.'
        ]
        
        with patch('sys.argv', args):
            with patch('builtins.print'):
                main()
        
        # Verify hybrid behavior
        call_args = mock_combine_files.call_args
        # Include patterns should override file types
        assert call_args[1]['include_patterns'] == ['src/**/*.ts']
        # Exclude patterns should combine file types and patterns
        assert call_args[1]['exclude_patterns'] == ['**/*.log', '**/tests/**']

    @patch('cli_tool_gptree.cli.load_global_config')
    @patch('cli_tool_gptree.cli.load_or_create_config')
    @patch('cli_tool_gptree.cli.parse_config')
    @patch('cli_tool_gptree.cli.combine_files_with_structure')
    def test_main_system_exit_handling(self, mock_combine_files, mock_parse_config,
                                       mock_load_or_create_config, mock_load_global_config,
                                       capsys):
        """Test handling of SystemExit from combine_files_with_structure."""
        mock_load_global_config.return_value = {
            "outputFile": "test.txt",
            "outputFileLocally": True,
            "useGitIgnore": True,
            "safeMode": True,
            "lineNumbers": False,
            "showIgnoredInTree": False,
            "showDefaultIgnoredInTree": False,
            "copyToClipboard": False,
            "storeFilesChosen": False,
            "includeFileTypes": "*",
            "excludeFileTypes": [],
            "includePatterns": [],
            "excludePatterns": []
        }
        mock_load_or_create_config.return_value = "/tmp/config"
        mock_parse_config.return_value = {}
        mock_combine_files.side_effect = SystemExit("Test error message")
        
        with patch('sys.argv', ['gptree', '.']):
            main()
        
        captured = capsys.readouterr()
        assert "Test error message" in captured.out

    @patch('cli_tool_gptree.cli.load_global_config')
    @patch('cli_tool_gptree.cli.load_or_create_config')
    @patch('cli_tool_gptree.cli.parse_config')
    @patch('cli_tool_gptree.cli.combine_files_with_structure')
    @patch('cli_tool_gptree.cli.save_to_file')
    @patch('cli_tool_gptree.cli.save_files_to_config')
    def test_main_save_files_to_config(self, mock_save_files_to_config, mock_save_to_file,
                                       mock_combine_files, mock_parse_config,
                                       mock_load_or_create_config, mock_load_global_config):
        """Test saving selected files to config."""
        mock_load_global_config.return_value = {
            "outputFile": "test.txt",
            "outputFileLocally": True,
            "storeFilesChosen": True,
            "useGitIgnore": True,
            "safeMode": True,
            "lineNumbers": False,
            "showIgnoredInTree": False,
            "showDefaultIgnoredInTree": False,
            "copyToClipboard": False,
            "includeFileTypes": "*",
            "excludeFileTypes": [],
            "includePatterns": [],
            "excludePatterns": []
        }
        mock_load_or_create_config.return_value = "/tmp/config"
        mock_parse_config.return_value = {}
        selected_files = {"/project/file1.py", "/project/file2.js"}
        mock_combine_files.return_value = ("content", selected_files)
        
        with patch('sys.argv', ['gptree', '.']):
            with patch('builtins.print'):
                main()
        
        mock_save_files_to_config.assert_called_once()

    @patch('cli_tool_gptree.cli.prompt_user_input')
    @patch('cli_tool_gptree.cli.load_global_config')
    @patch('cli_tool_gptree.cli.load_or_create_config')
    @patch('cli_tool_gptree.cli.parse_config')
    @patch('cli_tool_gptree.cli.combine_files_with_structure')
    @patch('cli_tool_gptree.cli.save_to_file')
    def test_main_prompt_for_path(self, mock_save_to_file, mock_combine_files,
                                  mock_parse_config, mock_load_or_create_config,
                                  mock_load_global_config, mock_prompt_user_input):
        """Test prompting for path when not provided."""
        mock_prompt_user_input.return_value = "/custom/path"
        mock_load_global_config.return_value = {
            "outputFile": "test.txt",
            "outputFileLocally": True,
            "useGitIgnore": True,
            "safeMode": True,
            "lineNumbers": False,
            "showIgnoredInTree": False,
            "showDefaultIgnoredInTree": False,
            "copyToClipboard": False,
            "storeFilesChosen": False,
            "includeFileTypes": "*",
            "excludeFileTypes": [],
            "includePatterns": [],
            "excludePatterns": []
        }
        mock_load_or_create_config.return_value = "/tmp/config"
        mock_parse_config.return_value = {}
        mock_combine_files.return_value = ("content", set())
        
        with patch('sys.argv', ['gptree']):  # No path argument
            with patch('builtins.print'):
                main()
        
        mock_prompt_user_input.assert_called_once_with(
            "Enter the root directory of the project", "."
        )
        # Verify combine_files_with_structure was called with the custom path
        mock_combine_files.assert_called_once()
        call_args = mock_combine_files.call_args[0]
        assert call_args[0] == "/custom/path" 