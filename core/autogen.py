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
Automatic generation of color configuration files for integrated applications
based on Kuntatinte color schemes.
"""
import configparser
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)

FORMAT_COLORS_OUTPUT: Dict[str, Any] = {
    "Fastfetch": {
    "fastfetchAccent": {
    "color": "",
    "alpha": ""
    },
},
"Starship": {
    "selectedAccent": {
    "color": "",
    "alpha": ""
    },
    "selectedAccentText": {
    "color": "",
    "alpha": "" 
    },
    "selectedDirFg": {
    "color": "",
    "alpha": ""
    },
    "selectedDirBg": {
    "color": "",
    "alpha": ""
    },
    "selectedDirText": {
    "color": "",
    "alpha": ""
    },
    "selectedGitFg": {
    "color": "",
    "alpha": ""
    },
    "selectedGitBg": {
    "color": "",
    "alpha": ""
    },
    "selectedGitText": {
    "color": "",
    "alpha": ""
    },
    "selectedOtherFg": {
    "color": "",
    "alpha": ""
    },
    "selectedOtherBg": {
    "color": "",
    "alpha": ""
    },
    "selectedOtherText": {
    "color": "",
    "alpha": ""
    },
},
"Ulauncher": {
    "ulauncherBgColor": {
    "color": "",
    "alpha": ""
    },
    "ulauncherBorderColor": {
    "color": "",
    "alpha": ""
    },
    "ulauncherPrefsBackground": {
    "color": "",
    "alpha": ""
    },
    "ulauncherInputColor": {
    "color": "",
    "alpha": ""
    },
    "ulauncherSelectedBgColor": {
    "color": "",
    "alpha": ""
    },
    "ulauncherSelectedFgColor": {
    "color": "",
    "alpha": ""
    },
    "ulauncherItemName": {
    "color": "",
    "alpha": ""
    },
    "ulauncherItemText": {
    "color": "",
    "alpha": ""
    },
    "ulauncherItemBoxSelected": {
    "color": "",
    "alpha": ""
    },
    "ulauncherItemNameSelected": {  
    "color": "",
    "alpha": ""
    },
    "ulauncherItemTextSelected": {
    "color": "",
    "alpha": ""
    },
    "ulauncherShortcutColor": {
    "color": "",
    "alpha": ""
    },
    "ulauncherShortcutColorSel": {
    "color": "",
    "alpha": ""
    },
    "ulauncherWhenSelected": {
    "color": "",
    "alpha": ""
    },
    "ulauncherWhenNotSelected": {
    "color": "",
    "alpha": ""
    },
},
}

def get_scheme_color(scheme_path: str, color_section: str, color_key: str) -> Optional[str]:
    """Extract a color value from a KDE color scheme file.
    
    Args:
        scheme_path: Path to the color scheme file
        color_section: Section name in the config file (e.g., 'Colors:Window')
        color_key: Key name within the section (e.g., 'BackgroundNormal')
    
    Returns:
        Hex color string in lowercase format, or None if not found/invalid
    """

    scheme_config = configparser.ConfigParser()
    scheme_config.read(scheme_path)
    try:
        color_value = scheme_config.get(color_section, color_key)
        match = re.match(r"#?([0-9A-Fa-f]{6})", color_value)
        if match:
            return f"#{match.group(1).lower()}"
    except (configparser.NoSectionError, configparser.NoOptionError):
        pass
    return None

def darker_color(colors: Dict[str, str]) -> Optional[str]:
    """Select the darkest color from a dictionary of colors.
    
    Args:
        colors: Dictionary mapping color names to hex color strings
    
    Returns:
        Hex color string of the darkest color, or None if colors is empty
        
    Note:
        This is currently a placeholder implementation that returns the first color.
    """
    # Placeholder implementation
    return next(iter(colors.values()), None)

def better_contrast_color(_base_color: str, colors: Dict[str, str]) -> Optional[str]:
    """Select a color with better contrast against a base color.
    
    Args:
        _base_color: Base color for contrast calculation (currently unused)
        colors: Dictionary mapping color names to hex color strings
    
    Returns:
        Hex color string with better contrast, or None if colors is empty
        
    Note:
        This is currently a placeholder implementation that returns the first color.
    """
    # Placeholder implementation
    return next(iter(colors.values()), None)

def lighter_color(colors: Dict[str, str]) -> Optional[str]:
    """Select the lightest color from a dictionary of colors.
    
    Args:
        colors: Dictionary mapping color names to hex color strings
    
    Returns:
        Hex color string of the lightest color, or None if colors is empty
        
    Note:
        This is currently a placeholder implementation that returns the first color.
    """
    # Placeholder implementation
    return next(iter(colors.values()), None)

def run_autogen(test_mode: bool = True, palette_mode: Optional[str] = None) -> str:
    """Run autogen generation.

    For now this function is a lightweight test-mode stub that returns a
    JSON-serializable dict describing which values would be generated.
    The UI and backend call this in test mode while the full implementation
    is being developed.

    Returns:
        JSON string with generated data or error information.
    """
    try:
        # Example generated payload used for UI testing. Real implementation
        # will compute values based on rules above and detected schemes.
        if test_mode:
            payload = {
                "status": "ok",
                "mode": "test" if test_mode else "prod",
                "palette_mode": palette_mode,
                "generated": {
                    "Fastfetch": {
                        "fastfetchAccent": {"color": "#3daee9", "alpha": ""}
                    },
                    "Starship": {
                        "selectedAccent": {"color": "#3daee9", "alpha": ""},
                        "selectedAccentText": {"color": "#ffffff", "alpha": ""}
                    }
                }
            }
            return json.dumps(payload)
        else:
            # Full implementation would go here
            return json.dumps({"status": "error", "message": "Not implemented"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

from core.config_manager import config


def _load_rules_from_templates(mode: str) -> Dict[str, Any]:
    """Load autogen rules JSON from user templates directory.

    Looks under `config.templates_dir / 'autogen_rules' / '<mode>.json'.
    Returns an empty dict if not found or on error.
    """
    try:
        templates_dir = config.templates_dir
        rules_path = Path(templates_dir) / "autogen_rules" / f"{mode}.json"
        if rules_path.exists():
            with open(rules_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load rules from templates: {e}")
    return {}