"""
Automatic generation of color configuration files for integrated applications
based on Kuntatinte color schemes.
"""
import configparser
import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from integrations.kuntatinte_colors import generate_and_save_kuntatinte_schemes, parse_scheme_file, get_scheme_file_path
from core.config_manager import config

logger = logging.getLogger(__name__)


def _extract_color_from_scheme(scheme_path: Path, section: str, key: str) -> tuple[Optional[str], float]:
    """Extract a color and opacity from a KDE color scheme file.
    
    Args:
        scheme_path: Path to the .colors file
        section: Section name (e.g., 'Colors:Window')
        key: Key name (e.g., 'BackgroundNormal')
    
    Returns:
        Tuple of (hex color string, opacity 0.0-1.0) or (None, 1.0) if not found
    """
    try:
        config = configparser.ConfigParser()
        config.read(scheme_path, encoding='utf-8')
        
        if config.has_section(section) and config.has_option(section, key):
            value = config.get(section, key)
            logger.info(f"Read from {scheme_path} [{section}] {key} = {value}")
            # Parse RGB/RGBA values like "191,173,160" or "191,173,160,255"

            if ',' in value:
                parts = value.split(',')
                if len(parts) >= 3:
                    r, g, b = map(int, parts[:3])
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    # Check for alpha (4th value)
                    if len(parts) >= 4:
                        alpha = int(parts[3])
                        opacity = alpha / 255.0
                    else:
                        opacity = 1.0
                    
                    logger.info(f"Parsed to hex: {hex_color}, opacity: {opacity}")
                    return hex_color, opacity
            else: # Handle hex format like "#bfada0"
                match = re.match(r"#?([0-9A-Fa-f]{6})([0-9A-Fa-f]{2})?", value)
                if match:
                    hex_color = f"#{match.group(1).lower()}"
                    if match.group(2):
                        alpha = int(match.group(2), 16)
                        opacity = alpha / 255.0
                    else:
                        opacity = 1.0
                    logger.info(f"Parsed to hex: {hex_color}, opacity: {opacity}")
                    return hex_color, opacity
    except Exception as e:
        logger.error(f"Error extracting color from scheme {scheme_path}: {e}")
    
    return None, 1.0

def get_active_color_scheme():
    try:
        result = subprocess.run(
            ["kreadconfig6", "--file", "kdeglobals", "--group", "General", "--key", "ColorScheme"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.CalledProcessError):
        kdeglobals = Path("~/.config/kdeglobals").expanduser()
        if kdeglobals.exists():
            config = configparser.ConfigParser()
            config.read(kdeglobals)
            return config.get("General", "ColorScheme", fallback=None)
    return None

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

def run_autogen(palette_mode: Optional[str] = None, palette: Optional[list[str]] = None, primary_index: int = 0, accent_override: str = "", primary_color: str = "") -> str:
    """Run autogen generation.

    Generates color configurations for integrated applications based on 
    Kuntatinte color schemes and autogen rules.

    Args:
        palette_mode: "dark" or "light" mode for generation.

    Returns:
        JSON string with generated data or error information.
    """
    try:
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
                        # Use accent_override if provided (central panel color), else extract from scheme
                        if accent_override:
                            color = accent_override
                            opacity = 1.0
                            logger.info(f"Using accent_override for PrimaryColor: {color}")
                        else:
                            color, opacity = _extract_color_from_scheme(scheme_path, "Colors:Window", "DecorationFocus")
                            logger.info(f"Extracted PrimaryColor from DecorationFocus: {color}, opacity: {opacity}")
                    else:
                        color = "#ff0000"  # fallback
                        opacity = 1.0
                elif extract_method == "color_scheme":
                    section = rule.get("scheme_section")
                    key = rule.get("scheme_key")
                    color, opacity = _extract_color_from_scheme(scheme_path, section, key)
                elif extract_method == "better_contrast":
                    base_color = rule.get("base_color")
                    group_colors = rule.get("group_colors", [])
                    # For now, use placeholders if TobeDefined
                    if base_color == "TobeDefined":
                        base_color = palette[0] if palette else "#ff0000"
                    if "TobeDefined" in group_colors:
                        group_colors = palette if palette else ["#ff0000"]
                    color = _get_better_contrast_color(base_color, group_colors)
                    opacity = 1.0
                else:
                    color = "#ff0000"  # fallback
                    opacity = 1.0
                
                # Convert opacity to percentage string
                alpha_str = str(round(opacity * 100))
                generated[app][prop] = {"color": color or "#ff0000", "alpha": alpha_str}
        
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


def run_autogen_current_colors(palette_mode: Optional[str] = None, primary_color: str = "", accent_override: str = "") -> str:
    """Run autogen generation using current color schemes (no regeneration).

    Generates color configurations for integrated applications based on 
    existing Kuntatinte color schemes and autogen rules.

    Args:
        palette_mode: "dark" or "light" mode for generation.
        primary_color: Primary color override.
        accent_override: Accent color override.

    Returns:
        JSON string with generated data or error information.
    """
    try:
        if not palette_mode:
            return json.dumps({"status": "error", "message": "palette_mode required"})
        
        # Use existing schemes - no regeneration
        # Get scheme path
        #scheme_name = "KuntatinteLight" if palette_mode == "light" else "KuntatinteDark"
        #scheme_path = get_scheme_file_path(scheme_name)
        # Get current color scheme path from system
        scheme_name = get_active_color_scheme()
        print(f"Active color scheme: {scheme_name}")
        if not scheme_name:
            scheme_name = "KuntatinteLight" if palette_mode == "light" else "KuntatinteDark"
        scheme_path = Path.home() / ".local/share/color-schemes" / f"{scheme_name}.colors"

        if not scheme_path or not scheme_path.exists():
            return json.dumps({"status": "error", "message": f"Color scheme {scheme_name} not found"})
        
        # Load rules
        rules = _load_rules_from_templates(palette_mode)
        if not rules:
            return json.dumps({"status": "error", "message": f"No rules found for mode {palette_mode}"})
        
        # Generate configs using existing scheme
        generated = {}
        for app, props in rules.items():
            generated[app] = {}
            for prop, rule in props.items():
                try:
                    extract_method = rule.get("extract_method")
                    if extract_method == "variable":
                        variable_key = rule.get("variable_key")
                        if variable_key == "PrimaryColor":
                            # Use accent_override if provided, else extract from scheme
                            if accent_override:
                                color = accent_override
                                opacity = 1.0
                                logger.info(f"Using accent_override for PrimaryColor: {color}")
                            else:
                                color, opacity = _extract_color_from_scheme(scheme_path, "Colors:Window", "DecorationFocus")
                                logger.info(f"Extracted PrimaryColor from DecorationFocus: {color}, opacity: {opacity}")
                        else:
                            color = "#ff0000"  # fallback
                            opacity = 1.0
                    elif extract_method == "color_scheme":
                        section = rule.get("scheme_section")
                        key = rule.get("scheme_key")
                        color, opacity = _extract_color_from_scheme(scheme_path, section, key)
                    elif extract_method == "better_contrast":
                        base_color = rule.get("base_color")
                        group_colors = rule.get("group_colors", [])
                        # For now, use placeholders if TobeDefined
                        if base_color == "TobeDefined":
                            base_color = primary_color or "#ff0000"
                        if "TobeDefined" in group_colors:
                            group_colors = [primary_color] if primary_color else ["#ff0000"]
                        color = _get_better_contrast_color(base_color, group_colors)
                        opacity = 1.0
                    else:
                        color = "#ff0000"  # fallback
                        opacity = 1.0
                    
                    # Convert opacity to percentage string
                    alpha_str = str(round(opacity * 100))
                    generated[app][prop] = {"color": color or "#ff0000", "alpha": alpha_str}
                except Exception as e:
                    logger.error(f"Error processing {app}.{prop}: {e}")
                    generated[app][prop] = {"color": "#ff0000", "alpha": "100"}
        
        payload = {
            "status": "ok",
            "mode": "prod",
            "palette_mode": palette_mode,
            "primary_index": 0,  # Not applicable for current colors mode
            "generated": generated
        }
        return json.dumps(payload)
        
    except Exception as e:
        logger.error(f"Error in run_autogen_current_colors: {e}")
        return json.dumps({"status": "error", "message": str(e)})