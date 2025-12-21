#!/usr/bin/env python3
# Copyright (C) 2025 Igu R. Spain
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
OpenRGB Color Control Utility.

Applies accent color to OpenRGB devices.

Workflow:
1. Execute openrgb command with specified accent color
2. Set mode to direct and brightness to 100
"""

import logging
import subprocess
from typing import Tuple

logger = logging.getLogger(__name__)


def apply_openrgb_accent(accent_color: str) -> Tuple[bool, str]:
    """Apply accent color to OpenRGB.
    
    Args:
        accent_color: Hex color string without # (e.g. 'ff0000')
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not accent_color:
        return False, "No accent color provided"
    
    # Validate hex color format
    if not all(c in '0123456789abcdefABCDEF' for c in accent_color) or len(accent_color) != 6:
        return False, "Invalid hex color format. Must be 6 hexadecimal digits."
    
    try:
        # Run openrgb command
        result = subprocess.run(
            ["openrgb", "--noautoconnect", "-c", accent_color, "-m", "direct", "-b", "100"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"OpenRGB accent applied successfully: {accent_color}")
        return True, ""
    except subprocess.CalledProcessError as e:
        error_msg = f"OpenRGB command failed: {e.stderr.strip()}"
        logger.error(error_msg)
        return False, error_msg
    except FileNotFoundError:
        return False, "OpenRGB is not installed or not in PATH"
    except Exception as e:
        error_msg = f"Unexpected error applying OpenRGB: {str(e)}"
        logger.error(error_msg)
        return False, error_msg