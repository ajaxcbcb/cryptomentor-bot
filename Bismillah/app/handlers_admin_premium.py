
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta, timezone
from app.lib.guards import admin_guard
from app.safe_send import safe_reply
from app.supabase_conn import upsert_user_tid, update_user_tid, get_user_by_tid

def _iso_days_from_now(days: int) -> str:
    """Calculate ISO timestamp for days from now"""
    return (datetime.now(timezone.utc) + timedelta(days=int(days))).isoformat()

@admin_guard
async def cmd_setpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set premium status for user"""
    args = context.args
    if len(args) != 2 or not args[0].isdigit():
        return await safe_reply(update.effective_message, 
            "❌ **Format:** `/setpremium <userid> <days|lifetime>`\n\n"
            "**Examples:**\n"
            "• `/setpremium 123456789 30` - 30 days premium\n"
            "• `/setpremium 123456789 lifetime` - Lifetime premium"
        )
    
    tid = int(args[0])
    dur = args[1].lower()
    
    try:
        if dur == "lifetime":
            result = upsert_user_tid(tid, is_premium=True, premium_until=None, banned=False)
            status = "✅ **LIFETIME PREMIUM SET**"
        else:
            if not dur.isdigit() or int(dur) < 0:
                return await safe_reply(update.effective_message, "❌ Days must be number ≥ 0 or 'lifetime'")
            
            until = _iso_days_from_now(int(dur))
            result = upsert_user_tid(tid, is_premium=True, premium_until=until, banned=False)
            status = f"✅ **{dur} DAYS PREMIUM SET**"
        
        # Verify the update
        verify = get_user_by_tid(tid) or {}
        premium_until = verify.get("premium_until")
        if premium_until:
            until_date = premium_until[:10]  # Just date part
            premium_info = f"Until: {until_date}"
        else:
            premium_info = "LIFETIME"
        
        message = f"""{status}

👤 **User ID:** {tid}
💎 **Premium:** {verify.get('is_premium', False)}
📅 **{premium_info}**
💳 **Credits:** {verify.get('credits', 0)}
🚫 **Banned:** {verify.get('banned', False)}

✅ **Update successful!**"""
        
        await safe_reply(update.effective_message, message)
        
    except Exception as e:
        await safe_reply(update.effective_message, f"❌ **Failed to set premium:** {str(e)}")

@admin_guard
async def cmd_remove_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove premium status from user"""
    if not context.args or not context.args[0].isdigit():
        return await safe_reply(update.effective_message, 
            "❌ **Format:** `/remove_premium <userid>`\n\n"
            "**Example:** `/remove_premium 123456789`"
        )
    
    tid = int(context.args[0])
    
    try:
        update_user_tid(tid, is_premium=False, premium_until=None)
        
        # Verify the update
        verify = get_user_by_tid(tid) or {}
        
        message = f"""✅ **PREMIUM REMOVED**

👤 **User ID:** {tid}
💎 **Premium:** {verify.get('is_premium', False)}
📅 **Until:** None
💳 **Credits:** {verify.get('credits', 0)}

✅ **Update successful!**"""
        
        await safe_reply(update.effective_message, message)
        
    except Exception as e:
        await safe_reply(update.effective_message, f"❌ **Failed to remove premium:** {str(e)}")

@admin_guard
async def cmd_grant_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grant credits to user"""
    if len(context.args) != 2 or not context.args[0].isdigit() or not context.args[1].isdigit():
        return await safe_reply(update.effective_message, 
            "❌ **Format:** `/grant_credits <userid> <amount>`\n\n"
            "**Example:** `/grant_credits 123456789 100`"
        )
    
    tid = int(context.args[0])
    amount = int(context.args[1])
    
    try:
        # Get current credits
        current = get_user_by_tid(tid) or {}
        old_credits = int(current.get("credits", 0))
        
        # Add credits
        total = old_credits + amount
        upsert_user_tid(tid, credits=total)
        
        # Verify the update
        verify = get_user_by_tid(tid) or {}
        new_credits = verify.get("credits", 0)
        
        message = f"""✅ **CREDITS GRANTED**

👤 **User ID:** {tid}
💳 **Credits Added:** +{amount}
📊 **Old Credits:** {old_credits}
📊 **New Credits:** {new_credits}

✅ **Update successful!**"""
        
        await safe_reply(update.effective_message, message)
        
    except Exception as e:
        await safe_reply(update.effective_message, f"❌ **Failed to grant credits:** {str(e)}")
