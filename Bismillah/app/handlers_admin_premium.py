from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from datetime import datetime, timezone, timedelta
from app.supabase_conn import get_supabase_client
from app.users_repo import get_user_by_telegram_id, set_premium, revoke_premium
from app.lib.guards import admin_guard
from app.safe_send import safe_reply
import asyncio

# Global lock for preventing concurrent premium operations
_locks = {}

def _lock(user_id):
    if user_id not in _locks:
        _locks[user_id] = asyncio.Lock()
    return _locks[user_id]

@admin_guard
async def cmd_set_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if len(context.args) != 2:
        return await safe_reply(msg, "Format: /setpremium <userid> <30d|lifetime>")

    user_arg, dur_arg = context.args
    if not user_arg.isdigit():
        return await safe_reply(msg, "User ID harus berupa angka")

    tid = int(user_arg)

    try:
        async with _lock(tid):
            if dur_arg.lower() == "lifetime":
                # Set lifetime premium
                updated_user = set_premium(tid, lifetime=True)
                
                # Verify the change
                verify_user = get_user_by_telegram_id(tid)
                if verify_user and verify_user.get('is_premium') and verify_user.get('is_lifetime'):
                    return await safe_reply(msg, 
                        f"✅ Premium LIFETIME set untuk user {tid}\n"
                        f"📊 Status: is_premium={verify_user.get('is_premium')}, "
                        f"is_lifetime={verify_user.get('is_lifetime')}")
                else:
                    return await safe_reply(msg, f"❌ Failed to verify lifetime premium for user {tid}")
            else:
                # Parse days (support "30d" or "30" format)
                days_str = dur_arg.replace('d', '')
                if not days_str.isdigit() or int(days_str) < 1:
                    return await safe_reply(msg, "Format: angka positif atau 'lifetime'\nContoh: 30d, 30, lifetime")

                days = int(days_str)
                
                # Set timed premium
                updated_user = set_premium(tid, lifetime=False, days=days)
                
                # Verify the change
                verify_user = get_user_by_telegram_id(tid)
                if verify_user and verify_user.get('is_premium'):
                    premium_until = verify_user.get('premium_until', 'N/A')
                    return await safe_reply(msg, 
                        f"✅ Premium {days} hari set untuk user {tid}\n"
                        f"📊 Status: is_premium={verify_user.get('is_premium')}\n"
                        f"Berlaku sampai: {premium_until}")
                else:
                    return await safe_reply(msg, f"❌ Failed to verify {days}d premium for user {tid}")

    except Exception as e:
        print(f"❌ Error in cmd_set_premium: {e}")
        import traceback
        traceback.print_exc()
        return await safe_reply(msg, f"❌ Error setpremium: {str(e)}")

# Add command to manually verify premium status
@admin_guard
async def cmd_verify_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if len(context.args) != 1 or not context.args[0].isdigit():
        return await safe_reply(msg, "Format: /verify_premium <userid>")

    tid = int(context.args[0])

    try:
        s = get_supabase_client()
        result = s.table("users").select("telegram_id, first_name, username, is_premium, is_lifetime, premium_until, credits").eq("telegram_id", tid).execute()
        
        if not result.data:
            return await safe_reply(msg, f"❌ User {tid} tidak ditemukan di database")

        user = result.data[0]
        
        status_msg = f"""🔍 **Verifikasi Premium User {tid}**

👤 **User Info:**
• Name: {user.get('first_name', 'N/A')}
• Username: @{user.get('username', 'N/A')}
• Credits: {user.get('credits', 0)}

🏆 **Premium Status:**
• is_premium: {user.get('is_premium')}
• is_lifetime: {user.get('is_lifetime')}
• premium_until: {user.get('premium_until')}

📊 **Raw Data:** `{user}`"""

        return await safe_reply(msg, status_msg)

    except Exception as e:
        return await safe_reply(msg, f"❌ Error verify premium: {str(e)}")

@admin_guard
async def cmd_revoke_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if len(context.args) != 1 or not context.args[0].isdigit():
        return await safe_reply(msg, "Format: /revoke_premium <userid>")

    tid = int(context.args[0])

    try:
        async with _lock(tid):
            # Check if user exists
            existing = get_user_by_telegram_id(tid)
            if not existing:
                return await safe_reply(msg, f"❌ User {tid} tidak ditemukan")

            # Revoke premium using repo function
            updated_user = revoke_premium(tid)

            # Verify revocation
            verify_user = get_user_by_telegram_id(tid)
            if verify_user and not verify_user.get("is_premium"):
                return await safe_reply(msg, 
                    f"✅ Premium REVOKED untuk user {tid}\n"
                    f"📊 Status: is_premium={verify_user.get('is_premium')}, "
                    f"is_lifetime={verify_user.get('is_lifetime')}")
            else:
                return await safe_reply(msg, f"❌ Gagal revoke premium untuk user {tid}")

    except Exception as e:
        return await safe_reply(msg, f"❌ Error revoke premium: {str(e)}")

@admin_guard
async def cmd_grant_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if len(context.args) != 2 or not context.args[0].isdigit() or not context.args[1].isdigit():
        return await safe_reply(msg, "Format: /grant_credits <userid> <amount>")

    tid = int(context.args[0])
    amount = int(context.args[1])

    try:
        async with _lock(tid):
            # Get current credits
            current_user = get_user_by_telegram_id(tid) or {}
            current_credits = current_user.get("credits", 0)
            new_credits = current_credits + amount

            # Update credits using Supabase
            s = get_supabase_client()
            s.table("users").update({"credits": new_credits}).eq("telegram_id", tid).execute()

            # Verify
            ref = get_user_by_telegram_id(tid) or {}
            if ref.get("credits", 0) >= new_credits:
                return await safe_reply(msg, f"✅ Credits granted: {amount} to user {tid}\nNew total: {ref.get('credits', 0)}")
            else:
                return await safe_reply(msg, f"❌ Failed to grant credits.\nTerbaca: {ref}")

    except Exception as e:
        return await safe_reply(msg, f"❌ Error grant credits: {e}")