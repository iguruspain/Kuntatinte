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

from integrations.kuntatinte_colors import generate_and_save_kuntatinte_schemes, parse_scheme_file
from core.config_manager import config
from core.color_utils import get_best_contrast

logger = logging.getLogger(__name__)


def _extract_color_from_scheme(scheme_path: Path, section: str, key: str) -> Optional[str]:
    """Extract a color from a KDE color scheme file.
    
    Args:
        scheme_path: Path to the .colors file
        section: Section name (e.g., 'Colors:Window')
        key: Key name (e.g., 'BackgroundNormal')
    
    Returns:
        Hex color string or None if not found
    """
    try:
        config = configparser.ConfigParser()
        config.read(scheme_path, encoding='utf-8')
        
        if config.has_section(section) and config.has_option(section, key):
            value = config.get(section, key)
            logger.info(f"Read from {scheme_path} [{section}] {key} = {value}")
            # Parse RGB values like "191,173,160"
            if ',' in value:
                parts = value.split(',')
                if len(parts) >= 3:
                    r, g, b = map(int, parts[:3])
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    logger.info(f"Parsed to hex: {hex_color}")
                    return hex_color
    except Exception as e:
        logger.error(f"Error extracting color from scheme {scheme_path}: {e}")
    return None


def _get_better_contrast_color(base_color: str, group_colors: list) -> str:
    """Get the color from group_colors that has better contrast with base_color.
    
    Args:
        base_color: Base color for contrast calculation
        group_colors: List of candidate colors
    
    Returns:
        Best contrasting color
    """
    if not group_colors:
        return base_color
    return get_best_contrast(base_color, group_colors)


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

def run_autogen(test_mode: bool = True, palette_mode: Optional[str] = None, palette: Optional[list[str]] = None, primary_index: int = 0, accent_override: str = "", primary_color: str = "") -> str:
    """Run autogen generation.

    Generates color configurations for integrated applications based on 
    Kuntatinte color schemes and autogen rules.

    Args:
        test_mode: If True, use test data. If False, generate real configs.
        palette_mode: "dark" or "light" mode for generation.

    Returns:
        JSON string with generated data or error information.
    """
    try:
        if test_mode:
            # Test mode: return example payload
            payload = {
                "status": "ok",
                "mode": "test",
                "palette_mode": palette_mode,
                "primary_index": primary_index,
                "generated": {
                    "Fastfetch": {
                        "fastfetchAccent": {"color": "#3daee9", "alpha": "100"}
                    },
                    "Starship": {
                        "selectedAccent": {"color": "#3daee9", "alpha": "100"},
                        "selectedAccentText": {"color": "#ffffff", "alpha": "100"}
                    }
                }
            }
            return json.dumps(payload)
        
        # Real implementation
        if not palette_mode:
            return json.dumps({"status": "error", "message": "palette_mode required"})
        
        # Generate Kuntatinte schemes if needed
        # Use provided palette or default
        if palette and len(palette) > 0:
            use_palette = palette
        else:
            use_palette = ["#3daee9", "#1d99f3", "#7f8c8d", "#34495e", "#2c3e50"]  # default
        
        # Handle accent_override like in backend
        if primary_index == -1 and accent_override:
            # Create a modified palette with accent as first element
            use_palette = [accent_override] + list(use_palette)
            use_primary_index = 0
        elif primary_color:
            if primary_color in use_palette:
                use_primary_index = use_palette.index(primary_color)
            else:
                # Add primary_color to the palette as first element
                use_palette = [primary_color] + list(use_palette)
                use_primary_index = 0
                logger.info(f"Added primary_color {primary_color} to palette, use_palette={use_palette}, use_primary_index={use_primary_index}")
        else:
            use_primary_index = primary_index
        
        logger.info(f"Final use_palette={use_palette}, use_primary_index={use_primary_index}")
        
        success, msg = generate_and_save_kuntatinte_schemes(use_palette, use_primary_index, 100, 5)
        if not success:
            return json.dumps({"status": "error", "message": f"Failed to generate schemes: {msg}"})
        
        # Load rules
        rules = _load_rules_from_templates(palette_mode)
        if not rules:
            return json.dumps({"status": "error", "message": f"No rules found for mode {palette_mode}"})
        
        # Get scheme path
        scheme_name = "KuntatinteLight" if palette_mode == "light" else "KuntatinteDark"
        scheme_path = Path.home() / ".local/share/color-schemes" / f"{scheme_name}.colors"
        if not scheme_path.exists():
            return json.dumps({"status": "error", "message": f"Scheme file not found: {scheme_path}"})
        
        # Generate colors
        generated = {}
        for app, app_rules in rules.items():
            generated[app] = {}
            for prop, rule in app_rules.items():
                extract_method = rule.get("extract_method")
                if extract_method == "variable":
                    variable_key = rule.get("variable_key")
                    if variable_key == "PrimaryColor":
                        # Use primary_color if provided, else extract from scheme
                        if primary_color:
                            color = primary_color
                            logger.info(f"Using provided primary_color: {color}")
                        else:
                            color = _extract_color_from_scheme(scheme_path, "Colors:Window", "DecorationFocus")
                            logger.info(f"Extracted PrimaryColor from DecorationFocus: {color}")
                    else:
                        color = "#ff0000"  # fallback
                elif extract_method == "color_scheme":
                    section = rule.get("scheme_section")
                    key = rule.get("scheme_key")
                    color = _extract_color_from_scheme(scheme_path, section, key)
                elif extract_method == "better_contrast":
                    base_color = rule.get("base_color")
                    group_colors = rule.get("group_colors", [])
                    # For now, use placeholders if TobeDefined
                    if base_color == "TobeDefined":
                        base_color = palette[0] if palette else "#ff0000"
                    if "TobeDefined" in group_colors:
                        group_colors = palette if palette else ["#ff0000"]
                    color = _get_better_contrast_color(base_color, group_colors)
                else:
                    color = "#ff0000"  # fallback
                
                generated[app][prop] = {"color": color or "#ff0000", "alpha": "100"}
        
        payload = {
            "status": "ok",
            "mode": "prod",
            "palette_mode": palette_mode,
            "primary_index": use_primary_index,
            "generated": generated
        }
        return json.dumps(payload)
        
    except Exception as e:
        logger.error(f"Error in run_autogen: {e}")
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