
import os
from telegram import Update
from telegram.ext import ContextTypes
from app.supabase_repo import ensure_user_exists, set_premium, revoke_premium, get_user_by_tid

def _admin_ids() -> set[int]:
    ids = set()
    for key in ("ADMIN1", "ADMIN2", "ADMIN"):
        val = os.getenv(key)
        if val and val.strip().isdigit():
            ids.add(int(val.strip()))
    return ids

def _is_admin(user_id: int) -> bool:
    return user_id in _admin_ids()

def _parse_duration(token: str) -> tuple[str, int]:
    """
    'lifetime' -> ('lifetime', 0)
    '30d' or '30' -> ('days', 30)
    '2m' -> ('months', 2)  (opsional, kalau mau dukung format ini)
    """
    t = token.strip().lower()
    if t == "lifetime":
        return ("lifetime", 0)
    if t.endswith("d"):
        n = int(t[:-1])
        return ("days", n)
    if t.endswith("m"):
        n = int(t[:-1])
        return ("months", n)
    # default: anggap hari
    return ("days", int(t))

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

    try:
        dtype, dval = _parse_duration(context.args[1])
    except Exception:
        await update.message.reply_text("❌ Format durasi tidak valid.")
        return

    try:
        # pastikan user ada meskipun belum /start
        ensure_user_exists(tg_id)
        row = set_premium(tg_id, dtype, dval)
        until = row.get("premium_until", "null")
        
        message = f"✅ Premium diaktifkan untuk user {tg_id}\n\n"
        message += f"📊 **Details:**\n"
        message += f"• **Type**: {dtype}\n"
        message += f"• **Value**: {dval}\n"
        message += f"• **Lifetime**: {row.get('is_lifetime')}\n"
        message += f"• **Premium**: {row.get('is_premium')}\n"
        message += f"• **Until**: {until}\n\n"
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
        row = revoke_premium(tg_id)
        
        message = f"✅ Premium dicabut untuk user {tg_id}\n\n"
        message += f"📊 **Status sekarang:**\n"
        message += f"• **Premium**: {row.get('is_premium')}\n"
        message += f"• **Lifetime**: {row.get('is_lifetime')}\n"
        message += f"• **Until**: {row.get('premium_until')}"
        
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
    
    row = get_user_by_tid(tg_id) or {}
    
    message = f"👤 **User Info (Supabase)**\n\n"
    message += f"🆔 **User ID**: {tg_id}\n"
    message += f"👤 **Name**: {row.get('first_name', 'Unknown')}\n"
    message += f"📧 **Username**: @{row.get('username', 'no_username')}\n"
    message += f"⭐ **Premium**: {row.get('is_premium', False)}\n"
    message += f"💎 **Lifetime**: {row.get('is_lifetime', False)}\n"
    message += f"📅 **Until**: {row.get('premium_until', 'N/A')}\n"
    message += f"💳 **Credits**: {row.get('credits', 0)}\n"
    message += f"📊 **In Database**: {'✅ Yes' if row else '❌ No'}"
    
    await update.message.reply_text(message)
