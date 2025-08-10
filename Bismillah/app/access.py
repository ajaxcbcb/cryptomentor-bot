
# app/access.py
from datetime import datetime, timezone
from typing import Optional
from app.db_router import get_user

def has_premium(telegram_id: int) -> bool:
    """Unified premium check via db_router"""
    rec = get_user(telegram_id) or {}
    
    if rec.get("banned"):
        return False
    
    if rec.get("is_premium"):
        # lifetime?
        if rec.get("premium_until") in (None, ""):
            return True
        try:
            until = datetime.fromisoformat(rec["premium_until"])
        except Exception:
            return False
        return until >= datetime.now(timezone.utc)
    
    return False

def is_lifetime_premium(telegram_id: int) -> bool:
    """Check if user has lifetime premium"""
    rec = get_user(telegram_id) or {}
    return (rec.get("is_premium", False) and 
            rec.get("premium_until") in (None, "") and 
            not rec.get("banned", False))

def is_banned(telegram_id: int) -> bool:
    """Check if user is banned"""
    rec = get_user(telegram_id) or {}
    return rec.get("banned", False)

def get_user_credits(telegram_id: int) -> int:
    """Get user credits via db_router"""
    rec = get_user(telegram_id) or {}
    return int(rec.get("credits", 0))
