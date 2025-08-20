
import os
from .stats import build_system_status

# Default ke file backup yang benar; bisa di-override via Secrets: LEGACY_JSON_PATH
DEFAULT_LEGACY_PATH = "premium_users_backup_20250802_130229.json"
LEGACY_JSON_PATH = os.getenv("LEGACY_JSON_PATH", DEFAULT_LEGACY_PATH)

# Jika kamu punya is_auto_signal_running(), pakai itu. Kalau tidak, biarkan True atau import dari autosignal.
try:
    from .autosignal import is_auto_signal_running
    _auto = is_auto_signal_running()
except Exception:
    _auto = True

def get_admin_panel_text():
    return build_system_status(
        auto_signals_running=_auto,
        legacy_json_path=LEGACY_JSON_PATH
    )
