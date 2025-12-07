#!/usr/bin/env python3
"""
Fastfetch Logo Tinting Utility.

Applies accent color tinting to the fastfetch logo image.

Workflow:
1. Read logo filename from fastfetch config.jsonc
2. Backup the current logo image
3. Apply accent tint to template image and save as the logo
4. Clear fastfetch cache
"""

import json
import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple


logger = logging.getLogger(__name__)

from core.config_manager import config as app_config


# =============================================================================
# Path Configuration
# =============================================================================

def _get_template_image() -> Path:
    """Get fastfetch logo template image path (default fallback)."""
    return app_config.fastfetch_template


def _get_active_logo() -> Path:
    """Get active logo path (custom if set, otherwise default template)."""
    return app_config.fastfetch_logo


def _get_custom_logo() -> Optional[Path]:
    """Get custom logo path if configured."""
    return app_config.fastfetch_custom_logo


def _get_config_dir() -> Path:
    """Get fastfetch config directory from app config."""
    return app_config.fastfetch_config_dir


def _get_config_path() -> Path:
    """Get fastfetch config.jsonc path."""
    return _get_config_dir() / 'config.jsonc'


def _get_cache_dir() -> Path:
    """Get fastfetch cache directory."""
    return Path.home() / '.cache' / 'fastfetch'


# =============================================================================
# Configuration Parsing
# =============================================================================

def _strip_jsonc_comments(content: str) -> str:
    """Remove JSONC-style comments from content.
    
    Handles // comments while preserving strings that contain //.
    
    Args:
        content: Raw JSONC file content
    
    Returns:
        Content with comments removed
    """
    lines = []
    for line in content.split('\n'):
        in_string = False
        result = []
        i = 0
        while i < len(line):
            if line[i] == '"' and (i == 0 or line[i-1] != '\\'):
                in_string = not in_string
                result.append(line[i])
            elif not in_string and line[i:i+2] == '//':
                break  # Rest of line is comment
            else:
                result.append(line[i])
            i += 1
        lines.append(''.join(result))
    return '\n'.join(lines)


def get_logo_path_from_config() -> Optional[Path]:
    """Read the logo source path from fastfetch config.jsonc.
    
    Returns:
        Full path to the logo image, or None if not found.
    """
    config_path = _get_config_path()
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Remove JSONC comments
        content = _strip_jsonc_comments(content)
        
        # Remove trailing commas (common in JSONC)
        content = re.sub(r',\s*([}\]])', r'\1', content)
        
        data = json.loads(content)
        
        # Extract logo source path
        logo_source = data.get('logo', {}).get('source', '')
        if logo_source:
            # Expand ~ to home directory
            return Path(logo_source.replace('~', str(Path.home())))
        
        return None
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Error parsing fastfetch config: {e}")
        return None


# =============================================================================
# Apply and Restore Functions
# =============================================================================

def apply_fastfetch_accent(accent_color: str) -> Tuple[bool, str]:
    """Apply accent color tint to fastfetch logo.
    
    Steps:
    1. Read logo path from config
    2. Backup existing logo (if no backup exists)
    3. Apply grayscale + tint from active logo (custom or default template)
    4. Clear cache
    
    Args:
        accent_color: Hex color string (e.g., '#569cc1')
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Get logo path from config
    logo_path = get_logo_path_from_config()
    if not logo_path:
        return False, "Could not read logo path from fastfetch config"
    
    backup_path = logo_path.with_suffix(logo_path.suffix + '.bak')
    cache_dir = _get_cache_dir()
    source_image = _get_active_logo()  # Use custom logo if set, otherwise default template
    
    if not source_image.exists():
        return False, f"Source image not found: {source_image}"
    
    # Ensure logo directory exists
    logo_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Backup existing logo if it exists and no backup yet
        if logo_path.exists() and not backup_path.exists():
            shutil.copy2(logo_path, backup_path)
        
        # Step 2: Convert source to grayscale and save to logo path
        subprocess.run([
            'magick', str(source_image),
            '-colorspace', 'gray',
            str(logo_path)
        ], check=True, capture_output=True)
        
        # Step 3: Apply tint with accent color
        subprocess.run([
            'magick', str(logo_path),
            '-fill', accent_color,
            '-tint', '80',
            str(logo_path)
        ], check=True, capture_output=True)
        
        # Step 4: Clear fastfetch cache
        if cache_dir.exists():
            shutil.rmtree(cache_dir, ignore_errors=True)
        
        return True, f"Fastfetch logo tinted: {logo_path}"
    
    except FileNotFoundError:
        return False, "ImageMagick (magick) not found. Please install it."
    except subprocess.CalledProcessError as e:
        return False, f"ImageMagick error: {e.stderr.decode() if e.stderr else str(e)}"
    except Exception as e:
        return False, f"Error: {e}"


def restore_fastfetch_backup() -> Tuple[bool, str]:
    """Restore fastfetch logo from backup file (.bak).
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Get logo path from config
    logo_path = get_logo_path_from_config()
    if not logo_path:
        return False, "Could not read logo path from fastfetch config"
    
    backup_path = logo_path.with_suffix(logo_path.suffix + '.bak')
    cache_dir = _get_cache_dir()
    
    if not backup_path.exists():
        return False, f"No backup file found: {backup_path}"
    
    try:
        shutil.copy2(backup_path, logo_path)
        
        # Clear cache
        if cache_dir.exists():
            shutil.rmtree(cache_dir, ignore_errors=True)
        
        return True, "Fastfetch logo restored from backup"
    except Exception as e:
        return False, f"Error: {e}"


# =============================================================================
# Preview Functions
# =============================================================================

def get_current_logo_path() -> Optional[str]:
    """Get current fastfetch logo path as string.
    
    Returns:
        Logo path string, or None if not configured.
    """
    path = get_logo_path_from_config()
    return str(path) if path else None


def get_active_logo_path() -> str:
    """Get active logo path (custom if set, otherwise default template).
    
    Returns:
        Active logo path string.
    """
    return str(_get_active_logo())


def get_template_path() -> str:
    """Get default template image path.
    
    Returns:
        Default template path string.
    """
    return str(_get_template_image())


def get_custom_logo_path() -> Optional[str]:
    """Get custom logo path if configured.
    
    Returns:
        Custom logo path string, or None if using default.
    """
    custom = _get_custom_logo()
    return str(custom) if custom else None


def set_custom_logo(image_path: str) -> Tuple[bool, str]:
    """Set a custom logo image.
    
    Saves the path to the config file. The original image stays in place.
    
    Args:
        image_path: Path to the custom logo image, or empty to reset to default.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if image_path:
        source = Path(image_path)
        if not source.exists():
            return False, f"Image not found: {image_path}"
    
    try:
        app_config.set_fastfetch_custom_logo(image_path)
        if image_path:
            return True, f"Custom logo set: {image_path}"
        else:
            return True, "Reset to default template"
    except Exception as e:
        return False, f"Error: {e}"


def generate_tinted_preview(source_path: str, accent_color: str) -> Optional[str]:
    """Generate a tinted preview of a logo image.
    
    Creates a temporary tinted version of the image for preview purposes.
    
    Args:
        source_path: Path to the source image
        accent_color: Hex color string (e.g., '#569cc1')
    
    Returns:
        Path to the preview image, or None on error.
    """
    import tempfile
    
    source = Path(source_path)
    if not source.exists():
        return None
    
    try:
        # Create temp file with same extension
        suffix = source.suffix or '.png'
        fd, preview_path = tempfile.mkstemp(suffix=suffix, prefix='fastfetch_preview_')
        import os
        os.close(fd)
        
        # Convert to grayscale
        subprocess.run([
            'magick', str(source),
            '-colorspace', 'gray',
            preview_path
        ], check=True, capture_output=True)
        
        # Apply tint
        subprocess.run([
            'magick', preview_path,
            '-fill', accent_color,
            '-tint', '80',
            preview_path
        ], check=True, capture_output=True)
        
        return preview_path
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        return None


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fastfetch.py <accent_hex_color>")
        print("       python fastfetch.py --restore")
        print("Example: python fastfetch.py '#569cc1'")
        sys.exit(1)
    
    if sys.argv[1] == '--restore':
        success, message = restore_fastfetch_backup()
    else:
        accent = sys.argv[1]
        success, message = apply_fastfetch_accent(accent)
    
    print(message)
    sys.exit(0 if success else 1)
