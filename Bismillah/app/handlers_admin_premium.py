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
            # Check if user exists before setting premium
            existing_user = get_user_by_telegram_id(tid)
            user_status = "existing" if existing_user else "new"
            
            if dur_arg.lower() == "lifetime":
                # Use direct set_premium function with auto-create
                success = set_premium(tid, lifetime=True)
                
                if success:
                    status_msg = "✅ **Premium LIFETIME berhasil di-set!**\n\n"
                    status_msg += f"👤 **User ID**: {tid}\n"
                    status_msg += f"📊 **Status**: {'User sudah ada' if user_status == 'existing' else '🆕 User baru dibuat otomatis'}\n"
                    status_msg += f"💎 **Premium**: LIFETIME (unlimited)\n"
                    status_msg += f"🎯 **Auto Signals**: ✅ Enabled\n\n"
                    if user_status == "new":
                        status_msg += "ℹ️ User akan mendapat nama placeholder sampai mereka /start"
                    return await safe_reply(msg, status_msg)
                else:
                    return await safe_reply(msg, f"❌ Gagal set premium lifetime untuk user {tid}")
            else:
                # Parse days (support "30d" or "30" format)
                days_str = dur_arg.replace('d', '')
                if not days_str.isdigit() or int(days_str) < 1:
                    return await safe_reply(msg, "Format: angka positif atau 'lifetime'\nContoh: 30d, 30, lifetime")

                days = int(days_str)
                
                # Use direct set_premium function with auto-create
                success = set_premium(tid, lifetime=False, days=days)
                
                if success:
                    # Calculate expiry date for display
                    expiry_date = (datetime.utcnow() + timedelta(days=days)).strftime('%d %B %Y - %H:%M WIB')
                    
                    status_msg = f"✅ **Premium {days} hari berhasil di-set!**\n\n"
                    status_msg += f"👤 **User ID**: {tid}\n"
                    status_msg += f"📊 **Status**: {'User sudah ada' if user_status == 'existing' else '🆕 User baru dibuat otomatis'}\n"
                    status_msg += f"💎 **Premium**: {days} hari\n"
                    status_msg += f"📅 **Berlaku sampai**: {expiry_date}\n\n"
                    if user_status == "new":
                        status_msg += "ℹ️ User akan mendapat nama placeholder sampai mereka /start"
                    return await safe_reply(msg, status_msg)
                else:
                    return await safe_reply(msg, f"❌ Gagal set premium {days} hari untuk user {tid}")

    except Exception as e:
        return await safe_reply(msg, f"❌ Error setpremium: {str(e)}")
        import traceback
        traceback.print_exc()

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
            success = revoke_premium(tid)

            if success:
                # Verify revocation
                updated_user = get_user_by_telegram_id(tid)
                if updated_user and not updated_user.get("is_premium"):
                    return await safe_reply(msg, f"✅ Premium REVOKED untuk user {tid}")
                else:
                    return await safe_reply(msg, f"❌ Revocation verification failed untuk user {tid}")
            else:
                return await safe_reply(msg, f"❌ Gagal revoke premium untuk user {tid}")

    except Exception as e:
        return await safe_reply(msg, f"❌ Error revoke premium: {str(e)}")

@admin_guard  
async def cmd_remove_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remove_premium command (alias for revoke_premium)"""
    # Just call the revoke_premium handler
    await cmd_revoke_premium(update, context)

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