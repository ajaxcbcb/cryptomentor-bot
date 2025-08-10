
# app/handlers_db_debug.py
from telegram import Update
from telegram.ext import ContextTypes
from app.db_router import db_status, get_user
from app.safe_send import safe_reply
from app.lib.guards import admin_guard

@admin_guard
async def cmd_db_trace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command untuk trace user data"""
    if not context.args or not context.args[0].isdigit():
        return await safe_reply(update.effective_message, "Format: /db_trace <userid>")
    
    tid = int(context.args[0])
    st = db_status()
    rec = get_user(tid) or {}
    
    # Format data untuk display
    premium_status = "NO"
    if rec.get("is_premium"):
        if rec.get("premium_until") in (None, ""):
            premium_status = "LIFETIME"
        else:
            premium_status = f"UNTIL {rec.get('premium_until', 'Unknown')}"
    
    banned_status = "YES" if rec.get("banned") else "NO"
    credits = rec.get("credits", 0)
    
    message = f"""🗄️ **Database Trace**

**Backend Info:**
• Mode: {st['mode']}
• Ready: {st['ready']}
• Note: {st['note']}

**User {tid} Data:**
• Premium: {premium_status}
• Banned: {banned_status}  
• Credits: {credits}

**Raw Record:**
{rec}"""
    
    await safe_reply(update.effective_message, message)
