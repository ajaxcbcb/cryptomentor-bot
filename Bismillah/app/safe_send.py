"""
safe_send.py — Helper untuk send message dengan error handling.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def safe_dm(bot, user_id: int, text: str, **kwargs) -> bool:
    """Send DM ke user, return True kalau berjaya."""
    try:
        await bot.send_message(chat_id=user_id, text=text, **kwargs)
        return True
    except Exception as e:
        logger.warning(f"safe_dm failed for user {user_id}: {e}")
        return False


async def safe_reply(update: Update, text: str, **kwargs) -> bool:
    """Reply ke message, return True kalau berjaya."""
    try:
        if update.message:
            await update.message.reply_text(text, **kwargs)
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, **kwargs)
        return True
    except Exception as e:
        logger.warning(f"safe_reply failed: {e}")
        return False
