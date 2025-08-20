
# app/middlewares/ensure_weekly_sb.py
import os
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Update
from app.supabase_conn import get_supabase_client

WEEKLY_REFRESH_CREDITS = int(os.getenv("WEEKLY_REFRESH_CREDITS", "50"))

class EnsureWeeklyCreditsMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        # Weekly refresh is now handled by scheduled task only
        # This middleware is disabled to prevent frequent credit changes
        # Credits are refreshed weekly on Monday at midnight via scheduled script
        
        return await handler(event, data)
