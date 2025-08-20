
# app/sb_repo.py
from __future__ import annotations
from typing import Optional, Dict, Any
from .supabase_conn import get_supabase_client

WEEKLY_FREE_CREDITS = 100  # bisa ubah ke env jika perlu

def ensure_user_and_welcome(
    tg_id: int, username: Optional[str]=None, first_name: Optional[str]=None, last_name: Optional[str]=None
) -> Dict[str, Any]:
    """Ensure user exists and handle weekly welcome credits"""
    try:
        s = get_supabase_client()
        payload = {
            "p_telegram_id": int(tg_id),
            "p_username": username,
            "p_first_name": first_name,
            "p_last_name": last_name,
            "p_weekly_quota": WEEKLY_FREE_CREDITS,
        }
        # User baru => credits=100 (idempotent); user lama -> update biodata ringan
        result = s.rpc("upsert_user_with_weekly_reset", payload).execute()
        return result.data or {}
    except Exception as e:
        print(f"Error ensuring user {tg_id}: {e}")
        return {}

def enforce_weekly_reset_calendar(tg_id: int) -> Dict[str, Any]:
    """Enforce weekly credit reset for non-premium users"""
    try:
        s = get_supabase_client()
        payload = {"p_telegram_id": int(tg_id), "p_weekly_quota": WEEKLY_FREE_CREDITS}
        # Non-premium & belum di pekan ini -> set 100; premium di-skip
        result = s.rpc("enforce_weekly_reset_calendar", payload).execute()
        return result.data or {}
    except Exception as e:
        print(f"Error enforcing weekly reset for {tg_id}: {e}")
        return {}

def stats_totals() -> tuple[int, int]:
    """Get total users and premium users count"""
    try:
        s = get_supabase_client()
        res = s.rpc("stats_totals").execute()
        row = res.data[0] if isinstance(res.data, list) else res.data
        return int(row.get("total_users", 0)), int(row.get("premium_users", 0))
    except Exception as e:
        print(f"Error getting stats totals: {e}")
        return 0, 0

def get_user_by_telegram_id(tg_id: int) -> Optional[Dict[str, Any]]:
    """Get user data by telegram ID"""
    try:
        s = get_supabase_client()
        result = s.table("users").select("*").eq("telegram_id", tg_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error getting user {tg_id}: {e}")
        return None
