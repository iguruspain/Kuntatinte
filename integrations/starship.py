"""
Starship Prompt Configuration.

Applies color customization to the Starship prompt configuration file.
"""

import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


logger = logging.getLogger(__name__)

from core.config_manager import config


# =============================================================================
# Constants
# =============================================================================

# Default color values
DEFAULT_COLORS = {
    'accent': '#3daee9',
    'accent_text': '#ffffff',
    'dir_fg': '#1d6586',
    'dir_bg': '#1d6586',
    'dir_text': '#ccdfee',
    'git_fg': '#8b9297',
    'git_bg': '#333a3f',
    'git_text': '#ccdfee',
    'other_fg': '#1d6586',
    'other_bg': '#61a0c4',
    'other_text': '#00344a',
}

# Color keys used in palette
COLOR_KEYS = [
    'accent', 'accent_text',
    'dir_fg', 'dir_bg', 'dir_text',
    'git_fg', 'git_bg', 'git_text',
    'other_fg', 'other_bg', 'other_text',
]


# =============================================================================
# Palette Building
# =============================================================================

def build_starship_palette(starship_colors: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Build the starship palette from provided colors or defaults.
    
    Args:
        starship_colors: Optional dictionary with color overrides
    
    Returns:
        Complete palette dictionary with all color keys
    """
    if starship_colors is None:
        starship_colors = {}
    
    return {key: starship_colors.get(key, DEFAULT_COLORS[key]) for key in COLOR_KEYS}


# =============================================================================
# Configuration Generation
# =============================================================================

def gen_starship_config(palette: Dict[str, str], template_file: Path) -> str:
    """Generate starship configuration from template with palette colors.
    
    Args:
        palette: Dictionary of color values
        template_file: Path to the template file
    
    Returns:
        Generated configuration content
    
    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    if isinstance(template_file, str):
        template_path = Path(os.path.expanduser(os.path.expandvars(template_file)))
    else:
        template_path = Path(template_file)

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Find the palette section
    m = re.search(r"^\[(?:palette|palettes)\.colors\]\s*$", template, flags=re.M)
    if not m:
        return template

    # Find section boundaries
    start_index = m.start()
    rest = template[m.end():]
    m2 = re.search(r"^\[", rest, flags=re.M)
    end_index = m.end() + m2.start() if m2 else len(template)

    palette_section = template[start_index:end_index]

    # Update color assignments in the palette section
    for key, color in palette.items():
        if not isinstance(color, str):
            continue
        pat = re.compile(rf"^\s*{re.escape(key)}\s*=.*$", flags=re.M)
        replacement = f"{key} = '{color}'"
        if pat.search(palette_section):
            palette_section = pat.sub(replacement, palette_section)
        else:
            if not palette_section.endswith('\n'):
                palette_section += '\n'
            palette_section += replacement + '\n'

    return template[:start_index] + palette_section + template[end_index:]


# =============================================================================
# Terminal Refresh
# =============================================================================

def refresh_starship() -> None:
    """Restart kitty terminal to apply new starship configuration."""
    if subprocess.run(['pgrep', 'kitty'], capture_output=True).stdout:
        subprocess.run(
            ['pkill', 'kitty'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        subprocess.Popen(
            ['kitty'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


# =============================================================================
# Color Loading
# =============================================================================

def load_starship_colors() -> Dict[str, str]:
    """Load current starship colors from the config file.
    
    Returns:
        Dictionary with color values (empty string if not found)
    """
    config_path = config.starship_config
    result = {key: '' for key in COLOR_KEYS}
    
    if not config_path.exists():
        return result
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the palette section
    m = re.search(r"^\[(?:palette|palettes)\.colors\]\s*$", content, flags=re.M)
    if not m:
        return result
    
    # Find section boundaries
    start_index = m.end()
    rest = content[start_index:]
    m2 = re.search(r"^\[", rest, flags=re.M)
    end_index = start_index + m2.start() if m2 else len(content)
    
    palette_section = content[start_index:end_index]
    
    # Extract each color value
    for key in result.keys():
        pat = re.compile(rf"^\s*{re.escape(key)}\s*=\s*['\"]([^'\"]+)['\"]", flags=re.M)
        match = pat.search(palette_section)
        if match:
            result[key] = match.group(1)
    
    return result


# =============================================================================
# Apply and Restore
# =============================================================================

def apply_starship_colors(colors: Dict[str, str]) -> Tuple[bool, str]:
    """Apply starship colors from the provided dictionary.
    
    Args:
        colors: Dictionary with color values
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    template_path = config.starship_template
    output_path = config.starship_config
    
    if not template_path.exists():
        return False, f"Template file not found: {template_path}"
    
    palette = build_starship_palette(colors)
    
    try:
        starship_config = gen_starship_config(palette, template_path)
    except FileNotFoundError as e:
        return False, str(e)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create backup if file exists
    if output_path.exists():
        backup_path = output_path.with_suffix('.toml.bak')
        shutil.copy2(output_path, backup_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(starship_config)
    
    refresh_starship()
    return True, f"Starship configuration applied: {output_path}"


def restore_starship_backup() -> Tuple[bool, str]:
    """Restore starship.toml from backup file.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    config_path = config.starship_config
    backup_path = config_path.with_suffix('.toml.bak')
    
    if not backup_path.exists():
        return False, "No backup file found"
    
    try:
        shutil.copy2(backup_path, config_path)
        refresh_starship()
        return True, "Backup restored successfully"
    except Exception as e:
        return False, f"Error restoring backup: {e}"


# =============================================================================
# CLI Interface
# =============================================================================

def main() -> None:
    """CLI entry point for standalone usage."""
    template_path = config.starship_template
    output_path = config.starship_config

    if not template_path.exists():
        logger.error(f"Could not find template file: {template_path}")
        return

    palette = build_starship_palette()
    
    try:
        starship_config = gen_starship_config(palette, template_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create backup
    if output_path.exists():
        backup_path = output_path.with_suffix('.toml.bak')
        shutil.copy2(output_path, backup_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(starship_config)

    refresh_starship()
    logger.info(f"Starship configuration generated at: {output_path}")


if __name__ == "__main__":
    main()
