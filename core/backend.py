"""
Palette Backend.

QObject backend that exposes application logic to QML for color palette
extraction and application theming.
"""

import json
import logging
import subprocess
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QStandardPaths
from PyQt6.QtCore import pyqtProperty  # type: ignore[attr-defined]
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QFileDialog, QColorDialog

from core.config_manager import config
from core.imagemagick import extract_colors_from_wallpaper, extract_accent_from_wallpaper
from core.material_you_colors import (
    extract_source_colors_from_image,
    is_available as is_material_you_available,
)
from core import autogen
from integrations.kuntatinte_colors import (
    # kde_colors exports
    get_current_scheme_name,
    read_color,
    write_color,
    get_color_set,
    get_color_set_from_scheme,
    get_all_colors,
    apply_palette_to_scheme,
    notify_color_change,
    get_color_schemes_list,
    apply_color_scheme,
    COLOR_SETS,
    COLOR_KEYS,
    parse_scheme_file,
    get_color_sections,
    get_inactive_sections,
    get_section_colors,
    save_color_scheme_from_data,
    # kde_colors_v2 exports
    generate_and_save_kuntatinte_schemes,
    get_preview_data,
)
from integrations.pywal import generate_palette as pywal_generate_palette



# Supported image file extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}


def is_command_available(command: str) -> bool:
    """Check if a command is available in the system PATH."""
    try:
        result = subprocess.run(
            ["which", command],
            capture_output=True,
            text=True,
            check=True
        )
        return result.returncode == 0
    except (OSError, subprocess.CalledProcessError):
        return False


def is_fastfetch_installed() -> bool:
    """Check if fastfetch is installed."""
    return is_command_available("fastfetch")


def is_starship_installed() -> bool:
    """Check if starship is installed."""
    return is_command_available("starship")


class PaletteBackend(QObject):
    """Backend that exposes application logic to QML."""
    
    # Signals - use 'QVariantList' to avoid Qt marshalling issues with Python lists
    colorsExtracted = pyqtSignal('QVariantList')
    accentExtracted = pyqtSignal(str)
    sourceColorsExtracted = pyqtSignal(str)  # JSON string to avoid marshalling issues
    extractionError = pyqtSignal(str)
    imageListChanged = pyqtSignal()
    
    # Properties exposed to QML
    @pyqtProperty(bool, constant=True)
    def debugUi(self) -> bool:
        """Whether UI debug logging and screenshots are enabled."""
        return config.debug_ui
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize the palette backend.
        
        Sets up caches, loads configuration, and initializes the wallpaper folder
        if one is configured.
        
        Args:
            parent: Parent QObject for Qt ownership hierarchy
        """
        super().__init__(parent)
        self._image_list: list[str] = []
        self._current_folder: Optional[Path] = None
        self._screenshot_counter = 0
        # Material You cache
        self._material_you_cache: dict[str, list[str]] = {}
        # No specific Pywal mode — use pywal module defaults
        # Keep last extracted source colors per image to avoid re-extraction
        self._last_source_colors: dict[str, list[str]] = {}
        # Track extractions in progress to avoid concurrent work
        self._extract_in_progress: set[str] = set()
        # Remember last emitted JSON for source colors to avoid duplicate signals
        self._last_emitted_source_json: dict[str, str] = {}
        
        # Load default wallpapers folder from config
        if config.wallpapers_folder and config.wallpapers_folder.exists():
            self.loadFolder(str(config.wallpapers_folder))
    
    # =========================================================================
    # Debug / Screenshot Capture
    # =========================================================================
    
    @pyqtSlot(str)
    def captureDebugScreenshot(self, event_name: str) -> None:
        """Capture a debug screenshot using spectacle.
        
        Only captures if debug_ui is enabled in config.
        
        Args:
            event_name: Name of the event that triggered the screenshot
        """
        if not config.debug_ui:
            return
            
        debug_dir = Path("/tmp/kuntatinte_debug")
        debug_dir.mkdir(exist_ok=True)
        self._screenshot_counter += 1
        filename = f"{self._screenshot_counter:03d}_{event_name}.png"
        filepath = debug_dir / filename
        logger.info(f"[UI] Capturing screenshot: {filepath}")
        subprocess.run(
            ["spectacle", "-b", "-n", "-o", str(filepath)],
            check=False
        )
    
    # =========================================================================
    # Application Availability Checks
    # =========================================================================
    
    @pyqtSlot(result='bool')
    def isFastfetchInstalled(self) -> bool:
        """Check if fastfetch is installed."""
        return is_fastfetch_installed()
    
    @pyqtSlot(result='bool')
    def isStarshipInstalled(self) -> bool:
        """Check if starship is installed."""
        return is_starship_installed()
    
    
    
    @pyqtSlot(result='QVariantList')
    def getAvailableSettings(self) -> list[str]:
        """Get list of available settings based on installed applications."""
        from integrations.ulauncher import is_ulauncher_installed
        
        available = []
        if is_fastfetch_installed():
            available.append("Fastfetch")
        if is_starship_installed():
            available.append("Starship")
        if is_ulauncher_installed():
            available.append("Ulauncher")
        available.append("Kuntatinte Color Scheme")
        return available
    
    @pyqtSlot(str, result='int')
    def getPanelWidth(self, setting_name: str) -> int:
        """Get panel width for a specific setting.
        
        Args:
            setting_name: Name of the setting (e.g., "Kuntatinte Color Scheme")
        
        Returns:
            Panel width in pixels
        """
        return config.get_panel_width(setting_name)
    
    @pyqtSlot(result='int')
    def getMinHeight(self) -> int:
        """Get minimum window height from config."""
        return config.get("ui", "min_height", 480)
    
    # =========================================================================
    # Image List Properties and Methods
    # =========================================================================
    
    @pyqtSlot(result='QVariantList')
    def getImageList(self) -> list[str]:
        """Get list of image paths in the current folder."""
        return self._image_list
    
    def _get_image_list(self) -> list[str]:
        return self._image_list
    
    imageList = pyqtProperty(list, _get_image_list, notify=imageListChanged)
    
    @pyqtSlot()
    def openFolderDialog(self) -> None:
        """Open native folder selection dialog."""
        # Start from last used folder, or Pictures folder, or home
        if self._current_folder and self._current_folder.exists():
            start_folder = str(self._current_folder)
        else:
            # Get user's Pictures folder (works regardless of language)
            pictures = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
            start_folder = pictures if pictures else str(Path.home())
        
        folder = QFileDialog.getExistingDirectory(
            None,
            "Select Image Folder",
            start_folder,
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.loadFolder(folder)
    
    @pyqtSlot(str)
    def loadFolder(self, folder_path: str) -> None:
        """Load images from a folder.
        
        Args:
            folder_path: Path to the folder to scan for images
        """
        self._current_folder = Path(folder_path)
        self._image_list = []
        
        if self._current_folder.exists() and self._current_folder.is_dir():
            for p in sorted(self._current_folder.iterdir()):
                if p.suffix.lower() in IMAGE_EXTENSIONS and p.is_file():
                    self._image_list.append(str(p))
            
            # Save folder to config for next session
            config.set("paths", "wallpapers_folder", folder_path)
        
        self.imageListChanged.emit()
    
    # =========================================================================
    # Color Extraction Methods
    # =========================================================================
    
    @pyqtSlot(str, str, str)
    def extractColors(self, image_path: str, method: str = "ImageMagick", mode: str = "dark") -> None:
        """Extract color palette from an image in a background thread.
        
        Args:
            image_path: Path to the image file
            method: Extraction method ("ImageMagick", "Pywal", or "KDE Material You")
            mode: Palette mode ("light" or "dark")
        """
        def _extract():
            """Internal function to perform color extraction in background thread."""
            try:
                if method == "Pywal":
                    colors = self._extract_colors_pywal(image_path)
                elif method == "KDE Material You":
                    colors = self._extract_colors_kde_material_you(image_path)
                else:
                    # For ImageMagick extraction, use specified mode
                    colors = extract_colors_from_wallpaper(image_path, mode)
                
                if colors is None:
                    colors = []
                
                # Convert to list of hex strings
                hex_colors = self._normalize_colors_to_hex(colors)
                # Emit signal from main thread
                self.colorsExtracted.emit(hex_colors)
            except Exception as e:
                self.extractionError.emit(str(e))
        
        # Run extraction in background thread
        thread = threading.Thread(target=_extract, daemon=True)
        thread.start()
    
    def _normalize_colors_to_hex(self, colors: list) -> list[str]:
        """Convert colors to hex string format.
        
        Args:
            colors: List of colors in various formats (str, tuple, list)
        
        Returns:
            List of hex color strings (#rrggbb)
        """
        hex_colors: list[str] = []
        for color in colors:
            if isinstance(color, str):
                hex_colors.append(color if color.startswith('#') else f'#{color}')
            elif isinstance(color, (list, tuple)) and len(color) >= 3:
                hex_colors.append(f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}')
        return hex_colors
    
    def _extract_colors_pywal(self, image_path: str) -> list:
        """Extract colors using pywal from cache or by generating new ones."""
        # Prefer the Python API integration; fall back will raise and be handled by the caller.
        try:
            colors = pywal_generate_palette(image_path, cols=16)
            if not colors:
                self.extractionError.emit("Pywal returned no colors")
                return []
            # Normalize to hex strings for the rest of the pipeline
            return self._normalize_colors_to_hex(colors)
        except Exception as e:
            msg = str(e)
            if 'no está instalado' in msg or 'wal (pywal CLI) no está instalado' in msg or 'pywal no está instalado' in msg:
                msg = msg + ". Instale con: pip install pywal"
            self.extractionError.emit(msg)
            return []
    
    def _extract_colors_kde_material_you(self, image_path: str) -> list:
        """Extract colors from KDE Material You Colors cache.
        
        Note: kde-material-you-colors must be running as a service/plasmoid
        for the cache to be up to date.
        """
        cache_file = Path.home() / ".cache" / "wal" / "colors.json"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    colors_dict = json.load(f)
                colors = colors_dict.get('colors', {})
                return [colors[f'color{i}'] for i in range(16) if f'color{i}' in colors]
            else:
                self.extractionError.emit(
                    "kde-material-you-colors cache not found (~/.cache/wal/colors.json)"
                )
                return []
                
        except json.JSONDecodeError:
            self.extractionError.emit("Error reading colors file")
            return []
        except Exception as e:
            self.extractionError.emit(f"KDE Material You error: {str(e)}")
            return []
    
    def _parse_color_to_hex(self, value: str) -> Optional[str]:
        """Convert a color in various formats to hex.
        
        Supports:
        - Hex: #rrggbb, #rrggbbaa
        - RGB: r,g,b
        - RGBA: r,g,b,a
        
        Returns:
            Color in #rrggbb format or None if invalid
        """
        try:
            value = value.strip()
            
            # Hex format
            if value.startswith('#'):
                if len(value) >= 7:
                    return value[:7].lower()
                return None
            
            # RGB or RGBA format
            if ',' in value:
                parts = value.split(",")
                if len(parts) >= 3:
                    r = int(parts[0].strip())
                    g = int(parts[1].strip())
                    b = int(parts[2].strip())
                    if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                        return f"#{r:02x}{g:02x}{b:02x}"
            
            return None
        except (ValueError, IndexError):
            return None
    
    # System color extraction removed: functionality deprecated with removal of "System" option
    
    @pyqtSlot(str)
    def extractAccent(self, image_path: str) -> None:
        """Extract the best accent color from an image in a background thread."""
        def _extract():
            """Internal function to perform accent color extraction in background thread."""
            try:
                logger.debug(f"extractAccent: extracting accent for {image_path}")
                accent = extract_accent_from_wallpaper(image_path)
                logger.debug(f"extractAccent: result={accent}")
                if accent:
                    self.accentExtracted.emit(accent)
                else:
                    self.extractionError.emit("Could not extract a vibrant accent color")
            except Exception as e:
                logger.error(f"extractAccent error: {e}")
                self.extractionError.emit(str(e))
        
        thread = threading.Thread(target=_extract, daemon=True)
        thread.start()
    
    @pyqtSlot(str)
    def extractSourceColors(self, image_path: str) -> None:
        """Extract Material You source colors from an image (synchronous).
        
        These are the seed colors that Material You uses to generate
        complete color schemes. Returns multiple options the user can choose from.
        """
        def _worker():
            try:
                if not is_material_you_available():
                    self.extractionError.emit("Material You extraction not available. Install materialyoucolor and Pillow.")
                    return

                colors = extract_source_colors_from_image(image_path, max_colors=7)
                if colors:
                    colors_json = json.dumps(colors)
                    logger.info(f"Material You source colors extracted ({len(colors)}): {colors}")
                    # Emit the fresh result (no caching)
                    self.sourceColorsExtracted.emit(colors_json)
                else:
                    self.extractionError.emit("Could not extract Material You colors")
            except Exception as e:
                self.extractionError.emit(str(e))

        # Run extraction in background thread without guards or caching
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    @pyqtSlot(str, result='QString')
    def runAutogen(self, mode: str) -> str:
        """Run autogen in test mode with a palette mode ("dark"/"light").

        Args:
            mode: Palette mode string from QML (e.g., "dark" or "light").

        Returns:
            JSON string with generated data or error.
        """
        try:
            result = autogen.run_autogen(test_mode=True, palette_mode=mode)
            return result if isinstance(result, str) else json.dumps(result)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    
    @pyqtSlot(result='bool')
    def isMaterialYouAvailable(self) -> bool:
        """Check if Material You color extraction is available."""
        return is_material_you_available()

    

    @pyqtSlot(str, int, float)
    def generateMaterialYouPalette(self, image_path: str, seed_index: int = 0, slider_percent: float = 50.0) -> None:
        """Generate a Material You style palette from an image seed in background.

        Args:
            image_path: path to image to extract seeds from (can be empty)
            seed_index: which source color index to use (0..n)
            slider_percent: 0-100 saturation/variant parameter
        """
        def worker():
            try:
                # Always perform a fresh extraction of source colors for this
                # generation to avoid shared caches/guards. We intentionally do
                # not rely on any stored state.
                seeds = extract_source_colors_from_image(image_path, max_colors=7)
                if not seeds:
                    self.extractionError.emit("Could not extract Material You source colors for generation")
                    return

                idx = max(0, min(seed_index, len(seeds) - 1))
                seed = seeds[idx]

                from core.color_utils import generate_palette_from_seed

                palette = generate_palette_from_seed(seed, mode=mode, slider_percent=slider_percent)

                # Emit to QML (no caching)
                self.colorsExtracted.emit(palette)
            except Exception as e:
                self.extractionError.emit(str(e))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    @pyqtSlot('QVariantList', str, int, float)
    def generateMaterialYouPaletteFromSeeds(self, seeds, mode: str, seed_index: int = 0, slider_percent: float = 50.0) -> None:
        """Generate Material You palette from supplied seeds (no caching).

        Args:
            seeds: list of seed hex strings (QVariantList from QML)
            mode: "light" or "dark"
            seed_index: index to use
            slider_percent: variant parameter 0-100
        """
        def worker():
            try:
                if not seeds or len(seeds) == 0:
                    self.extractionError.emit("No source seeds provided for generation")
                    return

                idx = max(0, min(seed_index, len(seeds) - 1))
                seed = seeds[idx]

                from core.color_utils import generate_palette_from_seed

                palette = generate_palette_from_seed(seed, mode=mode, slider_percent=slider_percent)
                self.colorsExtracted.emit(palette)
            except Exception as e:
                self.extractionError.emit(str(e))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    # =========================================================================
    # Color Selection Methods (for logging/debugging)
    # =========================================================================
    
    @pyqtSlot(str)
    def setAccentColor(self, color: str) -> None:
        """Store the selected accent color (does not apply to system)."""
        logger.info(f"Accent color selected: {color}")
    
    @pyqtSlot(str)
    def setAccentTextColor(self, color: str) -> None:
        """Store the selected accent text color (does not apply to system)."""
        logger.info(f"Accent text color selected: {color}")
    
    # =========================================================================
    # Color Picker Dialogs
    # =========================================================================
    
    @pyqtSlot(result='QString')
    def pickAccentColor(self) -> str:
        """Open native color picker dialog for accent color."""
        color = QColorDialog.getColor(
            QColor("#3daee9"), None, "Select accent color"
        )
        return color.name() if color.isValid() else ""
    
    @pyqtSlot(result='QString')
    def pickAccentTextColor(self) -> str:
        """Open native color picker dialog for accent text color."""
        color = QColorDialog.getColor(
            QColor("#ffffff"), None, "Select accent text color"
        )
        return color.name() if color.isValid() else ""
    
    @pyqtSlot(result='QString')
    def pickColor(self) -> str:
        """Open native color picker dialog for any color."""
        color = QColorDialog.getColor(
            QColor("#3daee9"), None, "Select color"
        )
        return color.name() if color.isValid() else ""
    
    # =========================================================================
    # Palette Variants
    # =========================================================================
    # =========================================================================
    # Wallpaper Methods
    # =========================================================================
    
    @pyqtSlot(str)
    def setAsWallpaper(self, image_path: str) -> None:
        """Apply image as desktop wallpaper using plasma-apply-wallpaperimage."""
        try:
            # Use plasma-apply-wallpaperimage (Plasma 6)
            subprocess.run(['plasma-apply-wallpaperimage', image_path], check=True)
            logger.info(f"Wallpaper set to: {image_path}")
        except FileNotFoundError:
            # Fallback: try with qdbus
            self._set_wallpaper_via_qdbus(image_path)
        except Exception as e:
            logger.error(f"Error setting wallpaper: {e}")
    
    def _set_wallpaper_via_qdbus(self, image_path: str) -> None:
        """Set wallpaper using qdbus as fallback method."""
        try:
            script = f'''
            var allDesktops = desktops();
            for (var i = 0; i < allDesktops.length; i++) {{
                var d = allDesktops[i];
                d.wallpaperPlugin = "org.kde.image";
                d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
                d.writeConfig("Image", "file://{image_path}");
            }}
            '''
            subprocess.run([
                'qdbus', 'org.kde.plasmashell', '/PlasmaShell',
                'org.kde.PlasmaShell.evaluateScript', script
            ], check=True)
            logger.info(f"Wallpaper set via qdbus to: {image_path}")
        except Exception as e:
            logger.error(f"Error setting wallpaper via qdbus: {e}")
    
    # =========================================================================
    # Starship Integration
    # =========================================================================
    
    @pyqtSlot(str, str, str, str, str, str, str, str, str, str, str, result='QString')
    def applyStarshipColors(
        self,
        accent: str, accent_text: str,
        dir_fg: str, dir_bg: str, dir_text: str,
        git_fg: str, git_bg: str, git_text: str,
        other_fg: str, other_bg: str, other_text: str
    ) -> str:
        """Apply colors to starship configuration.
        
        Returns:
            Empty string on success, error message on failure.
        """
        from integrations.starship import apply_starship_colors
        
        colors = {
            'accent': accent,
            'accent_text': accent_text,
            'dir_fg': dir_fg,
            'dir_bg': dir_bg,
            'dir_text': dir_text,
            'git_fg': git_fg,
            'git_bg': git_bg,
            'git_text': git_text,
            'other_fg': other_fg,
            'other_bg': other_bg,
            'other_text': other_text
        }
        
        # Filter empty colors
        colors = {k: v for k, v in colors.items() if v}
        
        success, message = apply_starship_colors(colors)
        if success:
            logger.info(f"Starship colors applied: {colors}")
            return ""
        else:
            logger.error(f"Error applying starship colors: {message}")
            return message
    
    @pyqtSlot(result='QVariantMap')
    def loadStarshipColors(self) -> dict:
        """Load current starship colors from config file.
        
        Returns:
            Dictionary with color values (empty string if not found).
        """
        from integrations.starship import load_starship_colors
        
        colors = load_starship_colors()
        logger.info(f"Starship colors loaded: {colors}")
        return colors
    
    @pyqtSlot(result='QString')
    def restoreStarshipBackup(self) -> str:
        """Restore starship.toml from backup file.
        
        Returns:
            Empty string on success, error message on failure.
        """
        from integrations.starship import restore_starship_backup
        
        success, message = restore_starship_backup()
        if success:
            logger.info("Starship backup restored")
            return ""
        else:
            logger.error(f"Error restoring starship backup: {message}")
            return message
    
    # =========================================================================
    # Fastfetch Integration
    # =========================================================================
    
    @pyqtSlot(str, result='QString')
    def applyFastfetchAccent(self, accent: str) -> str:
        """Apply accent color to fastfetch logo.
        
        Returns:
            Empty string on success, error message on failure.
        """
        from integrations.fastfetch import apply_fastfetch_accent
        
        if not accent:
            return "No accent color provided"
        
        success, message = apply_fastfetch_accent(accent)
        if success:
            logger.info(f"Fastfetch accent applied: {accent}")
            return ""
        else:
            logger.error(f"Error applying fastfetch accent: {message}")
            return message
    
    @pyqtSlot(result='QString')
    def restoreFastfetchOriginal(self) -> str:
        """Restore fastfetch logo from backup.
        
        Returns:
            Empty string on success, error message on failure.
        """
        from integrations.fastfetch import restore_fastfetch_backup
        
        success, message = restore_fastfetch_backup()
        if success:
            logger.info("Fastfetch logo restored from backup")
            return ""
        else:
            logger.error(f"Error restoring fastfetch logo: {message}")
            return message
    
    @pyqtSlot(result='QString')
    def getFastfetchTemplatePath(self) -> str:
        """Get the default fastfetch template image path.
        
        Returns:
            Path to default template as file:// URL, or empty string.
        """
        from integrations.fastfetch import get_template_path
        
        path = get_template_path()
        if path and Path(path).exists():
            return f"file://{path}"
        return ""
    
    @pyqtSlot(result='QString')
    def getFastfetchActiveLogo(self) -> str:
        """Get the active fastfetch logo path (custom or default).
        
        Returns:
            Path to active logo as file:// URL, or empty string.
        """
        from integrations.fastfetch import get_active_logo_path
        
        path = get_active_logo_path()
        if path and Path(path).exists():
            return f"file://{path}"
        return ""
    
    @pyqtSlot(result='QString')
    def getFastfetchCustomLogo(self) -> str:
        """Get the custom fastfetch logo path if set.
        
        Returns:
            Path to custom logo as file:// URL, or empty string if using default.
        """
        from integrations.fastfetch import get_custom_logo_path
        
        path = get_custom_logo_path()
        if path:
            return f"file://{path}"
        return ""
    
    @pyqtSlot(str, result='QString')
    def generateFastfetchPreview(self, accent: str) -> str:
        """Generate a tinted preview of the fastfetch logo.
        
        Args:
            accent: Hex color string
        
        Returns:
            Path to preview image as file:// URL, or empty string.
        """
        from integrations.fastfetch import get_active_logo_path, generate_tinted_preview
        
        if not accent:
            return ""
        
        # Use active logo (custom if set, otherwise default)
        source = get_active_logo_path()
        if not source or not Path(source).exists():
            return ""
        
        preview = generate_tinted_preview(source, accent)
        if preview:
            return f"file://{preview}"
        return ""
    
    @pyqtSlot(result='QString')
    def selectFastfetchLogo(self) -> str:
        """Open file dialog to select a new fastfetch logo.
        
        Returns:
            Selected file path as file:// URL, or empty string.
        """
        pictures_path = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )
        
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select Fastfetch Logo",
            pictures_path,
            "Images (*.png *.jpg *.jpeg *.webp *.gif *.bmp);;All Files (*)"
        )
        
        if file_path:
            return f"file://{file_path}"
        return ""
    
    @pyqtSlot(str, result='QString')
    def setFastfetchCustomLogo(self, image_url: str) -> str:
        """Set a custom fastfetch logo image.
        
        Args:
            image_url: File URL to the image, or empty to reset to default.
        
        Returns:
            Empty string on success, error message on failure.
        """
        from integrations.fastfetch import set_custom_logo
        
        # Convert file:// URL to path
        if image_url.startswith("file://"):
            image_path = image_url[7:]
        else:
            image_path = image_url
        
        success, message = set_custom_logo(image_path)
        if success:
            logger.info(f"Fastfetch custom logo: {image_path if image_path else 'reset to default'}")
            return ""
        else:
            logger.error(f"Error setting fastfetch logo: {message}")
            return message
    
    @pyqtSlot(result='QString')
    def resetFastfetchToDefault(self) -> str:
        """Reset fastfetch logo to default template.
        
        Returns:
            Empty string on success, error message on failure.
        """
        from integrations.fastfetch import set_custom_logo
        
        success, message = set_custom_logo("")
        if success:
            logger.info("Fastfetch logo reset to default template")
            return ""
        else:
            return message

    # =========================================================================
    # Ulauncher Methods
    # =========================================================================

    @pyqtSlot(result='bool')
    def isUlauncherInstalled(self) -> bool:
        """Check if Ulauncher is installed.
        
        Returns:
            True if Ulauncher is installed.
        """
        from integrations.ulauncher import is_ulauncher_installed
        return is_ulauncher_installed()

    @pyqtSlot(str, str, int, int, str, str, str, str, str, str, str, str, str, str, str, str, str, result='QString')
    def applyUlauncherColors(
        self,
        bg_color: str,
        window_border_color: str,
        bg_opacity: int,
        border_opacity: int,
        prefs_background: str,
        input_color: str,
        selected_bg_color: str,
        selected_fg_color: str,
        item_name: str,
        item_text: str,
        item_box_selected: str,
        item_name_selected: str,
        item_text_selected: str,
        item_shortcut_color: str,
        item_shortcut_color_sel: str,
        when_selected: str,
        when_not_selected: str
    ) -> str:
        """Apply colors to Ulauncher theme.
        
        Returns:
            Empty string on success, error message on failure.
        """
        from integrations.ulauncher import apply_ulauncher_theme
        
        colors = {
            'bg_color': bg_color,
            'window_border_color': window_border_color,
            'prefs_background': prefs_background,
            'input_color': input_color,
            'selected_bg_color': selected_bg_color,
            'selected_fg_color': selected_fg_color,
            'item_name': item_name,
            'item_text': item_text,
            'item_box_selected': item_box_selected,
            'item_name_selected': item_name_selected,
            'item_text_selected': item_text_selected,
            'item_shortcut_color': item_shortcut_color,
            'item_shortcut_color_sel': item_shortcut_color_sel,
            'when_selected': when_selected,
            'when_not_selected': when_not_selected,
        }
        
        opacities = {
            'bg_color': bg_opacity,
            'window_border_color': border_opacity,
        }
        
        success, message = apply_ulauncher_theme(colors, opacities)
        if success:
            logger.info("Ulauncher theme applied")
            return ""
        else:
            logger.error(f"Ulauncher error: {message}")
            return message

    @pyqtSlot(result='QString')
    def restoreUlauncherBackup(self) -> str:
        """Restore Ulauncher theme from backup.
        
        Returns:
            Empty string on success, error message on failure.
        """
        from integrations.ulauncher import restore_ulauncher_backup
        success, message = restore_ulauncher_backup()
        if success:
            logger.info("Ulauncher backup restored")
            return ""
        else:
            logger.error(f"Ulauncher restore error: {message}")
            return message

    @pyqtSlot(result='QString')
    def refreshUlauncher(self) -> str:
        """Restart Ulauncher to apply theme changes.
        
        Returns:
            Empty string on success, error message on failure.
        """
        from integrations.ulauncher import refresh_ulauncher
        success, message = refresh_ulauncher()
        if success:
            logger.info("Ulauncher restarted")
            return ""
        else:
            logger.error(f"Ulauncher refresh error: {message}")
            return message

    @pyqtSlot(result='QVariant')
    def loadUlauncherColors(self) -> dict:
        """Load current colors from Ulauncher theme.
        
        Returns:
            Dictionary with color values.
        """
        from integrations.ulauncher import get_current_colors as get_ulauncher_colors
        colors = get_ulauncher_colors()
        logger.info(f"Ulauncher colors loaded: {colors}")
        return colors

    # =========================================================================
    # KDE Color Scheme Methods
    # =========================================================================

    @pyqtSlot(result='QString')
    def getCurrentColorScheme(self) -> str:
        """Get the name of the current KDE color scheme."""
        return get_current_scheme_name()

    @pyqtSlot(result='QVariantList')
    def getColorSets(self) -> list:
        """Get list of KDE color set names."""
        return COLOR_SETS

    @pyqtSlot(result='QVariantList')
    def getColorKeys(self) -> list:
        """Get list of color keys within each set."""
        return COLOR_KEYS

    @pyqtSlot(str, result='QVariant')
    def getColorSet(self, color_set: str) -> dict:
        """Get all colors for a specific color set."""
        return get_color_set(color_set)

    @pyqtSlot(str, str, result='QVariant')
    def getColorSetFromScheme(self, scheme_name: str, color_set: str) -> dict:
        """Get all colors for a specific color set from a scheme file."""
        return get_color_set_from_scheme(scheme_name, color_set)

    @pyqtSlot(result='QVariant')
    def getAllKdeColors(self) -> dict:
        """Get all colors from all color sets."""
        return get_all_colors()

    @pyqtSlot(str, str, result='QString')
    def readKdeColor(self, color_set: str, key: str) -> str:
        """Read a specific color from the current scheme."""
        return read_color(color_set, key)

    @pyqtSlot(str, str, str, result='bool')
    def writeKdeColor(self, color_set: str, key: str, color: str) -> bool:
        """Write a specific color to kdeglobals."""
        return write_color(color_set, key, color)

    @pyqtSlot('QVariantList', str, result='bool')
    def applyPaletteToKde(self, palette: list, accent: str) -> bool:
        """Apply the extracted palette to KDE color scheme."""
        success = apply_palette_to_scheme(palette, accent if accent else None)
        if success:
            notify_color_change()
        return success

    @pyqtSlot(result='bool')
    def notifyKdeColorChange(self) -> bool:
        """Notify KDE about color scheme changes."""
        return notify_color_change()

    @pyqtSlot(result='QVariantList')
    def getColorSchemesList(self) -> list:
        """Get list of available KDE color schemes."""
        return get_color_schemes_list()

    @pyqtSlot(str, result='bool')
    def applyColorScheme(self, scheme_name: str) -> bool:
        """Apply a KDE color scheme by name."""
        return apply_color_scheme(scheme_name)

    @pyqtSlot(str, result='QVariantList')
    def getColorSections(self, scheme_name: str) -> list:
        """Get list of main color sections from a scheme (excludes Inactive sub-sections)."""
        return get_color_sections(scheme_name)

    @pyqtSlot(str, result='QVariantList')
    def getInactiveSections(self, scheme_name: str) -> list:
        """Get list of sections that have Inactive variants."""
        return get_inactive_sections(scheme_name)

    @pyqtSlot(str, str, result='QVariant')
    def getSectionColors(self, scheme_name: str, section: str) -> dict:
        """
        Get all colors for a section.
        Returns dict of {key: {color: "#hex", opacity: 0.0-1.0}}
        """
        colors = get_section_colors(scheme_name, section)
        # Convert tuple to dict for QML
        return {key: {"color": color, "opacity": opacity} for key, (color, opacity) in colors.items()}

    @pyqtSlot(str, result='QVariant')
    def getFullSchemeData(self, scheme_name: str) -> dict:
        """
        Get complete scheme data for editing.
        Returns dict of {section: {key: {color: "#hex", opacity: 0.0-1.0}}}
        """
        data = parse_scheme_file(scheme_name)
        result = {}
        for section, colors in data.items():
            result[section] = {}
            for key, (color, opacity) in colors.items():
                result[section][key] = {"color": color, "opacity": opacity}
        return result

    @pyqtSlot(str, bool, 'QVariant', result='bool')
    def saveKdeColorScheme(self, scheme_name: str, is_dark: bool, colors_data: dict) -> bool:
        """Save colors as a new KDE color scheme with backup."""
        return save_color_scheme_from_data(scheme_name, is_dark, colors_data)

    # =========================================================================
    # KDE Color Scheme V2 (Kuntatinte) Methods
    # =========================================================================

    @pyqtSlot('QVariantList', int, int, 'QString', result='QString')
    def generateKuntatinteSchemes(self, palette: list, primary_index: int, toolbar_opacity: int, accent_override: str = "") -> str:
        """Generate and save Kuntatinte Light and Dark color schemes.
        
        Args:
            palette: List of hex colors from wallpaper extraction
            primary_index: Index of the primary color in palette (-1 to use accent_override)
            toolbar_opacity: Opacity for toolbar/titlebar (0-100)
            accent_override: Optional hex color to use as primary instead of palette index
        
        Returns:
            Empty string on success, error message on failure.
        """
        # If accent_override provided and index is -1, use it
        if primary_index == -1 and accent_override:
            # Create a modified palette with accent as first element
            modified_palette = [accent_override] + list(palette)
            success, message = generate_and_save_kuntatinte_schemes(
                modified_palette, 0, toolbar_opacity
            )
        else:
            success, message = generate_and_save_kuntatinte_schemes(
                palette, primary_index, toolbar_opacity
            )
        if success:
            logger.info(f"Kuntatinte schemes generated: {message}")
            return ""
        else:
            logger.error(f"Error generating Kuntatinte schemes: {message}")
            return message

    @pyqtSlot('QVariantList', int, 'QString', result='QVariant')
    def getKuntatintePreview(self, palette: list, primary_index: int, accent_override: str = "") -> dict:
        """Get preview colors for Kuntatinte schemes.
        
        Args:
            palette: List of hex colors
            primary_index: Index of primary color (-1 to use accent_override)
            accent_override: Optional hex color to use as primary
        
        Returns:
            Dictionary with 'light' and 'dark' preview colors
        """
        if not palette:
            return {}
        # If accent_override provided and index is -1, use it
        if primary_index == -1 and accent_override:
            modified_palette = [accent_override] + list(palette)
            return get_preview_data(modified_palette, 0)
        return get_preview_data(palette, primary_index)

    @pyqtSlot('QVariantList', int, int, 'QString', result='QString')
    def generateAndApplyKuntatinte(self, palette: list, primary_index: int, toolbar_opacity: int, accent_override: str = "") -> str:
        """Generate, save and apply Kuntatinte scheme based on current mode.
        
        Args:
            palette: List of hex colors from wallpaper extraction
            primary_index: Index of the primary color in palette (-1 to use accent_override)
            toolbar_opacity: Opacity for toolbar/titlebar (0-100)
            accent_override: Optional hex color to use as primary
        
        Returns:
            Empty string on success, error message on failure.
        """
        if primary_index == -1 and accent_override:
            modified_palette = [accent_override] + list(palette)
            success, message = generate_and_save_kuntatinte_schemes(
                modified_palette, 0, toolbar_opacity
            )
        else:
            success, message = generate_and_save_kuntatinte_schemes(
                palette, primary_index, toolbar_opacity
            )
        if not success:
            return message
        return ""

