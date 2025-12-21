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
ImageMagick Color Extraction.

Extract ANSI-compatible color palettes from images using ImageMagick.
Supports automatic detection of monochrome, low-diversity, and chromatic images.
"""

import hashlib
import json
import logging
import os
import re
import subprocess
from typing import Callable, Dict, List, Optional, Any, cast


logger = logging.getLogger(__name__)

from core.color_utils import (
    hex_to_rgb,
    hex_to_hsl,
    hsl_to_hex,
    is_dark_color,
    calculate_hue_distance,
)
from core.color_utils import HSL
from core.file_utils import (
    ensure_directory_exists,
    file_exists,
    read_file_as_text,
    write_text_to_file,
)


# =============================================================================
# Constants
# =============================================================================

# Palette configuration
ANSI_PALETTE_SIZE = 16
DOMINANT_COLORS_TO_EXTRACT = 24
CACHE_VERSION = 3

# Image analysis thresholds
MONOCHROME_SATURATION_THRESHOLD = 15
MONOCHROME_IMAGE_THRESHOLD = 0.7
LOW_DIVERSITY_THRESHOLD = 0.6
SIMILAR_HUE_RANGE = 30
SIMILAR_LIGHTNESS_RANGE = 20

# Color filtering thresholds
MIN_CHROMATIC_SATURATION = 15
TOO_DARK_THRESHOLD = 20
TOO_BRIGHT_THRESHOLD = 85

# Background/foreground thresholds
VERY_DARK_BACKGROUND_THRESHOLD = 20
VERY_LIGHT_BACKGROUND_THRESHOLD = 80
MIN_BACKGROUND_LIGHTNESS_DARK = 8
MAX_BACKGROUND_LIGHTNESS_LIGHT = 92
MIN_LIGHTNESS_ON_DARK_BG = 55
MAX_LIGHTNESS_ON_LIGHT_BG = 45
MIN_FOREGROUND_CONTRAST = 40
ABSOLUTE_MIN_LIGHTNESS = 25

# Brightness normalization
OUTLIER_LIGHTNESS_THRESHOLD = 25
BRIGHT_THEME_THRESHOLD = 50
DARK_COLOR_THRESHOLD = 50

# Palette generation
SUBTLE_PALETTE_SATURATION = 28
MONOCHROME_SATURATION = 5
MONOCHROME_COLOR8_SATURATION_FACTOR = 0.5
BRIGHT_COLOR_LIGHTNESS_BOOST = 18
BRIGHT_COLOR_SATURATION_BOOST = 1.25

# ANSI color hue values
ANSI_COLOR_HUES = {
    'RED': 0,
    'GREEN': 120,
    'YELLOW': 60,
    'BLUE': 240,
    'MAGENTA': 300,
    'CYAN': 180,
}

ANSI_HUE_ARRAY = [
    ANSI_COLOR_HUES['RED'],
    ANSI_COLOR_HUES['GREEN'],
    ANSI_COLOR_HUES['YELLOW'],
    ANSI_COLOR_HUES['BLUE'],
    ANSI_COLOR_HUES['MAGENTA'],
    ANSI_COLOR_HUES['CYAN'],
]

# ImageMagick settings - optimized for performance
IMAGE_SCALE_SIZE = '400x300>'  # Reduced from 800x600 for better performance
IMAGE_BIT_DEPTH = 8

# Performance optimizations
DOMINANT_COLORS_TO_EXTRACT = 16  # Reduced from 24 for faster processing


# =============================================================================
# Cache Management
# =============================================================================

def get_cache_dir() -> str:
    """Get the cache directory path for storing extracted palettes."""
    home = os.path.expanduser('~')
    return os.path.join(home, '.cache', 'kuntatinte', 'color-cache')


def get_cache_key(image_path: str, light_mode: bool) -> Optional[str]:
    """Generate a cache key for an image and mode combination.
    
    Args:
        image_path: Path to the image file
        light_mode: Whether to generate a light mode palette
    
    Returns:
        MD5 hash string or None on error
    """
    try:
        mtime = int(os.path.getmtime(image_path))
        mode_str = 'light' if light_mode else 'dark'
        data = f"{image_path}-{mtime}-{mode_str}"
        return hashlib.md5(data.encode('utf-8')).hexdigest()
    except (OSError, ValueError) as e:
        logger.error(f'Error generating cache key: {e}')
        return None


def load_cached_palette(cache_key: str) -> Optional[List[str]]:
    """Load a cached palette if available and valid.
    
    Args:
        cache_key: Cache key from get_cache_key()
    
    Returns:
        List of hex color strings or None if not cached
    """
    try:
        cache_dir = get_cache_dir()
        cache_path = os.path.join(cache_dir, f"{cache_key}.json")
        if not file_exists(cache_path):
            return None
        content = read_file_as_text(cache_path)
        data = json.loads(content)
        if (
            data.get('version') == CACHE_VERSION
            and isinstance(data.get('palette'), list)
            and len(data.get('palette')) == ANSI_PALETTE_SIZE
        ):
            logger.info('Using cached color extraction result')
            return data.get('palette')
        return None
    except (OSError, ValueError, json.JSONDecodeError) as e:
        logger.error(f'Error loading cache: {e}')
        return None


def save_palette_to_cache(cache_key: str, palette: List[str]) -> None:
    """Save a palette to the cache.
    
    Args:
        cache_key: Cache key from get_cache_key()
        palette: List of hex color strings
    """
    try:
        cache_dir = get_cache_dir()
        ensure_directory_exists(cache_dir)
        cache_path = os.path.join(cache_dir, f"{cache_key}.json")
        data = {'palette': palette, 'version': CACHE_VERSION}
        write_text_to_file(cache_path, json.dumps(data, indent=2))
        logger.info('Saved color extraction to cache')
    except (OSError, ValueError) as e:
        logger.error(f'Error saving to cache: {e}')


# =============================================================================
# ImageMagick Integration
# =============================================================================

# Pre-compiled regex pattern for histogram parsing
_HISTOGRAM_PATTERN = re.compile(r"^\s*(\d+):\s*\([^)]+\)\s*(#[0-9A-Fa-f]{6})")


def parse_histogram_output(output: str) -> List[str]:
    """Parse ImageMagick histogram output to extract hex colors.
    
    Args:
        output: Raw histogram output from ImageMagick
    
    Returns:
        List of hex color strings sorted by frequency (most common first)
    """
    lines = output.splitlines()
    color_data = []
    for line in lines:
        m = _HISTOGRAM_PATTERN.match(line)
        if m:
            count = int(m.group(1))
            hexc = m.group(2).upper()
            color_data.append({'hex': hexc, 'count': count})
    color_data.sort(key=lambda x: x['count'], reverse=True)
    return [c['hex'] for c in color_data]


def extract_dominant_colors(image_path: str, num_colors: int) -> List[str]:
    """Extract dominant colors from an image using ImageMagick.
    
    Args:
        image_path: Path to the image file
        num_colors: Number of colors to extract
    
    Returns:
        List of hex color strings
    
    Raises:
        RuntimeError: If ImageMagick fails or no colors are extracted
    """
    argv = [
        'magick',
        image_path,
        '-scale', IMAGE_SCALE_SIZE,
        '-colors', str(num_colors),
        '-depth', str(IMAGE_BIT_DEPTH),
        '-format', '%c',
        'histogram:info:-',
    ]

    try:
        proc = subprocess.run(argv, capture_output=True, text=True, check=True)
        colors = parse_histogram_output(proc.stdout)
        if len(colors) == 0:
            raise RuntimeError('No colors extracted from image')
        return colors
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ImageMagick error: {e.stderr}") from e
    except Exception:
        raise


# =============================================================================
# HSL Cache and Color Analysis
# =============================================================================

# Module-level cache for HSL conversions - persistent across extractions
_hsl_cache: Dict[str, HSL] = {}
_HSL_CACHE_MAX_SIZE = 1000  # Limit cache size to prevent memory issues


def get_color_hsl(hex_color: str) -> HSL:
    """Get HSL values for a hex color with persistent caching.
    
    Args:
        hex_color: Hex color string
    
    Returns:
        Dictionary with h, s, l values
    """
    if hex_color in _hsl_cache:
        return _hsl_cache[hex_color]
    
    # Check cache size and clear if too large
    if len(_hsl_cache) >= _HSL_CACHE_MAX_SIZE:
        # Keep most recently used colors (simple LRU approximation)
        recent_keys = list(_hsl_cache.keys())[-_HSL_CACHE_MAX_SIZE // 2:]
        _hsl_cache.clear()
        # Note: This is a simple implementation. A proper LRU cache would be better
    
    hsl = hex_to_hsl(hex_color)
    _hsl_cache[hex_color] = hsl
    return hsl


def clear_hsl_cache() -> None:
    """Clear the HSL conversion cache."""
    _hsl_cache.clear()


# =============================================================================
# Image Type Detection
# =============================================================================

def is_monochrome_image(colors: List[str]) -> bool:
    """Check if image colors are predominantly monochrome/grayscale.
    
    Args:
        colors: List of hex color strings
    
    Returns:
        True if image is considered monochrome
    """
    low_sat = sum(
        1 for c in colors
        if get_color_hsl(c)['s'] < MONOCHROME_SATURATION_THRESHOLD
    )
    return (low_sat / len(colors)) > MONOCHROME_IMAGE_THRESHOLD


def has_low_color_diversity(colors: List[str]) -> bool:
    """Check if image has low color diversity (similar hues/lightness).
    
    Args:
        colors: List of hex color strings
    
    Returns:
        True if colors are too similar to each other
    """
    hsl_colors = [get_color_hsl(c) for c in colors]
    similar = 0
    total = 0
    n = len(hsl_colors)
    for i in range(n):
        for j in range(i + 1, n):
            c1 = hsl_colors[i]
            c2 = hsl_colors[j]
            if (c1['s'] < MONOCHROME_SATURATION_THRESHOLD or
                    c2['s'] < MONOCHROME_SATURATION_THRESHOLD):
                continue
            total += 1
            hue_diff = calculate_hue_distance(c1['h'], c2['h'])
            light_diff = abs(c1['l'] - c2['l'])
            if hue_diff < SIMILAR_HUE_RANGE and light_diff < SIMILAR_LIGHTNESS_RANGE:
                similar += 1
    if total == 0:
        return False
    return (similar / total) > LOW_DIVERSITY_THRESHOLD


# =============================================================================
# Background and Foreground Selection
# =============================================================================

def find_background_color(
    colors: List[str],
    light_mode: bool
) -> Dict[str, Any]:
    """Find the best background color from extracted colors.
    
    Args:
        colors: List of hex color strings
        light_mode: Whether to find a light background
    
    Returns:
        Dictionary with 'color' (hex) and 'index' keys
    """
    bg_index = -1
    bg_lightness = -1 if light_mode else 101
    
    for i, c in enumerate(colors):
        hsl = get_color_hsl(c)
        if light_mode:
            if hsl['l'] > bg_lightness and hsl['l'] <= MAX_BACKGROUND_LIGHTNESS_LIGHT:
                bg_lightness = hsl['l']
                bg_index = i
        else:
            if hsl['l'] < bg_lightness and hsl['l'] >= MIN_BACKGROUND_LIGHTNESS_DARK:
                bg_lightness = hsl['l']
                bg_index = i

    if bg_index == -1:
        # Find closest to target
        target = MAX_BACKGROUND_LIGHTNESS_LIGHT if light_mode else MIN_BACKGROUND_LIGHTNESS_DARK
        closest = 0
        best_dist = float('inf')
        for i, c in enumerate(colors):
            hsl = get_color_hsl(c)
            d = abs(hsl['l'] - target)
            if d < best_dist:
                best_dist = d
                closest = i
        bg_index = closest

    selected = colors[bg_index]
    selected_hsl = get_color_hsl(selected)

    if not light_mode and selected_hsl['l'] < MIN_BACKGROUND_LIGHTNESS_DARK:
        return {
            'color': hsl_to_hex(
                selected_hsl['h'], selected_hsl['s'], MIN_BACKGROUND_LIGHTNESS_DARK
            ),
            'index': bg_index
        }

    if light_mode and selected_hsl['l'] > MAX_BACKGROUND_LIGHTNESS_LIGHT:
        return {
            'color': hsl_to_hex(
                selected_hsl['h'], selected_hsl['s'], MAX_BACKGROUND_LIGHTNESS_LIGHT
            ),
            'index': bg_index
        }

    return {'color': selected, 'index': bg_index}


def find_foreground_color(
    colors: List[str],
    light_mode: bool,
    used_indices: set,
    bg_lightness: float
) -> Dict[str, Any]:
    """Find the best foreground color with sufficient contrast.
    
    Args:
        colors: List of hex color strings
        light_mode: Whether palette is for light mode
        used_indices: Set of indices already used
        bg_lightness: Background lightness for contrast calculation
    
    Returns:
        Dictionary with 'color' (hex) and 'index' keys
    """
    fg_index = -1
    fg_lightness = 101 if light_mode else -1
    
    for i, c in enumerate(colors):
        if i in used_indices:
            continue
        hsl = get_color_hsl(c)
        if light_mode:
            if hsl['l'] < fg_lightness:
                fg_lightness = hsl['l']
                fg_index = i
        else:
            if hsl['l'] > fg_lightness:
                fg_lightness = hsl['l']
                fg_index = i

    if fg_index == -1:
        target = (max(0, bg_lightness - MIN_FOREGROUND_CONTRAST) if light_mode
                  else min(100, bg_lightness + MIN_FOREGROUND_CONTRAST))
        return {'color': hsl_to_hex(0, 0, target), 'index': 0}

    selected = colors[fg_index]
    selected_hsl = get_color_hsl(selected)
    contrast = abs(selected_hsl['l'] - bg_lightness)
    
    if contrast < MIN_FOREGROUND_CONTRAST:
        target = (max(0, bg_lightness - MIN_FOREGROUND_CONTRAST) if light_mode
                  else min(100, bg_lightness + MIN_FOREGROUND_CONTRAST))
        return {
            'color': hsl_to_hex(selected_hsl['h'], selected_hsl['s'], target),
            'index': fg_index
        }

    return {'color': selected, 'index': fg_index}


# =============================================================================
# Color Matching and Adjustment
# =============================================================================

def calculate_color_score(hsl: HSL, target_hue: float) -> float:
    """Calculate how well a color matches a target ANSI hue.
    
    Args:
        hsl: HSL dictionary of the color
        target_hue: Target ANSI hue value
    
    Returns:
        Score (lower is better)
    """
    hue_diff = calculate_hue_distance(hsl['h'], target_hue) * 3
    saturation_penalty = 50 if hsl['s'] < MIN_CHROMATIC_SATURATION else 0
    lightness_penalty = 0
    if hsl['l'] < TOO_DARK_THRESHOLD or hsl['l'] > TOO_BRIGHT_THRESHOLD:
        lightness_penalty = 10
    return hue_diff + saturation_penalty + lightness_penalty


def find_best_color_match(
    target_hue: float,
    color_pool: List[str],
    used_indices: set
) -> int:
    """Find the best matching color for a target hue.
    
    Args:
        target_hue: Target ANSI hue value
        color_pool: List of available colors
        used_indices: Set of already used indices
    
    Returns:
        Index of the best matching color
    """
    best_index = -1
    best_score = float('inf')
    
    for i, c in enumerate(color_pool):
        if i in used_indices:
            continue
        hsl = get_color_hsl(c)
        score = calculate_color_score(hsl, target_hue)
        if score < best_score:
            best_score = score
            best_index = i
    
    if best_index == -1:
        for i in range(len(color_pool)):
            if i not in used_indices:
                return i
        return 0
    return best_index


def generate_bright_version(hex_color: Optional[str]) -> str:
    """Generate a brighter version of a color for ANSI bright colors.
    
    Args:
        hex_color: Original hex color
    
    Returns:
        Brighter hex color
    """
    if not hex_color:
        return '#000000'
    hsl = get_color_hsl(hex_color)
    new_l = min(100, hsl['l'] + BRIGHT_COLOR_LIGHTNESS_BOOST)
    new_s = min(100, hsl['s'] * BRIGHT_COLOR_SATURATION_BOOST)
    return hsl_to_hex(hsl['h'], new_s, new_l)


def adjust_color_lightness(hex_color: str, target_lightness: float) -> str:
    """Adjust a color to a specific lightness.
    
    Args:
        hex_color: Original hex color
        target_lightness: Target lightness (0-100)
    
    Returns:
        Adjusted hex color
    """
    hsl = get_color_hsl(hex_color)
    return hsl_to_hex(hsl['h'], hsl['s'], target_lightness)


def sort_colors_by_lightness(colors: List[str]) -> List[Dict]:
    """Sort colors by lightness with cached HSL values.
    
    Args:
        colors: List of hex colors
    
    Returns:
        List of dictionaries with color, lightness, and hue
    """
    arr = []
    for c in colors:
        hsl = get_color_hsl(c)  # Uses persistent cache
        arr.append({'color': c, 'lightness': hsl['l'], 'hue': hsl['h']})
    arr.sort(key=lambda x: x['lightness'])
    return arr


# =============================================================================
# Palette Generation
# =============================================================================

def generate_subtle_balanced_palette(
    dominant_colors: List[str],
    light_mode: bool
) -> List[Optional[str]]:
    """Generate a subtle palette for low-diversity images.
    
    Args:
        dominant_colors: List of dominant colors from image
        light_mode: Whether to generate light mode palette
    
    Returns:
        16-color ANSI palette
    """
    sorted_by_lightness = sort_colors_by_lightness(dominant_colors)
    darkest = sorted_by_lightness[0]
    lightest = sorted_by_lightness[-1]

    chromatic = [
        c for c in dominant_colors
        if get_color_hsl(c)['s'] > MONOCHROME_SATURATION_THRESHOLD
    ]
    avg_hue = (
        (sum(get_color_hsl(c)['h'] for c in chromatic) / len(chromatic))
        if chromatic else darkest['hue']
    )

    palette: List[Optional[str]] = [None] * ANSI_PALETTE_SIZE
    palette[0] = lightest['color'] if light_mode else darkest['color']
    palette[7] = darkest['color'] if light_mode else lightest['color']

    for i in range(len(ANSI_HUE_ARRAY)):
        lightness = 50 + (i - 2.5) * 4
        palette[i + 1] = hsl_to_hex(
            ANSI_HUE_ARRAY[i], SUBTLE_PALETTE_SATURATION, lightness
        )

    color8_lightness = (
        max(0, lightest['lightness'] - 15) if light_mode
        else min(100, darkest['lightness'] + 15)
    )
    palette[8] = hsl_to_hex(
        avg_hue, SUBTLE_PALETTE_SATURATION * 0.5, color8_lightness
    )

    bright_saturation = SUBTLE_PALETTE_SATURATION + 8
    for i in range(len(ANSI_HUE_ARRAY)):
        base_lightness = 50 + (i - 2.5) * 4
        adjustment = -8 if light_mode else 8
        lightness = max(0, min(100, base_lightness + adjustment))
        palette[i + 9] = hsl_to_hex(
            ANSI_HUE_ARRAY[i], bright_saturation, lightness
        )

    palette[15] = (
        hsl_to_hex(
            avg_hue, SUBTLE_PALETTE_SATURATION * 0.3,
            max(0, darkest['lightness'] - 5)
        ) if light_mode
        else hsl_to_hex(
            avg_hue, SUBTLE_PALETTE_SATURATION * 0.3,
            min(100, lightest['lightness'] + 5)
        )
    )

    return palette


def generate_monochrome_palette(
    gray_colors: List[str],
    light_mode: bool
) -> List[Optional[str]]:
    """Generate a grayscale palette for monochrome images.
    
    Args:
        gray_colors: List of grayscale colors from image
        light_mode: Whether to generate light mode palette
    
    Returns:
        16-color ANSI palette
    """
    sorted_by_lightness = sort_colors_by_lightness(gray_colors)
    darkest = sorted_by_lightness[0]
    lightest = sorted_by_lightness[-1]
    base_hue = darkest['hue']

    palette: List[Optional[str]] = [None] * ANSI_PALETTE_SIZE
    palette[0] = lightest['color'] if light_mode else darkest['color']
    palette[7] = darkest['color'] if light_mode else lightest['color']

    MIN_STEP = 3
    if light_mode:
        startL = darkest['lightness'] + 10
        endL = min(darkest['lightness'] + 40, lightest['lightness'] - 10)
        if endL <= startL:
            startL = max(0, darkest['lightness'])
            endL = min(100, lightest['lightness'])
        rng = max(endL - startL, MIN_STEP * 5)
        step = rng / 5.0
        for i in range(1, 7):
            lightness = max(0, min(100, startL + (i - 1) * step))
            palette[i] = hsl_to_hex(base_hue, MONOCHROME_SATURATION, lightness)
    else:
        startL = max(darkest['lightness'] + 30, lightest['lightness'] - 40)
        endL = lightest['lightness'] - 10
        if endL <= startL:
            startL = max(0, darkest['lightness'] + 10)
            endL = min(100, lightest['lightness'])
        rng = max(endL - startL, MIN_STEP * 5)
        step = rng / 5.0
        for i in range(1, 7):
            lightness = max(0, min(100, startL + (i - 1) * step))
            palette[i] = hsl_to_hex(base_hue, MONOCHROME_SATURATION, lightness)

    color8_lightness = (
        max(0, darkest['lightness'] + 5) if light_mode
        else min(100, lightest['lightness'] - 25)
    )
    palette[8] = hsl_to_hex(
        base_hue,
        MONOCHROME_SATURATION * MONOCHROME_COLOR8_SATURATION_FACTOR,
        color8_lightness
    )

    for i in range(1, 7):
        hsl = get_color_hsl(cast(str, palette[i]))
        adjustment = -10 if light_mode else 10
        newL = max(0, min(100, hsl['l'] + adjustment))
        palette[i + 8] = hsl_to_hex(base_hue, MONOCHROME_SATURATION, newL)

    palette[15] = (
        hsl_to_hex(base_hue, 2, max(0, darkest['lightness'] - 5))
        if light_mode
        else hsl_to_hex(base_hue, 2, min(100, lightest['lightness'] + 5))
    )

    return palette


def generate_chromatic_palette(
    dominant_colors: List[str],
    light_mode: bool
) -> List[Optional[str]]:
    """Generate a colorful palette for chromatic images.
    
    Args:
        dominant_colors: List of dominant colors from image
        light_mode: Whether to generate light mode palette
    
    Returns:
        16-color ANSI palette
    """
    background = find_background_color(dominant_colors, light_mode)
    used = set([background['index']])
    bg_hsl = get_color_hsl(background['color'])

    foreground = find_foreground_color(
        dominant_colors, light_mode, used, bg_hsl['l']
    )
    used.add(foreground['index'])

    palette: List[Optional[str]] = [None] * ANSI_PALETTE_SIZE
    palette[0] = background['color']
    palette[7] = foreground['color']

    for i in range(len(ANSI_HUE_ARRAY)):
        match_index = find_best_color_match(
            ANSI_HUE_ARRAY[i], dominant_colors, used
        )
        palette[i + 1] = dominant_colors[match_index]
        used.add(match_index)

    color8_lightness = (
        min(100, bg_hsl['l'] + 15) if is_dark_color(background['color'], DARK_COLOR_THRESHOLD)
        else max(0, bg_hsl['l'] - 15)
    )
    palette[8] = hsl_to_hex(bg_hsl['h'], bg_hsl['s'] * 0.5, color8_lightness)

    for i in range(1, 7):
        palette[i + 8] = generate_bright_version(palette[i])

    palette[15] = generate_bright_version(foreground['color'])
    return palette


# =============================================================================
# Brightness Normalization
# =============================================================================

def adjust_color_for_dark_background(
    palette: List[str],
    color_info: Dict
) -> None:
    """Adjust a color for visibility on dark backgrounds.
    
    Args:
        palette: Palette to modify in place
        color_info: Dictionary with 'lightness' and 'index' keys
    """
    if color_info['lightness'] >= MIN_LIGHTNESS_ON_DARK_BG:
        return
    adjusted = MIN_LIGHTNESS_ON_DARK_BG + color_info['index'] * 3
    logger.debug(
        f"Adjusting color {color_info['index']} for dark background: "
        f"{color_info['lightness']:.1f}% → {adjusted:.1f}%"
    )
    if not palette[color_info['index']]:
        palette[color_info['index']] = '#000000'
    palette[color_info['index']] = adjust_color_lightness(
        palette[color_info['index']], adjusted
    )
    if 1 <= color_info['index'] <= 6:
        palette[color_info['index'] + 8] = generate_bright_version(
            palette[color_info['index']]
        )


def adjust_color_for_light_background(
    palette: List[str],
    color_info: Dict
) -> None:
    """Adjust a color for visibility on light backgrounds.
    
    Args:
        palette: Palette to modify in place
        color_info: Dictionary with 'lightness' and 'index' keys
    """
    if color_info['lightness'] <= MAX_LIGHTNESS_ON_LIGHT_BG:
        return
    adjusted = max(
        ABSOLUTE_MIN_LIGHTNESS,
        MAX_LIGHTNESS_ON_LIGHT_BG - color_info['index'] * 2
    )
    logger.debug(
        f"Adjusting color {color_info['index']} for light background: "
        f"{color_info['lightness']:.1f}% → {adjusted:.1f}%"
    )
    if not palette[color_info['index']]:
        palette[color_info['index']] = '#000000'
    palette[color_info['index']] = adjust_color_lightness(
        palette[color_info['index']], adjusted
    )
    if 1 <= color_info['index'] <= 6:
        palette[color_info['index'] + 8] = generate_bright_version(
            palette[color_info['index']]
        )


def adjust_outlier_color(
    palette: List[str],
    outlier: Dict,
    avg_lightness: float,
    is_bright_theme: bool
) -> None:
    """Adjust colors that are outliers in terms of lightness.
    
    Args:
        palette: Palette to modify in place
        outlier: Dictionary with color info
        avg_lightness: Average lightness of palette
        is_bright_theme: Whether the theme is bright overall
    """
    is_dark_outlier_in_bright = (
        is_bright_theme and
        outlier['lightness'] < avg_lightness - OUTLIER_LIGHTNESS_THRESHOLD
    )
    is_bright_outlier_in_dark = (
        not is_bright_theme and
        outlier['lightness'] > avg_lightness + OUTLIER_LIGHTNESS_THRESHOLD
    )
    if not is_dark_outlier_in_bright and not is_bright_outlier_in_dark:
        return
    
    adjusted = (avg_lightness - 10) if is_dark_outlier_in_bright else (avg_lightness + 10)
    typ = 'dark' if is_dark_outlier_in_bright else 'bright'
    logger.debug(
        f"Adjusting {typ} outlier color {outlier['index']}: "
        f"{outlier['lightness']:.1f}% → {adjusted:.1f}%"
    )
    if not palette[outlier['index']]:
        palette[outlier['index']] = '#000000'
    palette[outlier['index']] = adjust_color_lightness(
        palette[outlier['index']], adjusted
    )
    if 1 <= outlier['index'] <= 6:
        palette[outlier['index'] + 8] = generate_bright_version(
            palette[outlier['index']]
        )


def normalize_brightness(palette: List[Optional[str]]) -> List[str]:
    """Normalize palette brightness for consistency and contrast.
    
    Args:
        palette: 16-color ANSI palette
    
    Returns:
        Normalized palette
    """
    # Ensure no None values before analysis and work with concrete str list
    pal_strs: List[str] = [p if p is not None else '#000000' for p in palette]

    # Cache HSL values to avoid repeated conversions
    hsl_cache = {color: get_color_hsl(color) for color in pal_strs}
    
    bg_hsl = hsl_cache[pal_strs[0]]
    bg_lightness = bg_hsl['l']
    
    if bg_lightness < MIN_BACKGROUND_LIGHTNESS_DARK:
        logger.debug(
            f"Normalizing background from {bg_lightness}% "
            f"to {MIN_BACKGROUND_LIGHTNESS_DARK}%"
        )
        palette[0] = hsl_to_hex(
            bg_hsl['h'], bg_hsl['s'], MIN_BACKGROUND_LIGHTNESS_DARK
        )
        bg_lightness = MIN_BACKGROUND_LIGHTNESS_DARK
    elif bg_lightness > MAX_BACKGROUND_LIGHTNESS_LIGHT:
        logger.debug(
            f"Normalizing background from {bg_lightness}% "
            f"to {MAX_BACKGROUND_LIGHTNESS_LIGHT}%"
        )
        palette[0] = hsl_to_hex(
            bg_hsl['h'], bg_hsl['s'], MAX_BACKGROUND_LIGHTNESS_LIGHT
        )
        bg_lightness = MAX_BACKGROUND_LIGHTNESS_LIGHT

    is_very_dark = bg_lightness < VERY_DARK_BACKGROUND_THRESHOLD
    is_very_light = bg_lightness > VERY_LIGHT_BACKGROUND_THRESHOLD

    indices = [1, 2, 3, 4, 5, 6, 7]
    ansi_colors = [
        {
            'index': i,
            'lightness': hsl_cache[pal_strs[i]]['l'],
            'hue': hsl_cache[pal_strs[i]]['h'],
            'saturation': hsl_cache[pal_strs[i]]['s']
        }
        for i in indices
    ]

    avg_lightness = sum(c['lightness'] for c in ansi_colors) / len(ansi_colors)
    is_bright_theme = avg_lightness > BRIGHT_THEME_THRESHOLD

    if is_very_dark:
        for c in ansi_colors:
            adjust_color_for_dark_background(pal_strs, c)
        return pal_strs

    if is_very_light:
        for c in ansi_colors:
            adjust_color_for_light_background(pal_strs, c)
        return pal_strs

    outliers = [
        c for c in ansi_colors
        if abs(c['lightness'] - avg_lightness) > OUTLIER_LIGHTNESS_THRESHOLD
    ]
    for out in outliers:
        adjust_outlier_color(pal_strs, out, avg_lightness, is_bright_theme)

    color8_hsl = hsl_cache[pal_strs[8]]
    if is_very_dark and color8_hsl['l'] < MIN_LIGHTNESS_ON_DARK_BG:
        adjusted = min(MIN_LIGHTNESS_ON_DARK_BG, bg_lightness + 15)
        logger.debug(
            f"Normalizing color8 (bright black) from "
            f"{color8_hsl['l']}% to {adjusted}%"
        )
        pal_strs[8] = hsl_to_hex(color8_hsl['h'], color8_hsl['s'], adjusted)

    color15_hsl = hsl_cache[pal_strs[15]]
    color15_contrast = abs(color15_hsl['l'] - bg_lightness)
    if color15_contrast < MIN_FOREGROUND_CONTRAST:
        target = (
            min(100, bg_lightness + MIN_FOREGROUND_CONTRAST + 10)
            if is_very_dark
            else max(0, bg_lightness - MIN_FOREGROUND_CONTRAST - 10)
        )
        logger.debug(
            f"Normalizing color15 (bright white) from "
            f"{color15_hsl['l']}% to {target}% for better contrast"
        )
        pal_strs[15] = hsl_to_hex(color15_hsl['h'], color15_hsl['s'], target)

    return pal_strs


# =============================================================================
# Main Extraction Functions
# =============================================================================

def extract_colors_with_imagemagick(
    image_path: str,
    light_mode: bool = False
) -> List[str]:
    """Extract a 16-color ANSI palette from an image.
    
    Automatically detects image type (monochrome, low-diversity, chromatic)
    and generates an appropriate palette.
    
    Args:
        image_path: Path to the image file
        light_mode: Whether to generate a light mode palette
    
    Returns:
        16-color ANSI palette as list of hex strings
    
    Raises:
        RuntimeError: If not enough colors can be extracted
    """
    cache_key = get_cache_key(image_path, light_mode)
    if cache_key:
        cached = load_cached_palette(cache_key)
        if cached:
            return cached

    dominant = extract_dominant_colors(image_path, DOMINANT_COLORS_TO_EXTRACT)
    if len(dominant) < 8:
        raise RuntimeError('Not enough colors extracted from image')

    # HSL cache is now persistent, no need to clear it

    if is_monochrome_image(dominant):
        logger.info('Detected monochrome/grayscale image - generating grayscale palette')
        palette = generate_monochrome_palette(dominant, light_mode)
    elif has_low_color_diversity(dominant):
        logger.info('Detected low color diversity - generating subtle balanced palette')
        palette = generate_subtle_balanced_palette(dominant, light_mode)
    else:
        logger.info('Detected diverse chromatic image - generating vibrant colorful palette')
        palette = generate_chromatic_palette(dominant, light_mode)

    palette = normalize_brightness(palette)

    if cache_key:
        save_palette_to_cache(cache_key, palette)

    return palette


def extract_colors_from_wallpaper(
    image_path: str,
    mode: str = "auto",
    on_success: Optional[Callable[[List[str]], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None
) -> Optional[List[str]]:
    """Extract colors from a wallpaper image.
    
    Convenience wrapper with optional callbacks.
    
    Args:
        image_path: Path to the image file
        on_success: Optional callback for successful extraction
        on_error: Optional callback for errors
    
    Returns:
        16-color palette or None if extraction fails
    """
    try:
        # Determine light_mode flag based on requested mode
        if mode == "light":
            light_mode = True
        elif mode == "dark":
            light_mode = False
        else:
            # Auto: decide based on average lightness of dominant colors
            dominant = extract_dominant_colors(image_path, DOMINANT_COLORS_TO_EXTRACT)
            if len(dominant) == 0:
                light_mode = False
            else:
                # compute average lightness
                total = 0.0
                for c in dominant:
                    total += get_color_hsl(c)['l']
                avg = total / len(dominant)
                light_mode = avg > 50.0

        colors = extract_colors_with_imagemagick(image_path, light_mode)
        if on_success:
            on_success(colors)
        return colors
    except Exception as e:
        if on_error:
            on_error(e)
        else:
            raise


def extract_accent_from_wallpaper(image_path: str) -> Optional[str]:
    """Extract the most vibrant accent color from an image.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Hex color string of the best accent color, or None
    """
    try:
        result = subprocess.run(
            [
                "magick", image_path, "-resize", "64x64", "-colors", "8",
                "-format", "%c", "histogram:info:"
            ],
            capture_output=True, text=True, check=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    
    from colorsys import rgb_to_hsv
    best_color, best_score = None, 0
    
    for line in result.stdout.split('\n'):
        match = re.search(r'#([0-9A-Fa-f]{6})', line)
        if not match:
            continue
        
        hex_color = match.group(1).lower()
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        h, s, v = rgb_to_hsv(r / 255, g / 255, b / 255)
        
        # Score by vibrancy, skip grays
        if s > 0.15 and 0.15 < v < 0.95:
            score = s * v
            if score > best_score:
                best_score, best_color = score, f"#{hex_color}"
    
    return best_color


# =============================================================================
# CLI Interface
# =============================================================================

def _print_palette_terminal(palette: List[str]) -> None:
    """Print a visual representation of the palette in the terminal."""

    def fg_for_color(hex_color: str) -> tuple[int, int, int]:
        """Determine appropriate foreground color for a background color.
        
        Returns white text for dark backgrounds, black text for light backgrounds.
        
        Args:
            hex_color: Background color in hex format
            
        Returns:
            RGB tuple for foreground text color
        """
        hsl = hex_to_hsl(hex_color)
        return (0, 0, 0) if hsl['l'] > 50 else (255, 255, 255)

    for row in range(2):
        for i in range(8):
            idx = row * 8 + i
            if idx >= len(palette):
                break
            hexc = palette[idx]
            r, g, b = hex_to_rgb(hexc)
            fg = fg_for_color(hexc)
            swatch = (
                f"\x1b[48;2;{r};{g};{b}m"
                f"\x1b[38;2;{fg[0]};{fg[1]};{fg[2]}m  {hexc}  \x1b[0m"
            )
            print(swatch, end='')
        print()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print('Usage: python3 imagemagick.py /path/to/image')
        sys.exit(1)
    
    path = sys.argv[1]
    pal = extract_colors_from_wallpaper(path, "auto")
    
    if pal:
        _print_palette_terminal(pal)
        print(json.dumps(pal, indent=2))
