
from datetime import datetime, timezone
from app.users_repo import get_user_by_telegram_id, is_premium_active

def is_premium(tid: int) -> bool:
    """Check if user has active premium using Supabase data only"""
    try:
        return is_premium_active(tid)
    except Exception as e:
        print(f"❌ Error checking premium for user {tid}: {e}")
        return False

def get_user_credits(tid: int) -> int:
    """Get user credits from Supabase"""
    try:
        u = get_user_by_telegram_id(tid)
        if not u:
            return 0
        return int(u.get("credits", 0))
    except Exception as e:
        print(f"❌ Error getting credits for user {tid}: {e}")
        return 0

def is_banned(tid: int) -> bool:
    """Check if user is banned"""
    try:
        u = get_user_by_telegram_id(tid)
        if not u:
            return False
        return bool(u.get("banned", False))
    except Exception as e:
        print(f"❌ Error checking banned status for user {tid}: {e}")
        return False

def get_user_info(tid: int) -> dict:
    """Get complete user info from Supabase"""
    try:
        user = get_user_by_telegram_id(tid)
        return user or {}
    except Exception as e:
        print(f"❌ Error getting user info for {tid}: {e}")
        return {}
