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
    admin_main = (os.getenv("ADMIN") or "").strip().strip('"').strip("'")
    admin1 = (os.getenv("ADMIN1") or "").strip().strip('"').strip("'")
    admin2 = (os.getenv("ADMIN2") or "").strip().strip('"').strip("'")
    admin_user_id = (os.getenv("ADMIN_USER_ID") or "").strip().strip('"').strip("'")
    admin2_user_id = (os.getenv("ADMIN2_USER_ID") or "").strip().strip('"').strip("'")

    env_status = []
    if admin_main:
        env_status.append(f"ADMIN={admin_main} (Super Admin)")
    if admin1:
        env_status.append(f"ADMIN1={admin1}")
    if admin2:
        env_status.append(f"ADMIN2={admin2}")
    if admin_user_id:
        env_status.append(f"ADMIN_USER_ID={admin_user_id} (Legacy)")
    if admin2_user_id:
        env_status.append(f"ADMIN2_USER_ID={admin2_user_id} (Legacy)")

    message = f"""🔧 **Admin Debug Information**

👤 **Caller Info:**
• **Your ID**: `{uid}`
• **Is Admin**: {is_admin(uid)}

🔑 **Resolved Admin IDs**: {ids if ids else 'NONE'}

⚙️ **Environment Variables**:
{chr(10).join(env_status) if env_status else 'No admin env vars set'}

💡 **Expected Setup**:
• Set `ADMIN` = `{uid}` in Replit Secrets (Super Admin)
• Or set `ADMIN1` = `{uid}` for first admin
• Set `ADMIN2` = `<second_admin_id>` for second admin
• Restart bot after changes

🔧 **Current Priority Order**:
1. ADMIN (Super Admin with full control)
2. ADMIN1, ADMIN2 (Primary admins)
3. Dynamic admins (added by Super Admin)
4. Legacy: ADMIN_USER_ID, ADMIN2_USER_ID"""

    await update.effective_message.reply_text(message, parse_mode='Markdown')