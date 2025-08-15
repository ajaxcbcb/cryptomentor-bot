
import asyncio
from app.db.local_db import (
    init_db, upsert_user, get_user, set_premium_with_value, 
    remove_premium, add_credits, is_premium, get_user_credits,
    count_users, count_premium_users
)

def db_status():
    """Get database status"""
    return {
        'mode': 'local_sqlite',
        'ready': True,
        'note': 'Local SQLite database ready - No Supabase dependencies'
    }

def _run_async(coro):
    """Helper to run async functions in sync context"""
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

def init_db_sync():
    """Initialize database synchronously"""
    return _run_async(init_db())

def add_premium(user_id: int, duration: str):
    """Add premium to user"""
    try:
        if duration.lower() == 'lifetime':
            _run_async(set_premium_with_value(str(user_id), 'lifetime', 0))
            return True, f"✅ Lifetime premium granted to user {user_id}"
        elif duration.isdigit():
            days = int(duration)
            _run_async(set_premium_with_value(str(user_id), 'days', days))
            return True, f"✅ {days} days premium granted to user {user_id}"
        else:
            return False, f"❌ Invalid duration format: {duration}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def remove_premium_sync(user_id: int):
    """Remove premium from user"""
    try:
        _run_async(remove_premium(str(user_id)))
        return True, f"✅ Premium removed from user {user_id}"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def grant_credits(user_id: int, amount: int):
    """Grant credits to user"""
    try:
        _run_async(add_credits(str(user_id), amount))
        new_balance = _run_async(get_user_credits(str(user_id)))
        return True, new_balance
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def get_user_info(user_id: int):
    """Get user information"""
    try:
        return _run_async(get_user(str(user_id)))
    except Exception as e:
        return None

def check_user_banned(user_id: int):
    """Check if user is banned (not implemented in local SQLite)"""
    return False

def ban_user(user_id: int):
    """Ban user (not implemented in local SQLite)"""
    pass

def unban_user(user_id: int):
    """Unban user (not implemented in local SQLite)"""
    pass

# Initialize on import
init_db_sync()
