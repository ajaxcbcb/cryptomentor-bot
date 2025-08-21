import os
from telegram import Update
from telegram.ext import ContextTypes
from app.supabase_repo import ensure_user_exists, set_premium_normalized, revoke_premium, get_user_by_tid, get_vuser_by_tid

def _admin_ids() -> set[int]:
    ids = set()
    for key in ("ADMIN_IDS", "ADMIN1", "ADMIN2", "ADMIN"):
        raw = os.getenv(key, "")
        if not raw: 
            continue
        for tok in raw.replace(";", ",").replace(" ", "").split(","):
            if tok.isdigit():
                ids.add(int(tok))
    return ids

def _is_admin(user_id: int) -> bool:
    return user_id in _admin_ids()

async def cmd_setpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_admin(uid):
        await update.message.reply_text(f"❌ Admin only. Your ID: {uid}")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setpremium <telegram_id> <lifetime|<days>d|<days>|<months>m>")
        return

    try:
        tg_id = int(context.args[0])
    except Exception:
        await update.message.reply_text("❌ ID tidak valid.")
        return

    duration_token = context.args[1]

    try:
        # Pastikan user ada meskipun belum /start
        ensure_user_exists(tg_id)
        v = set_premium_normalized(tg_id, duration_token)

        message = f"✅ Premium updated for user {tg_id}\n\n"
        message += f"📊 **Details:**\n"
        message += f"• **Premium**: {v.get('is_premium')}\n"
        message += f"• **Lifetime**: {v.get('is_lifetime')}\n"
        message += f"• **Active**: {v.get('premium_active')}\n"
        message += f"• **Until**: {v.get('premium_until', 'N/A')}\n\n"
        message += f"💡 User dapat langsung menggunakan fitur premium tanpa perlu /start"

        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"⚠️ setpremium failed: {e}")

async def cmd_revoke_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_admin(uid):
        await update.message.reply_text(f"❌ Admin only. Your ID: {uid}")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /revoke_premium <telegram_id>")
        return

    try:
        tg_id = int(context.args[0])
    except Exception:
        await update.message.reply_text("❌ ID tidak valid.")
        return

    try:
        ensure_user_exists(tg_id)  # kalau belum ada, buat dulu lalu revoke = tetap non-premium
        v = revoke_premium(tg_id)

        message = f"✅ Premium revoked for user {tg_id}\n\n"
        message += f"📊 **Status sekarang:**\n"
        message += f"• **Premium**: {v.get('is_premium')}\n"
        message += f"• **Lifetime**: {v.get('is_lifetime')}\n"
        message += f"• **Active**: {v.get('premium_active')}\n"
        message += f"• **Until**: {v.get('premium_until')}"

        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"⚠️ revoke_premium failed: {e}")

async def cmd_whois(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /whois <telegram_id>")
        return

    try:
        tg_id = int(context.args[0])
    except Exception:
        await update.message.reply_text("❌ ID tidak valid.")
        return

    v = get_vuser_by_tid(tg_id) or {}

    message = f"👤 **User Info (v_users)**\n\n"
    message += f"🆔 **User ID**: {tg_id}\n"
    message += f"👤 **Name**: {v.get('first_name', 'Unknown')}\n"
    message += f"📧 **Username**: @{v.get('username', 'no_username')}\n"
    message += f"⭐ **Premium**: {v.get('is_premium', False)}\n"
    message += f"💎 **Lifetime**: {v.get('is_lifetime', False)}\n"
    message += f"🔥 **Active**: {v.get('premium_active', False)}\n"
    message += f"📅 **Until**: {v.get('premium_until', 'N/A')}\n"
    message += f"💳 **Credits**: {v.get('credits', 0)}\n"
    message += f"📊 **In Database**: {'✅ Yes' if v else '❌ No'}"

    await update.message.reply_text(message)