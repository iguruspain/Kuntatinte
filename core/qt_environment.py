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
Qt Environment Setup.

Configures Qt environment variables before importing PyQt6 to ensure
proper integration with KDE Plasma and system themes.
"""

import os
from pathlib import Path


# System paths for Qt6 plugins
SYSTEM_PLUGIN_PATHS = [
    '/usr/lib/qt6/plugins',
    '/usr/lib64/qt6/plugins',
    '/usr/lib/x86_64-linux-gnu/qt6/plugins',
]

# System paths for QML imports
QML_IMPORT_PATHS = [
    '/usr/lib/qt6/qml',
    '/usr/lib64/qt6/qml',
    '/usr/lib/x86_64-linux-gnu/qt6/qml',
]


def _prepend_to_env_path(var_name: str, path: str) -> None:
    """Prepend a path to an environment variable (colon-separated)."""
    existing = os.environ.get(var_name, '')
    if path not in existing:
        if existing:
            os.environ[var_name] = f"{path}:{existing}"
        else:
            os.environ[var_name] = path


def _setup_plugin_paths() -> None:
    """Configure Qt plugin paths for native KDE theme support.
    
    PyQt6 ships its own plugins which don't include KDE theme support.
    Adding system plugin paths enables KDEPlasmaPlatformTheme.
    """
    for plugin_path in SYSTEM_PLUGIN_PATHS:
        if Path(plugin_path).is_dir():
            _prepend_to_env_path('QT_PLUGIN_PATH', plugin_path)
            break


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
    _setup_plugin_paths()
    _setup_xdg_runtime_dir()
    _detect_wayland()
    _setup_platform_theme()


def setup_qml_import_paths() -> None:
    """Configure QML import paths to find Kirigami and other system components.
    
    This should be called after creating the QML engine.
    """
    for qml_path in QML_IMPORT_PATHS:
        if Path(qml_path).is_dir():
            _prepend_to_env_path('QML_IMPORT_PATH', qml_path)
            _prepend_to_env_path('QML2_IMPORT_PATH', qml_path)
            break


def add_qml_import_paths_to_engine(engine) -> None:
    """Add QML import paths to the QML engine.
    
    Args:
        engine: QQmlApplicationEngine instance
    """
    for qml_path in QML_IMPORT_PATHS:
        if Path(qml_path).is_dir():
            engine.addImportPath(qml_path)
