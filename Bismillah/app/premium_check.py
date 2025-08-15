
from datetime import datetime, timezone
from app.supabase_conn import get_user_by_tid

def is_premium(tid: int) -> bool:
    """Check if user has active premium using Supabase data only"""
    try:
        u = get_user_by_tid(tid) or {}
        if u.get("banned"): 
            return False
        if not u.get("is_premium"): 
            return False
        
        pu = u.get("premium_until")
        if pu is None:  # Lifetime premium
            return True
            
        # Check if premium is still valid
        try:
            premium_until = datetime.fromisoformat(pu.replace('Z', '+00:00'))
            return premium_until >= datetime.now(timezone.utc)
        except Exception:
            return False
    except Exception:
        return False

def get_user_credits(tid: int) -> int:
    """Get user credits from Supabase"""
    try:
        u = get_user_by_tid(tid) or {}
        return u.get("credits", 0)
    except Exception:
        return 0

def is_banned(tid: int) -> bool:
    """Check if user is banned"""
    try:
        u = get_user_by_tid(tid) or {}
        return bool(u.get("banned", False))
    except Exception:
        return False

def get_user_info(tid: int) -> dict:
    """Get complete user info from Supabase"""
    try:
        return get_user_by_tid(tid) or {}
    except Exception:
        return {}
