
# app/middlewares/ensure_weekly_sb.py
from __future__ import annotations
from typing import Callable, Dict, Any, Awaitable, Optional, Union

# Support both aiogram v3 and telebot
try:
    from aiogram import BaseMiddleware
    from aiogram.types import TelegramObject, Message, CallbackQuery
    AIOGRAM_AVAILABLE = True
except ImportError:
    AIOGRAM_AVAILABLE = False
    BaseMiddleware = object
    TelegramObject = object

from ..sb_repo import ensure_user_and_welcome, enforce_weekly_reset_calendar

def _extract_user_info(obj) -> Optional[Dict[str, Any]]:
    """Extract user info from telegram object"""
    u = getattr(obj, "from_user", None) or getattr(obj, "user", None)
    if not u:
        return None
    
    return {
        "id": getattr(u, "id", None),
        "username": getattr(u, "username", None),
        "first_name": getattr(u, "first_name", None),
        "last_name": getattr(u, "last_name", None)
    }

def touch_user_sync(message_or_callback) -> None:
    """Synchronous user touch for telebot"""
    user_info = _extract_user_info(message_or_callback)
    if not user_info or not user_info["id"]:
        return
        
    try:
        ensure_user_and_welcome(
            user_info["id"], 
            user_info["username"], 
            user_info["first_name"], 
            user_info["last_name"]
        )
        enforce_weekly_reset_calendar(user_info["id"])
    except Exception as e:
        print(f"Error touching user {user_info['id']}: {e}")

# Aiogram v3 middleware (if available)
if AIOGRAM_AVAILABLE:
    class EnsureWeeklySBMiddleware(BaseMiddleware):
        async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                           event: TelegramObject, data: Dict[str, Any]) -> Any:
            # Touch user before processing
            user_info = _extract_user_info(event)
            if user_info and user_info["id"]:
                try:
                    ensure_user_and_welcome(
                        user_info["id"], 
                        user_info["username"], 
                        user_info["first_name"], 
                        user_info["last_name"]
                    )
                    enforce_weekly_reset_calendar(user_info["id"])
                except Exception as e:
                    print(f"Middleware error for user {user_info['id']}: {e}")
            
            return await handler(event, data)
else:
    # Dummy class for telebot compatibility
    class EnsureWeeklySBMiddleware:
        pass
