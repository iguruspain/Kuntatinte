#!/usr/bin/env python3
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
Ulauncher Theme Configuration.

Applies color customization to generate a Ulauncher theme based on
KDE color scheme and accent colors.
"""

import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


logger = logging.getLogger(__name__)

from core.config_manager import config as app_config
from core.color_utils import (
    rgb_to_hex,
    hex_to_rgba,
    normalize_color,
)


# =============================================================================
# Constants
# =============================================================================

# Default Ulauncher colors
DEFAULT_COLORS = {
    'bg_color': '#2a2e32',
    'window_border_color': '#3daee9',
    'prefs_background': '#31363b',
    'input_color': '#fcfcfc',
    'selected_bg_color': '#3daee9',
    'selected_fg_color': '#fcfcfc',
    'item_name': '#fcfcfc',
    'item_text': '#bdc3c7',
    'item_shortcut_color': '#3daee9',
    'item_box_selected': '#3daee9',
    'item_name_selected': '#1d1d1d',
    'item_text_selected': '#1d1d1d',
    'item_shortcut_color_sel': '#fcfcfc',
    'when_selected': '#fcfcfc',
    'when_not_selected': '#3daee9',
}

# Color keys used in palette
COLOR_KEYS = list(DEFAULT_COLORS.keys())


# =============================================================================
# Path Configuration
# =============================================================================

def _get_template_dir() -> Path:
    """Get ulauncher template directory from app config."""
    return app_config.ulauncher_template_dir


def _get_output_dir() -> Path:
    """Get ulauncher theme output directory from app config."""
    return app_config.ulauncher_theme_dir


def _get_backup_dir() -> Path:
    """Get backup directory for ulauncher theme."""
    return app_config.cache_dir / "ulauncher_backup"


# =============================================================================
# Palette Building
# =============================================================================

def build_ulauncher_palette(colors: Dict[str, str]) -> Dict[str, str]:
    """Build Ulauncher color palette from provided colors.
    
    Args:
        colors: Dictionary with color values. Expected keys:
            - bg_color: Window background
            - window_border_color: Window border
            - input_color: Input text color
            - item_name: Result item name color
            - item_text: Result item description color
            - item_box_selected: Selected item background
            - item_name_selected: Selected item name color
            - item_text_selected: Selected item description color
            - item_shortcut_color: Shortcut color (unselected)
            - item_shortcut_color_sel: Shortcut color (selected)
            - when_selected: Matched text highlight when selected
            - when_not_selected: Matched text highlight when not selected
    
    Returns:
        Complete palette dictionary with all required colors
    """
    palette: Dict[str, str] = {}
    
    for key in COLOR_KEYS:
        value = colors.get(key)
        if value:
            normalized = normalize_color(value)
            palette[key] = normalized if normalized else DEFAULT_COLORS[key]
        else:
            palette[key] = DEFAULT_COLORS[key]
    
    return palette


# =============================================================================
# Configuration Generation
# =============================================================================

def gen_ulauncher_config(palette: Dict[str, str], opacities: Optional[Dict[str, int]] = None) -> Tuple[str, str]:
    """Generate Ulauncher configuration from palette.
    
    Args:
        palette: Color palette dictionary
        opacities: Optional dict with opacity values (0-100) for rgba colors
    
    Returns:
        Tuple of (manifest_content, css_content)
    
    Raises:
        FileNotFoundError: If template files don't exist
    """
    if opacities is None:
        opacities = {}
    
    template_dir = _get_template_dir()
    manifest_path = template_dir / "manifest.json"
    css_path = template_dir / "theme.css"
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Template manifest not found: {manifest_path}")
    if not css_path.exists():
        raise FileNotFoundError(f"Template CSS not found: {css_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = f.read()
    with open(css_path, 'r', encoding='utf-8') as f:
        css = f.read()
    
    # Replace placeholders in manifest
    for key, value in palette.items():
        placeholder = f'"{key}": "hex_color"'
        replacement = f'"{key}": "{value}"'
        manifest = manifest.replace(placeholder, replacement)
    
    # Replace placeholders in CSS
    for key, value in palette.items():
        # rgba format - use opacity if provided
        placeholder_rgba = f'@define-color {key} rgba_color;'
        alpha = opacities.get(key, 100) / 100.0  # Default 100% opacity
        replacement_rgba = f'@define-color {key} {hex_to_rgba(value, alpha)};'
        css = css.replace(placeholder_rgba, replacement_rgba)
        
        # hex format
        placeholder_hex = f'@define-color {key} hex_color;'
        replacement_hex = f'@define-color {key} {value};'
        css = css.replace(placeholder_hex, replacement_hex)
    
    return manifest, css


# =============================================================================
# Theme Application
# =============================================================================

def _create_backup() -> bool:
    """Create backup of current Ulauncher theme.
    
    Returns:
        True if backup created, False if no theme to backup
    """
    output_dir = _get_output_dir()
    backup_dir = _get_backup_dir()
    
    if not output_dir.exists():
        return False
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup manifest and CSS
    for filename in ['manifest.json', 'theme.css']:
        src = output_dir / filename
        if src.exists():
            shutil.copy2(src, backup_dir / filename)
    
    return True


def _restore_backup() -> Tuple[bool, str]:
    """Restore Ulauncher theme from backup.
    
    Returns:
        Tuple of (success, message)
    """
    backup_dir = _get_backup_dir()
    output_dir = _get_output_dir()
    
    if not backup_dir.exists():
        return False, "No backup found"
    
    manifest_backup = backup_dir / 'manifest.json'
    css_backup = backup_dir / 'theme.css'
    
    if not manifest_backup.exists() or not css_backup.exists():
        return False, "Incomplete backup"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    shutil.copy2(manifest_backup, output_dir / 'manifest.json')
    shutil.copy2(css_backup, output_dir / 'theme.css')
    
    return True, "Backup restored"


def apply_ulauncher_theme(colors: Dict[str, str], opacities: Optional[Dict[str, int]] = None) -> Tuple[bool, str]:
    """Apply colors to Ulauncher theme.
    
    Args:
        colors: Dictionary with color values for the theme
        opacities: Optional dict with opacity values (0-100) for rgba colors
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Build palette
        palette = build_ulauncher_palette(colors)
        
        # Generate config with opacities
        manifest, css = gen_ulauncher_config(palette, opacities)
        
        # Create backup before applying
        _create_backup()
        
        # Ensure output directory exists
        output_dir = _get_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy static files from template
        template_dir = _get_template_dir()
        for filename in ['LICENSE', 'theme-gtk-3.20.css']:
            src = template_dir / filename
            dst = output_dir / filename
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
        
        # Write generated files
        with open(output_dir / 'manifest.json', 'w', encoding='utf-8') as f:
            f.write(manifest)
        with open(output_dir / 'theme.css', 'w', encoding='utf-8') as f:
            f.write(css)
        
        # Update Ulauncher settings to use our theme and restart
        _update_ulauncher_settings()
        refresh_ulauncher()
        
        return True, "Theme applied successfully"
    
    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error applying theme: {e}"


def _update_ulauncher_settings() -> None:
    """Update Ulauncher settings.json to use kuntatinte theme."""
    settings_path = Path.home() / '.config' / 'ulauncher' / 'settings.json'
    
    if not settings_path.exists():
        return
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '"theme-name"' in content:
            content = re.sub(
                r'"theme-name"\s*:\s*"[^"]*"',
                '"theme-name": "kuntatinte"',
                content
            )
            with open(settings_path, 'w', encoding='utf-8') as f:
                f.write(content)
    except Exception as e:
        logger.warning(f"Could not update Ulauncher settings: {e}")


def restore_ulauncher_backup() -> Tuple[bool, str]:
    """Restore Ulauncher theme from backup.
    
    Returns:
        Tuple of (success, message)
    """
    return _restore_backup()


def refresh_ulauncher() -> Tuple[bool, str]:
    """Restart Ulauncher to apply theme changes.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Ensure settings point to our theme
        _update_ulauncher_settings()
        
        # Kill existing Ulauncher
        subprocess.run(['pkill', 'ulauncher'], capture_output=True)
        
        # Restart with our settings
        env = os.environ.copy()
        env['GDK_BACKEND'] = 'x11'
        subprocess.Popen(
            ['ulauncher', '--hide-window', '--no-window-shadow'],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        return True, "Ulauncher restarted"
    
    except Exception as e:
        return False, f"Error restarting Ulauncher: {e}"


# =============================================================================
# Public API
# =============================================================================

def get_current_colors() -> Dict[str, Any]:
    """Get current colors from applied theme.
    
    Returns:
        Dictionary with color values and opacities, or empty dict if not found
    """
    output_dir = _get_output_dir()
    css_path = output_dir / 'theme.css'
    manifest_path = output_dir / 'manifest.json'
    
    if not css_path.exists():
        return {}
    
    colors: Dict[str, Any] = {}
    
    try:
        # Read colors from CSS
        with open(css_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse @define-color statements
        # Match: @define-color name #rrggbb; or @define-color name rgba(...);
        for key in COLOR_KEYS:
            if key in ['when_selected', 'when_not_selected']:
                continue  # These are in manifest.json
            
            # Try hex format first
            hex_match = re.search(rf'@define-color\s+{key}\s+(#[0-9a-fA-F]{{6}});', content)
            if hex_match:
                colors[key] = hex_match.group(1).lower()
                continue
            
            # Try rgba format - also extract opacity
            rgba_match = re.search(rf'@define-color\s+{key}\s+rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', content)
            if rgba_match:
                r, g, b = int(rgba_match.group(1)), int(rgba_match.group(2)), int(rgba_match.group(3))
                alpha = float(rgba_match.group(4))
                colors[key] = rgb_to_hex(r, g, b)
                # Store opacity as integer 0-100
                colors[f'{key}_opacity'] = int(alpha * 100)
        
        # Read when_selected and when_not_selected from manifest.json
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            hl_colors = manifest.get('matched_text_hl_colors', {})
            if 'when_selected' in hl_colors:
                colors['when_selected'] = normalize_color(hl_colors['when_selected']) or ''
            if 'when_not_selected' in hl_colors:
                colors['when_not_selected'] = normalize_color(hl_colors['when_not_selected']) or ''
        
        return colors
    except Exception as e:
        logger.error(f"Error loading Ulauncher colors: {e}")
        return {}


def has_backup() -> bool:
    """Check if a backup exists.
    
    Returns:
        True if backup exists
    """
    backup_dir = _get_backup_dir()
    return (backup_dir / 'manifest.json').exists() and (backup_dir / 'theme.css').exists()


def is_ulauncher_installed() -> bool:
    """Check if Ulauncher is installed.
    
    Returns:
        True if Ulauncher is found
    """
    try:
        result = subprocess.run(['which', 'ulauncher'], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False
