\"\"\"
Admin handlers for UID verification.
\"\"\"
from telegram import Update
from telegram.ext import ContextTypes
from app.supabase_repo import save_autotrade_session
import logging

logger = logging.getLogger(__name__)

async def callback_uid_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # query.data: uid_acc_{user_id}
    try:
        user_id = int(query.data.split("_")[-1])
        
        # 1. Update status in Supabase
        from app.supabase_repo import _client
        s = _client()
        s.table("autotrade_sessions").update({
            "status": "uid_verified",
            "updated_at": __import__('datetime').datetime.utcnow().isoformat()
        }).eq("telegram_id", user_id).execute()
        
        # 2. Notify User
        from app.lib.auth import generate_dashboard_url
        dash_url = generate_dashboard_url(user_id)
        
        msg_to_user = (
            "🎉 <b>Identity Verified!</b>\n\n"
            "Your Bitunix UID has been approved by our team. "
            "You can now access the Web Dashboard to configure your API keys and start trading."
        )
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [[InlineKeyboardButton("🌐 Open Web Dashboard", url=dash_url)]]
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=msg_to_user,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.warning(f"Failed to notify user {user_id} of approval: {e}")
            
        await query.edit_message_text(f"✅ Approved User {user_id}")
        
    except Exception as e:
        logger.error(f"Error in callback_uid_acc: {e}")
        await query.edit_message_text(f"❌ Error: {e}")


async def callback_uid_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = int(query.data.split("_")[-1])
        
        # 1. Update status in Supabase
        from app.supabase_repo import _client
        s = _client()
        s.table("autotrade_sessions").update({
            "status": "uid_rejected",
            "updated_at": __import__('datetime').datetime.utcnow().isoformat()
        }).eq("telegram_id", user_id).execute()
        
        # 2. Notify User
        msg_to_user = (
            "❌ <b>Verification Rejected</b>\n\n"
            "Your UID verification request was rejected. "
            "Please ensure you registered using our referral link and try again."
        )
        try:
            await context.bot.send_message(chat_id=user_id, text=msg_to_user, parse_mode='HTML')
        except Exception: pass
        
        await query.edit_message_text(f"❌ Rejected User {user_id}")
        
    except Exception as e:
        logger.error(f"Error in callback_uid_reject: {e}")
        await query.edit_message_text(f"❌ Error: {e}")
