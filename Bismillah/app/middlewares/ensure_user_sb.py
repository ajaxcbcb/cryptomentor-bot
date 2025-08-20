
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from ..sb_client import upsert_user_with_weekly_reset_rpc, enforce_weekly_reset_calendar_rpc

def _touch_user(obj):
    """Touch user to ensure registration and weekly reset"""
    u = getattr(obj, "from_user", None)
    if not u: 
        return
    
    try:
        # 1) Ensure user is registered + new users get 100 credits
        upsert_user_with_weekly_reset_rpc(
            u.id,
            getattr(u, "username", None),
            getattr(u, "first_name", None),
            getattr(u, "last_name", None),
        )
        
        # 2) Enforce weekly reset (Monday 00:00 UTC), idempotent for non-premium
        enforce_weekly_reset_calendar_rpc(u.id)
    except Exception as e:
        # Silent fail to not interrupt bot functionality
        print(f"⚠️ User touch failed for {u.id}: {e}")

class EnsureUserSupabaseMiddleware(BaseMiddleware):
    """Middleware to ensure user registration and weekly credit reset"""
    
    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        # Handle different event types
        if isinstance(event, Message):
            _touch_user(event)
        elif isinstance(event, CallbackQuery):
            _touch_user(event)
        
        # Continue with the handler
        return await handler(event, data)
