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
            s = get_supabase_client()
            
            # First ensure user exists
            existing_user = s.table("users").select("*").eq("telegram_id", tid).limit(1).execute()
            if not existing_user.data:
                # Create user first if doesn't exist
                s.table("users").insert({
                    "telegram_id": tid,
                    "first_name": f"User{tid}",
                    "username": None,
                    "credits": 100,
                    "is_premium": False,
                    "is_lifetime": False
                }).execute()
                print(f"✅ Created new user {tid}")

            # Parse duration and set premium using RPC
            if dur_arg.lower() == "lifetime":
                # Call RPC with lifetime
                result = s.rpc("set_premium", {
                    "p_telegram_id": tid,
                    "p_duration_type": "lifetime",
                    "p_duration_value": 0
                }).execute()
                
                print(f"🔍 RPC set_premium result for lifetime: {result.data}")
                
                if result.data and result.data.get('success'):
                    # Verify the change
                    verify = s.table("users").select("is_premium, is_lifetime, premium_until").eq("telegram_id", tid).execute()
                    if verify.data:
                        user = verify.data[0]
                        status = f"is_premium={user.get('is_premium')}, is_lifetime={user.get('is_lifetime')}, premium_until={user.get('premium_until')}"
                        return await safe_reply(msg, f"✅ Premium LIFETIME set untuk user {tid}\n📊 Status: {status}")
                    else:
                        return await safe_reply(msg, f"✅ Premium LIFETIME set untuk user {tid} (verification failed)")
                else:
                    error = result.data.get('error', 'Unknown error') if result.data else 'No response'
                    return await safe_reply(msg, f"❌ Failed to set lifetime premium: {error}\nRPC Response: {result.data}")
            else:
                # Parse days (support "30d" or "30" format)
                days_str = dur_arg.replace('d', '')
                if not days_str.isdigit() or int(days_str) < 1:
                    return await safe_reply(msg, "Format: angka positif atau 'lifetime'\nContoh: 30d, 30, lifetime")

                days = int(days_str)
                
                # Call RPC with days
                result = s.rpc("set_premium", {
                    "p_telegram_id": tid,
                    "p_duration_type": "days",
                    "p_duration_value": days
                }).execute()
                
                print(f"🔍 RPC set_premium result for {days}d: {result.data}")
                
                if result.data and result.data.get('success'):
                    premium_until = result.data.get('premium_until', 'N/A')
                    # Verify the change
                    verify = s.table("users").select("is_premium, is_lifetime, premium_until").eq("telegram_id", tid).execute()
                    if verify.data:
                        user = verify.data[0]
                        status = f"is_premium={user.get('is_premium')}, premium_until={user.get('premium_until')}"
                        return await safe_reply(msg, f"✅ Premium {days} hari set untuk user {tid}\n📊 Status: {status}\nBerlaku sampai: {premium_until}")
                    else:
                        return await safe_reply(msg, f"✅ Premium {days} hari set untuk user {tid}\nBerlaku sampai: {premium_until}")
                else:
                    error = result.data.get('error', 'Unknown error') if result.data else 'No response'
                    return await safe_reply(msg, f"❌ Failed to set {days}d premium: {error}\nRPC Response: {result.data}")

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
            revoke_premium(tid)

            # Verify revocation
            updated_user = get_user_by_telegram_id(tid)
            if updated_user and not updated_user.get("is_premium"):
                return await safe_reply(msg, f"✅ Premium REVOKED untuk user {tid}")
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