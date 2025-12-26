"""
Qt Environment Setup.

Configures Qt environment variables before importing PyQt6 to ensure
proper integration with KDE Plasma and system themes.
"""

import os
from pathlib import Path

def _setup_xdg_runtime_dir() -> None:
    """Configure XDG_RUNTIME_DIR if not already set."""
    if os.environ.get('XDG_RUNTIME_DIR'):
        return
    
    uid = str(os.geteuid())
    candidate = f'/run/user/{uid}'
    if Path(candidate).is_dir():
        os.environ['XDG_RUNTIME_DIR'] = candidate


def _detect_wayland() -> None:
    """Detect and configure Wayland display if available."""
    if os.environ.get('WAYLAND_DISPLAY'):
        return
    
    uid = str(os.geteuid())
    runtime = Path(f'/run/user/{uid}')
    if runtime.is_dir():
        for p in runtime.iterdir():
            if p.name.startswith('wayland'):
                os.environ['WAYLAND_DISPLAY'] = p.name
                break


def _setup_platform_theme() -> None:
    """Configure Qt platform theme based on current desktop environment."""
    if os.environ.get('QT_QPA_PLATFORMTHEME'):
        return
    
    xdg = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
    if 'kde' in xdg or 'plasma' in xdg:
        os.environ['QT_QPA_PLATFORMTHEME'] = 'kde'
    elif 'gnome' in xdg:
        os.environ['QT_QPA_PLATFORMTHEME'] = 'gtk3'


def setup_qt_environment() -> None:
    """Configure the environment for Qt to use native system plugins.
    
    This must be called BEFORE importing PyQt6 modules.
    """
    _setup_xdg_runtime_dir()
    _detect_wayland()
    _setup_platform_theme()

