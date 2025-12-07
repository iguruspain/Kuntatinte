"""
Material You Color Extraction.

Extract seed colors from images using Material You's color quantization algorithm.
Uses the materialyoucolor library for extracting visually pleasing accent colors.
"""

from typing import List, Optional, Any, Iterable, cast
import logging

logger = logging.getLogger(__name__)

# Try to import materialyoucolor - it may not be installed
try:
    from materialyoucolor.quantize import QuantizeCelebi  # type: ignore[import-not-found]
    from materialyoucolor.score.score import Score, ScoreOptions  # type: ignore[import-not-found]
    from materialyoucolor.hct import Hct  # type: ignore[import-not-found]
    HAS_MATERIAL_YOU = True
except ImportError:
    HAS_MATERIAL_YOU = False
    QuantizeCelebi = None  # type: ignore[misc, assignment]
    Score = None  # type: ignore[misc, assignment]
    ScoreOptions = None  # type: ignore[misc, assignment]
    Hct = None  # type: ignore[misc, assignment]
    logging.warning("materialyoucolor not installed. Material You color extraction disabled.")

# Try to import PIL for image loading
try:
    from PIL import Image  # type: ignore[import-not-found]
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None  # type: ignore[misc, assignment]
    logging.warning("Pillow not installed. Material You color extraction disabled.")


# =============================================================================
# Constants
# =============================================================================

# Score options for extracting multiple seed colors
SCORE_OPTIONS_DICT = {
    'desired': 7,  # Number of colors to extract (ANSI colors target)
    'fallback_color_argb': 0xFF4285F4,  # Google Blue as fallback
    'filter': True,  # Avoid unsuitable colors
    'dislike_filter': True,  # Fix globally disliked colors
}


# =============================================================================
# Color Conversion Utilities
# =============================================================================

def argb_to_hex(argb: int) -> str:
    """Convert ARGB integer to hex color string.
    
    Args:
        argb: ARGB integer (0xAARRGGBB format)
    
    Returns:
        Hex color string (e.g., "#ff5500")
    """
    r_val = (argb >> 16) & 0xFF
    g_val = (argb >> 8) & 0xFF
    b_val = argb & 0xFF
    return f"#{r_val:02x}{g_val:02x}{b_val:02x}"


def hex_to_argb(hex_color: str) -> int:
    """Convert hex color string to ARGB integer.
    
    Args:
        hex_color: Hex color string (e.g., "#ff5500" or "ff5500")
    
    Returns:
        ARGB integer
    """
    hex_color = hex_color.lstrip('#')
    r_val = int(hex_color[0:2], 16)
    g_val = int(hex_color[2:4], 16)
    b_val = int(hex_color[4:6], 16)
    return (0xFF << 24) | (r_val << 16) | (g_val << 8) | b_val


def get_color_chroma(argb: int) -> float:
    """Get the chroma (colorfulness) of a color.
    
    Args:
        argb: ARGB integer
    
    Returns:
        Chroma value (0-100+)
    """
    if not HAS_MATERIAL_YOU:
        return 0.0
    assert Hct is not None
    hct = Hct.from_int(argb)
    return hct.chroma


# =============================================================================
# Material You Color Extraction
# =============================================================================

def extract_source_colors_from_image(image_path: str, max_colors: int = 7) -> List[str]:
    """Extract source colors from an image using Material You's algorithm.
    
    Uses QuantizeCelebi and Score from materialyoucolor to extract
    visually pleasing seed colors that can be used to generate
    Material You color schemes.
    
    Args:
        image_path: Path to the image file
        max_colors: Maximum number of colors to extract (default: 7)
    
    Returns:
        List of hex color strings, sorted by score (most pleasing first)
    """
    if not HAS_MATERIAL_YOU or not HAS_PIL:
        logging.warning("Material You extraction requires materialyoucolor and Pillow")
        return []
    
    # Assert for type checker
    assert Image is not None
    assert QuantizeCelebi is not None
    assert ScoreOptions is not None
    assert Score is not None
    
    try:
        # Open and resize image for faster processing
        img = Image.open(image_path)
        
        # Convert to RGBA if needed
        if img.mode == "RGB":
            img = img.convert("RGBA")
        elif img.mode != "RGBA":
            img = img.convert("RGBA")
        
        # Resize to 64px width for speed (smaller = faster)
        basewidth = 64
        wpercent = basewidth / float(img.size[0])
        hsize = int(float(img.size[1]) * float(wpercent))
        img = img.resize((basewidth, hsize), Image.Resampling.NEAREST)
        
        # Get pixel data
        image_data = img.getdata()
        # `Image.getdata()` returns an ImagingCore that isn't typed as Iterable in stubs;
        # cast to Iterable[Any] so the type checker accepts conversion to list.
        pixel_array = list(cast(Iterable[Any], image_data))
        
        # Quantize colors using Material You's algorithm
        # Returns a dict of {argb: count}
        quantized = QuantizeCelebi(pixel_array, 64)
        
        # Score and rank the colors
        score_options = ScoreOptions(
            desired=max_colors,
            fallback_color_argb=SCORE_OPTIONS_DICT['fallback_color_argb'],
            filter=SCORE_OPTIONS_DICT['filter'],
            dislike_filter=SCORE_OPTIONS_DICT['dislike_filter'],
        )
        ranked_colors = Score.score(quantized, score_options)
        
        img.close()
        
        # Convert ARGB integers to hex strings
        hex_colors = [argb_to_hex(argb) for argb in ranked_colors]
        
        return hex_colors[:max_colors]
        
    except Exception as e:
        logging.error(f"Error extracting Material You colors: {e}")
        return []


def get_best_seed_color(image_path: str) -> Optional[str]:
    """Get the single best seed color from an image.
    
    This is the primary accent color that Material You would use
    to generate a complete color scheme.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Hex color string of the best seed, or None
    """
    best_colors = extract_source_colors_from_image(image_path, max_colors=1)
    return best_colors[0] if best_colors else None


def extract_source_colors_with_info(image_path: str, max_colors: int = 7) -> List[dict]:
    """Extract source colors with additional color information.
    
    Returns colors with their HCT (Hue, Chroma, Tone) values for
    more detailed analysis.
    
    Args:
        image_path: Path to the image file
        max_colors: Maximum number of colors to extract
    
    Returns:
        List of dicts with 'hex', 'hue', 'chroma', 'tone' keys
    """
    if not HAS_MATERIAL_YOU or not HAS_PIL:
        return []
    
    assert Hct is not None
    
    hex_colors = extract_source_colors_from_image(image_path, max_colors)
    
    result = []
    for hex_color in hex_colors:
        argb = hex_to_argb(hex_color)
        hct = Hct.from_int(argb)
        result.append({
            'hex': hex_color,
            'hue': hct.hue,
            'chroma': hct.chroma,
            'tone': hct.tone,
        })
    
    return result


def is_available() -> bool:
    """Check if Material You color extraction is available.
    
    Returns:
        True if materialyoucolor and Pillow are installed
    """
    return HAS_MATERIAL_YOU and HAS_PIL


# =============================================================================
# CLI Interface for testing
# =============================================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python material_you_colors.py /path/to/image")
        print(f"\nMaterial You available: {is_available()}")
        sys.exit(1)
    
    main_image_path = sys.argv[1]
    
    if not is_available():
        print("Error: materialyoucolor and/or Pillow not installed")
        print("Install with: pip install materialyoucolor Pillow")
        sys.exit(1)
    
    print(f"Extracting colors from: {main_image_path}")
    colors = extract_source_colors_with_info(main_image_path)
    
    if colors:
        print(f"\nFound {len(colors)} source colors:")
        for i, color_info in enumerate(colors):
            hex_c = color_info['hex']
            hue = color_info['hue']
            chroma = color_info['chroma']
            tone = color_info['tone']
            
            # Print colored swatch
            r, g, b = int(hex_c[1:3], 16), int(hex_c[3:5], 16), int(hex_c[5:7], 16)
            swatch = f"\033[48;2;{r};{g};{b}m    \033[0m"
            
            print(f"  {i}: {swatch} {hex_c}  H:{hue:.0f}° C:{chroma:.1f} T:{tone:.0f}")
    else:
        print("No colors extracted")
