
from datetime import datetime, timezone
from app.supabase_conn import get_user_by_tid

def is_premium(tid: int) -> bool:
    """Check if user is premium via Supabase"""
    try:
        rec = get_user_by_tid(tid) or {}
        if rec.get("banned"):
            return False
        if not rec.get("is_premium"):
            return False
        pu = rec.get("premium_until")
        if pu is None:  # lifetime
            return True
        try:
            return datetime.fromisoformat(pu) >= datetime.now(timezone.utc)
        except Exception:
            return False
    except Exception:
        return False

def get_user_credits(tid: int) -> int:
    """Get user credits via Supabase"""
    try:
        rec = get_user_by_tid(tid) or {}
        return max(0, rec.get("credits", 0))
    except Exception:
        return 0

def is_user_banned(tid: int) -> bool:
    """Check if user is banned via Supabase"""
    try:
        rec = get_user_by_tid(tid) or {}
        return bool(rec.get("banned", False))
    except Exception:
        return False
