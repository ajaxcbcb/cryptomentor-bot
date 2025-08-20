
# app/sb_repo.py
import os
from typing import Optional, Dict, Any, Tuple
from .supabase_conn import get_supabase_client

WELCOME_CREDITS = int(os.getenv("WELCOME_CREDITS", "100"))

def _san(u: Optional[str]) -> Optional[str]:
    if not u: return None
    u = u.strip().lstrip("@").lower()
    return u or None

def user_exists(tg_id: int) -> bool:
    s = get_supabase_client()
    res = s.table("users").select("telegram_id").eq("telegram_id", int(tg_id)).limit(1).execute()
    return bool(res.data)

def ref_exists(ref_id: int) -> bool:
    s = get_supabase_client()
    res = s.table("users").select("telegram_id").eq("telegram_id", int(ref_id)).limit(1).execute()
    return bool(res.data)

def upsert_user_ref_required(
    tg_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    referred_by: Optional[int],
) -> Dict[str, Any]:
    if referred_by is None:
        raise ValueError("Referral required: missing referred_by")
    if referred_by == tg_id:
        raise ValueError("Referral invalid: self-ref")
    if not ref_exists(referred_by):
        raise ValueError("Referral invalid: referrer not found")

    s = get_supabase_client()
    payload = {
        "p_telegram_id": int(tg_id),
        "p_username": _san(username),
        "p_first_name": first_name,
        "p_last_name": last_name,
        "p_welcome_quota": WELCOME_CREDITS,
        "p_referred_by": int(referred_by),
    }
    return s.rpc("upsert_user_with_welcome", payload).execute().data or {}

def set_premium_rpc(tg_id: int, duration_type: str, duration_value: int = 0) -> None:
    s = get_supabase_client()
    s.rpc("set_premium", {
        "p_telegram_id": int(tg_id),
        "p_duration_value": int(duration_value),
        "p_duration_type": duration_type,  # 'days'|'months'|'lifetime'
    }).execute()

def stats_totals() -> Tuple[int, int]:
    s = get_supabase_client()
    res = s.rpc("stats_totals").execute()
    row = res.data[0] if isinstance(res.data, list) else res.data
    return int(row.get("total_users", 0)), int(row.get("premium_users", 0))

def get_user_by_tid(tg_id: int) -> Optional[Dict[str, Any]]:
    """Get user data by telegram ID"""
    s = get_supabase_client()
    res = s.table("users").select("*").eq("telegram_id", int(tg_id)).limit(1).execute()
    return res.data[0] if res.data else None

def ensure_user_and_welcome(tg_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]) -> Dict[str, Any]:
    """Ensure user exists with weekly reset - for existing users without referral requirement"""
    s = get_supabase_client()
    payload = {
        "p_telegram_id": int(tg_id),
        "p_username": _san(username),
        "p_first_name": first_name,
        "p_last_name": last_name,
        "p_welcome_quota": WELCOME_CREDITS,
    }
    return s.rpc("upsert_user_with_weekly_reset", payload).execute().data or {}
