from .stats import build_system_status
from .autosignal import is_auto_signal_running

AUTO_SIGNALS_RUNNING = True
# Set ini jika ingin hardcode path JSON lama, atau biarkan None untuk auto-detect
LEGACY_JSON_PATH = None  # contoh: "data/users.json"

def get_admin_panel_text():
    # Get auto signal status from module
    try:
        auto_running = is_auto_signal_running()
    except:
        auto_running = AUTO_SIGNALS_RUNNING

    return build_system_status(
        auto_signals_running=auto_running,
        legacy_json_path=LEGACY_JSON_PATH
    )