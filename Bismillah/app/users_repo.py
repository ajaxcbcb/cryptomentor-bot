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

def touch_user_from_update(update):
    """Auto-upsert user to Supabase from Telegram update object"""
    try:
        user = update.effective_user
        if not user:
            return

        # Try new sb_client first
        try:
            from .sb_client import upsert_user_via_rpc
            upsert_user_via_rpc(
                telegram_id=user.id,
                username=getattr(user, 'username', None),
                first_name=getattr(user, 'first_name', None),
                last_name=getattr(user, 'last_name', None)
            )
            print(f"✅ User {user.id} upserted via RPC")
            return
        except ImportError:
            print("ℹ️ sb_client not found, falling back to direct Supabase connection.")
            pass
        except Exception as e:
            print(f"⚠️ Error calling upsert_user_via_rpc for user {user.id}: {e}")
            # Continue to fallback if RPC call fails

        # Fallback to existing supabase connection
        try:
            from .supabase_conn import get_supabase_client
            supabase = get_supabase_client()

            # Safe upsert - only send allowed fields
            user_data = {
                "telegram_id": user.id,
                "username": getattr(user, 'username', None),
                "first_name": getattr(user, 'first_name', None),
                "last_name": getattr(user, 'last_name', None)
            }

            # Remove None values to avoid DB issues
            user_data = {k: v for k, v in user_data.items() if v is not None}

            # Use upsert to handle existing users
            result = supabase.table("users").upsert(user_data, on_conflict="telegram_id").execute()
            print(f"✅ User {user.id} upserted to Supabase via direct connection")

        except Exception as e:
            print(f"⚠️ Failed to upsert user {user.id} to Supabase via direct connection: {e}")

    except Exception as e:
        print(f"❌ Critical error in touch_user_from_update: {e}")

def touch_user_from_message(message):
    """Helper for telebot-style message objects"""
    try:
        user = message.from_user
        if not user:
            print("⚠️ No user found in message.")
            return

        # Create update-like object for compatibility
        class MockUpdate:
            def __init__(self, user):
                self.effective_user = user

        touch_user_from_update(MockUpdate(user))

    except Exception as e:
        print(f"❌ Error in touch_user_from_message: {e}")

def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict]:
    """Legacy compatibility function - get user by telegram ID"""
    if not SUPABASE_AVAILABLE:
        return None
    
    try:
        from app.supabase_conn import get_user_by_tid
        return get_user_by_tid(telegram_id)
    except Exception as e:
        print(f"Error getting user by telegram_id {telegram_id}: {e}")
        return None

def upsert_user_via_rpc(telegram_id: int, username: Optional[str]=None, first_name: Optional[str]=None, last_name: Optional[str]=None, referred_by: Optional[int]=None) -> Optional[Dict]:
    """Legacy compatibility function - upsert user via RPC"""
    if not SUPABASE_AVAILABLE:
        return None
    
    try:
        from app.supabase_conn import upsert_user_via_rpc as sb_upsert
        return sb_upsert(telegram_id, username, first_name, last_name, referred_by)
    except Exception as e:
        print(f"Error upserting user {telegram_id}: {e}")
        return None