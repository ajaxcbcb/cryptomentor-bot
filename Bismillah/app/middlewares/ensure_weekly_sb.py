# app/middlewares/ensure_weekly_sb.py
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from ..sb_repo import ensure_user_and_welcome, enforce_weekly_reset_calendar

def _touch(obj):
    """Touch user to ensure existence and weekly reset"""
    u = getattr(obj, "from_user", None)
    if not u:
        return

    # Ensure user exists with basic info
    ensure_user_and_welcome(
        u.id,
        getattr(u, "username", None),
        getattr(u, "first_name", None),
        getattr(u, "last_name", None)
    )

    # Enforce weekly reset if applicable
    try:
        enforce_weekly_reset_calendar(u.id)
    except Exception as e:
        print(f"Weekly reset error for user {u.id}: {e}")

class EnsureWeeklySBMiddleware(BaseMiddleware):
    """Middleware to ensure user exists and handle weekly credits"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Touch user for messages and callback queries
        if isinstance(event, (Message, CallbackQuery)):
            _touch(event)

        return await handler(event, data)