
import os
from .stats import build_system_status

# Default to correct backup file; can be overridden via Secrets: LEGACY_JSON_PATH
DEFAULT_LEGACY_PATH = "premium_users_backup_20250802_130229.json"
LEGACY_JSON_PATH = os.getenv("LEGACY_JSON_PATH", DEFAULT_LEGACY_PATH)

# Try to import autosignal function, fallback to True if not available
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
