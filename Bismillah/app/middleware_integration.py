
# app/middleware_integration.py
from telegram import Update
from telegram.ext import ContextTypes
from typing import Optional
from .sb_repo import get_user_row, upsert_user_strict

JOIN_TEXT_NO_REF = (
    "🚪 Untuk bergabung, gunakan tautan referral.\n"
    "• Minta teman kirimkan link: https://t.me/{bot_username}?start=<USER_ID>\n"
    "• Atau klik link undangan yang valid dari komunitas.\n\n"
    "ℹ️ Referral wajib agar akunmu terdaftar."
)

JOIN_TEXT_BAD_REF = (
    "⚠️ Referral tidak valid.\n"
    "• Pastikan kamu memakai link resmi yang berisi ID Telegram perujuk.\n"
    "• Coba minta ulang link referral dari temanmu."
)

def parse_ref_from_start(text: str) -> Optional[int]:
    """Parse referral ID from /start command"""
    if not text or not text.startswith("/start"):
        return None
    parts = text.split(maxsplit=1)
    if len(parts) != 2:
        return None
    try:
        return int(parts[1])
    except (ValueError, TypeError):
        return None

async def handle_new_user_referral_gate(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_username: str) -> bool:
    """
    Handle new user with referral gate logic
    Returns True if user should continue, False if blocked
    """
    if not update.effective_user:
        return True
        
    user = update.effective_user
    
    # Check if user already exists
    if get_user_row(user.id):
        return True
    
    # New user - check if this is a /start command with referral
    if update.message and update.message.text and update.message.text.startswith("/start"):
        ref_id = parse_ref_from_start(update.message.text)
        if ref_id:
            try:
                upsert_user_strict(
                    tg_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    referred_by=ref_id
                )
                return True  # Registration successful, continue
            except Exception as e:
                await update.effective_message.reply_text(
                    JOIN_TEXT_BAD_REF,
                    parse_mode='HTML'
                )
                return False
        else:
            # /start without referral
            await update.effective_message.reply_text(
                JOIN_TEXT_NO_REF.format(bot_username=bot_username),
                parse_mode='HTML'
            )
            return False
    
    # Not a /start command, block new user
    await update.effective_message.reply_text(
        JOIN_TEXT_NO_REF.format(bot_username=bot_username),
        parse_mode='HTML'
    )
    return False

async def ensure_user_exists_legacy(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Ensure user exists for legacy users (without referral requirement)"""
    try:
        if not get_user_row(user_id):
            upsert_user_strict(user_id, username, first_name, last_name, None)
    except Exception as e:
        print(f"Warning: Could not ensure user {user_id} exists: {e}")

# Aiogram middleware setup
from aiogram import Dispatcher
from app.middlewares.ensure_weekly_sb import EnsureWeeklyCreditsMiddleware

def setup_middlewares(dp: Dispatcher):
    """Setup all middlewares for the bot"""
    
    # Weekly credits refresh middleware
    dp.message.middleware(EnsureWeeklyCreditsMiddleware())
    dp.callback_query.middleware(EnsureWeeklyCreditsMiddleware())
    
    print("✅ Middlewares configured")

def setup_routers(dp: Dispatcher):
    """Setup all routers for the bot"""
    
    try:
        # Import and register routers
        from app.routers.core import router as core_router
        from app.routers.admin_set_premium import router as admin_premium_router
        from app.routers.admin_set_credit_all import router as admin_credit_router
        from app.routers.admin_tools import router as admin_tools_router
        
        dp.include_router(core_router)
        dp.include_router(admin_premium_router) 
        dp.include_router(admin_credit_router)
        dp.include_router(admin_tools_router)
        
        print("✅ Routers configured")
        
    except ImportError as e:
        print(f"⚠️ Router import error: {e}")
