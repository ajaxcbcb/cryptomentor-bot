
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
import html
from supabase_conn import health, env_ok

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
    from app.admin_status import get_admin_status
    from app.admin_auth import is_admin, denied
    
    uid = update.effective_user.id if update and update.effective_user else None
    
    if not is_admin(uid):
        await update.effective_message.reply_text(denied(uid))
        return
    
    # Get status from admin status module
    status_data = await get_admin_status()
    
    status_msg = f"👑 **Supabase Status Check** (Admin: {uid})\n\n"
    
    # Environment validation
    status_msg += f"🔐 **Environment Variables:**\n"
    import os
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
    status_msg += f"{'✅' if status_data['ok'] else '❌'} **Status**: {status_data['reason']}\n"
    status_msg += f"📊 **Users**: {status_data['total_users']} | **Premium**: {status_data['premium_users']}\n"
    status_msg += f"⏰ **Last Check**: {status_data['timestamp']}\n"
    
    if not status_data['ok']:
        if "unauthorized" in status_data['reason']:
            status_msg += f"\n💡 **Fix**: Use service_role key, not anon key"
        elif "SUPABASE_URL" in status_data['reason']:
            status_msg += f"\n💡 **Fix**: Set SUPABASE_URL in Secrets"
    
    status_msg += f"\n🌐 Environment: {'Production' if os.getenv('REPLIT_DEPLOYMENT') else 'Development'}"
    
    await _safe_reply_status(update.effective_message, status_msg)
