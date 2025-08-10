
from telegram import Update
from telegram.ext import ContextTypes
from app.lib.guards import admin_guard
from app.safe_send import safe_reply
from app.supabase_conn import update_user_tid, get_user_by_tid

@admin_guard
async def cmd_user_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to set arbitrary user fields"""
    if len(context.args) < 3 or not context.args[0].isdigit():
        return await safe_reply(update.effective_message, 
            "❌ **Format:** `/user_set <userid> <field> <value>`\n\n"
            "**Examples:**\n"
            "• `/user_set 123456789 banned false`\n"
            "• `/user_set 123456789 credits 500`\n"
            "• `/user_set 123456789 is_premium true`\n\n"
            "**Value types:**\n"
            "• `true/false` → boolean\n"
            "• `123` → integer\n"
            "• `null` → NULL\n"
            "• `text` → string"
        )
    
    tid = int(context.args[0])
    field = context.args[1]
    value = " ".join(context.args[2:])
    
    try:
        # Type coercion
        if value.lower() in ("true", "false"):
            payload = {field: value.lower() == "true"}
        elif value.isdigit():
            payload = {field: int(value)}
        elif value.lower() == "null":
            payload = {field: None}
        else:
            payload = {field: value}
        
        # Update user
        update_user_tid(tid, **payload)
        
        # Verify the update
        verify = get_user_by_tid(tid) or {}
        
        message = f"""✅ **USER FIELD UPDATED**

👤 **User ID:** {tid}
🔧 **Field:** {field}
📝 **Value:** {value}
🔄 **Applied:** {payload[field]}

📊 **Current User Data:**
💎 Premium: {verify.get('is_premium', False)}
📅 Until: {verify.get('premium_until', 'None')[:10] if verify.get('premium_until') else 'None'}
💳 Credits: {verify.get('credits', 0)}
🚫 Banned: {verify.get('banned', False)}

✅ **Update successful!**"""
        
        await safe_reply(update.effective_message, message)
        
    except Exception as e:
        await safe_reply(update.effective_message, f"❌ **Failed to update field:** {str(e)}")
