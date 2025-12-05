# module for automatic generation of color configuration files for integrated applications based on Kuntatinte color schemes
import configparser
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional


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


DEFAULT_COLORS: Dict[str, Any] = {
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

# Extraction methods: color_scheme, better_contrast, darker, lighter, variable, fixed
# color_scheme: extract directly from scheme, parameters: scheme_section, scheme_key
# better_contrast: select color with better contrast against group of colors, parameters: base_color, group_colors (list of colors)
# darker: select darker color from group of colors: group_colors (list of colors)
# lighter: select lighter color from group of colors: group_colors (list of colors)
# variable: use another variable's value, parameters: variable_key
# fixed: use a fixed color value, parameters: color_value

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


def load_autogen_rules(mode: Optional[str]) -> Dict[str, Any]:
    """Public helper to load rules for 'dark' or 'light'.

    Falls back to an empty dict if no template is present.
    """
    if not mode:
        return {}
    mode_key = str(mode).lower()
    return _load_rules_from_templates(mode_key)

def autogen():
    # Raise a popup to select mode: dark or light
    # trigger Generate Both button in settings panel Kuntatinte color scheme and get primary color selected to store in a variable PrimaryColor
    # read both generated Kuntatinte color schemes files (dark and light) and extract colors based on rules for each mode
    # generate json files for dark and light, based in DEFAULT_COLORS structure with extracted colors in folder ~/.config/kuntatinte/autogen/
    # load in the application the values of the properties regarding mode selected (dark or light) and in each settings panel
    mode = "dark"  # or "light", depending on user selection in popup
    rules = load_autogen_rules(mode)

    # For demonstration, print the selected rules (loaded from templates)
    print(f"Using rules for {mode} mode (loaded from templates):")
    print(json.dumps(rules, indent=4))