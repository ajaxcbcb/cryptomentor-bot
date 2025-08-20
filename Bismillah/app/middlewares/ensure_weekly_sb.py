
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
        # Extract user info
        user = None
        if event.message and event.message.from_user:
            user = event.message.from_user
        elif event.callback_query and event.callback_query.from_user:
            user = event.callback_query.from_user
            
        if user:
            try:
                # Check and refresh weekly credits
                s = get_supabase_client()
                now = datetime.utcnow()
                week_ago = now - timedelta(days=7)
                
                # Check if user needs weekly refresh
                res = s.table("users").select("*").eq("telegram_id", user.id).single().execute()
                if res.data:
                    user_data = res.data
                    last_refresh = user_data.get("last_weekly_refresh")
                    
                    if not last_refresh or datetime.fromisoformat(last_refresh.replace('Z', '+00:00')) < week_ago:
                        # Give weekly refresh
                        new_credits = user_data.get("credits", 0) + WEEKLY_REFRESH_CREDITS
                        s.table("users").update({
                            "credits": new_credits,
                            "last_weekly_refresh": now.isoformat()
                        }).eq("telegram_id", user.id).execute()
                        
            except Exception as e:
                print(f"Weekly refresh error for user {user.id}: {e}")
        
        return await handler(event, data)
