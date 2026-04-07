import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "../db/user_risk_settings.json")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(data):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Failed to save user risk settings: {e}")

def get_manual_settings(user_id: int):
    """Returns (manual_margin, manual_leverage) for a user."""
    settings = load_settings()
    user_str = str(user_id)
    if user_str in settings:
        return float(settings[user_str].get("manual_margin", 10)), int(settings[user_str].get("manual_leverage", 10))
    return 10.0, 10

def set_manual_settings(user_id: int, margin: float, leverage: int):
    """Saves manual margin and leverage preferences."""
    settings = load_settings()
    user_str = str(user_id)
    if user_str not in settings:
        settings[user_str] = {}
    settings[user_str]["manual_margin"] = float(margin)
    settings[user_str]["manual_leverage"] = int(leverage)
    save_settings(settings)
