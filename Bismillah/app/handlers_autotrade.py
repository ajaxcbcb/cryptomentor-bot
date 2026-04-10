\"\"\"
AutoTrade Handlers - Gatekeeper Mode (Phase 1 Migration)
Redirection flow from Telegram Bot to Web Dashboard.
\"\"\"

import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from typing import Optional, Dict

from app.supabase_repo import get_autotrade_session, save_autotrade_session
from app.lib.auth import generate_dashboard_url

# Conversation states
WAITING_BITUNIX_UID = 6

# Constants
BITUNIX_REFERRAL_URL = "https://www.bitunix.com/register?vipCode=sq45"
PORTFOLIO_STATUS = "portfolio_status"

async def cmd_autotrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Registration logic
    try:
        from app.chat_store import remember_chat
        remember_chat(user_id, update.effective_chat.id)
    except Exception:
        pass

    # Background registration
    import asyncio
    async def _register_user():
        try:
            from app.supabase_repo import upsert_user_with_welcome
            await asyncio.to_thread(upsert_user_with_welcome, user_id, user.username, user.first_name, user.last_name, 100)
        except Exception: pass
    asyncio.create_task(_register_user())

    # 1. Check Verification Status from Supabase
    try:
        session = get_autotrade_session(user_id)
        status = session.get("status", "none") if session else "none"
        uid = session.get("bitunix_uid") if session else None
    except Exception:
        status = "none"
        uid = None

    dash_url = generate_dashboard_url(user_id, user.username, user.first_name)

    # 2. Gatekeeper Logic
    if status == "active" or status == "uid_verified":
        text = (
            f"✅ <b>Identity Verified</b>\n\n"
            f"UID: <code>{uid}</code>\n"
            f"Status: <b>{status.upper()}</b>\n\n"
            f"Your account is verified. You can now manage all trading operations, "
            f"API keys, and risk settings directly from the web dashboard."
        )
        keyboard = [
            [InlineKeyboardButton("🌐 Go to Web Dashboard", url=dash_url)],
            [InlineKeyboardButton("📊 Portfolio Status", callback_data=PORTFOLIO_STATUS)]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        return

    if status == "pending_verification":
        text = (
            f"⏳ <b>Verification Pending</b>\n\n"
            f"UID: <code>{uid}</code>\n\n"
            f"Your UID is currently being verified by our team. "
            f"Once approved, you will be notified here and can start trading on the dashboard."
        )
        keyboard = [[InlineKeyboardButton("🌐 Open Web Dashboard", url=dash_url)]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        return

    # User not yet verified or session missing
    text = (
        f"🚀 <b>Welcome to CryptoMentor AI</b>\n\n"
        f"To start automated trading, you need to verify your account by connecting it to your Bitunix UID.\n\n"
        f"1️⃣ <b>Register on Bitunix</b> (if you haven't)\n"
        f"2️⃣ <b>Submit your UID</b> for verification\n"
        f"3️⃣ <b>Configure API</b> on the Web Dashboard\n\n"
        f"Choose an option below:"
    )
    keyboard = [
        [InlineKeyboardButton("🌐 Register / Open Dashboard", url=dash_url)],
        [InlineKeyboardButton("🆔 Submit UID here", callback_data="submit_uid_bot")],
        [InlineKeyboardButton("🔗 Register on Bitunix", url=BITUNIX_REFERRAL_URL)]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')


# ------------------------------------------------------------------ #
#  UID Submission Flow (Manual via Bot)                               #
# ------------------------------------------------------------------ #

async def handle_submit_uid_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "📝 <b>Submit Bitunix UID</b>\n\n"
        "Please enter your Bitunix UID (numbers only).\n\n"
        "<i>Note: If you don't have one, please register using the link in the previous menu first.</i>",
        parse_mode='HTML'
    )
    return WAITING_BITUNIX_UID


async def process_uid_input_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not uid.isdigit():
        await update.message.reply_text("❌ UID must be numbers only. Please try again:")
        return WAITING_BITUNIX_UID
        
    try:
        from app.supabase_repo import _client
        s = _client()
        s.table("autotrade_sessions").upsert({
            "telegram_id": user_id,
            "bitunix_uid": uid,
            "status": "pending_verification",
            "updated_at": datetime.utcnow().isoformat()
        }, on_conflict="telegram_id").execute()
        
        await notify_admins_of_uid(context.bot, user_id, uid)
        
        dash_url = generate_dashboard_url(user_id, update.effective_user.username, update.effective_user.first_name)
        
        await update.message.reply_text(
            f"✅ <b>UID Submitted!</b>\n\n"
            f"UID: <code>{uid}</code>\n"
            f"Status: <b>PENDING VERIFICATION</b>\n\n"
            f"We will verify your UID and notify you shortly. In the meantime, "
            f"you can explore the Web Dashboard.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Open Dashboard", url=dash_url)]]),
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error saving UID: {e}")
        
    return ConversationHandler.END


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END


async def callback_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Operation cancelled.")
    return ConversationHandler.END


async def notify_admins_of_uid(bot, user_id: int, uid: str):
    admin_ids = []
    for key in ['ADMIN_IDS', 'ADMIN1', 'ADMIN2', 'ADMIN_USER_ID', 'ADMIN2_USER_ID']:
        val = os.getenv(key)
        if val:
            for part in val.split(','):
                part = part.strip()
                if part.isdigit(): admin_ids.append(int(part))
    
    msg = (
        f"🔔 <b>New UID Verification Request</b>\n\n"
        f"User ID: <code>{user_id}</code>\n"
        f"Bitunix UID: <code>{uid}</code>\n\n"
        f"Approving this will allow the user to start trading on the dashboard."
    )
    for aid in set(admin_ids):
        try: await bot.send_message(chat_id=aid, text=msg, parse_mode='HTML')
        except Exception: pass


def register_autotrade_handlers(application):
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("autotrade", cmd_autotrade),
            CommandHandler("start", cmd_autotrade),
            CallbackQueryHandler(handle_submit_uid_bot, pattern="^submit_uid_bot$"),
        ],
        states={
            WAITING_BITUNIX_UID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_uid_input_bot),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cmd_cancel),
            CallbackQueryHandler(callback_cancel, pattern="^at_cancel$"),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
    application.add_handler(conv)
    
    # Ad-hoc UID approval callbacks for admins
    from app.handlers_autotrade_admin import callback_uid_acc, callback_uid_reject
    application.add_handler(CallbackQueryHandler(callback_uid_acc, pattern="^uid_acc_\\d+$"))
    application.add_handler(CallbackQueryHandler(callback_uid_reject, pattern="^uid_reject_\\d+$"))

    print("✅ AutoTrade Gatekeeper handlers registered")
