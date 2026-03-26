# app/lib/guards.py
from functools import wraps
import os
from typing import List, Set
import logging

logger = logging.getLogger(__name__)

def _resolve_admin_ids() -> Set[int]:
    """Resolve admin IDs from various environment variables"""
    ids = set()

    # Primary admin sources
    for key in ["ADMIN1", "ADMIN2", "ADMIN_USER_ID", "ADMIN2_USER_ID"]:
        val = (os.getenv(key) or "").strip().strip('"').strip("'")
        if val.isdigit():
            ids.add(int(val))

    return ids

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    if not user_id:
        return False
    return user_id in _resolve_admin_ids()

def admin_guard(func):
    """Decorator to restrict access to admin users only"""
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user_id = getattr(update.effective_user, "id", None) if update and update.effective_user else None

        if not user_id or not is_admin(user_id):
            logger.warning(f"Access denied for user {user_id} in admin function {func.__name__}")
            if update and update.effective_message:
                await update.effective_message.reply_text("❌ Access denied. Admin only.")
            return

        return await func(update, context, *args, **kwargs)
    return wrapper

def premium_guard(func):
    """Decorator to restrict access to premium users only"""
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user_id = getattr(update.effective_user, "id", None) if update and update.effective_user else None

        if not user_id:
            if update and update.effective_message:
                await update.effective_message.reply_text("❌ User ID tidak ditemukan.")
            return

        try:
            from supabase_client import supabase_service
            if not supabase_service.is_premium(user_id):
                if update and update.effective_message:
                    await update.effective_message.reply_text("❌ Fitur khusus premium. Upgrade untuk akses unlimited!")
                return
        except Exception as e:
            logger.error(f"Error checking premium status for user {user_id}: {e}")
            if update and update.effective_message:
                await update.effective_message.reply_text("❌ Gagal memeriksa status premium. Coba lagi nanti.")
            return

        return await func(update, context, *args, **kwargs)
    return wrapper