import os
import logging
from typing import Tuple, Dict, Any, Optional, List

try:
    from supabase import create_client, Client
except Exception as e:
    create_client = None
    Client = None
    _import_error = str(e)

def _getenv(k: str) -> str:
    return os.getenv(k) or os.environ.get(k)

SUPABASE_URL = _getenv("SUPABASE_URL")
# Utamakan SERVICE KEY; fallback agar tetap bisa tes minimal
SUPABASE_KEY = <REDACTED_SUPABASE_KEY>
WEEKLY_FREE_CREDITS = int(os.getenv("WEEKLY_FREE_CREDITS", "100"))

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

# RPC wrapper functions for user management
def upsert_user_with_weekly_reset_rpc(telegram_id: int, username: str=None, first_name: str=None, last_name: str=None):
    """Upsert user with automatic weekly reset logic"""
    if not available():
        raise RuntimeError(f"Supabase client not available: {diagnostics}")
    payload = {
        "p_telegram_id": int(telegram_id),
        "p_username": username,
        "p_first_name": first_name,
        "p_last_name": last_name,
        "p_weekly_quota": WEEKLY_FREE_CREDITS,
    }
    return supabase.rpc("upsert_user_with_weekly_reset", payload).execute().data

def enforce_weekly_reset_calendar_rpc(telegram_id: int):
    """Enforce weekly reset based on calendar (Monday 00:00 UTC)"""
    if not available():
        return {"reset": False}

    payload = {
        "p_telegram_id": int(telegram_id),
        "p_weekly_quota": WEEKLY_FREE_CREDITS
    }
    return supabase.rpc("enforce_weekly_reset_calendar", payload).execute().data

def reset_all_free_users_this_week_rpc() -> int:
    """Reset all free users credits for this week"""
    if not available():
        return 0

    payload = {"p_weekly_quota": WEEKLY_FREE_CREDITS}
    result = supabase.rpc("reset_all_free_users_this_week", payload).execute().data
    return result if result is not None else 0

def admin_set_credits_all_rpc(amount: int, include_premium: bool=False) -> int:
    """Admin function to set credits for all users"""
    if not available():
        return 0

    payload = {
        "p_amount": int(amount),
        "p_only_free": (not include_premium)
    }
    result = supabase.rpc("admin_set_credits_all", payload).execute().data
    return result if result is not None else 0