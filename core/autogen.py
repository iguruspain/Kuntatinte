# module for automatic generation of color configuration files for integrated applications based on Kuntatinte color schemes
import configparser
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional



FORMAT_COLORS_OUTPUT: Dict[str, Any] = {
    "Fastfetch": {
    "fastfetchAccent": {
    "color": "",
    "alpha": ""
    },
},
"Starship": {
    "selectedAccent": {
    "color": "",
    "alpha": ""
    },
    "selectedAccentText": {
    "color": "",
    "alpha": "" 
    },
    "selectedDirFg": {
    "color": "",
    "alpha": ""
    },
    "selectedDirBg": {
    "color": "",
    "alpha": ""
    },
    "selectedDirText": {
    "color": "",
    "alpha": ""
    },
    "selectedGitFg": {
    "color": "",
    "alpha": ""
    },
    "selectedGitBg": {
    "color": "",
    "alpha": ""
    },
    "selectedGitText": {
    "color": "",
    "alpha": ""
    },
    "selectedOtherFg": {
    "color": "",
    "alpha": ""
    },
    "selectedOtherBg": {
    "color": "",
    "alpha": ""
    },
    "selectedOtherText": {
    "color": "",
    "alpha": ""
    },
},
"Ulauncher": {
    "ulauncherBgColor": {
    "color": "",
    "alpha": ""
    },
    "ulauncherBorderColor": {
    "color": "",
    "alpha": ""
    },
    "ulauncherPrefsBackground": {
    "color": "",
    "alpha": ""
    },
    "ulauncherInputColor": {
    "color": "",
    "alpha": ""
    },
    "ulauncherSelectedBgColor": {
    "color": "",
    "alpha": ""
    },
    "ulauncherSelectedFgColor": {
    "color": "",
    "alpha": ""
    },
    "ulauncherItemName": {
    "color": "",
    "alpha": ""
    },
    "ulauncherItemText": {
    "color": "",
    "alpha": ""
    },
    "ulauncherItemBoxSelected": {
    "color": "",
    "alpha": ""
    },
    "ulauncherItemNameSelected": {  
    "color": "",
    "alpha": ""
    },
    "ulauncherItemTextSelected": {
    "color": "",
    "alpha": ""
    },
    "ulauncherShortcutColor": {
    "color": "",
    "alpha": ""
    },
    "ulauncherShortcutColorSel": {
    "color": "",
    "alpha": ""
    },
    "ulauncherWhenSelected": {
    "color": "",
    "alpha": ""
    },
    "ulauncherWhenNotSelected": {
    "color": "",
    "alpha": ""
    },
},
}

def get_scheme_color(scheme_path: str, color_section: str, color_key: str) -> Optional[str]:

    config = configparser.ConfigParser()
    config.read(scheme_path)
    try:
        color_value = config.get(color_section, color_key)
        match = re.match(r"#?([0-9A-Fa-f]{6})", color_value)
        if match:
            return f"#{match.group(1).lower()}"
    except (configparser.NoSectionError, configparser.NoOptionError):
        pass
    return None

def darker_color(colors: Dict[str, str]) -> Optional[str]:
    # Placeholder implementation
    return next(iter(colors.values()), None)
def better_contrast_color(base_color: str, colors: Dict[str, str]) -> Optional[str]:
    # Placeholder implementation
    return next(iter(colors.values()), None)
def lighter_color(colors: Dict[str, str]) -> Optional[str]:
    # Placeholder implementation
    return next(iter(colors.values()), None)

def run_autogen(test_mode: bool = True, palette_mode: Optional[str] = None) -> str:
    """Run autogen generation.

    For now this function is a lightweight test-mode stub that returns a
    JSON-serializable dict describing which values would be generated.
    The UI and backend call this in test mode while the full implementation
    is being developed.

    Returns:
        JSON string with generated data or error information.
    """
    try:
        # Example generated payload used for UI testing. Real implementation
        # will compute values based on rules above and detected schemes.
        payload = {
            "status": "ok",
            "mode": "test" if test_mode else "prod",
            "palette_mode": palette_mode,
            "generated": {
                "Fastfetch": {
                    "fastfetchAccent": {"color": "#3daee9", "alpha": ""}
                },
                "Starship": {
                    "selectedAccent": {"color": "#3daee9", "alpha": ""},
                    "selectedAccentText": {"color": "#ffffff", "alpha": ""}
                }
            }
        }
        return json.dumps(payload)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

from core.config_manager import config


def _load_rules_from_templates(mode: str) -> Dict[str, Any]:
    """Load autogen rules JSON from user templates directory.

    Looks under `config.templates_dir / 'autogen_rules' / '<mode>.json'.
    Returns an empty dict if not found or on error.
    """
    try:
        templates_dir = config.templates_dir
        rules_path = Path(templates_dir) / "autogen_rules" / f"{mode}.json"
        if rules_path.exists():
            with open(rules_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[autogen] failed to load rules from templates: {e}")
    return {}