"""
Pywal palette generation based on Kuntatinte Color Scheme inputs.
"""

import json
import logging
from typing import Dict, Any, Optional
import os

try:
    from material_color_utilities import (
        theme_from_color,
        TonalPalette,
        Hct,
        argb_from_hex,
        hex_from_argb
    )
    MATERIAL_COLOR_UTILITIES_AVAILABLE = True
except ImportError:
    MATERIAL_COLOR_UTILITIES_AVAILABLE = False
    # Fallback imports
    from .imagemagick import get_color_hsl
    from .color_utils import hsl_to_hex

from integrations.pywal import generate_palette

logger = logging.getLogger(__name__)

def load_pywal_colors(cache_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Load colors.json from pywal cache."""
    if cache_dir is None:
        cache_dir = os.path.expanduser("~/.cache/wal")
    
    colors_path = os.path.join(cache_dir, "colors.json")
    if os.path.exists(colors_path):
        try:
            with open(colors_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load pywal colors.json: {e}")
    return None

def compare_pywal_palettes(kuntatinte_palette: Dict[str, Any], pywal_palette: Dict[str, Any]) -> str:
    """Compare Kuntatinte palette with pywal palette and return differences."""
    result = "Comparison between Kuntatinte and pywal palettes:\n\n"
    
    # Extract colors from kuntatinte (assuming it's the format from generate_pywal_palettes)
    # kuntatinte_palette should have 'Dark Palette' and 'Light Palette'
    kuntatinte_dark = kuntatinte_palette.get('Dark Palette', {})
    kuntatinte_light = kuntatinte_palette.get('Light Palette', {})
    
    # pywal_palette is typically {'color0': '#...', 'color1': '#...', ...}
    pywal_colors = pywal_palette.get('colors', pywal_palette)  # Handle both formats
    
    # Compare dark palette (assuming dark is used)
    result += "Dark Palette Comparison:\n"
    for i in range(16):
        color_key = f'color{i}'
        kuntatinte_color = kuntatinte_dark.get(color_key, 'N/A')
        pywal_color = pywal_colors.get(color_key, 'N/A')
        match = "✓" if kuntatinte_color == pywal_color else "✗"
        result += f"  {color_key}: Kuntatinte={kuntatinte_color} | pywal={pywal_color} {match}\n"
    
    result += "\nLight Palette Comparison:\n"
    for i in range(16):
        color_key = f'color{i}'
        kuntatinte_color = kuntatinte_light.get(color_key, 'N/A')
        pywal_color = pywal_colors.get(color_key, 'N/A')
        match = "✓" if kuntatinte_color == pywal_color else "✗"
        result += f"  {color_key}: Kuntatinte={kuntatinte_color} | pywal={pywal_color} {match}\n"
    
    return result

def generate_tones_from_color(base_hex: str, chroma_multiplier: float = 1.0, tone_multiplier: float = 1.0) -> Dict[str, str]:
    """Generate a set of tones from a base color, simulating Material You palettes."""
    # Material You tone levels: 0, 10, 20, ..., 100
    # Map to lightness values (0 = black, 100 = white)
    tone_to_lightness = {
        0: 0, 10: 10, 20: 20, 30: 30, 40: 40, 50: 50,
        60: 60, 70: 70, 80: 80, 90: 90, 95: 95, 99: 99, 100: 100
    }
    
    tones = {}
    hsl = get_color_hsl(base_hex)
    base_saturation = hsl['s'] * chroma_multiplier  # Apply chroma multiplier to saturation
    base_saturation = min(100, max(0, base_saturation))
    
    for tone, lightness in tone_to_lightness.items():
        # Adjust lightness with tone_multiplier (closer to 1.0 keeps original, <1.0 darker, >1.0 lighter)
        adjusted_lightness = lightness * tone_multiplier
        adjusted_lightness = min(100, max(0, adjusted_lightness))
        
        # Adjust saturation slightly for different tones
        saturation = base_saturation * (0.5 + adjusted_lightness / 200.0)  # Lower saturation for extremes
        saturation = min(100, max(0, saturation))
        tones[tone] = hsl_to_hex(hsl['h'], saturation, adjusted_lightness)
    
    return tones

def adjust_brightness(hex_color: str, factor: float) -> str:
    """Adjust brightness of a hex color."""
    if MATERIAL_COLOR_UTILITIES_AVAILABLE:
        # Use material-color-utilities for more accurate adjustment
        argb = argb_from_hex(hex_color)
        hct = Hct(argb)
        new_tone = min(100, max(0, int(hct.tone * factor)))
        # Use TonalPalette to get the color at the new tone
        palette = TonalPalette(hct.hue, hct.chroma)
        return palette.get(new_tone)
    else:
        # Fallback to HSL
        hsl = get_color_hsl(hex_color)
        new_l = min(100, max(0, hsl['l'] * factor))
        return hsl_to_hex(hsl['h'], hsl['s'], new_l)

def get_color_schemes(primary_color: str, scheme_variant: int = 5, chroma_multiplier: float = 1.0, tone_multiplier: float = 1.0) -> Dict[str, Any]:
    """Generate color schemes for dark and light modes."""
    if MATERIAL_COLOR_UTILITIES_AVAILABLE:
        # Use material-color-utilities for accurate Material You colors
        primary_argb = argb_from_hex(primary_color)
        primary_hct = Hct(primary_argb)
        
        # Apply chroma multiplier
        modified_chroma = primary_hct.chroma * chroma_multiplier
        
        # Create palettes
        primary_palette = TonalPalette(primary_hct.hue, modified_chroma)
        
        # Generate tones with tone multiplier applied
        tones = {}
        for tone in [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99]:
            modified_tone = min(100, max(0, int(tone * tone_multiplier)))
            tones[tone] = primary_palette.get(modified_tone)
        
        # For dark scheme: use darker tones for backgrounds, lighter for foregrounds
        dark_primary = {k: v for k, v in tones.items() if k in [30, 40, 50, 60, 70]}
        dark_secondary = {k: adjust_brightness(v, 0.9) for k, v in dark_primary.items()}  # Slightly dim
        dark_neutral = {k: v for k, v in tones.items() if k in [10, 20, 80, 90, 99]}
        
        # For light scheme: use lighter tones
        light_primary = {k: v for k, v in tones.items() if k in [40, 50, 60, 70, 80]}
        light_secondary = {k: adjust_brightness(v, 1.1) for k, v in light_primary.items()}  # Slightly brighter
        light_neutral = {k: v for k, v in tones.items() if k in [10, 20, 80, 90, 95, 99]}
    else:
        # Fallback to HSL approximations
        # Generate full tonal palette
        tones = generate_tones_from_color(primary_color, chroma_multiplier, tone_multiplier)
        
        # For dark scheme: use darker tones for backgrounds, lighter for foregrounds
        dark_primary = {k: v for k, v in tones.items() if k in [30, 40, 50, 60, 70, 80]}
        dark_secondary = {k: adjust_brightness(v, 0.9) for k, v in dark_primary.items()}  # Slightly dim
        dark_neutral = {k: v for k, v in tones.items() if k in [10, 20, 80, 90, 99]}
        
        # For light scheme: use lighter tones
        light_primary = {k: v for k, v in tones.items() if k in [40, 50, 60, 70, 80, 90]}
        light_secondary = {k: adjust_brightness(v, 1.1) for k, v in light_primary.items()}  # Slightly brighter
        light_neutral = {k: v for k, v in tones.items() if k in [10, 20, 80, 90, 95, 99]}
    
    return {
        'dark': {
            'primary': dark_primary,
            'secondary': dark_secondary,
            'neutral': dark_neutral
        },
        'light': {
            'primary': light_primary,
            'secondary': light_secondary,
            'neutral': light_neutral
        }
    }

def generate_pywal_palettes(primary_color: str, accent_color: str = "", scheme_variant: int = 5, chroma_multiplier: float = 1.0, tone_multiplier: float = 1.0, wallpaper_path: Optional[str] = None) -> str:
    """Generate pywal palettes for light and dark modes."""
    try:
        # Use primary_color as base
        color_source = primary_color or "#6750A4"  # Default Material You purple
        
        # Get schemes
        schemes = get_color_schemes(color_source, scheme_variant, chroma_multiplier, tone_multiplier)
        
        # Extract wallpaper colors if provided
        wallpaper_special_colors = None
        if wallpaper_path:
            try:
                wallpaper_palette = generate_palette(wallpaper_path, cols=16)
                if len(wallpaper_palette) >= 16:
                    wallpaper_special_colors = {
                        'background': wallpaper_palette[0],  # color0
                        'foreground': wallpaper_palette[15]  # color15
                    }
                logger.info(f"Extracted special colors from wallpaper: {wallpaper_special_colors}")
            except Exception as e:
                logger.warning(f"Failed to extract colors from wallpaper: {e}")
        
        # Build output with parameters
        params = {
            "primary_color": color_source,
            "accent_color": accent_color,
            "scheme_variant": scheme_variant,
            "chroma_multiplier": chroma_multiplier,
            "tone_multiplier": tone_multiplier,
            "wallpaper_path": wallpaper_path
        }
        
        result = f"Input Parameters:\n{json.dumps(params, indent=2)}\n\n"
        
        # Build pywal-like palettes (simplified)
        dark_primary = schemes['dark']['primary']
        dark_secondary = schemes['dark']['secondary']
        dark_neutral = schemes['dark']['neutral']
        
        dark_palette = {
            'background': wallpaper_special_colors['background'] if wallpaper_special_colors else dark_neutral[10],
            'foreground': wallpaper_special_colors['foreground'] if wallpaper_special_colors else dark_neutral[90],
            'color0': dark_neutral[10],
            'color1': dark_primary[70],
            'color2': dark_secondary[70],
            'color3': dark_primary[60],
            'color4': dark_primary[50],
            'color5': dark_secondary[50],
            'color6': dark_primary[40],
            'color7': dark_neutral[80],
            'color8': dark_neutral[20],
            'color9': dark_primary[60],
            'color10': dark_secondary[60],
            'color11': dark_primary[50],
            'color12': dark_primary[40],
            'color13': dark_secondary[40],
            'color14': dark_primary[30],
            'color15': dark_neutral[90],
        }
        
        light_primary = schemes['light']['primary']
        light_secondary = schemes['light']['secondary']
        light_neutral = schemes['light']['neutral']
        
        light_palette = {
            'background': wallpaper_special_colors['background'] if wallpaper_special_colors else light_neutral[99],
            'foreground': wallpaper_special_colors['foreground'] if wallpaper_special_colors else light_neutral[10],
            'color0': light_neutral[99],
            'color1': light_primary[40],
            'color2': light_secondary[40],
            'color3': light_primary[40],
            'color4': light_primary[50],
            'color5': light_secondary[50],
            'color6': light_primary[60],
            'color7': light_neutral[20],
            'color8': light_neutral[80],
            'color9': light_primary[50],
            'color10': light_secondary[50],
            'color11': light_primary[60],
            'color12': light_primary[70],
            'color13': light_secondary[70],
            'color14': light_primary[80],
            'color15': light_neutral[10],
        }
        
        result += f"Dark Palette:\n{json.dumps(dark_palette, indent=2)}\n\nLight Palette:\n{json.dumps(light_palette, indent=2)}"
        logger.info("Generated pywal palettes")
        return result
    except Exception as e:
        logger.error(f"Error generating pywal palettes: {e}")
        return f"Error: {str(e)}"

def generate_and_compare_pywal_palettes(primary_color: str, accent_color: str = "", scheme_variant: int = 5, chroma_multiplier: float = 1.0, tone_multiplier: float = 1.0, wallpaper_path: Optional[str] = None, pywal_cache_dir: Optional[str] = None) -> str:
    """Generate pywal palettes and compare with current pywal cache."""
    # Generate Kuntatinte palette
    kuntatinte_output = generate_pywal_palettes(primary_color, accent_color, scheme_variant, chroma_multiplier, tone_multiplier, wallpaper_path)
    
    # Try to load pywal colors
    pywal_colors = load_pywal_colors(pywal_cache_dir)
    if pywal_colors is None:
        return kuntatinte_output + "\n\nNo pywal colors.json found in cache."
    
    # Parse kuntatinte output to get palettes
    try:
        # The output has "Dark Palette:\n{json}\n\nLight Palette:\n{json}"
        lines = kuntatinte_output.split('\n')
        dark_start = None
        light_start = None
        for i, line in enumerate(lines):
            if line.startswith('Dark Palette:'):
                dark_start = i + 1
            elif line.startswith('Light Palette:'):
                light_start = i + 1
        
        if dark_start and light_start:
            dark_json = '\n'.join(lines[dark_start:light_start-2])  # -2 to skip empty line
            light_json = '\n'.join(lines[light_start:])
            kuntatinte_dark = json.loads(dark_json)
            kuntatinte_light = json.loads(light_json)
            kuntatinte_palettes = {
                'Dark Palette': kuntatinte_dark,
                'Light Palette': kuntatinte_light
            }
        else:
            return kuntatinte_output + "\n\nFailed to parse Kuntatinte palettes for comparison."
    except Exception as e:
        return kuntatinte_output + f"\n\nFailed to parse palettes: {e}"
    
    # Compare
    comparison = compare_pywal_palettes(kuntatinte_palettes, pywal_colors)
    
    return kuntatinte_output + "\n\n" + comparison

def save_kuntatinte_colors_json(primary_color: str, accent_color: str = "", scheme_variant: int = 5, chroma_multiplier: float = 1.0, tone_multiplier: float = 1.0, wallpaper_path: Optional[str] = None, config_dir: str = "") -> None:
    """Generate and save Kuntatinte colors as pywal-style colors.json."""
    import json
    from pathlib import Path
    
    if not config_dir:
        config_dir = str(Path.home() / ".config" / "kuntatinte")
    
    Path(config_dir).mkdir(parents=True, exist_ok=True)
    colors_path = Path(config_dir) / "colors.json"
    
    # Generate palettes
    schemes = get_color_schemes(primary_color, scheme_variant, chroma_multiplier, tone_multiplier)
    
    # Extract wallpaper colors if provided
    wallpaper_special_colors = None
    if wallpaper_path:
        try:
            wallpaper_palette = generate_palette(wallpaper_path, cols=16)
            if len(wallpaper_palette) >= 16:
                wallpaper_special_colors = {
                    'background': wallpaper_palette[0],
                    'foreground': wallpaper_palette[15]
                }
        except Exception as e:
            logger.warning(f"Failed to extract colors from wallpaper: {e}")
    
    # Use dark palette for pywal format
    dark_primary = schemes['dark']['primary']
    dark_secondary = schemes['dark']['secondary']
    dark_neutral = schemes['dark']['neutral']
    
    dark_palette = {
        'background': wallpaper_special_colors['background'] if wallpaper_special_colors else dark_neutral[10],
        'foreground': wallpaper_special_colors['foreground'] if wallpaper_special_colors else dark_neutral[90],
        'color0': dark_neutral[10],
        'color1': dark_primary[70],
        'color2': dark_secondary[70],
        'color3': dark_primary[60],
        'color4': dark_primary[50],
        'color5': dark_secondary[50],
        'color6': dark_primary[40],
        'color7': dark_neutral[80],
        'color8': dark_neutral[20],
        'color9': dark_primary[60],
        'color10': dark_secondary[60],
        'color11': dark_primary[50],
        'color12': dark_primary[40],
        'color13': dark_secondary[40],
        'color14': dark_primary[30],
        'color15': dark_neutral[90],
    }
    
    # Convert to pywal format
    pywal_json = {
        "wallpaper": wallpaper_path or primary_color,
        "alpha": "100",
        "special": {
            "background": dark_palette['background'],
            "foreground": dark_palette['foreground'],
            "cursor": dark_palette['foreground']
        },
        "colors": {k: v for k, v in dark_palette.items() if k.startswith('color')}
    }
    
    with open(colors_path, 'w', encoding='utf-8') as f:
        json.dump(pywal_json, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Saved Kuntatinte colors.json to {colors_path}")

def compare_colors_json(kuntatinte_config_dir: str = "", pywal_cache_dir: str = "") -> bool:
    """Compare Kuntatinte's colors.json with pywal's colors.json.

    Returns:
        True if palettes match, False otherwise.
    """
    import json
    import os
    from pathlib import Path
    
    if not kuntatinte_config_dir:
        kuntatinte_config_dir = str(Path.home() / ".config" / "kuntatinte")
    
    if not pywal_cache_dir:
        pywal_cache_dir = os.path.expanduser("~/.cache/wal")
    
    kuntatinte_path = Path(kuntatinte_config_dir) / "colors.json"
    pywal_path = Path(pywal_cache_dir) / "colors.json"
    
    if not kuntatinte_path.exists():
        logger.warning("Kuntatinte colors.json not found")
        return False
    
    if not pywal_path.exists():
        logger.warning("pywal colors.json not found")
        return False
    
    with open(kuntatinte_path, 'r') as f:
        kuntatinte_data = json.load(f)
    
    with open(pywal_path, 'r') as f:
        pywal_data = json.load(f)
    
    # Compare colors
    kuntatinte_colors = kuntatinte_data.get('colors', {})
    pywal_colors = pywal_data.get('colors', {})
    
    kuntatinte_special = kuntatinte_data.get('special', {})
    pywal_special = pywal_data.get('special', {})
    
    matches = True
    for i in range(16):
        color_key = f'color{i}'
        k_color = kuntatinte_colors.get(color_key)
        p_color = pywal_colors.get(color_key)
        if k_color != p_color:
            logger.info(f"Color mismatch {color_key}: Kuntatinte={k_color}, pywal={p_color}")
            matches = False
    
    # Compare special colors
    for key in ['background', 'foreground']:
        k_special = kuntatinte_special.get(key)
        p_special = pywal_special.get(key)
        if k_special != p_special:
            logger.info(f"Special color mismatch {key}: Kuntatinte={k_special}, pywal={p_special}")
            matches = False
    
    logger.info(f"Palette comparison result: {'matches' if matches else 'does not match'}")
    return matches