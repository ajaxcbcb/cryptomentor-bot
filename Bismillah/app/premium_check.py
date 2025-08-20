from datetime import datetime, timezone
from app.users_repo import get_user_by_telegram_id, is_premium_active

def is_premium(tid: int) -> bool:
    """Check if user has active premium status"""
    try:
        return is_premium_active(tid)
    except Exception as e:
        print(f"Error checking premium status for {tid}: {e}")
        return False

def get_user_credits(tid: int) -> int:
    """Get user's current credits"""
    try:
        from app.users_repo import get_credits
        return get_credits(tid)
    except Exception as e:
        print(f"Error getting credits for {tid}: {e}")
        return 0

def is_banned(tid: int) -> bool:
    """Check if user is banned"""
    try:
        u = get_user_by_telegram_id(tid)
        if not u:
            return False
        return bool(u.get("banned", False))
    except Exception as e:
        print(f"Error checking banned status for {tid}: {e}")
        return False

def get_user_info(tid: int) -> dict:
    """Get complete user info from Supabase"""
    try:
        user = get_user_by_telegram_id(tid)
        return user or {}
    except Exception as e:
        print(f"Error getting user info for {tid}: {e}")
        return {}