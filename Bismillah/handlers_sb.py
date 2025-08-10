
from telegram import Update
from telegram.ext import ContextTypes
from supabase_conn import health

async def cmd_sb_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only command to check Supabase connection status"""
    uid = update.effective_user.id if update and update.effective_user else None
    
    # Check if user is admin (using existing is_admin logic from bot.py)
    # Get bot instance to access admin check
    bot_instance = context.bot_data.get('bot_instance')
    if not bot_instance or not hasattr(bot_instance, 'is_admin') or not bot_instance.is_admin(uid):
        return await update.effective_message.reply_text("❌ Kamu tidak punya izin.")
    
    # Perform health check
    ok, info = health()
    
    if ok:
        await update.effective_message.reply_text(f"✅ Supabase: {info}")
    else:
        await update.effective_message.reply_text(f"❌ Supabase: {info}")
