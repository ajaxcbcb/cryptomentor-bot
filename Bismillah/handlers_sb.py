
from telegram import Update
from telegram.ext import ContextTypes
from supabase_conn import health

async def cmd_sb_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only command to check Supabase connection status"""
    uid = update.effective_user.id if update and update.effective_user else None
    
    # Enhanced admin check with environment variable fallback
    import os
    admin_ids = set()
    
    # Load admin IDs from environment variables
    for i in range(1, 10):
        env_key = f'ADMIN{i}'
        admin_id_str = os.getenv(env_key, '0')
        try:
            admin_id = int(admin_id_str)
            if admin_id > 0:
                admin_ids.add(admin_id)
        except ValueError:
            continue
    
    # Check if user is admin
    is_admin = uid in admin_ids
    
    if not is_admin:
        await update.effective_message.reply_text(
            f"❌ **Admin Access Required**\n\n"
            f"**Your ID**: {uid}\n"
            f"**Admin IDs**: {sorted(list(admin_ids)) if admin_ids else 'NONE CONFIGURED'}\n\n"
            f"⚙️ **Setup Instructions:**\n"
            f"1. Buka Secrets tab di Replit\n"
            f"2. Tambahkan `ADMIN1` = {uid}\n"
            f"3. Restart bot untuk apply changes\n\n"
            f"💡 Atau contact owner untuk menambahkan ID Anda ke admin list.",
            parse_mode='Markdown'
        )
        return
    
    # Perform health check
    ok, info = health()
    
    status_msg = f"👑 **Supabase Status Check** (Admin: {uid})\n\n"
    
    if ok:
        status_msg += f"✅ **Status**: {info}\n"
        status_msg += f"🔗 **Connection**: Healthy\n"
        status_msg += f"🌐 **Environment**: {'Production' if os.getenv('REPLIT_DEPLOYMENT') else 'Development'}"
    else:
        status_msg += f"❌ **Status**: {info}\n"
        status_msg += f"🔗 **Connection**: Failed\n"
        status_msg += f"⚠️ **Action Required**: Check environment variables"
    
    await update.effective_message.reply_text(status_msg, parse_mode='Markdown')
