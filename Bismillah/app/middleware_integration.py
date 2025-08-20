
# app/middleware_integration.py
from telegram import Update
from telegram.ext import ContextTypes
from typing import Optional
from .sb_repo import user_exists, upsert_user_ref_required, ensure_user_and_welcome

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
    if user_exists(user.id):
        return True
    
    # New user - check if this is a /start command with referral
    if update.message and update.message.text and update.message.text.startswith("/start"):
        ref_id = parse_ref_from_start(update.message.text)
        if ref_id:
            try:
                upsert_user_ref_required(
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
        if not user_exists(user_id):
            ensure_user_and_welcome(user_id, username, first_name, last_name)
    except Exception as e:
        print(f"Warning: Could not ensure user {user_id} exists: {e}")
