import asyncio
from app.db.local_db import is_premium as local_is_premium, get_user_credits as local_get_credits

def _run_async(coro):
    """Helper to run async functions in sync context"""
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

def is_premium(user_id: int) -> bool:
    """Check if user has premium status"""
    try:
        return _run_async(local_is_premium(str(user_id)))
    except Exception as e:
        print(f"Error checking premium status: {e}")
        return False

def get_user_credits(user_id: int) -> int:
    """Get user credit balance"""
    try:
        return _run_async(local_get_credits(str(user_id)))
    except Exception as e:
        print(f"Error getting user credits: {e}")
        return 0