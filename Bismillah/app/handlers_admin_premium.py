
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
        print(f"🔄 Setting premium for user {tid}, duration: {dur}")
        
        # Check user exists first
        existing_user = get_user_by_tid(tid)
        print(f"📊 Existing user data: {existing_user}")
        
        if dur == "lifetime":
            print("🔄 Setting lifetime premium...")
            result = upsert_user_tid(tid, is_premium=True, premium_until=None, banned=False)
            status = "✅ **LIFETIME PREMIUM SET**"
        else:
            if not dur.isdigit() or int(dur) < 0:
                return await safe_reply(update.effective_message, "❌ Days must be number ≥ 0 or 'lifetime'")
            
            until = _iso_days_from_now(int(dur))
            print(f"🔄 Setting {dur} days premium until: {until}")
            result = upsert_user_tid(tid, is_premium=True, premium_until=until, banned=False)
            status = f"✅ **{dur} DAYS PREMIUM SET**"
        
        print(f"📝 Upsert result: {result}")
        
        # Wait a moment and verify the update
        import time
        time.sleep(1)
        
        verify = get_user_by_tid(tid)
        print(f"🔍 Verification result: {verify}")
        
        if not verify:
            return await safe_reply(update.effective_message, "❌ **Failed to verify user after update**")
        
        # Double check the premium status
        is_premium = verify.get('is_premium', False)
        premium_until = verify.get("premium_until")
        
        if premium_until:
            try:
                until_date = premium_until[:10]  # Just date part
                premium_info = f"Until: {until_date}"
            except:
                premium_info = f"Until: {premium_until}"
        else:
            premium_info = "LIFETIME"
        
        # Get fresh premium count to show impact
        from app.supabase_conn import sb_get_premium_count
        counts = sb_get_premium_count()
        
        message = f"""{status}

👤 **User ID:** {tid}
💎 **Premium:** {is_premium}
📅 **{premium_info}**
💳 **Credits:** {verify.get('credits', 0)}
🚫 **Banned:** {verify.get('banned', False)}

📊 **Current Premium Count:**
🔓 Lifetime: {counts.get('lifetime', 0)}
⏰ Timed: {counts.get('timed', 0)}
📈 Total: {counts.get('total', 0)}

✅ **Update successful!**"""
        
        await safe_reply(update.effective_message, message)
        
    except Exception as e:
        error_msg = f"❌ **Failed to set premium:** {str(e)}"
        print(f"❌ SetPremium Error: {e}")
        import traceback
        traceback.print_exc()
        await safe_reply(update.effective_message, error_msg)

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
