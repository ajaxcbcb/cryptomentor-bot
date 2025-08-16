
import os
import sys
from datetime import datetime, timezone
from typing import Optional, Dict

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.supabase_conn import get_supabase_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase connection not available for user repository")

TZ = timezone.utc
ALLOWED_USER_FIELDS = {"telegram_id", "username", "first_name", "last_name"}

def _sanitize(payload: dict) -> dict:
    """Sanitize payload to only include allowed fields and remove None values"""
    sanitized = {}
    for k, v in payload.items():
        if k in ALLOWED_USER_FIELDS and v is not None:
            sanitized[k] = v
    return sanitized

def ensure_user(telegram_id: int, username: Optional[str]=None, first_name: Optional[str]=None, last_name: Optional[str]=None) -> Optional[Dict]:
    """Ensure user exists in Supabase, create/update if needed"""
    if not SUPABASE_AVAILABLE or not telegram_id:
        return None
    
    try:
        raw = {
            "telegram_id": telegram_id, 
            "username": username, 
            "first_name": first_name, 
            "last_name": last_name
        }
        data = _sanitize(raw)
        
        if not data.get("telegram_id"):
            return None
        
        supabase = get_supabase_client()
        res = supabase.table("users").upsert(data, on_conflict="telegram_id").select("*").execute()
        
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
        
    except Exception as e:
        print(f"Error ensuring user {telegram_id}: {e}")
        return None

def touch_user_from_message(message):
    """Extract user info from Telegram message and ensure user exists in Supabase"""
    if not message or not hasattr(message, 'from_user'):
        return None
    
    user = message.from_user
    if not user or not user.id:
        return None
    
    return ensure_user(
        telegram_id=user.id,
        username=getattr(user, "username", None),
        first_name=getattr(user, "first_name", None),
        last_name=getattr(user, "last_name", None),
    )

def touch_user_from_update(update):
    """Extract user info from Telegram update and ensure user exists in Supabase"""
    if not update:
        return None
    
    # Try message first
    if hasattr(update, 'message') and update.message:
        return touch_user_from_message(update.message)
    
    # Try callback query
    if hasattr(update, 'callback_query') and update.callback_query:
        cq = update.callback_query
        if hasattr(cq, 'from_user') and cq.from_user:
            user = cq.from_user
            return ensure_user(
                telegram_id=user.id,
                username=getattr(user, "username", None),
                first_name=getattr(user, "first_name", None),
                last_name=getattr(user, "last_name", None),
            )
    
    # Try effective_user
    if hasattr(update, 'effective_user') and update.effective_user:
        user = update.effective_user
        return ensure_user(
            telegram_id=user.id,
            username=getattr(user, "username", None),
            first_name=getattr(user, "first_name", None),
            last_name=getattr(user, "last_name", None),
        )
    
    return None
