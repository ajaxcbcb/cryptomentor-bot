from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from datetime import datetime, timedelta, timezone
import asyncio

from app.lib.guards import admin_guard
from app.safe_send import safe_reply
from app.supabase_conn import get_supabase_client
from app.users_repo import get_user_by_telegram_id


_locks = {}
def _lock(uid: int) -> asyncio.Lock:
    if uid not in _locks:
        _locks[uid] = asyncio.Lock()
    return _locks[uid]

def _iso_days_from_now(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=int(days))).isoformat()

@admin_guard
async def cmd_setpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    
    # Parse arguments - support both "30d" and "30" format
    if len(context.args) != 2 or not context.args[0].isdigit():
        return await safe_reply(msg, "Format: /setpremium <userid> <30d|lifetime>")
    
    tid = int(context.args[0])
    dur_arg = context.args[1].lower().strip()

    async with _lock(tid):
        try:
            s = get_supabase_client()
            
            # Ensure user exists first
            existing = get_user_by_telegram_id(tid)
            if not existing:
                # Create user if doesn't exist
                insert_data = {
                    "telegram_id": tid,
                    "username": f"user_{tid}",
                    "first_name": "Unknown",
                    "is_premium": False,
                    "is_lifetime": False,
                    "credits": 100
                }
                s.table("users").insert(insert_data).execute()
                print(f"✅ Created new user {tid} for premium upgrade")

            if dur_arg == "lifetime":
                # Set lifetime premium
                update_data = {
                    "is_premium": True,
                    "is_lifetime": True,
                    "premium_until": None
                }
            else:
                # Parse days (support "30d" or "30" format)
                days_str = dur_arg.replace('d', '')
                if not days_str.isdigit() or int(days_str) < 0:
                    return await safe_reply(msg, "Format days: angka positif atau 'lifetime'\nContoh: 30d, 30, lifetime")
                
                days = int(days_str)
                premium_until = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
                
                update_data = {
                    "is_premium": True,
                    "is_lifetime": False,
                    "premium_until": premium_until
                }

            # Update user premium status
            result = s.table("users").update(update_data).eq("telegram_id", tid).execute()
            
            if not result.data:
                return await safe_reply(msg, f"❌ Failed to update user {tid}")

            # Verify update
            updated_user = get_user_by_telegram_id(tid)
            if updated_user and updated_user.get("is_premium"):
                if dur_arg == "lifetime":
                    return await safe_reply(msg, f"✅ Premium LIFETIME set untuk user {tid}")
                else:
                    return await safe_reply(msg, f"✅ Premium {days_str} hari set untuk user {tid}\nBerlaku sampai: {updated_user.get('premium_until', 'N/A')}")
            else:
                return await safe_reply(msg, f"❌ Verification failed untuk user {tid}")

        except Exception as e:
            return await safe_reply(msg, f"❌ Error setpremium: {e}")

@admin_guard
async def cmd_revoke_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if len(context.args) != 1 or not context.args[0].isdigit():
        return await safe_reply(msg, "Format: /revoke_premium <userid>")

    tid = int(context.args[0])

    try:
        async with _lock(tid):
            s = get_supabase_client()
            
            # Check if user exists
            existing = get_user_by_telegram_id(tid)
            if not existing:
                return await safe_reply(msg, f"❌ User {tid} tidak ditemukan")

            # Remove premium status
            update_data = {
                "is_premium": False,
                "is_lifetime": False,
                "premium_until": None
            }
            
            result = s.table("users").update(update_data).eq("telegram_id", tid).execute()
            
            if not result.data:
                return await safe_reply(msg, f"❌ Failed to revoke premium untuk user {tid}")

            # Verify
            updated_user = get_user_by_telegram_id(tid)
            if updated_user and not updated_user.get("is_premium"):
                return await safe_reply(msg, f"✅ Premium berhasil di-revoke untuk user {tid}")
            else:
                return await safe_reply(msg, f"❌ Verification failed untuk user {tid}")

    except Exception as e:
        return await safe_reply(msg, f"❌ Error revoke premium: {e}")

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