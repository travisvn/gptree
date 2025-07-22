"""
GPTree CLI Tool - A tool to provide LLM context for coding projects
by combining project files into a single text file with directory tree structure.
"""

from .cli import main, CURRENT_VERSION
from .config import DEFAULT_CONFIG, CONFIG_VERSION
from .builder import SAFE_MODE_MAX_FILES, SAFE_MODE_MAX_LENGTH

__version__ = CURRENT_VERSION
__all__ = ['main', 'CURRENT_VERSION', 'DEFAULT_CONFIG', 'CONFIG_VERSION', 
           'SAFE_MODE_MAX_FILES', 'SAFE_MODE_MAX_LENGTH']
