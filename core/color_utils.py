"""
Color Utilities.

Functions for color space conversions: hex, RGB, and HSL.
Also includes contrast and luminance calculations.
"""

import re
from typing import Optional, Tuple, TypedDict, List


class RGB(TypedDict):
    """RGB color representation with values 0-255."""
    r: int
    g: int
    b: int


class HSL(TypedDict):
    """HSL color representation (h: 0-360, s: 0-100, l: 0-100)."""
    h: float
    s: float
    l: float


# =============================================================================
# Basic Conversions
# =============================================================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple.
    
    Args:
        hex_color: Color in #rrggbb or rrggbb format
    
    Returns:
        Tuple of (r, g, b) values 0-255
        
    Raises:
        ValueError: If hex string is invalid
    """
    s = hex_color.lstrip('#')
    if len(s) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    
    return (
        int(s[0:2], 16),
        int(s[2:4], 16),
        int(s[4:6], 16)
    )


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex color.
    
    Args:
        r, g, b: Color components 0-255
    
    Returns:
        Color in #rrggbb format (lowercase)
    """
    return f'#{r:02x}{g:02x}{b:02x}'


def hex_to_rgba(hex_color: str, alpha: float = 0.8) -> str:
    """Convert hex color to rgba() CSS string.
    
    Args:
        hex_color: Color in #rrggbb format
        alpha: Alpha value 0.0-1.0
    
    Returns:
        CSS rgba() string
    """
    r, g, b = hex_to_rgb(hex_color)
    return f'rgba({r}, {g}, {b}, {alpha})'


def normalize_color(color: Optional[str]) -> Optional[str]:
    """Normalize a color value to '#rrggbb' format.
    
    Args:
        color: Color string in various formats
    
    Returns:
        Normalized color or None if invalid
    """
    if not color or not isinstance(color, str):
        return None
    
    s = color.strip()
    m = re.match(r"#?([0-9A-Fa-f]{6})", s)
    if not m:
        return None
    return f"#{m.group(1).lower()}"


# =============================================================================
# HSL Conversions
# =============================================================================

def rgb_to_hsl(r: int, g: int, b: int) -> HSL:
    """Convert RGB values to HSL dictionary.
    
    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)
    
    Returns:
        HSL dictionary with h (0-360), s (0-100), l (0-100)
    """
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    mx = max(r_, g_, b_)
    mn = min(r_, g_, b_)
    diff = mx - mn
    
    l = (mx + mn) / 2.0
    
    if diff == 0:
        h = 0.0
        s = 0.0
    else:
        s = diff / (1 - abs(2 * l - 1))
        
        if mx == r_:
            h_ = ((g_ - b_) / diff) % 6
        elif mx == g_:
            h_ = ((b_ - r_) / diff) + 2
        else:
            h_ = ((r_ - g_) / diff) + 4
        
        h = h_ * 60.0
        if h < 0:
            h += 360.0
    
    return {
        'h': round(h, 2),
        's': round(s * 100, 2),
        'l': round(l * 100, 2)
    }


def hex_to_hsl(hex_color: str) -> HSL:
    """Convert hex color to HSL dictionary.
    
    Args:
        hex_color: Color in #rrggbb format
    
    Returns:
        HSL dictionary with h (0-360), s (0-100), l (0-100)
    """
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hsl(r, g, b)


def hsl_to_rgb(h: float, s: float, l: float) -> RGB:
    """Convert HSL values to RGB dictionary.
    
    Args:
        h: Hue (0-360)
        s: Saturation (0-100)
        l: Lightness (0-100)
    
    Returns:
        RGB dictionary with r, g, b values (0-255)
    """
    s_ = s / 100.0
    l_ = l / 100.0
    
    c = (1 - abs(2 * l_ - 1)) * s_
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = l_ - c / 2
    
    if 0 <= h < 60:
        r1, g1, b1 = c, x, 0
    elif 60 <= h < 120:
        r1, g1, b1 = x, c, 0
    elif 120 <= h < 180:
        r1, g1, b1 = 0, c, x
    elif 180 <= h < 240:
        r1, g1, b1 = 0, x, c
    elif 240 <= h < 300:
        r1, g1, b1 = x, 0, c
    else:
        r1, g1, b1 = c, 0, x
    
    return {
        'r': max(0, min(255, int(round((r1 + m) * 255)))),
        'g': max(0, min(255, int(round((g1 + m) * 255)))),
        'b': max(0, min(255, int(round((b1 + m) * 255))))
    }


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL values to hex color string.
    
    Args:
        h: Hue (0-360, will be wrapped)
        s: Saturation (0-100, will be clamped)
        l: Lightness (0-100, will be clamped)
    
    Returns:
        Hex color string with # prefix (e.g., '#FF5500')
    """
    rgb = hsl_to_rgb(
        h % 360,
        max(0, min(100, s)),
        max(0, min(100, l))
    )
    return '#{0:02X}{1:02X}{2:02X}'.format(rgb['r'], rgb['g'], rgb['b'])


# =============================================================================
# Luminance and Contrast
# =============================================================================

def get_luminance(hex_color: str) -> float:
    """Calculate relative luminance of a color.
    
    Uses the WCAG 2.0 formula for relative luminance.
    
    Args:
        hex_color: Color in #rrggbb format
    
    Returns:
        Relative luminance 0.0-1.0
    """
    def srgb_to_linear(c: int) -> float:
        c_norm = c / 255.0
        return c_norm / 12.92 if c_norm <= 0.04045 else ((c_norm + 0.055) / 1.055) ** 2.4
    
    r, g, b = hex_to_rgb(hex_color)
    return 0.2126 * srgb_to_linear(r) + 0.7152 * srgb_to_linear(g) + 0.0722 * srgb_to_linear(b)


def get_contrast_ratio(color1: str, color2: str) -> float:
    """Calculate contrast ratio between two colors.
    
    Uses the WCAG 2.0 formula for contrast ratio.
    
    Args:
        color1, color2: Colors in #rrggbb format
    
    Returns:
        Contrast ratio (1.0 to 21.0)
    """
    lum1 = get_luminance(color1)
    lum2 = get_luminance(color2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def get_best_contrast(base_color: str, candidates: List[str]) -> str:
    """Get the color with best contrast against base color.
    
    Args:
        base_color: Base color to contrast against
        candidates: List of candidate colors
    
    Returns:
        Best contrasting color, or black/white if no candidates
    """
    # Filter and normalize candidates, keeping only valid colors
    valid_candidates: List[str] = []
    for c in candidates:
        normalized = normalize_color(c)
        if normalized:
            valid_candidates.append(normalized)
    
    if not valid_candidates:
        # Choose between black and white
        base_lum = get_luminance(base_color)
        return '#000000' if base_lum > 0.5 else '#ffffff'
    
    best_color = valid_candidates[0]
    best_contrast = get_contrast_ratio(base_color, best_color)
    
    for color in valid_candidates[1:]:
        contrast = get_contrast_ratio(base_color, color)
        if contrast > best_contrast:
            best_contrast = contrast
            best_color = color
    
    return best_color


# =============================================================================
# Color Analysis
# =============================================================================

def is_dark_color(hex_color: str, threshold: float = 35.0) -> bool:
    """Check if a color is considered dark based on lightness.
    
    Args:
        hex_color: Hex color string
        threshold: Lightness threshold (0-100), default 35
    
    Returns:
        True if lightness is below threshold
    """
    hsl = hex_to_hsl(hex_color)
    return hsl['l'] < threshold


def is_light_color(hex_color: str, threshold: float = 65.0) -> bool:
    """Check if a color is considered light based on lightness.
    
    Args:
        hex_color: Hex color string
        threshold: Lightness threshold (0-100), default 65
    
    Returns:
        True if lightness is above threshold
    """
    hsl = hex_to_hsl(hex_color)
    return hsl['l'] > threshold


def calculate_hue_distance(hue1: float, hue2: float) -> float:
    """Calculate the shortest distance between two hue values.
    
    Args:
        hue1: First hue value (0-360)
        hue2: Second hue value (0-360)
    
    Returns:
        Distance in degrees (0-180)
    """
    diff = abs(hue1 - hue2)
    if diff > 180:
        diff = 360 - diff
    return diff


def is_grayscale(hex_color: str, saturation_threshold: float = 10.0) -> bool:
    """Check if a color is grayscale (very low saturation).
    
    Args:
        hex_color: Hex color string
        saturation_threshold: Maximum saturation to consider grayscale
    
    Returns:
        True if saturation is below threshold
    """
    hsl = hex_to_hsl(hex_color)
    return hsl['s'] < saturation_threshold


# =============================================================================
# Palette Variants (Material You style)
# =============================================================================

# Variant indices matching Material You naming
VARIANT_CONTENT = 0
VARIANT_EXPRESSIVE = 1
VARIANT_FIDELITY = 2
VARIANT_MONOCHROME = 3
VARIANT_NEUTRAL = 4
VARIANT_TONALSPOT = 5  # Default
VARIANT_VIBRANT = 6
VARIANT_RAINBOW = 7
VARIANT_FRUITSALAD = 8

VARIANT_NAMES = [
    "Content",
    "Expressive", 
    "Fidelity",
    "Monochrome",
    "Neutral",
    "TonalSpot",
    "Vibrant",
    "Rainbow",
    "FruitSalad"
]


def adjust_color_saturation(hex_color: str, factor: float) -> str:
    """Adjust the saturation of a color by a factor.
    
    Args:
        hex_color: Color in #rrggbb format
        factor: Saturation multiplier (0 = grayscale, 1 = unchanged, >1 = more saturated)
    
    Returns:
        Adjusted color in #rrggbb format
    """
    hsl = hex_to_hsl(hex_color)
    new_s = max(0, min(100, hsl['s'] * factor))
    return hsl_to_hex(hsl['h'], new_s, hsl['l'])


def adjust_color_lightness(hex_color: str, factor: float) -> str:
    """Adjust the lightness of a color by a factor.
    
    Args:
        hex_color: Color in #rrggbb format
        factor: Lightness multiplier
    
    Returns:
        Adjusted color in #rrggbb format
    """
    hsl = hex_to_hsl(hex_color)
    new_l = max(0, min(100, hsl['l'] * factor))
    return hsl_to_hex(hsl['h'], hsl['s'], new_l)


def shift_hue(hex_color: str, degrees: float) -> str:
    """Shift the hue of a color by specified degrees.
    
    Args:
        hex_color: Color in #rrggbb format
        degrees: Hue shift in degrees (can be negative)
    
    Returns:
        Color with shifted hue in #rrggbb format
    """
    hsl = hex_to_hsl(hex_color)
    new_h = (hsl['h'] + degrees) % 360
    return hsl_to_hex(new_h, hsl['s'], hsl['l'])


def blend_colors(color1: str, color2: str, ratio: float) -> str:
    """Blend two colors together.
    
    Args:
        color1: First color in #rrggbb format
        color2: Second color in #rrggbb format
        ratio: Blend ratio (0 = color1, 1 = color2)
    
    Returns:
        Blended color in #rrggbb format
    """
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    
    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)
    
    return rgb_to_hex(r, g, b)


def apply_variant_to_color(hex_color: str, variant: int, index: int = 0, total: int = 16) -> str:
    """Apply a variant transformation to a single color.
    
    Args:
        hex_color: Color in #rrggbb format
        variant: Variant index (0-8)
        index: Position of color in palette (for rainbow/fruitsalad)
        total: Total colors in palette
    
    Returns:
        Transformed color in #rrggbb format
    """
    hsl = hex_to_hsl(hex_color)
    
    if variant == VARIANT_MONOCHROME:
        # Completely desaturated
        return hsl_to_hex(hsl['h'], 0, hsl['l'])
    
    elif variant == VARIANT_NEUTRAL:
        # Very low saturation (15% of original)
        return hsl_to_hex(hsl['h'], hsl['s'] * 0.15, hsl['l'])
    
    elif variant == VARIANT_CONTENT:
        # Slightly reduced saturation, faithful to content
        return hsl_to_hex(hsl['h'], hsl['s'] * 0.7, hsl['l'])
    
    elif variant == VARIANT_FIDELITY:
        # Keep colors very close to original
        return hsl_to_hex(hsl['h'], hsl['s'] * 0.9, hsl['l'])
    
    elif variant == VARIANT_TONALSPOT:
        # Default - keep as is
        return hex_color
    
    elif variant == VARIANT_VIBRANT:
        # Boost saturation
        new_s = min(100, hsl['s'] * 1.4)
        return hsl_to_hex(hsl['h'], new_s, hsl['l'])
    
    elif variant == VARIANT_EXPRESSIVE:
        # High saturation + slight hue shift for variety
        new_s = min(100, hsl['s'] * 1.3)
        hue_shift = (index - total / 2) * 3  # Spread hues slightly
        new_h = (hsl['h'] + hue_shift) % 360
        return hsl_to_hex(new_h, new_s, hsl['l'])
    
    elif variant == VARIANT_RAINBOW:
        # Distribute hues evenly across the spectrum
        base_hue = hsl['h']
        hue_offset = (index / total) * 360
        new_h = (base_hue + hue_offset) % 360
        new_s = max(60, hsl['s'])  # Ensure minimum saturation
        return hsl_to_hex(new_h, new_s, hsl['l'])
    
    elif variant == VARIANT_FRUITSALAD:
        # Complementary colors with high saturation
        hue_steps = [0, 30, 60, 120, 180, 210, 270, 300]
        hue_offset = hue_steps[index % len(hue_steps)]
        new_h = (hsl['h'] + hue_offset) % 360
        new_s = max(70, min(100, hsl['s'] * 1.2))
        return hsl_to_hex(new_h, new_s, hsl['l'])
    
    return hex_color


def apply_variant_to_palette(colors: List[str], variant: int) -> List[str]:
    """Apply a variant transformation to a complete palette.
    
    Args:
        colors: List of hex colors
        variant: Variant index (0-8)
    
    Returns:
        List of transformed hex colors
    """
    return [
        apply_variant_to_color(color, variant, i, len(colors))
        for i, color in enumerate(colors)
    ]


def interpolate_palette_variants(
    colors: List[str], 
    from_variant: int, 
    to_variant: int, 
    progress: float
) -> List[str]:
    """Interpolate between two palette variants.
    
    Args:
        colors: Original palette colors
        from_variant: Starting variant index
        to_variant: Target variant index
        progress: Interpolation progress (0 = from_variant, 1 = to_variant)
    
    Returns:
        Interpolated palette
    """
    from_palette = apply_variant_to_palette(colors, from_variant)
    to_palette = apply_variant_to_palette(colors, to_variant)
    
    return [
        blend_colors(from_color, to_color, progress)
        for from_color, to_color in zip(from_palette, to_palette)
    ]


def get_palette_at_slider_position(colors: List[str], slider_value: float) -> List[str]:
    """Get palette based on slider position (0-100).
    
    The slider moves through variants:
    0-12.5: Content -> Fidelity
    12.5-25: Fidelity -> Neutral  
    25-37.5: Neutral -> Monochrome
    37.5-50: Monochrome -> TonalSpot
    50-62.5: TonalSpot -> Vibrant
    62.5-75: Vibrant -> Expressive
    75-87.5: Expressive -> Rainbow
    87.5-100: Rainbow -> FruitSalad
    
    Args:
        colors: Original palette colors
        slider_value: Slider position (0-100)
    
    Returns:
        Transformed palette
    """
    # Define variant sequence for slider
    variant_sequence = [
        VARIANT_CONTENT,
        VARIANT_FIDELITY,
        VARIANT_NEUTRAL,
        VARIANT_MONOCHROME,
        VARIANT_TONALSPOT,
        VARIANT_VIBRANT,
        VARIANT_EXPRESSIVE,
        VARIANT_RAINBOW,
        VARIANT_FRUITSALAD
    ]
    
    num_segments = len(variant_sequence) - 1
    segment_size = 100.0 / num_segments
    
    # Clamp slider value
    slider_value = max(0, min(100, slider_value))
    
    # Find which segment we're in
    segment_index = int(slider_value / segment_size)
    if segment_index >= num_segments:
        segment_index = num_segments - 1
    
    # Calculate progress within segment
    segment_start = segment_index * segment_size
    progress = (slider_value - segment_start) / segment_size
    
    from_variant = variant_sequence[segment_index]
    to_variant = variant_sequence[segment_index + 1]
    
    return interpolate_palette_variants(colors, from_variant, to_variant, progress)


def get_variant_name_at_slider_position(slider_value: float) -> str:
    """Get the name of the closest variant at slider position.
    
    Args:
        slider_value: Slider position (0-100)
    
    Returns:
        Name of the closest variant
    """
    variant_sequence = [
        VARIANT_CONTENT,
        VARIANT_FIDELITY,
        VARIANT_NEUTRAL,
        VARIANT_MONOCHROME,
        VARIANT_TONALSPOT,
        VARIANT_VIBRANT,
        VARIANT_EXPRESSIVE,
        VARIANT_RAINBOW,
        VARIANT_FRUITSALAD
    ]
    
    num_variants = len(variant_sequence)
    segment_size = 100.0 / (num_variants - 1)
    
    # Find closest variant
    closest_index = round(slider_value / segment_size)
    closest_index = max(0, min(num_variants - 1, closest_index))
    
    return VARIANT_NAMES[variant_sequence[closest_index]]

