
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from ..sb_client import upsert_user_with_weekly_reset_rpc, enforce_weekly_reset_calendar_rpc
import logging

def _touch(obj):
    """Touch user - ensure they exist in Supabase and apply weekly reset"""
    u = getattr(obj, "from_user", None)
    if not u:
        return
    
    try:
        # User baru: 100 credits (atau sesuai WEEKLY_FREE_CREDITS)
        upsert_user_with_weekly_reset_rpc(
            u.id, 
            getattr(u, "username", None), 
            getattr(u, "first_name", None), 
            getattr(u, "last_name", None)
        )
        
        # Weekly reset (Sen 00:00 UTC), idempotent untuk non-premium
        try:
            enforce_weekly_reset_calendar_rpc(u.id)
        except Exception as e:
            logging.warning(f"Weekly reset failed for user {u.id}: {e}")
            
    except Exception as e:
        logging.error(f"Failed to touch user {u.id}: {e}")

class EnsureUserSBMiddleware(BaseMiddleware):
    """Middleware to ensure user exists in Supabase and apply weekly reset"""
    
    async def __call__(
        self, 
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], 
        event: TelegramObject, 
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            _touch(event)
        elif isinstance(event, CallbackQuery):
            _touch(event)
        
        return await handler(event, data)
