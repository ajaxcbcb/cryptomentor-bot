
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
        # Weekly refresh is ONLY handled by scheduled task on Monday 00:00
        # This middleware is completely disabled to prevent credit resets
        # Only the scheduled weekly_credit_refresh_supabase.py should modify credits
        
        return await handler(event, data)
