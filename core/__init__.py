"""
Core modules for Kuntatinte.
- backend: QML Backend interface
- config_manager: Configuration management
- color_utils: Color manipulation utilities
- file_utils: File operations utilities
- qt_environment: Qt/QML environment setup
- imagemagick: ImageMagick color extraction
"""

from .config_manager import config, Config
from .qt_environment import setup_qt_environment
from .backend import PaletteBackend
