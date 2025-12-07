"""
Configuration Manager.

Handles loading and saving application configuration from TOML file.

Always uses ~/.config/kuntatinte for configuration.
On first run, copies config.toml and templates from project directory.
"""

import re
import shutil
import tomllib
from pathlib import Path
from typing import Any, Optional
import logging


logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

APP_NAME = "kuntatinte"
USER_CONFIG_DIR = Path.home() / ".config" / APP_NAME
PROJECT_DIR = Path(__file__).parent.parent  # Go up from core/ to project root


# =============================================================================
# User Config Initialization
# =============================================================================

def _generate_default_config() -> str:
    """Generate default config.toml content from DEFAULTS."""
    lines = ["# Kuntatinte Configuration File\n"]
    lines.append("# Auto-generated from defaults\n\n")
    
    for section, values in DEFAULTS.items():
        # Check if this section has subsections (nested dicts)
        subsections = {k: v for k, v in values.items() if isinstance(v, dict)}
        regular_values = {k: v for k, v in values.items() if not isinstance(v, dict)}
        
        # Write regular values
        if regular_values:
            lines.append(f"[{section}]\n")
            for key, value in regular_values.items():
                lines.append(f"{key} = {_format_toml_value(value)}\n")
            lines.append("\n")
        
        # Write subsections
        for sub_name, sub_values in subsections.items():
            lines.append(f"[{section}.{sub_name}]\n")
            for key, value in sub_values.items():
                lines.append(f"{key} = {_format_toml_value(value)}\n")
            lines.append("\n")
    
    return "".join(lines)


def _format_toml_value(value: Any) -> str:
    """Format a Python value for TOML."""
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        formatted_items = [_format_toml_value(item) for item in value]
        return "[" + ", ".join(formatted_items) + "]"
    elif isinstance(value, dict):
        items = [f"{k} = {_format_toml_value(v)}" for k, v in value.items()]
        return "{ " + ", ".join(items) + " }"
    else:
        return f'"{value}"'


def _init_user_config() -> bool:
    """Initialize user configuration directory if needed.
    
    - Copies templates from project directory if they exist
    - Generates config.toml from DEFAULTS if not present
    
    Returns:
        True if initialization was performed, False if already initialized
    """
    config_file = USER_CONFIG_DIR / "config.toml"
    templates_dir = USER_CONFIG_DIR / "templates"
    
    initialized = False
    
    # Create user config directory if needed
    if not USER_CONFIG_DIR.exists():
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        initialized = True
    
    # Create config.toml if not present
    if not config_file.exists():
        # Try to copy from project first
        bundled_config = PROJECT_DIR / "config.toml"
        if bundled_config.exists():
            shutil.copy2(bundled_config, config_file)
            logger.info(f"Copied config from project: {config_file}")
        else:
            # Generate from defaults
            config_content = _generate_default_config()
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            logger.info(f"Generated default config: {config_file}")
        initialized = True
    
    # Copy templates directory if not present
    bundled_templates = PROJECT_DIR / "templates"
    if not templates_dir.exists() and bundled_templates.exists():
        shutil.copytree(bundled_templates, templates_dir)
        logger.info(f"Copied templates to: {templates_dir}")
        initialized = True
    
    return initialized


# =============================================================================
# Default Configuration
# =============================================================================

DEFAULTS: dict[str, dict[str, Any]] = {
    "paths": {
        "wallpapers_folder": "",
        "starship_config": "~/.config/starship.toml",
        "fastfetch_config_dir": "~/.config/fastfetch",
        "fastfetch_custom_logo": "",
        "ulauncher_theme_dir": "~/.config/ulauncher/user-themes/kuntatinte",
    },
    "cache": {
        "cache_dir": "kuntatinte",
    },
    "ui": {
        "debug_ui": False,
        "left_panel_visible": True,
        "right_panel_visible": False,
        "min_height": 700,  # Minimum window height (matches initial height)
        "panel_width": {
            # Minimum/initial widths for panels
            "central_panel": 400,  # Minimum width for central panel content
            "wallpapers": 250,     # Minimum width for wallpapers panel
            # Settings panel widths (fixed, not resizable)
            "fastfetch": 280,
            "starship": 280,
            "ulauncher": 380,
            "kuntatinte_color_scheme": 520,
        },
    },
}


# =============================================================================
# Configuration Class
# =============================================================================

class Config:
    """Application configuration manager."""
    
    def __init__(self) -> None:
        """Initialize configuration."""
        # Initialize user config directory if needed
        _init_user_config()
        
        self._config_path = USER_CONFIG_DIR / "config.toml"
        self._templates_dir = USER_CONFIG_DIR / "templates"
        self._config: dict[str, dict[str, Any]] = {}
        self._load()
    
    def _load(self) -> None:
        """Load configuration from TOML file."""
        if self._config_path.exists():
            try:
                with open(self._config_path, "rb") as f:
                    self._config = tomllib.load(f)
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
                self._config = {}
        else:
            self._config = {}
    
    def _save(self) -> None:
        """Save configuration to TOML file.
        
        Uses regex-based replacement to preserve comments and formatting.
        """
        if not self._config_path.exists():
            self._write_full_config()
            return
        
        try:
            with open(self._config_path, "r", encoding='utf-8') as f:
                content = f.read()
            
            # Update each value in the file
            for section, values in self._config.items():
                for key, value in values.items():
                    # Skip dict values - they are subsections like [ui.panel_width]
                    if isinstance(value, dict):
                        continue
                    content = self._update_value_in_content(content, section, key, value)
            
            with open(self._config_path, "w", encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.warning(f"Could not save config: {e}")
    
    def _update_value_in_content(self, content: str, section: str, key: str, value: Any) -> str:
        """Update a single value in the TOML content."""
        toml_value = self._format_toml_value(value)
        
        pattern = rf'(^{re.escape(key)}\s*=\s*)(["\'\[]?)[^\n]*(\s*(?:#.*)?)$'
        replacement = rf'\g<1>{toml_value}\3'
        
        section_pattern = rf'\[{re.escape(section)}\]'
        section_match = re.search(section_pattern, content)
        
        if section_match:
            next_section = re.search(r'\n\[', content[section_match.end():])
            if next_section:
                section_end = section_match.end() + next_section.start()
            else:
                section_end = len(content)
            
            section_content = content[section_match.end():section_end]
            
            key_pattern = rf'^{re.escape(key)}\s*='
            if re.search(key_pattern, section_content, flags=re.MULTILINE):
                updated_section = re.sub(pattern, replacement, section_content, flags=re.MULTILINE)
            else:
                updated_section = section_content.rstrip() + f"\n{key} = {toml_value}\n"
            
            content = content[:section_match.end()] + updated_section + content[section_end:]
        else:
            content = content.rstrip() + f"\n\n[{section}]\n{key} = {toml_value}\n"
        
        return content
    
    def _format_toml_value(self, value: Any) -> str:
        """Format a Python value for TOML."""
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            formatted_items = [self._format_toml_value(item) for item in value]
            return "[" + ", ".join(formatted_items) + "]"
        elif isinstance(value, dict):
            items = [f"{k} = {self._format_toml_value(v)}" for k, v in value.items()]
            return "{ " + ", ".join(items) + " }"
        else:
            return f'"{value}"'
    
    def _write_full_config(self) -> None:
        """Write a complete new config file."""
        lines = ["# Kuntatinte Configuration File\n\n"]
        
        for section, values in self._config.items():
            lines.append(f"[{section}]\n")
            for key, value in values.items():
                toml_value = self._format_toml_value(value)
                lines.append(f"{key} = {toml_value}\n")
            lines.append("\n")
        
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding='utf-8') as f:
            f.writelines(lines)
    
    def set(self, section: str, key: str, value: Any, save: bool = True) -> None:
        """Set a configuration value."""
        if section not in self._config:
            self._config[section] = {}
        
        self._config[section][key] = value
        
        if save:
            self._save()
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        if section in self._config and key in self._config[section]:
            return self._config[section][key]
        
        if section in DEFAULTS and key in DEFAULTS[section]:
            return DEFAULTS[section][key]
        
        return default
    
    def get_path(self, section: str, key: str) -> Path:
        """Get a configuration value as an expanded Path."""
        value = self.get(section, key, "")
        if not value:
            return Path()
        return Path(value).expanduser()
    
    # =========================================================================
    # Directory Properties
    # =========================================================================
    
    @property
    def app_dir(self) -> Path:
        """Application configuration directory (~/.config/kuntatinte)."""
        return USER_CONFIG_DIR
    
    @property
    def templates_dir(self) -> Path:
        """Templates directory."""
        return self._templates_dir
    
    @property
    def starship_template(self) -> Path:
        """Starship template file path."""
        return self._templates_dir / "starship" / "starship.toml"
    
    @property
    def fastfetch_template(self) -> Path:
        """Fastfetch logo template image path."""
        return self._templates_dir / "fastfetch" / "logo.png"
    
    @property
    def ulauncher_template_dir(self) -> Path:
        """Ulauncher template directory."""
        return self._templates_dir / "ulauncher"

    @property
    def fastfetch_custom_logo(self) -> Optional[Path]:
        """Custom fastfetch logo path, or None if using default template."""
        custom = self.get("paths", "fastfetch_custom_logo", "")
        if custom:
            path = Path(custom.replace("~", str(Path.home())))
            if path.exists():
                return path
        return None
    
    @property
    def fastfetch_logo(self) -> Path:
        """Active fastfetch logo path (custom if set, otherwise default template)."""
        custom = self.fastfetch_custom_logo
        if custom:
            return custom
        return self.fastfetch_template
    
    def set_fastfetch_custom_logo(self, path: str) -> None:
        """Set custom fastfetch logo path."""
        self.set("paths", "fastfetch_custom_logo", path)
    
    # =========================================================================
    # Path Configuration Properties
    # =========================================================================
    
    @property
    def wallpapers_folder(self) -> Path:
        """Default wallpapers folder. Returns Pictures folder if not set."""
        path = self.get_path("paths", "wallpapers_folder")
        if not path or str(path) == "." or str(path) == "":
            from PyQt6.QtCore import QStandardPaths
            pictures = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
            return Path(pictures) if pictures else Path.home()
        return path
    
    @property
    def starship_config(self) -> Path:
        """Starship configuration file path."""
        return self.get_path("paths", "starship_config")
    
    @property
    def fastfetch_config_dir(self) -> Path:
        """Fastfetch configuration directory."""
        return self.get_path("paths", "fastfetch_config_dir")
    
    @property
    def ulauncher_theme_dir(self) -> Path:
        """Ulauncher theme output directory."""
        path = self.get_path("paths", "ulauncher_theme_dir")
        if not path or str(path) == ".":
            return Path.home() / ".config" / "ulauncher" / "user-themes" / "kuntatinte"
        return path

    @property
    def cache_dir(self) -> Path:
        """Cache directory path."""
        cache_value = self.get("cache", "cache_dir", "kuntatinte")
        cache_path = Path(cache_value)
        
        if not cache_path.is_absolute():
            cache_path = Path.home() / ".cache" / cache_path
        
        return cache_path
    
    # =========================================================================
    # Extraction Properties
    # =========================================================================
    
    # =========================================================================
    # UI Properties
    # =========================================================================
    
    @property
    def debug_ui(self) -> bool:
        """Enable UI debug logging and screenshots."""
        return self.get("ui", "debug_ui", False)
    
    @property
    def left_panel_visible(self) -> bool:
        """Left panel visibility on startup."""
        return self.get("ui", "left_panel_visible", True)
    
    @property
    def right_panel_visible(self) -> bool:
        """Right panel visibility on startup."""
        return self.get("ui", "right_panel_visible", False)
    
    def get_panel_width(self, setting_name: str) -> int:
        """Get panel width for a specific setting."""
        key = setting_name.lower().replace(" ", "_")
        
        panel_width = self.get("ui", "panel_width", {})
        if isinstance(panel_width, dict):
            if key in panel_width:
                return panel_width[key]
            return panel_width.get("fastfetch", 280)  # Default fallback
        
        return 280


# =============================================================================
# Global Instance
# =============================================================================

config = Config()
