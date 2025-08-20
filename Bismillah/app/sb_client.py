
import os
from typing import Tuple, Dict, Any

try:
    from supabase import create_client, Client
except Exception as e:
    create_client = None
    Client = None
    _import_error = str(e)

def _getenv(k: str) -> str:
    return os.getenv(k) or os.environ.get(k)

SUPABASE_URL = _getenv("SUPABASE_URL")
# Utamakan SERVICE KEY; fallback ke ANON agar tetap bisa tes minimal
SUPABASE_KEY = _getenv("SUPABASE_SERVICE_KEY") or _getenv("SUPABASE_ANON_KEY")

diagnostics: Dict[str, Any] = {}
supabase = None  # type: ignore

def _validate_env():
    if not SUPABASE_URL:
        diagnostics["missing_SUPABASE_URL"] = True
    if not SUPABASE_KEY:
        diagnostics["missing_SUPABASE_KEY"] = True
    if SUPABASE_URL and not SUPABASE_URL.startswith("http"):
        diagnostics["invalid_url"] = SUPABASE_URL

def init_client():
    global supabase
    _validate_env()
    if create_client is None:
        diagnostics["import_error"] = _import_error
        supabase = None
        return
    if diagnostics.get("missing_SUPABASE_URL") or diagnostics.get("missing_SUPABASE_KEY"):
        supabase = None
        return
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase = client
    except Exception as e:
        diagnostics["init_error"] = str(e)
        supabase = None

init_client()

def available() -> bool:
    return supabase is not None

def health() -> Tuple[bool, str]:
    """Pakai RPC hc() agar error jelas."""
    if not available():
        return False, f"client_not_initialized | diag={diagnostics}"
    try:
        res = supabase.rpc("hc").execute()  # type: ignore
        return True, f"OK {res.data}"
    except Exception as e:
        return False, f"rpc_hc_failed: {e} | diag={diagnostics}"

def upsert_user_via_rpc(telegram_id: int, username: str=None, first_name: str=None, last_name: str=None) -> Dict[str, Any]:
    """Gunakan RPC server-side untuk upsert (aman terhadap RLS & skema)."""
    if not available():
        raise RuntimeError(f"Supabase client not available: {diagnostics}")
    payload = {
        "p_telegram_id": int(telegram_id),
        "p_username": username,
        "p_first_name": first_name,
        "p_last_name": last_name
    }
    res = supabase.rpc("upsert_user_rpc", payload).execute()  # type: ignore
    return res.data or {}
