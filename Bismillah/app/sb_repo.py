
import os
from typing import Optional, Dict, Any, Tuple
from .supabase_conn import get_supabase_client

WEEKLY_FREE_CREDITS = int(os.getenv("WEEKLY_FREE_CREDITS", "100"))

def _san(u: Optional[str]) -> Optional[str]:
    if not u: 
        return None
    u = u.strip().lstrip("@").lower()
    return u or None

def ensure_user_and_welcome(tg_id: int, username: str = None, first_name: str = None, last_name: str = None) -> Dict[str, Any]:
    try:
        s = get_supabase_client()
        return s.rpc("upsert_user_with_weekly_reset", {
            "p_telegram_id": int(tg_id),
            "p_username": _san(username),
            "p_first_name": first_name,
            "p_last_name": last_name,
            "p_weekly_quota": WEEKLY_FREE_CREDITS,
        }).execute().data or {}
    except Exception as e:
        print(f"Error ensuring user {tg_id}: {e}")
        return {}

def enforce_weekly_reset_calendar(tg_id: int) -> Dict[str, Any]:
    try:
        s = get_supabase_client()
        return s.rpc("enforce_weekly_reset_calendar", {
            "p_telegram_id": int(tg_id),
            "p_weekly_quota": WEEKLY_FREE_CREDITS,
        }).execute().data or {}
    except Exception as e:
        print(f"Error enforcing weekly reset for {tg_id}: {e}")
        return {}

def stats_totals() -> Tuple[int, int]:
    try:
        s = get_supabase_client()
        res = s.rpc("stats_totals").execute()
        row = res.data[0] if isinstance(res.data, list) else res.data
        return int(row.get("total_users", 0)), int(row.get("premium_users", 0))
    except Exception as e:
        print(f"Error getting stats totals: {e}")
        return 0, 0

def admin_set_credits_all(amount: int, include_premium: bool = False) -> int:
    try:
        s = get_supabase_client()
        r = s.rpc("admin_set_credits_all", {
            "p_amount": int(amount), 
            "p_only_free": not include_premium
        }).execute()
        return int(r.data or 0)
    except Exception as e:
        print(f"Error setting credits for all: {e}")
        return 0

def set_premium(tg_id: int, duration_type: str, duration_value: int = 0) -> None:
    try:
        s = get_supabase_client()
        s.rpc("set_premium", {
            "p_telegram_id": int(tg_id),
            "p_duration_type": duration_type,    # 'days' | 'months' | 'lifetime'
            "p_duration_value": int(duration_value),
        }).execute()
    except Exception as e:
        print(f"Error setting premium for {tg_id}: {e}")

def get_user_by_telegram_id(tg_id: int) -> Optional[Dict[str, Any]]:
    try:
        s = get_supabase_client()
        result = s.table("users").select("*").eq("telegram_id", tg_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error getting user {tg_id}: {e}")
        return None
