
from ..sb_client import upsert_user_with_weekly_reset_rpc, enforce_weekly_reset_calendar_rpc

def touch_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Manual user touch function for non-middleware usage"""
    try:
        # 1) Ensure user is registered + new users get 100 credits
        upsert_user_with_weekly_reset_rpc(
            user_id,
            username,
            first_name,
            last_name,
        )
        
        # 2) Enforce weekly reset (Monday 00:00 UTC), idempotent for non-premium
        enforce_weekly_reset_calendar_rpc(user_id)
        return True
    except Exception as e:
        print(f"⚠️ Manual user touch failed for {user_id}: {e}")
        return False
