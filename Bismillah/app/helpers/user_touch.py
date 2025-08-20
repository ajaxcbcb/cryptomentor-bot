
from ..sb_client import upsert_user_with_weekly_reset_rpc, enforce_weekly_reset_calendar_rpc
import logging

def touch_user(message):
    """Touch user for telebot compatibility - ensure they exist in Supabase and apply weekly reset"""
    if not hasattr(message, 'from_user') or not message.from_user:
        return
    
    user = message.from_user
    
    try:
        # User baru: credits sesuai WEEKLY_FREE_CREDITS
        upsert_user_with_weekly_reset_rpc(
            user.id,
            getattr(user, 'username', None),
            getattr(user, 'first_name', None),
            getattr(user, 'last_name', None)
        )
        
        # Weekly reset (Sen 00:00 UTC), idempotent untuk non-premium
        try:
            enforce_weekly_reset_calendar_rpc(user.id)
        except Exception as e:
            logging.warning(f"Weekly reset failed for user {user.id}: {e}")
            
    except Exception as e:
        logging.error(f"Failed to touch user {user.id}: {e}")
