#!/usr/bin/env python3
# Copyright (C) 2025 iguruspain
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
Kuntatinte - Color Palette Tools.

A modern application for extracting color palettes from images
using QML with Kirigami for a native KDE Plasma experience.
"""

import sys
import logging
from pathlib import Path

# Import config manager first to configure logging
from core.config_manager import config

# Configure logging based on config
def setup_logging():
    """Configure logging based on user configuration."""
    if not config.logging_enabled:
        # Disable all logging
        logging.getLogger().setLevel(logging.CRITICAL + 1)
        
        # Suppress Qt/QML debug messages
        import os
        os.environ['QT_LOGGING_RULES'] = 'qt.qml=false'
        
        # Install Qt message handler to suppress all Qt messages
        def silent_qt_handler(mode, context, message):
            # Suppress all Qt messages when logging is disabled
            pass
        
        # Import here to avoid circular imports
        from PyQt6.QtCore import qInstallMessageHandler
        qInstallMessageHandler(silent_qt_handler)
        
        # Also redirect stdout and stderr as backup
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        return
    
    # When logging is enabled, allow Qt messages but filter them
    import os
    # Suppress QML debug messages but allow other Qt messages
    os.environ['QT_LOGGING_RULES'] = '*.qml=false;qt.qml=false'
    
    # Install Qt message handler to filter messages
    def qt_message_handler(mode, context, message):
        # Suppress libpng warnings and QML debug messages
        if "libpng warning" in message or message.startswith("qml:"):
            return
        # Log other Qt messages as warnings
        logger.warning(f"Qt: {message}")
    
    from PyQt6.QtCore import qInstallMessageHandler
    qInstallMessageHandler(qt_message_handler)
    
    # Map string levels to logging constants
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    level = level_map.get(config.logging_level.upper(), logging.INFO)
    
    if config.logging_file:
        # Log to file
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=config.logging_file,
            filemode='a'  # Append mode
        )
    else:
        # Log to console
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

setup_logging()
logger = logging.getLogger(__name__)

# Configure Qt environment BEFORE importing PyQt6
from core.qt_environment import (
    setup_qt_environment,
    setup_qml_import_paths,
    add_qml_import_paths_to_engine
)

setup_qt_environment()

from PyQt6.QtCore import QUrl
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication

from core.backend import PaletteBackend


def main() -> None:
    """Application entry point."""
    # Set up QML import paths for Kirigami
    setup_qml_import_paths()
    
    app = QApplication(sys.argv)
    app.setApplicationName("Kuntatinte")
    app.setOrganizationName("PaletteTools")
    app.setOrganizationDomain("local")
    
    # Create QML engine
    engine = QQmlApplicationEngine()
    
    # Add import paths to engine
    add_qml_import_paths_to_engine(engine)
    
    # Create and inject backend
    backend = PaletteBackend()
    context = engine.rootContext()
    if context is not None:
        context.setContextProperty("backend", backend)
    
    # Load QML file
    qml_file = Path(__file__).parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    
    if not engine.rootObjects():
        logger.error("Could not load QML interface")
        logger.error(f"File: {qml_file}")
        sys.exit(1)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
