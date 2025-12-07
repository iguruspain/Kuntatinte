#!/usr/bin/env python3
"""
Kuntatinte - Color Palette Tools.

A modern application for extracting color palettes from images
using QML with Kirigami for a native KDE Plasma experience.
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Qt environment BEFORE importing PyQt6
from core.qt_environment import (
    setup_qt_environment,
    setup_qml_import_paths,
    add_qml_import_paths_to_engine
)

setup_qt_environment()

from PyQt6.QtCore import QUrl, QtMsgType
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication

from core.backend import PaletteBackend


def qt_message_handler(_mode: QtMsgType, _context, message: str) -> None:
    """Filter out noisy Qt warnings."""
    # Suppress libpng ICC profile warnings
    if "libpng warning" in message:
        return
    # Log other messages
    logger.warning(message)


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
