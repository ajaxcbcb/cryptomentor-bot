import re
from telegram.constants import ParseMode

async def safe_reply(update, text: str, prefer_html: bool = True):
    try:
        if prefer_html:
            return await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception:
        pass
    return await update.effective_message.reply_text(text, disable_web_page_preview=True)

async def safe_edit(bot, chat_id, message_id, text: str, prefer_html: bool = True):
    try:
        if prefer_html:
            return await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
    except Exception:
        pass
    return await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        disable_web_page_preview=True
    )