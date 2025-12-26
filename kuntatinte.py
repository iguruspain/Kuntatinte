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
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add file handler if file is specified
    if config.logging_file:
        file_handler = logging.FileHandler(config.logging_file, mode='a')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Add console handler if console is enabled
    if config.logging_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

setup_logging()
logger = logging.getLogger(__name__)

# Configure Qt environment BEFORE importing PyQt6
from core.qt_environment import (
    setup_qt_environment,
)

setup_qt_environment()

from PyQt6.QtCore import QUrl
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication

from core.backend import PaletteBackend


def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Kuntatinte")
    app.setOrganizationName("PaletteTools")
    app.setOrganizationDomain("local")
    
    # Create QML engine
    engine = QQmlApplicationEngine()
    
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
