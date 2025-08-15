
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
import html
from app.supabase_conn import health, env_ok

def _format_md_v2(text: str) -> str:
    """Escape all special characters for MarkdownV2"""
    return escape_markdown(text, version=2)

async def _safe_reply_status(message, raw_text: str):
    """
    Try to send as MarkdownV2 (escaped).
    If fails, fallback to HTML <pre> (escaped).
    If still fails, send plain text without parse mode.
    """
    # 1) MarkdownV2 (escaped)
    try:
        md2 = _format_md_v2(raw_text)
        await message.reply_text(md2, parse_mode=ParseMode.MARKDOWN_V2)
        return
    except Exception as e_md2:
        pass

    # 2) HTML <pre> (escaped)
    try:
        html_text = f"<pre>{html.escape(raw_text)}</pre>"
        await message.reply_text(html_text, parse_mode=ParseMode.HTML)
        return
    except Exception as e_html:
        pass

    # 3) Plain text fallback
    await message.reply_text(raw_text)

async def cmd_sb_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only command to check Supabase connection status"""
    uid = update.effective_user.id if update and update.effective_user else None
    
    # Dynamic admin check with environment variable fallback
    import os
    admin_ids = set()
    
    # Check ADMIN1, ADMIN2, etc.
    for i in range(1, 10):
        env_key = f'ADMIN{i}'
        admin_id_str = (os.getenv(env_key) or "").strip()
        
        # Fallback to old naming format
        if not admin_id_str and i <= 2:
            fallback_key = f'ADMIN{i}_USER_ID' if i > 1 else 'ADMIN_USER_ID'
            admin_id_str = (os.getenv(fallback_key) or "").strip()
        
        # Add to set if valid
        if admin_id_str and admin_id_str.lower() != "none":
            admin_ids.add(str(admin_id_str))
    
    # Check if user is admin (string comparison)
    is_admin = str(uid) in admin_ids
    
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
    
    # Perform environment check first
    env_check_ok, env_info = env_ok()
    
    # Perform health check
    ok, info = health()
    
    status_msg = f"👑 **Supabase Status Check** (Admin: {uid})\n\n"
    
    # Environment validation
    status_msg += f"🔐 **Environment Variables:**\n"
    sb_url = os.getenv('SUPABASE_URL', 'NOT SET')
    sb_key = os.getenv('SUPABASE_SERVICE_KEY', 'NOT SET')
    
    # Mask sensitive info
    if sb_url != 'NOT SET':
        status_msg += f"• SUPABASE_URL: {'✅ SET' if 'supabase.co' in sb_url else '❌ INVALID'}\n"
    else:
        status_msg += f"• SUPABASE_URL: ❌ NOT SET\n"
    
    if sb_key != 'NOT SET':
        status_msg += f"• SUPABASE_SERVICE_KEY: ✅ SET\n"
    else:
        status_msg += f"• SUPABASE_SERVICE_KEY: ❌ NOT SET\n"
    
    status_msg += f"\n🔗 **Connection Test:**\n"
    
    if ok:
        status_msg += f"✅ **Status**: {info}\n"
        status_msg += f"✅ **Health**: Connection Successful\n"
    else:
        status_msg += f"❌ **Status**: {info}\n"
        status_msg += f"❌ **Health**: Connection Failed\n"
        
        # Troubleshooting hints
        if "SUPABASE_URL belum diset" in info:
            status_msg += f"\n💡 **Fix**: Set SUPABASE_URL in Secrets"
        elif "tidak valid" in info:
            status_msg += f"\n💡 **Fix**: Use https://<ref>.supabase.co format"
        elif "SUPABASE_SERVICE_KEY belum diset" in info:
            status_msg += f"\n💡 **Fix**: Set SUPABASE_SERVICE_KEY in Secrets"
        elif "table_status=404" in info:
            status_msg += f"\n💡 **Fix**: Create 'users' table in Supabase"
        elif "401" in info or "403" in info:
            status_msg += f"\n💡 **Fix**: Use service_role key, not anon key"
    
    status_msg += f"\n🌐 Environment: {'Production' if os.getenv('REPLIT_DEPLOYMENT') else 'Development'}"
    
    await _safe_reply_status(update.effective_message, status_msg)
