
import os
from .stats import build_system_status

# Default ke file backup yang kamu sebutkan; bisa di-override via Secrets ENV: LEGACY_JSON_PATH
DEFAULT_LEGACY_PATH = "premium_users_backup_20250802_130229.json"
LEGACY_JSON_PATH = os.getenv("LEGACY_JSON_PATH", DEFAULT_LEGACY_PATH)

def get_admin_panel_text():
    # build_system_status harus menerima legacy_json_path=...
    return build_system_status(
        auto_signals_running=True,          # status autosignal kamu sendiri; kalau sudah ada import, boleh ganti
        legacy_json_path=LEGACY_JSON_PATH   # <-- penting: pakai file lokal ini
    )
