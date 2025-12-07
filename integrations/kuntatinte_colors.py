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

# Core color utilities
from core.color_utils import (
    hex_to_rgb, hex_to_hsl, hsl_to_hex,
    blend_colors, get_contrast_ratio,
)


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

    a = int(opacity * 255)

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
    hsl = hex_to_hsl(base_color)
    palette: Dict[int, str] = {}
    for tone in TONES:
        new_l = tone
        palette[tone] = hsl_to_hex(hsl['h'], hsl['s'], new_l)
    return palette


def generate_neutral_palette(base_color: str, saturation_factor: float = 0.08) -> Dict[int, str]:
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
    current = color
    for _ in range(100):
        contrast = get_contrast_ratio(current, background)
        if contrast >= min_contrast:
            return current
        current = blend_colors(current, target_color, step)
    return current


def scale_saturation(hex_color: str, factor: float) -> str:
    hsl = hex_to_hsl(hex_color)
    new_s = min(100, max(0, hsl['s'] * factor))
    return hsl_to_hex(hsl['h'], new_s, hsl['l'])


def lighten_color(hex_color: str, amount: float, target: str) -> str:
    return blend_colors(hex_color, target, amount)


def hex2alpha(hex_color: str, opacity: int) -> str:
    r, g, b = hex_to_rgb(hex_color)
    a = int(opacity * 255 / 100)
    return f"{r},{g},{b},{a}"


def format_rgb(hex_color: str) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return f"{r},{g},{b}"


def format_rgba(hex_color: str, opacity: float = 1.0) -> str:
    r, g, b = hex_to_rgb(hex_color)
    a = int(opacity * 255)
    return f"{r},{g},{b},{a}"


class KuntatinteSchemeGenerator:
    def __init__(
        self,
        palette: List[str],
        primary_index: int = 0,
        toolbar_opacity: int = 100
    ):
        self.palette = palette
        self.primary = palette[primary_index] if palette else "#3daee9"
        self.toolbar_opacity = toolbar_opacity
        self._generate_palettes()
        self._light_scheme = self._generate_light_scheme()
        self._dark_scheme = self._generate_dark_scheme()

    def _generate_palettes(self):
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

        self._generate_semantic_colors()

    def _generate_semantic_colors(self) -> None:
        base_colors = {
            'link': "#2980b9",
            'visited': "#9b59b6",
            'negative': "#da4453",
            'neutral': "#f67400",
            'positive': "#27ae60",
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

    def _generate_scheme(self, is_dark: bool) -> str:
        """Generate a KDE color scheme for light or dark mode.
        
        Args:
            is_dark: True for dark scheme, False for light scheme
            
        Returns:
            KDE color scheme as string
        """
        if is_dark:
            # Dark mode: use low tones for surfaces, high tones for "on" colors
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
            # Light mode: use high tones for surfaces, low tones for "on" colors
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
BackgroundNormal={format_rgb(surface_dim)}
DecorationFocus={format_rgb(primary)}
DecorationHover={format_rgb(inverse_primary)}
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
    toolbar_opacity: int = 100
) -> Tuple[str, str]:
    generator = KuntatinteSchemeGenerator(palette, primary_index, toolbar_opacity)
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
    toolbar_opacity: int = 100
) -> Tuple[bool, str]:
    if not palette:
        return False, "No palette provided"

    light_scheme, dark_scheme = generate_kuntatinte_schemes(
        palette, primary_index, toolbar_opacity
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


def get_preview_data(
    palette: List[str],
    primary_index: int = 0
) -> Dict[str, Any]:
    generator = KuntatinteSchemeGenerator(palette, primary_index)
    return {
        'light': generator.get_preview_colors(False),
        'dark': generator.get_preview_colors(True),
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
    'generate_and_save_kuntatinte_schemes', 'get_preview_data', 'KuntatinteSchemeGenerator'
]
