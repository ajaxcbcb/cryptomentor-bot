
"""
Router cepat untuk verifikasi koneksi Supabase dan testing command.
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import os
from typing import Optional

# Import fungsi dari users_repo
from app.users_repo import (
    ensure_user_registered, get_user_by_telegram_id,
    set_premium, revoke_premium, set_credits,
    stats_totals, is_premium_active
)
from app.supabase_conn import health

# Admin check
ADMINS = {int(x.strip()) for x in (os.getenv("ADMIN_IDS", "").split(",") if os.getenv("ADMIN_IDS") else [])}

def _admin(uid: int) -> bool:
    return uid in ADMINS

def _parse_ref(text: str) -> Optional[int]:
    """Parse referral ID from command text"""
    if not text:
        return None
    parts = text.split(maxsplit=1)
    if len(parts) == 2:
        try:
            return int(parts[1])
        except:
            return None
    return None

async def diag_supabase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Diagnostic command untuk check Supabase connection"""
    ok, detail = health()
    tot = prem = 0
    if ok:
        try:
            tot, prem = stats_totals()
        except Exception as e:
            detail = f"stats_totals error: {e}"
    
    message = f"""🔧 **Supabase Diagnostic**

**Connection**: {'✅ Connected' if ok else '❌ Failed'}
**Details**: {detail}
**Total Users**: {tot}
**Premium Users**: {prem}"""

    await update.message.reply_text(message, parse_mode='Markdown')

async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current user info from database"""
    user_id = update.effective_user.id
    row = get_user_by_telegram_id(user_id) or {}
    
    message = f"""👤 **Your Database Info**

**Credits**: {row.get('credits', '—')}
**Premium**: {row.get('is_premium', False)}
**Lifetime**: {row.get('is_lifetime', False)}
**Premium Until**: {row.get('premium_until', 'N/A')}
**Active Premium**: {is_premium_active(user_id)}"""

    await update.message.reply_text(message, parse_mode='Markdown')

async def setpremium_quick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick setpremium command for testing"""
    uid = update.effective_user.id
    if not _admin(uid):
        await update.message.reply_text(f"❌ Admin only. Your ID: {uid}")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "**Usage**: `/setpremium <telegram_id> <lifetime|days|months> [value]`\n\n"
            "**Examples**:\n"
            "• `/setpremium 123456789 lifetime`\n"
            "• `/setpremium 123456789 days 30`\n"
            "• `/setpremium 123456789 months 3`",
            parse_mode='Markdown'
        )
        return

    try:
        tg_id = int(context.args[0])
        dtype = context.args[1].lower()
        dval = int(context.args[2]) if len(context.args) >= 3 and dtype in ("days", "months") else 0
        
        set_premium(tg_id, dtype, dval)
        row = get_user_by_telegram_id(tg_id) or {}
        
        await update.message.reply_text(
            f"✅ **Premium Set Successfully**\n\n"
            f"**User ID**: {tg_id}\n"
            f"**Premium**: {row.get('is_premium')}\n"
            f"**Lifetime**: {row.get('is_lifetime')}\n"
            f"**Until**: {row.get('premium_until')}",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ setpremium failed: {e}")

async def revoke_premium_quick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick revoke premium command"""
    uid = update.effective_user.id
    if not _admin(uid):
        await update.message.reply_text(f"❌ Admin only. Your ID: {uid}")
        return

    if len(context.args) < 1:
        await update.message.reply_text("**Usage**: `/revoke_premium <telegram_id>`", parse_mode='Markdown')
        return

    try:
        tg_id = int(context.args[0])
        revoke_premium(tg_id)
        row = get_user_by_telegram_id(tg_id) or {}
        
        await update.message.reply_text(
            f"✅ **Premium Revoked**\n\n"
            f"**User ID**: {tg_id}\n"
            f"**Premium**: {row.get('is_premium')}\n"
            f"**Lifetime**: {row.get('is_lifetime')}\n"
            f"**Until**: {row.get('premium_until')}",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ revoke failed: {e}")

async def setcredits_quick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick set credits command"""
    uid = update.effective_user.id
    if not _admin(uid):
        await update.message.reply_text(f"❌ Admin only. Your ID: {uid}")
        return

    if len(context.args) < 2:
        await update.message.reply_text("**Usage**: `/setcredits <telegram_id> <amount>`", parse_mode='Markdown')
        return

    try:
        tg_id = int(context.args[0])
        amount = int(context.args[1])
        
        set_credits(tg_id, amount)
        row = get_user_by_telegram_id(tg_id) or {}
        
        await update.message.reply_text(
            f"✅ **Credits Set**\n\n"
            f"**User ID**: {tg_id}\n"
            f"**Amount**: {amount}\n"
            f"**Current Credits**: {row.get('credits')}",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ setcredits failed: {e}")

# Command handlers untuk registrasi
def get_handlers():
    """Return list of command handlers"""
    return [
        CommandHandler("diag_supabase", diag_supabase),
        CommandHandler("me", me_command),
        CommandHandler("setpremium_quick", setpremium_quick),
        CommandHandler("revoke_premium_quick", revoke_premium_quick),
        CommandHandler("setcredits_quick", setcredits_quick),
    ]
