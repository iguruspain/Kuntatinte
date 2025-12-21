#!/usr/bin/env python3
"""
Script to test if Kuntatinte generates the same colors as kde-material-you-colors
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.material_you_colors import extract_source_colors_from_image
from core.color_utils import create_material_you_scheme, get_material_you_colors_from_scheme
from integrations.kuntatinte_colors import generate_kuntatinte_schemes

def test_color_equality():
    # Use the specific LadyX.png image as requested
    test_image = "/home/iguruspain/Imágenes/wallpapers/LadyX.png"

    if not os.path.exists(test_image):
        print(f"Test image not found: {test_image}")
        return

    # Extract colors using Kuntatinte's method
    palette = extract_source_colors_from_image(test_image, max_colors=2)
    print(f"Extracted palette: {palette}")

    if not palette:
        print("No colors extracted")
        return

    # Generate schemes with Kuntatinte (variant 5 = TonalSpot, tone_multiplier=0.8 like kde-material-you-colors)
    light_scheme, dark_scheme = generate_kuntatinte_schemes(palette, scheme_variant=5, tone_multiplier=0.8)

    print("Kuntatinte Light scheme generated successfully")
    print("Kuntatinte Dark scheme generated successfully")

    # Parse the KDE color scheme to extract key colors
    import configparser
    from io import StringIO

    def parse_kde_colors(scheme_text):
        config = configparser.ConfigParser()
        config.optionxform = lambda optionstr: optionstr
        config.read_string(scheme_text)
        
        print(f"DEBUG: Available sections: {config.sections()}")
        
        colors = {}
        for section in config.sections():
            if section.startswith('Colors:'):
                print(f"DEBUG: Section {section}: {dict(config[section])}")
                colors.update(config[section])
        return colors

    light_colors = parse_kde_colors(light_scheme)
    dark_colors = parse_kde_colors(dark_scheme)
    
    # Parse again to get config object
    config = configparser.ConfigParser()
    config.optionxform = lambda optionstr: optionstr
    config.read_string(light_scheme)
    
    print("\nKuntatinte Light colors (sample):")
    for key, value in list(light_colors.items())[:10]:
        print(f"  {key}: {value}")
    
    print("\nKuntatinte Dark colors (sample):")
    for key, value in list(dark_colors.items())[:10]:
        print(f"  {key}: {value}")

    # Now compare with direct Material You colors
    primary_color = palette[0]
    print(f"\nUsing primary color: {primary_color}")

    scheme_light = create_material_you_scheme(primary_color, is_dark=False, variant=5)
    scheme_dark = create_material_you_scheme(primary_color, is_dark=True, variant=5)

    colors_light = get_material_you_colors_from_scheme(scheme_light, is_dark=False)
    colors_dark = get_material_you_colors_from_scheme(scheme_dark, is_dark=True)

    print("\nDirect Material You colors (light):")
    for key, value in list(colors_light.items())[:10]:
        print(f"  {key}: {value}")

    print("\nDirect Material You colors (dark):")
    for key, value in list(colors_dark.items())[:10]:
        print(f"  {key}: {value}")

    print("\n=== COMPARISON ===")
    
    # Convert KDE RGB to hex for comparison
    def rgb_to_hex(rgb_str):
        r, g, b = map(int, rgb_str.split(','))
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    
    # Read kde-material-you-colors scheme
    kde_scheme_path = "/home/iguruspain/.local/share/color-schemes/MaterialYouDark.colors"
    kde_colors = {}
    
    if os.path.exists(kde_scheme_path):
        import configparser
        kde_config = configparser.ConfigParser()
        kde_config.optionxform = lambda optionstr: optionstr
        kde_config.read(kde_scheme_path)
        
        for section in kde_config.sections():
            if section.startswith('Colors:'):
                kde_colors[section] = {}
                for key, value in kde_config[section].items():
                    # Convert hex to RGB for comparison
                    if value.startswith('#'):
                        kde_colors[section][key] = hex_to_rgb(value)
                    else:
                        # Already RGB
                        kde_colors[section][key] = tuple(map(int, value.split(',')))
    
    # Compare all colors section by section
    print("\n=== COMPLETE COLOR COMPARISON ===")
    
    kuntatinte_config = configparser.ConfigParser()
    kuntatinte_config.optionxform = lambda optionstr: optionstr
    kuntatinte_config.read_string(dark_scheme)
    
    total_differences = 0
    total_colors = 0
    
    for section in kuntatinte_config.sections():
        if section.startswith('Colors:'):
            print(f"\n{section}:")
            
            if section in kde_colors:
                for key in kuntatinte_config[section]:
                    total_colors += 1
                    kuntatinte_rgb = tuple(map(int, kuntatinte_config[section][key].split(',')))
                    kde_rgb = kde_colors[section].get(key)
                    
                    if kde_rgb:
                        diff = tuple(abs(a - b) for a, b in zip(kuntatinte_rgb, kde_rgb))
                        max_diff = max(diff)
                        
                        if max_diff > 5:  # Only show significant differences
                            print(f"  {key}: Kuntatinte={kuntatinte_rgb} vs KDE={kde_rgb} (diff={diff})")
                            total_differences += 1
                        elif max_diff > 0:
                            print(f"  {key}: Kuntatinte={kuntatinte_rgb} vs KDE={kde_rgb} (minor diff={diff})")
                    else:
                        print(f"  {key}: Kuntatinte={kuntatinte_rgb} (not in KDE scheme)")
            else:
                print(f"  Section not found in KDE scheme")
    
    print(f"\nSUMMARY: {total_differences} significant differences out of {total_colors} colors compared")
    
    # Old comparison (keep for reference)
    mapping_light = {
        'Colors:View.BackgroundNormal': 'surface',
        'Colors:View.ForegroundNormal': 'onSurface', 
        'Colors:Selection.DecorationFocus': 'primary',
        'Colors:Selection.DecorationHover': 'secondary',
    }
    
    print("\n=== LEGACY COMPARISON (for reference) ===")
    for kde_key, my_key in mapping_light.items():
        section, color_key = kde_key.split('.')
        if section in config and color_key in config[section]:
            kde_rgb = config[section][color_key]
            kde_hex = rgb_to_hex(kde_rgb)
            my_hex = colors_light[my_key]
            match = kde_hex.lower() == my_hex.lower()
            print(f"Light {kde_key}: {kde_rgb} ({kde_hex}) == {my_key}: {my_hex} : {match}")
            
    # Also check what surface actually is
    print(f"\nMaterial You surface: {colors_light.get('surface', 'N/A')}")
    if 'Colors:View' in config:
        print(f"Kuntatinte Colors:View.BackgroundNormal: {config['Colors:View'].get('BackgroundNormal', 'N/A')}")

if __name__ == "__main__":
    test_color_equality()