"""integrations.kuntatinte_colors

A unified module that combines the functionality of the old
`kde_colors.py` and `kde_colors_v2.py`. This file replaces both
previous ones and is the only module that the application should use.
"""

import configparser
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime


logger = logging.getLogger(__name__)

# Core color utilities - imported locally to avoid circular imports
# from core.color_utils import (
#     hex_to_rgb, hex_to_hsl, hsl_to_hex,
#     blend_colors, get_contrast_ratio,
#     create_material_you_scheme, get_material_you_colors_from_scheme,
#     is_material_you_available,
# )


# ---------------------------------------------------------------------------
# KDE color scheme helper functions (originalmente en `kde_colors.py`)
# ---------------------------------------------------------------------------


def get_scheme_file_path(scheme_name: str) -> Path | None:
    """Get the file path for a color scheme by name."""
    user_path = Path.home() / ".local/share/color-schemes" / f"{scheme_name}.colors"
    if user_path.exists():
        return user_path

    system_path = Path("/usr/share/color-schemes") / f"{scheme_name}.colors"
    if system_path.exists():
        return system_path

    return None


def parse_scheme_file(scheme_name: str) -> Dict[str, Dict[str, Tuple[str, float]]]:
    scheme_path = get_scheme_file_path(scheme_name)
    if not scheme_path:
        return {}

    result: Dict[str, Dict[str, Tuple[str, float]]] = {}

    try:
        config = configparser.ConfigParser()
        config.optionxform = lambda optionstr: optionstr
        config.read(scheme_path)

        for section in config.sections():
            result[section] = {}
            for key, value in config.items(section):
                hex_color, opacity = parse_kde_color(value)
                result[section][key] = (hex_color, opacity)

        return result
    except Exception as e:
        logger.error(f"Error parsing scheme file: {e}")
        return {}


def get_scheme_structure(scheme_name: str) -> Dict[str, List[str]]:
    data = parse_scheme_file(scheme_name)
    return {section: list(keys.keys()) for section, keys in data.items()}


def get_color_sections(scheme_name: str) -> List[str]:
    data = parse_scheme_file(scheme_name)
    return [s for s in data.keys() if s.startswith("Colors:") and "][" not in s]


def get_inactive_sections(scheme_name: str) -> List[str]:
    data = parse_scheme_file(scheme_name)
    inactive: List[str] = []
    for s in data.keys():
        if "][Inactive" in s:
            base = s.split("][")[0]
            inactive.append(base)
    return inactive


def get_section_colors(scheme_name: str, section: str) -> Dict[str, Tuple[str, float]]:
    data = parse_scheme_file(scheme_name)
    return data.get(section, {})


def get_current_scheme_name() -> str:
    try:
        result = subprocess.run(
            ["kreadconfig6", "--group", "General", "--key", "ColorScheme"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() or "Unknown"
    except Exception as e:
        logger.error(f"Error getting current scheme: {e}")
        return "Unknown"


def parse_kde_color(color_str: str) -> tuple[str, float]:
    if not color_str:
        return "#000000", 1.0

    color_str = color_str.strip()

    if color_str.startswith("#"):
        if len(color_str) == 9:  # #aarrggbb
            alpha = int(color_str[1:3], 16)
            hex_color = "#" + color_str[3:9]
            return hex_color, alpha / 255.0
        elif len(color_str) == 7:
            return color_str, 1.0
        return "#000000", 1.0

    if "," in color_str:
        parts = [p.strip() for p in color_str.split(",")]
        if len(parts) >= 3:
            try:
                r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                hex_color = f"#{r:02x}{g:02x}{b:02x}"

                if len(parts) == 4:
                    alpha = int(parts[3])
                    return hex_color, alpha / 255.0

                return hex_color, 1.0
            except ValueError:
                pass

    return "#000000", 1.0


def format_kde_color(hex_color: str, opacity: float = 1.0, always_rgba: bool = True) -> str:
    if not hex_color or not hex_color.startswith("#"):
        return "0,0,0,255" if always_rgba else "0,0,0"

    hex_str = hex_color.lstrip("#")
    if len(hex_str) == 6:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
    else:
        return "0,0,0,255" if always_rgba else "0,0,0"

    a = round(opacity * 255)

    if always_rgba:
        return f"{r},{g},{b},{a}"
    elif opacity < 1.0:
        return f"{r},{g},{b},{a}"
    else:
        return f"{r},{g},{b}"


def read_color(color_set: str, key: str) -> str:
    try:
        group = f"Colors:{color_set}"
        result = subprocess.run(
            ["kreadconfig6", "--file", "kdeglobals", "--group", group, "--key", key],
            capture_output=True,
            text=True
        )
        color_str = result.stdout.strip()
        hex_color, _ = parse_kde_color(color_str)
        return hex_color
    except Exception as e:
        logger.error(f"Error reading color: {e}")
        return "#000000"


def read_color_with_opacity(color_set: str, key: str) -> tuple[str, float]:
    try:
        group = f"Colors:{color_set}"
        result = subprocess.run(
            ["kreadconfig6", "--file", "kdeglobals", "--group", group, "--key", key],
            capture_output=True,
            text=True
        )
        color_str = result.stdout.strip()
        return parse_kde_color(color_str)
    except Exception as e:
        logger.error(f"Error reading color: {e}")
        return "#000000", 1.0


def write_color(color_set: str, key: str, color: str, opacity: float = 1.0, notify: bool = False) -> bool:
    try:
        group = f"Colors:{color_set}"
        kde_color = format_kde_color(color, opacity)

        cmd = ["kwriteconfig6", "--file", "kdeglobals", "--group", group, "--key", key, kde_color]
        if notify:
            cmd.insert(-1, "--notify")

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error writing color: {e}")
        return False


# Legacy constants
COLOR_SETS = ["View", "Window", "Button", "Selection", "Tooltip", "Complementary", "Header"]
COLOR_KEYS = [
    "BackgroundNormal", "BackgroundAlternate",
    "ForegroundNormal", "ForegroundInactive",
    "DecorationFocus", "DecorationHover"
]


def get_color_set(color_set: str) -> dict:
    colors = {}
    for key in COLOR_KEYS:
        colors[key] = read_color(color_set, key)
    return colors


def get_all_colors() -> dict:
    all_colors = {}
    for color_set in COLOR_SETS:
        all_colors[color_set] = get_color_set(color_set)
    return all_colors


def apply_palette_to_scheme(palette: list, accent: str | None = None) -> bool:
    if len(palette) < 8:
        logger.error("Palette must have at least 8 colors")
        return False

    # Import here to avoid circular imports
    from core.color_utils import hex_to_hsl

    # Cache HSL conversions to avoid repeated calculations
    hsl_cache = {color: hex_to_hsl(color) for color in palette}
    
    sorted_palette = sorted(palette, key=lambda c: hsl_cache[c]['l'])
    avg_luminance = sum(hsl_cache[c]['l'] for c in palette) / len(palette)
    is_dark = avg_luminance < 50

    if is_dark:
        bg_dark = sorted_palette[0]
        bg_normal = sorted_palette[1]
        bg_alt = sorted_palette[2]
        fg_inactive = sorted_palette[4]
        fg_normal = sorted_palette[-1]
        fg_active = sorted_palette[-2]
    else:
        bg_dark = sorted_palette[-1]
        bg_normal = sorted_palette[-2]
        bg_alt = sorted_palette[-3]
        fg_inactive = sorted_palette[3]
        fg_normal = sorted_palette[0]
        fg_active = sorted_palette[1]

    accent_color = accent if accent else palette[0]

    color_mapping = {
        "View": {
            "BackgroundNormal": bg_dark,
            "BackgroundAlternate": bg_normal,
            "ForegroundNormal": fg_normal,
            "ForegroundInactive": fg_inactive,
            "ForegroundActive": fg_active,
            "DecorationFocus": accent_color,
            "DecorationHover": accent_color,
        },
        "Window": {
            "BackgroundNormal": bg_normal,
            "BackgroundAlternate": bg_alt,
            "ForegroundNormal": fg_normal,
            "ForegroundInactive": fg_inactive,
            "ForegroundActive": fg_active,
            "DecorationFocus": accent_color,
            "DecorationHover": accent_color,
        },
        "Button": {
            "BackgroundNormal": bg_normal,
            "BackgroundAlternate": bg_alt,
            "ForegroundNormal": fg_normal,
            "ForegroundInactive": fg_inactive,
            "ForegroundActive": fg_active,
            "DecorationFocus": accent_color,
            "DecorationHover": accent_color,
        },
        "Selection": {
            "BackgroundNormal": accent_color,
            "BackgroundAlternate": accent_color,
            "ForegroundNormal": fg_normal if is_dark else bg_dark,
            "ForegroundInactive": fg_inactive,
            "ForegroundActive": fg_active,
            "DecorationFocus": accent_color,
            "DecorationHover": accent_color,
        },
        "Tooltip": {
            "BackgroundNormal": bg_normal,
            "BackgroundAlternate": bg_alt,
            "ForegroundNormal": fg_normal,
            "ForegroundInactive": fg_inactive,
            "ForegroundActive": fg_active,
            "DecorationFocus": accent_color,
            "DecorationHover": accent_color,
        },
        "Complementary": {
            "BackgroundNormal": bg_normal,
            "BackgroundAlternate": bg_dark,
            "ForegroundNormal": fg_normal,
            "ForegroundInactive": fg_inactive,
            "ForegroundActive": fg_active,
            "DecorationFocus": accent_color,
            "DecorationHover": accent_color,
        },
        "Header": {
            "BackgroundNormal": bg_normal,
            "BackgroundAlternate": bg_normal,
            "ForegroundNormal": fg_normal,
            "ForegroundInactive": fg_inactive,
            "ForegroundActive": fg_active,
            "DecorationFocus": accent_color,
            "DecorationHover": accent_color,
        },
    }

    success = True
    for color_set, colors in color_mapping.items():
        for key, color in colors.items():
            if not write_color(color_set, key, color):
                success = False

    return success


def notify_color_change():
    try:
        subprocess.run(
            ["kwriteconfig6", "--file", "kdeglobals", "--group", "General", 
             "--key", "ColorSchemeHash", "--notify", ""],
            capture_output=True
        )
        return True
    except Exception as e:
        logger.error(f"Error notifying color change: {e}")
        return False


def read_color_from_scheme(scheme_name: str, color_set: str, key: str) -> str:
    scheme_path = get_scheme_file_path(scheme_name)
    if not scheme_path:
        return "#000000"

    try:
        group = f"Colors:{color_set}"
        result = subprocess.run(
            ["kreadconfig6", "--file", str(scheme_path), "--group", group, "--key", key],
            capture_output=True,
            text=True
        )
        color_str = result.stdout.strip()
        hex_color, _ = parse_kde_color(color_str)
        return hex_color
    except Exception as e:
        logger.error(f"Error reading color from scheme: {e}")
        return "#000000"


def get_color_set_from_scheme(scheme_name: str, color_set: str) -> dict:
    colors = {}
    for key in COLOR_KEYS:
        colors[key] = read_color_from_scheme(scheme_name, color_set, key)
    return colors


def get_color_schemes_list() -> list:
    schemes: List[str] = []

    system_path = Path("/usr/share/color-schemes")
    if system_path.exists():
        schemes.extend([f.stem for f in system_path.glob("*.colors")])

    user_path = Path.home() / ".local/share/color-schemes"
    if user_path.exists():
        schemes.extend([f.stem for f in user_path.glob("*.colors")])

    return sorted(set(schemes))


def apply_color_scheme(scheme_name: str) -> bool:
    try:
        result = subprocess.run(
            ["plasma-apply-colorscheme", scheme_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error applying color scheme: {e}")
        return False


def save_color_scheme(scheme_name: str, _is_dark: bool) -> bool:
    user_schemes_dir = Path.home() / ".local/share/color-schemes"
    user_schemes_dir.mkdir(parents=True, exist_ok=True)

    scheme_path = user_schemes_dir / f"{scheme_name}.colors"

    if scheme_path.exists():
        backup_dir = user_schemes_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{scheme_name}_{timestamp}.colors"
        shutil.copy(scheme_path, backup_path)
        logger.info(f"Backup created: {backup_path}")

    try:
        config = configparser.ConfigParser()
        config.optionxform = lambda optionstr: optionstr

        config['General'] = {
            'ColorScheme': scheme_name,
            'Name': scheme_name
        }

        for color_set in COLOR_SETS:
            section = f"Colors:{color_set}"
            config[section] = {}
            for key in COLOR_KEYS:
                color = read_color(color_set, key)
                if color and color != "#000000":
                    hex_color = color.lstrip("#")
                    if len(hex_color) == 6:
                        r = int(hex_color[0:2], 16)
                        g = int(hex_color[2:4], 16)
                        b = int(hex_color[4:6], 16)
                        config[section][key] = f"{r},{g},{b}"

        wm_section = "WM"
        config[wm_section] = {}
        wm_keys = ["activeBackground", "activeForeground", "inactiveBackground", 
                   "inactiveForeground", "activeBlend", "inactiveBlend"]
        for key in wm_keys:
            try:
                result = subprocess.run(
                    ["kreadconfig6", "--file", "kdeglobals", "--group", "WM", "--key", key],
                    capture_output=True, text=True
                )
                if result.stdout.strip():
                    config[wm_section][key] = result.stdout.strip()
            except:
                pass

        with open(scheme_path, 'w') as f:
            config.write(f, space_around_delimiters=False)

        logger.info(f"Color scheme saved: {scheme_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving color scheme: {e}")
        return False


def save_color_scheme_from_data(scheme_name: str, _is_dark: bool, colors_data: dict) -> bool:
    user_schemes_dir = Path.home() / ".local/share/color-schemes"
    user_schemes_dir.mkdir(parents=True, exist_ok=True)

    scheme_path = user_schemes_dir / f"{scheme_name}.colors"

    if scheme_path.exists():
        backup_dir = user_schemes_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{scheme_name}_{timestamp}.colors"
        shutil.copy(scheme_path, backup_path)
        logger.info(f"Backup created: {backup_path}")

    try:
        config = configparser.ConfigParser()
        config.optionxform = lambda optionstr: optionstr

        config['General'] = {
            'ColorScheme': scheme_name,
            'Name': scheme_name,
            'shadeSortColumn': 'true'
        }

        config['KDE'] = {
            'contrast': '4'
        }

        for section, keys in colors_data.items():
            if section in ['General', 'KDE']:
                continue
            if section not in config:
                config[section] = {}
            for key, value in keys.items():
                if isinstance(value, dict) and 'color' in value:
                    color = value.get('color', '#000000')
                    opacity = value.get('opacity', 1.0)
                    config[section][key] = format_kde_color(color, opacity, always_rgba=True)
                else:
                    config[section][key] = str(value)

        with open(scheme_path, 'w') as f:
            config.write(f, space_around_delimiters=False)

        logger.info(f"Color scheme saved: {scheme_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving color scheme: {e}")
        return False


# ---------------------------------------------------------------------------
# Kuntatinte v2 generator (originalmente en `kde_colors_v2.py`)
# ---------------------------------------------------------------------------


# Tone helpers
TONES = list(range(0, 101))


def generate_tonal_palette(base_color: str) -> Dict[int, str]:
    # Import here to avoid circular imports
    from core.color_utils import hex_to_hsl, hsl_to_hex
    hsl = hex_to_hsl(base_color)
    palette: Dict[int, str] = {}
    for tone in TONES:
        new_l = tone
        palette[tone] = hsl_to_hex(hsl['h'], hsl['s'], new_l)
    return palette


def generate_neutral_palette(base_color: str, saturation_factor: float = 0.08) -> Dict[int, str]:
    # Import here to avoid circular imports
    from core.color_utils import hex_to_hsl, hsl_to_hex
    hsl = hex_to_hsl(base_color)
    palette: Dict[int, str] = {}
    for tone in TONES:
        new_s = hsl['s'] * saturation_factor
        palette[tone] = hsl_to_hex(hsl['h'], new_s, tone)
    return palette


def blend2contrast(
    color: str,
    background: str,
    target_color: str,
    min_contrast: float = 4.5,
    step: float = 0.05,
    _lighter: bool = True
) -> str:
    # Import here to avoid circular imports
    from core.color_utils import get_contrast_ratio, blend_colors
    current = color
    for _ in range(100):
        contrast = get_contrast_ratio(current, background)
        if contrast >= min_contrast:
            return current
        current = blend_colors(current, target_color, step)
    return current


def scale_saturation(hex_color: str, factor: float) -> str:
    # Import here to avoid circular imports
    from core.color_utils import hex_to_hsl, hsl_to_hex
    hsl = hex_to_hsl(hex_color)
    new_s = min(100, max(0, hsl['s'] * factor))
    return hsl_to_hex(hsl['h'], new_s, hsl['l'])


def lighten_color(hex_color: str, amount: float, target: str) -> str:
    return blend_colors(hex_color, target, amount)


def hex2alpha(hex_color: str, opacity: int) -> str:
    # Import here to avoid circular imports
    from core.color_utils import hex_to_rgb
    r, g, b = hex_to_rgb(hex_color)
    a = int(opacity * 255 / 100)
    return f"{r},{g},{b},{a}"


def format_rgb(hex_color: str) -> str:
    # Import here to avoid circular imports
    from core.color_utils import hex_to_rgb
    r, g, b = hex_to_rgb(hex_color)
    return f"{r},{g},{b}"


def format_rgba(hex_color: str, opacity: float = 1.0) -> str:
    # Import here to avoid circular imports
    from core.color_utils import hex_to_rgb
    r, g, b = hex_to_rgb(hex_color)
    a = int(opacity * 255)
    return f"{r},{g},{b},{a}"


class KuntatinteSchemeGenerator:
    def __init__(
        self,
        palette: List[str],
        primary_index: int = 0,
        scheme_variant: int = 5,
        toolbar_opacity: int = 100,
        chroma_multiplier: float = 1.0,
        tone_multiplier: float = 0.8
    ):
        self.palette = palette
        self.primary = palette[primary_index] if palette else "#3daee9"
        self.scheme_variant = scheme_variant
        self.toolbar_opacity = toolbar_opacity
        self.chroma_multiplier = chroma_multiplier
        self.tone_multiplier = tone_multiplier
        self._generate_palettes()
        self._light_scheme = self._generate_light_scheme()
        self._dark_scheme = self._generate_dark_scheme()

    def _generate_palettes(self):
        # Import here to avoid circular imports
        from core.color_utils import is_material_you_available
        
        if is_material_you_available():
            self._generate_material_you_colors()
        else:
            self._generate_palettes_fallback()

    def _generate_material_you_colors(self):
        """Generate Material You color schemes using HCT system."""
        # Import here to avoid circular imports
        from core.color_utils import create_material_you_scheme, get_material_you_colors_from_scheme, hex_to_hsl, hsl_to_hex
        
        # Create schemes
        scheme_light = create_material_you_scheme(self.primary, is_dark=False, variant=self.scheme_variant)
        scheme_dark = create_material_you_scheme(self.primary, is_dark=True, variant=self.scheme_variant)
        
        # Apply multipliers to the schemes
        if self.chroma_multiplier != 1.0 or self.tone_multiplier != 1.0:
            scheme_light = self._apply_multipliers_to_scheme(scheme_light, self.chroma_multiplier, self.tone_multiplier)
            scheme_dark = self._apply_multipliers_to_scheme(scheme_dark, self.chroma_multiplier, self.tone_multiplier)
        
        # Generate colors
        self.colors_light = get_material_you_colors_from_scheme(scheme_light, is_dark=False)
        self.colors_dark = get_material_you_colors_from_scheme(scheme_dark, is_dark=True)
        
        # Apply multipliers to the generated colors
        if self.chroma_multiplier != 1.0 or self.tone_multiplier != 1.0:
            self.colors_light = self._apply_multipliers_to_colors(self.colors_light, self.chroma_multiplier, self.tone_multiplier)
            self.colors_dark = self._apply_multipliers_to_colors(self.colors_dark, self.chroma_multiplier, self.tone_multiplier)
        
        # Generate additional colors for compatibility
        self._generate_extra_colors()
        
        # Generate tonal palettes for compatibility (using fallback method)
        self.tones_primary = generate_tonal_palette(self.primary)
        self.tones_neutral = generate_neutral_palette(self.primary, 0.05)
        self.tones_neutral_variant = generate_neutral_palette(self.primary, 0.12)

        hsl = hex_to_hsl(self.primary)
        secondary_hue = (hsl['h'] + 30) % 360
        secondary = hsl_to_hex(secondary_hue, hsl['s'] * 0.6, hsl['l'])
        self.tones_secondary = generate_tonal_palette(secondary)

        tertiary_hue = (hsl['h'] + 60) % 360
        tertiary = hsl_to_hex(tertiary_hue, hsl['s'] * 0.8, hsl['l'])
        self.tones_tertiary = generate_tonal_palette(tertiary)

        self.tones_error = generate_tonal_palette("#ba1a1a")
        
        # Generate semantic colors (links, etc.)
        self._generate_semantic_colors(self.colors_dark['primary'])

    def _generate_extra_colors(self):
        """Generate additional colors needed for KDE scheme compatibility."""
        # Use Material You colors to generate the extra colors
        base_colors = {
            'link': self.colors_light['primary'],  # Use primary for link
            'visited': self.colors_light['tertiary'],  # Use tertiary for visited
            'negative': '#dc362e',  # Standard red for negative
            'neutral': '#f57c00',  # Standard orange for neutral  
            'positive': '#238823',  # Standard green for positive
        }
        
        self.colors: Dict[str, Dict[str, Dict[str, str]]] = {}

        for name, base in base_colors.items():
            palette = generate_tonal_palette(base)
            self.colors[name] = {
                'light': {
                    'primary': palette[40],
                    'onPrimaryFixedVariant': palette[30],
                },
                'dark': {
                    'primary': palette[80],
                    'onPrimaryFixedVariant': palette[80],
                }
            }

    def _apply_multipliers_to_scheme(self, scheme, chroma_multiplier: float, tone_multiplier: float):
        """Apply chroma and tone multipliers to a Material You scheme."""
        # Import here to avoid circular imports
        try:
            from materialyoucolor.hct import Hct
        except ImportError:
            # If multipliers can't be applied, return original scheme
            return scheme
        
        # Get all color properties from the scheme
        color_props = [
            'primary', 'onPrimary', 'primaryContainer', 'onPrimaryContainer',
            'secondary', 'onSecondary', 'secondaryContainer', 'onSecondaryContainer', 
            'tertiary', 'onTertiary', 'tertiaryContainer', 'onTertiaryContainer',
            'error', 'onError', 'errorContainer', 'onErrorContainer',
            'surface', 'onSurface', 'surfaceVariant', 'onSurfaceVariant',
            'outline', 'outlineVariant', 'shadow', 'scrim',
            'inverseSurface', 'inverseOnSurface', 'inversePrimary'
        ]
        
        # Modify colors in place
        for prop in color_props:
            if hasattr(scheme, prop):
                original_argb = getattr(scheme, prop)
                # Convert ARGB to HCT
                hct = Hct.from_int(original_argb)
                # Apply multipliers
                hct.chroma *= chroma_multiplier
                hct.tone *= tone_multiplier
                # Convert back to ARGB and set
                modified_argb = hct.to_int()
                setattr(scheme, prop, modified_argb)
        
        return scheme

    def _apply_multipliers_to_colors(self, colors: Dict[str, str], chroma_multiplier: float, tone_multiplier: float) -> Dict[str, str]:
        """Apply chroma and tone multipliers to color dictionary."""
        # Import here to avoid circular imports
        try:
            from materialyoucolor.hct import Hct
            from core.color_utils import hex_to_rgb
        except ImportError:
            return colors
        
        modified_colors = {}
        for name, hex_color in colors.items():
            # Convert hex to RGB to ARGB
            rgb = hex_to_rgb(hex_color)
            argb = (255 << 24) | (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
            
            # Convert to HCT
            hct = Hct.from_int(argb)
            
            # Apply multipliers
            hct.chroma *= chroma_multiplier
            hct.tone *= tone_multiplier
            
            # Convert back to hex
            modified_argb = hct.to_int()
            r = (modified_argb >> 16) & 0xFF
            g = (modified_argb >> 8) & 0xFF
            b = modified_argb & 0xFF
            modified_colors[name] = f"#{r:02x}{g:02x}{b:02x}"
        
        return modified_colors

    def _generate_palettes_fallback(self):
        """Generate color palettes using HSL fallback when Material You is not available."""
        # Import here to avoid circular imports
        from core.color_utils import hex_to_hsl, hsl_to_hex
        
        # Generate basic colors using HSL
        hsl = hex_to_hsl(self.primary)
        
        # Light theme colors
        self.colors_light = {
            'primary': self.primary,
            'onPrimary': hsl_to_hex(hsl['h'], hsl['s'], 0.95),
            'primaryContainer': hsl_to_hex(hsl['h'], hsl['s'] * 0.8, 0.88),
            'onPrimaryContainer': hsl_to_hex(hsl['h'], hsl['s'], 0.15),
            'secondary': hsl_to_hex((hsl['h'] + 30) % 360, hsl['s'] * 0.6, hsl['l']),
            'onSecondary': hsl_to_hex((hsl['h'] + 30) % 360, hsl['s'] * 0.6, 0.95),
            'secondaryContainer': hsl_to_hex((hsl['h'] + 30) % 360, hsl['s'] * 0.4, 0.88),
            'onSecondaryContainer': hsl_to_hex((hsl['h'] + 30) % 360, hsl['s'] * 0.6, 0.15),
            'tertiary': hsl_to_hex((hsl['h'] + 60) % 360, hsl['s'] * 0.8, hsl['l']),
            'onTertiary': hsl_to_hex((hsl['h'] + 60) % 360, hsl['s'] * 0.8, 0.95),
            'tertiaryContainer': hsl_to_hex((hsl['h'] + 60) % 360, hsl['s'] * 0.6, 0.88),
            'onTertiaryContainer': hsl_to_hex((hsl['h'] + 60) % 360, hsl['s'] * 0.8, 0.15),
            'error': '#ba1a1a',
            'onError': '#ffffff',
            'errorContainer': '#ffdad6',
            'onErrorContainer': '#410002',
            'surface': '#fff8f4',
            'onSurface': '#201812',
            'surfaceVariant': '#f5ded3',
            'onSurfaceVariant': '#53443b',
            'outline': '#857468',
            'outlineVariant': '#d8c2b4',
            'surfaceContainer': '#f9f0ea',
            'surfaceContainerLow': '#fff8f4',
            'surfaceContainerHigh': '#f3e9e1',
            'surfaceContainerHighest': '#ede1d9',
            'surfaceContainerLowest': '#ffffff',
        }
        
        # Dark theme colors
        self.colors_dark = {
            'primary': self.primary,
            'onPrimary': hsl_to_hex(hsl['h'], hsl['s'], 0.15),
            'primaryContainer': hsl_to_hex(hsl['h'], hsl['s'] * 0.8, 0.25),
            'onPrimaryContainer': hsl_to_hex(hsl['h'], hsl['s'], 0.95),
            'secondary': hsl_to_hex((hsl['h'] + 30) % 360, hsl['s'] * 0.6, hsl['l']),
            'onSecondary': hsl_to_hex((hsl['h'] + 30) % 360, hsl['s'] * 0.6, 0.15),
            'secondaryContainer': hsl_to_hex((hsl['h'] + 30) % 360, hsl['s'] * 0.4, 0.25),
            'onSecondaryContainer': hsl_to_hex((hsl['h'] + 30) % 360, hsl['s'] * 0.6, 0.95),
            'tertiary': hsl_to_hex((hsl['h'] + 60) % 360, hsl['s'] * 0.8, hsl['l']),
            'onTertiary': hsl_to_hex((hsl['h'] + 60) % 360, hsl['s'] * 0.8, 0.15),
            'tertiaryContainer': hsl_to_hex((hsl['h'] + 60) % 360, hsl['s'] * 0.6, 0.25),
            'onTertiaryContainer': hsl_to_hex((hsl['h'] + 60) % 360, hsl['s'] * 0.8, 0.95),
            'error': '#ffb4ab',
            'onError': '#690005',
            'errorContainer': '#93000a',
            'onErrorContainer': '#ffb4ab',
            'surface': '#201812',
            'onSurface': '#ede1d9',
            'surfaceVariant': '#53443b',
            'onSurfaceVariant': '#d8c2b4',
            'outline': '#a08d80',
            'outlineVariant': '#53443b',
            'surfaceContainer': '#271d15',
            'surfaceContainerLow': '#201812',
            'surfaceContainerHigh': '#2b241c',
            'surfaceContainerHighest': '#363027',
            'surfaceContainerLowest': '#0b0906',
        }
        
        # Generate tonal palettes
        self.tones_primary = generate_tonal_palette(self.primary)
        self.tones_neutral = generate_neutral_palette(self.primary, 0.05)
        self.tones_neutral_variant = generate_neutral_palette(self.primary, 0.12)
        
        secondary_hue = (hsl['h'] + 30) % 360
        secondary = hsl_to_hex(secondary_hue, hsl['s'] * 0.6, hsl['l'])
        self.tones_secondary = generate_tonal_palette(secondary)
        
        tertiary_hue = (hsl['h'] + 60) % 360
        tertiary = hsl_to_hex(tertiary_hue, hsl['s'] * 0.8, hsl['l'])
        self.tones_tertiary = generate_tonal_palette(tertiary)
        
        self.tones_error = generate_tonal_palette("#ba1a1a")
        
        # Generate semantic colors
        self._generate_semantic_colors(self.primary)

    def _generate_semantic_colors(self, primary_color_for_harmonize: str) -> None:
        """Generate semantic colors (link, visited, negative, neutral, positive) using the exact same approach as kde-material-you-colors."""
        # Import here to avoid circular imports
        from core.color_utils import create_material_you_scheme, get_material_you_colors_from_scheme
        from materialyoucolor.blend import Blend
        from materialyoucolor.utils.color_utils import argb_from_rgb
        
        def hex_to_argb(hex_color: str) -> int:
            """Convert hex color to ARGB int."""
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return argb_from_rgb(r, g, b)
        
        def argb_to_hex(argb: int) -> str:
            """Convert ARGB int to hex color."""
            r = (argb >> 16) & 0xFF
            g = (argb >> 8) & 0xFF
            b = argb & 0xFF
            return f"#{r:02x}{g:02x}{b:02x}"
        
        # Use the exact same base colors as kde-material-you-colors
        base_text_states = [
            {"name": "link", "value": "#2980b9", "blend": True},
            {"name": "visited", "value": "#9b59b6", "blend": True},
            {"name": "negative", "value": "#da4453", "blend": True},
            {"name": "neutral", "value": "#f67400", "blend": True},
            {"name": "positive", "value": "#27ae60", "blend": True},
        ]

        self.colors: Dict[str, Dict[str, Dict[str, str]]] = {}

        # Get the primary color from the main Material You scheme for harmonization
        # This should be the primary from the dark scheme as used in kde-material-you-colors
        
        for color in base_text_states:
            name = color["name"]
            base_hex = color["value"]
            
            # Harmonize with primary color if blend is True (as in kde-material-you-colors)
            if color["blend"]:
                base_argb = hex_to_argb(base_hex)
                harmonized_argb = Blend.harmonize(base_argb, hex_to_argb(primary_color_for_harmonize))
                harmonized_hex = argb_to_hex(harmonized_argb)
            else:
                harmonized_hex = base_hex
            
            # Create a vibrant scheme for this semantic color (like kde-material-you-colors does)
            scheme = create_material_you_scheme(harmonized_hex, is_dark=False, variant=6)  # SchemeVibrant
            colors_light = get_material_you_colors_from_scheme(scheme, is_dark=False)
            
            scheme_dark = create_material_you_scheme(harmonized_hex, is_dark=True, variant=6)
            colors_dark = get_material_you_colors_from_scheme(scheme_dark, is_dark=True)
            
            # Apply multipliers if available
            if hasattr(self, 'chroma_multiplier') and hasattr(self, 'tone_multiplier'):
                # Apply multipliers to the semantic colors
                colors_light = self._apply_multipliers_to_colors(colors_light, self.chroma_multiplier, self.tone_multiplier)
                colors_dark = self._apply_multipliers_to_colors(colors_dark, self.chroma_multiplier, self.tone_multiplier)
            
            self.colors[name] = {
                'light': {
                    'primary': colors_light.get('primary', harmonized_hex),
                    'onPrimaryFixedVariant': colors_light.get('onPrimaryFixedVariant', harmonized_hex),
                },
                'dark': {
                    'primary': colors_dark.get('primary', harmonized_hex),
                    'onPrimaryFixedVariant': colors_dark.get('onPrimaryFixedVariant', harmonized_hex),
                }
            }

    def _generate_scheme(self, is_dark: bool) -> str:
        """Generate a KDE color scheme for light or dark mode.
        
        Args:
            is_dark: True for dark scheme, False for light scheme
            
        Returns:
            KDE color scheme as string
        """
        # Use Material You colors if available, otherwise fall back to tonal palettes
        if hasattr(self, 'colors_light') and hasattr(self, 'colors_dark'):
            colors = self.colors_dark if is_dark else self.colors_light
            
            # Map Material You colors to KDE scheme colors (similar to kde-material-you-colors)
            primary = colors['primary']
            on_primary = colors['onPrimary']
            secondary = colors['secondary']
            on_secondary = colors['onSecondary']
            
            surface = colors['surface']
            on_surface = colors['onSurface']
            surface_variant = colors['surfaceVariant']
            on_surface_variant = colors['onSurfaceVariant']
            surface_container = colors['surfaceContainer']
            surface_container_high = colors['surfaceContainerHigh']
            surface_container_highest = colors['surfaceContainerHighest']
            surface_container_lowest = colors['surfaceContainerLowest']
            
            # Use the correct surface colors for View background (matching kde-material-you-colors)
            surface_dim = colors['surfaceDim']
            surface_bright = colors['surfaceBright']
            
            outline = colors['outline']
            
            # Use correct inverse and secondary colors
            inverse_surface = colors['inverseSurface']
            inverse_primary = colors['inversePrimary']
            secondary_fixed = colors['secondaryFixed']
            
            # Secondary container for WM section
            secondary_container = colors['secondaryContainer']
            
            # For extras (link, negative, etc.)
            if hasattr(self, 'colors') and 'link' in self.colors:
                extras_mode = 'dark' if is_dark else 'light'
                link_primary = self.colors['link'][extras_mode]['primary']
                negative_primary = self.colors['negative'][extras_mode]['primary']
                neutral_primary = self.colors['neutral'][extras_mode]['primary']
                positive_primary = self.colors['positive'][extras_mode]['primary']
                visited_primary = self.colors['visited'][extras_mode]['primary']
            else:
                # Fallback colors
                link_primary = '#2980b9' if not is_dark else '#5dade2'
                negative_primary = '#da4453' if not is_dark else '#ec7063'
                neutral_primary = '#f67400' if not is_dark else '#f8c471'
                positive_primary = '#27ae60' if not is_dark else '#82e0aa'
                visited_primary = '#9b59b6' if not is_dark else '#bb8fce'
            
            if is_dark:
                extras_mode = 'dark'
                color_scheme_name = 'KuntatinteDark'
                inactive_enabled = 'true'
                active_blend = '252,252,252'
                inactive_blend = '161,169,177'
            else:
                extras_mode = 'light'
                color_scheme_name = 'KuntatinteLight'
                inactive_enabled = 'false'
                active_blend = '227,229,231'
                inactive_blend = '239,240,241'
        else:
            # Fallback to tonal palette method
            if is_dark:
                surface = self.tones_neutral[10]
                surface_dim = self.tones_neutral[5]
                surface_container = self.tones_neutral[12]
                surface_container_high = self.tones_neutral[17]
                surface_container_highest = self.tones_neutral[22]
                surface_container_lowest = self.tones_neutral[5]
                surface_variant = self.tones_neutral_variant[30]

                on_surface = self.tones_neutral[90]
                on_surface_variant = self.tones_neutral_variant[80]
                outline = self.tones_neutral_variant[60]

                primary = self.tones_primary[80]
                on_primary = self.tones_primary[20]

                secondary = self.tones_secondary[80]
                on_secondary = self.tones_secondary[20]
                secondary_container = self.tones_secondary[30]

                inverse_surface = self.tones_neutral[90]
                inverse_primary = self.tones_primary[40]

                extras_mode = 'dark'
                color_scheme_name = 'KuntatinteDark'
                inactive_enabled = 'true'
                active_blend = '252,252,252'
                inactive_blend = '161,169,177'
            else:
                surface = self.tones_neutral[99]
                surface_dim = self.tones_neutral[95]
                surface_container = self.tones_neutral[94]
                surface_container_high = self.tones_neutral[92]
                surface_container_highest = self.tones_neutral[90]
                surface_container_lowest = self.tones_neutral[100]
                surface_variant = self.tones_neutral_variant[90]

                on_surface = self.tones_neutral[10]
                on_surface_variant = self.tones_neutral_variant[30]
                outline = self.tones_neutral_variant[50]

                primary = self.tones_primary[40]
                on_primary = self.tones_primary[100]

                secondary = self.tones_secondary[40]
                on_secondary = self.tones_secondary[100]
                secondary_container = self.tones_secondary[90]

                inverse_surface = self.tones_neutral[20]
                inverse_primary = self.tones_primary[80]

                extras_mode = 'light'
                color_scheme_name = 'KuntatinteLight'
                inactive_enabled = 'false'
                active_blend = '227,229,231'
                inactive_blend = '239,240,241'

        extras = self.colors

        scheme = f"""[ColorEffects:Disabled]
Color={format_rgb(surface_container)}
ColorAmount=0.5
ColorEffect=3
ContrastAmount=0
ContrastEffect=0
IntensityAmount=0
IntensityEffect=0

[ColorEffects:Inactive]
ChangeSelectionColor=true
Color={format_rgb(surface_container_lowest)}
ColorAmount=0.025
ColorEffect=0
ContrastAmount=0.1
ContrastEffect=0
Enable={inactive_enabled}
IntensityAmount=0
IntensityEffect=0

[Colors:Button]
BackgroundAlternate={format_rgb(surface_variant)}
BackgroundNormal={format_rgb(surface_container_high)}
DecorationFocus={format_rgb(primary)}
DecorationHover={format_rgb(primary)}
ForegroundActive={format_rgb(on_surface)}
ForegroundInactive={format_rgb(outline)}
ForegroundLink={format_rgb(extras['link'][extras_mode]['primary'])}
ForegroundNegative={format_rgb(extras['negative'][extras_mode]['primary'])}
ForegroundNeutral={format_rgb(extras['neutral'][extras_mode]['primary'])}
ForegroundNormal={format_rgb(on_surface)}
ForegroundPositive={format_rgb(extras['positive'][extras_mode]['primary'])}
ForegroundVisited={format_rgb(extras['visited'][extras_mode]['primary'])}

[Colors:Complementary]
BackgroundAlternate={format_rgb(surface)}
BackgroundNormal={format_rgb(surface_container)}
DecorationFocus={format_rgb(primary)}
DecorationHover={format_rgb(primary)}
ForegroundActive={format_rgb(inverse_surface)}
ForegroundInactive={format_rgb(outline)}
ForegroundLink={format_rgb(extras['link'][extras_mode]['primary'])}
ForegroundNegative={format_rgb(extras['negative'][extras_mode]['primary'])}
ForegroundNeutral={format_rgb(extras['neutral'][extras_mode]['primary'])}
ForegroundNormal={format_rgb(on_surface_variant)}
ForegroundPositive={format_rgb(extras['positive'][extras_mode]['primary'])}
ForegroundVisited={format_rgb(extras['visited'][extras_mode]['primary'])}

[Colors:Header]
BackgroundAlternate={format_rgb(surface_container)}
BackgroundNormal={format_rgb(surface_container)}
DecorationFocus={format_rgb(primary)}
DecorationHover={format_rgb(primary)}
ForegroundActive={format_rgb(inverse_surface)}
ForegroundInactive={format_rgb(outline)}
ForegroundLink={format_rgb(extras['link'][extras_mode]['primary'])}
ForegroundNegative={format_rgb(extras['negative'][extras_mode]['primary'])}
ForegroundNeutral={format_rgb(extras['neutral'][extras_mode]['primary'])}
ForegroundNormal={format_rgb(on_surface_variant)}
ForegroundPositive={format_rgb(extras['positive'][extras_mode]['primary'])}
ForegroundVisited={format_rgb(extras['visited'][extras_mode]['primary'])}

[Colors:Header][Inactive]
BackgroundAlternate={format_rgb(surface_container)}
BackgroundNormal={format_rgb(surface_container)}
DecorationFocus={format_rgb(primary)}
DecorationHover={format_rgb(primary)}
ForegroundActive={format_rgb(inverse_surface)}
ForegroundInactive={format_rgb(outline)}
ForegroundLink={format_rgb(extras['link'][extras_mode]['primary'])}
ForegroundNegative={format_rgb(extras['negative'][extras_mode]['primary'])}
ForegroundNeutral={format_rgb(extras['neutral'][extras_mode]['primary'])}
ForegroundNormal={format_rgb(on_surface_variant)}
ForegroundPositive={format_rgb(extras['positive'][extras_mode]['primary'])}
ForegroundVisited={format_rgb(extras['visited'][extras_mode]['primary'])}

[Colors:Selection]
BackgroundAlternate={format_rgb(primary)}
BackgroundNormal={format_rgb(primary)}
DecorationFocus={format_rgb(primary)}
DecorationHover={format_rgb(secondary)}
ForegroundActive={format_rgb(on_primary)}
ForegroundInactive={format_rgb(on_primary)}
ForegroundLink={format_rgb(extras['link'][extras_mode]['onPrimaryFixedVariant'])}
ForegroundNegative={format_rgb(extras['negative'][extras_mode]['onPrimaryFixedVariant'])}
ForegroundNeutral={format_rgb(extras['neutral'][extras_mode]['onPrimaryFixedVariant'])}
ForegroundNormal={format_rgb(on_primary)}
ForegroundPositive={format_rgb(extras['positive'][extras_mode]['onPrimaryFixedVariant'])}
ForegroundVisited={format_rgb(extras['visited'][extras_mode]['onPrimaryFixedVariant'])}

[Colors:Tooltip]
BackgroundAlternate={format_rgb(surface_variant)}
BackgroundNormal={format_rgb(surface_container)}
DecorationFocus={format_rgb(primary)}
DecorationHover={format_rgb(primary)}
ForegroundActive={format_rgb(on_surface)}
ForegroundInactive={format_rgb(outline)}
ForegroundLink={format_rgb(extras['link'][extras_mode]['primary'])}
ForegroundNegative={format_rgb(extras['negative'][extras_mode]['primary'])}
ForegroundNeutral={format_rgb(extras['neutral'][extras_mode]['primary'])}
ForegroundNormal={format_rgb(on_surface)}
ForegroundPositive={format_rgb(extras['positive'][extras_mode]['primary'])}
ForegroundVisited={format_rgb(extras['visited'][extras_mode]['primary'])}

[Colors:View]
BackgroundAlternate={format_rgb(surface_container)}
BackgroundNormal={format_rgb(surface_dim if is_dark else surface_bright)}
DecorationFocus={format_rgb(primary)}
DecorationHover={format_rgb(inverse_primary if is_dark else secondary_fixed)}
ForegroundActive={format_rgb(inverse_surface)}
ForegroundInactive={format_rgb(outline)}
ForegroundLink={format_rgb(extras['link'][extras_mode]['primary'])}
ForegroundNegative={format_rgb(extras['negative'][extras_mode]['primary'])}
ForegroundNeutral={format_rgb(extras['neutral'][extras_mode]['primary'])}
ForegroundNormal={format_rgb(on_surface)}
ForegroundPositive={format_rgb(extras['positive'][extras_mode]['primary'])}
ForegroundVisited={format_rgb(extras['visited'][extras_mode]['primary'])}

[Colors:Window]
BackgroundAlternate={format_rgb(surface_variant)}
BackgroundNormal={format_rgb(surface_container)}
DecorationFocus={format_rgb(primary)}
DecorationHover={format_rgb(primary)}
ForegroundActive={format_rgb(extras['link'][extras_mode]['primary'])}
ForegroundInactive={format_rgb(outline)}
ForegroundLink={format_rgb(extras['link'][extras_mode]['primary'])}
ForegroundNegative={format_rgb(extras['negative'][extras_mode]['primary'])}
ForegroundNeutral={format_rgb(extras['neutral'][extras_mode]['primary'])}
ForegroundNormal={format_rgb(on_surface_variant)}
ForegroundPositive={format_rgb(extras['positive'][extras_mode]['primary'])}
ForegroundVisited={format_rgb(extras['visited'][extras_mode]['primary'])}

[General]
ColorScheme={color_scheme_name}
Name={color_scheme_name}
shadeSortColumn=true

[KDE]
contrast=4

[WM]
activeBackground={hex2alpha(surface_container_highest, self.toolbar_opacity)}
activeBlend={active_blend}
activeForeground={format_rgb(on_surface)}
inactiveBackground={hex2alpha(secondary_container, self.toolbar_opacity)}
inactiveBlend={inactive_blend}
inactiveForeground={format_rgb(on_surface_variant)}
"""
        return scheme

    def _generate_light_scheme(self) -> str:
        """Generate light KDE color scheme."""
        return self._generate_scheme(is_dark=False)

    def _generate_dark_scheme(self) -> str:
        """Generate dark KDE color scheme."""
        return self._generate_scheme(is_dark=True)

    def get_light_scheme(self) -> str:
        return self._light_scheme

    def get_dark_scheme(self) -> str:
        return self._dark_scheme

    def get_tonal_palettes(self) -> Dict[str, Dict[int, str]]:
        return {
            'primary': self.tones_primary,
            'secondary': self.tones_secondary,
            'tertiary': self.tones_tertiary,
            'neutral': self.tones_neutral,
            'neutralVariant': self.tones_neutral_variant,
            'error': self.tones_error,
        }

    def get_preview_colors(self, is_dark: bool = True) -> Dict[str, str]:
        if is_dark:
            return {
                'surface': self.tones_neutral[10],
                'onSurface': self.tones_neutral[90],
                'primary': self.tones_primary[80],
                'onPrimary': self.tones_primary[20],
                'secondary': self.tones_secondary[80],
                'tertiary': self.tones_tertiary[80],
                'error': self.tones_error[80],
                'outline': self.tones_neutral_variant[60],
            }
        else:
            return {
                'surface': self.tones_neutral[99],
                'onSurface': self.tones_neutral[10],
                'primary': self.tones_primary[40],
                'onPrimary': self.tones_primary[100],
                'secondary': self.tones_secondary[40],
                'tertiary': self.tones_tertiary[40],
                'error': self.tones_error[40],
                'outline': self.tones_neutral_variant[50],
            }


def generate_kuntatinte_schemes(
    palette: List[str],
    primary_index: int = 0,
    toolbar_opacity: int = 100,
    scheme_variant: int = 5,
    chroma_multiplier: float = 1.0,
    tone_multiplier: float = 0.8
) -> Tuple[str, str]:
    generator = KuntatinteSchemeGenerator(palette, primary_index, scheme_variant, toolbar_opacity, chroma_multiplier, tone_multiplier)
    return generator.get_light_scheme(), generator.get_dark_scheme()


def save_kuntatinte_scheme(scheme_content: str, scheme_name: str) -> Tuple[bool, str]:
    user_schemes_dir = Path.home() / ".local/share/color-schemes"
    user_schemes_dir.mkdir(parents=True, exist_ok=True)

    scheme_path = user_schemes_dir / f"{scheme_name}.colors"

    if scheme_path.exists():
        backup_dir = user_schemes_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{scheme_name}_{timestamp}.colors"
        try:
            shutil.copy(scheme_path, backup_path)
        except Exception as e:
            logger.warning(f"Could not create backup: {e}")

    try:
        with open(scheme_path, 'w', encoding='utf-8') as f:
            f.write(scheme_content)
        return True, f"Scheme saved: {scheme_path}"
    except Exception as e:
        return False, f"Error saving scheme: {e}"


def apply_kuntatinte_scheme(scheme_name: str) -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            ["plasma-apply-colorscheme", scheme_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True, f"Applied: {scheme_name}"
        else:
            return False, f"Error: {result.stderr}"
    except Exception as e:
        return False, f"Error applying scheme: {e}"


def generate_and_save_kuntatinte_schemes(
    palette: List[str],
    primary_index: int = 0,
    toolbar_opacity: int = 100,
    scheme_variant: int = 5
) -> Tuple[bool, str]:
    if not palette:
        return False, "No palette provided"

    light_scheme, dark_scheme = generate_kuntatinte_schemes(
        palette, primary_index, toolbar_opacity, scheme_variant
    )

    success_light, msg_light = save_kuntatinte_scheme(light_scheme, "KuntatinteLight")
    success_dark, msg_dark = save_kuntatinte_scheme(dark_scheme, "KuntatinteDark")

    if success_light and success_dark:
        return True, "Kuntatinte Light and Dark schemes generated successfully"
    else:
        errors = []
        if not success_light:
            errors.append(msg_light)
        if not success_dark:
            errors.append(msg_dark)
        return False, "; ".join(errors)


def parse_scheme_colors(scheme_content: str) -> Dict[str, str]:
    """Parse KDE color scheme content and extract key colors for preview."""
    lines = scheme_content.split('\n')
    colors = {}
    
    current_section = None
    for line in lines:
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            current_section = line[1:-1]
        elif '=' in line and current_section:
            key, value = line.split('=', 1)
            key = key.strip()
            
            # Extract RGB values from KDE color format (e.g., "191,173,160")
            if ',' in value:
                rgb = value.strip()
                # Convert to hex format for QML
                try:
                    r, g, b = map(int, rgb.split(','))
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    # Map KDE color keys to preview-friendly names
                    if current_section == 'Colors:Window':
                        if key == 'BackgroundNormal':
                            colors['window_bg'] = hex_color
                        elif key == 'ForegroundNormal':
                            colors['window_fg'] = hex_color
                    elif current_section == 'Colors:Button':
                        if key == 'BackgroundNormal':
                            colors['button_bg'] = hex_color
                        elif key == 'ForegroundNormal':
                            colors['button_fg'] = hex_color
                    elif current_section == 'Colors:View':
                        if key == 'BackgroundNormal':
                            colors['view_bg'] = hex_color
                        elif key == 'ForegroundNormal':
                            colors['view_fg'] = hex_color
                    elif current_section == 'Colors:Selection':
                        if key == 'BackgroundNormal':
                            colors['selection_bg'] = hex_color
                        elif key == 'ForegroundNormal':
                            colors['selection_fg'] = hex_color
                    elif current_section == 'Colors:Button':
                        if key == 'BackgroundAlternate':
                            colors['button_alt_bg'] = hex_color
                        elif key == 'DecorationHover':
                            colors['button_hover'] = hex_color
                except ValueError:
                    pass
    
    # Provide defaults if colors not found
    colors.setdefault('window_bg', '#f5f5f5')
    colors.setdefault('window_fg', '#000000')
    colors.setdefault('button_bg', '#e0e0e0')
    colors.setdefault('button_fg', '#000000')
    colors.setdefault('button_alt_bg', '#d0d0d0')
    colors.setdefault('button_hover', '#c0c0c0')
    colors.setdefault('view_bg', '#ffffff')
    colors.setdefault('view_fg', '#000000')
    colors.setdefault('selection_bg', '#0078d4')
    colors.setdefault('selection_fg', '#ffffff')
    
    return colors


def get_preview_data(
    palette: List[str],
    primary_index: int = 0,
    scheme_variant: int = 5
) -> Dict[str, Any]:
    generator = KuntatinteSchemeGenerator(palette, primary_index, scheme_variant)
    
    # Generate actual KDE schemes to get real colors
    light_scheme = generator.get_light_scheme()
    dark_scheme = generator.get_dark_scheme()
    
    # Parse the schemes to extract real KDE section colors
    light_colors = parse_scheme_colors(light_scheme)
    dark_colors = parse_scheme_colors(dark_scheme)
    
    return {
        'light': light_colors,
        'dark': dark_colors,
        'palettes': generator.get_tonal_palettes(),
    }


__all__ = [
    # kde-like helpers
    'get_scheme_file_path', 'parse_scheme_file', 'get_scheme_structure',
    'get_color_sections', 'get_inactive_sections', 'get_section_colors',
    'get_current_scheme_name', 'parse_kde_color', 'format_kde_color',
    'read_color', 'read_color_with_opacity', 'write_color', 'COLOR_SETS', 'COLOR_KEYS',
    'get_color_set', 'get_all_colors', 'apply_palette_to_scheme', 'notify_color_change',
    'read_color_from_scheme', 'get_color_set_from_scheme', 'get_color_schemes_list',
    'apply_color_scheme', 'save_color_scheme', 'save_color_scheme_from_data',
    # v2 generator
    'generate_kuntatinte_schemes', 'save_kuntatinte_scheme', 'apply_kuntatinte_scheme',
    'generate_and_save_kuntatinte_schemes', 'get_preview_data', 'parse_scheme_colors', 'KuntatinteSchemeGenerator'
]
