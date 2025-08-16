
import os
from .stats import build_system_status

# Coba ambil status dari autosignal; fallback ke env agar tidak crash
try:
    from .autosignal import is_auto_signal_running
except Exception:
    def is_auto_signal_running() -> bool:
        return os.getenv("AUTO_SIGNALS_DEFAULT", "1") == "1"

# Jika masih memakai data JSON lama, isi path; biarkan None untuk auto-detect di stats
LEGACY_JSON_PATH = None  # contoh: "data/users.json"

def get_admin_panel_text():
    return build_system_status(
        auto_signals_running=is_auto_signal_running(),
        legacy_json_path=LEGACY_JSON_PATH
    )
