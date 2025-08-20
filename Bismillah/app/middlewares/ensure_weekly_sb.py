
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from ..sb_repo import ensure_user_and_welcome, enforce_weekly_reset_calendar

def _touch(obj):
    u = getattr(obj, "from_user", None)
    if not u: 
        return
    
    try:
        ensure_user_and_welcome(
            u.id, 
            getattr(u, "username", None), 
            getattr(u, "first_name", None), 
            getattr(u, "last_name", None)
        )
        enforce_weekly_reset_calendar(u.id)
    except Exception as e:
        print(f"Error in middleware for user {u.id}: {e}")

class EnsureWeeklySBMiddleware(BaseMiddleware):
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
