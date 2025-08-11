
# app/handlers_admin_debug.py
from telegram import Update
from telegram.ext import ContextTypes
from app.lib.auth import is_admin, _resolve_admin_ids
import os

async def cmd_whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user ID and admin status"""
    uid = getattr(update.effective_user, "id", None)
    username = getattr(update.effective_user, "username", "No username")
    first_name = getattr(update.effective_user, "first_name", "Unknown")
    
    message = f"""👤 **Your Information:**

• **User ID**: `{uid}`
• **Username**: @{username}
• **Name**: {first_name}
• **Admin Status**: {'✅ ADMIN' if is_admin(uid) else '❌ NOT ADMIN'}"""
    
    await update.effective_message.reply_text(message, parse_mode='Markdown')

async def cmd_admin_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug admin configuration"""
    uid = getattr(update.effective_user, "id", None)
    ids = sorted(list(_resolve_admin_ids()))
    
    # Check environment variables
    admin1 = (os.getenv("ADMIN1") or "").strip().strip('"').strip("'")
    admin2 = (os.getenv("ADMIN2") or "").strip().strip('"').strip("'")
    admin_user_id = (os.getenv("ADMIN_USER_ID") or "").strip().strip('"').strip("'")
    admin2_user_id = (os.getenv("ADMIN2_USER_ID") or "").strip().strip('"').strip("'")
    
    env_status = []
    if admin1:
        env_status.append(f"ADMIN1={admin1}")
    if admin2:
        env_status.append(f"ADMIN2={admin2}")
    if admin_user_id:
        env_status.append(f"ADMIN_USER_ID={admin_user_id}")
    if admin2_user_id:
        env_status.append(f"ADMIN2_USER_ID={admin2_user_id}")
    
    message = f"""🔧 **Admin Debug Information**

👤 **Caller Info:**
• **Your ID**: `{uid}`
• **Is Admin**: {is_admin(uid)}

🔑 **Resolved Admin IDs**: {ids if ids else 'NONE'}

⚙️ **Environment Variables**:
{chr(10).join(env_status) if env_status else 'No admin env vars set'}

💡 **Expected Setup**:
• Set `ADMIN1` = `{uid}` in Replit Secrets
• Optional: Set `ADMIN2` for second admin
• Restart bot after changes"""
    
    await update.effective_message.reply_text(message, parse_mode='Markdown')
