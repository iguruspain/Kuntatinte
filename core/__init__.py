# Copyright (C) 2025 iguruspain
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
