
# app/safe_send.py
from telegram.constants import ParseMode
from telegram.error import Forbidden, BadRequest
from telegram.helpers import escape_markdown
import html
from app.chat_store import get_chat_id, remove_chat

def _md2(s: str) -> str:
    """Escape markdown for v2"""
    return escape_markdown(s, version=2)

async def safe_reply(message, text: str):
    """
    Safe reply to message with fallback parse modes
    """
    try:
        return await message.reply_text(_md2(text), parse_mode=ParseMode.MARKDOWN_V2)
    except Exception:
        try:
            return await message.reply_text(f"<pre>{html.escape(text)}</pre>", parse_mode=ParseMode.HTML)
        except Exception:
            return await message.reply_text(text)

async def safe_dm(bot, target_user_id: int, text: str):
    """
    DM user only if they have given consent (started the bot)
    Raises PermissionError if no consent
    """
    chat_id = get_chat_id(target_user_id)
    if chat_id is None:
        # User hasn't started bot, no consent to DM
        raise PermissionError("NO_CHAT_CONSENT")
    
    try:
        return await bot.send_message(chat_id=chat_id, text=_md2(text), parse_mode=ParseMode.MARKDOWN_V2)
    except (Forbidden, BadRequest):
        # Try HTML fallback
        try:
            return await bot.send_message(chat_id=chat_id, text=f"<pre>{html.escape(text)}</pre>", parse_mode=ParseMode.HTML)
        except (Forbidden, BadRequest) as e:
            # User blocked/left bot - remove consent
            remove_chat(target_user_id)
            raise e

async def safe_broadcast(bot, text: str, consented_users_only: bool = True):
    """
    Safe broadcast to users with consent
    Returns (success_count, failed_count, no_consent_count)
    """
    from app.chat_store import get_all_consented_users
    
    success = 0
    failed = 0
    no_consent = 0
    
    if consented_users_only:
        # Only send to users who have started the bot
        consented = get_all_consented_users()
        for user_id_str, data in consented.items():
            try:
                user_id = int(user_id_str)
                await safe_dm(bot, user_id, text)
                success += 1
            except PermissionError:
                no_consent += 1
            except Exception as e:
                print(f"Broadcast failed for user {user_id}: {e}")
                failed += 1
    
    return success, failed, no_consent
