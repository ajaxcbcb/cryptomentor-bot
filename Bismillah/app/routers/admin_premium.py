
import os
from telegram import Update
from telegram.ext import ContextTypes
from app.supabase_repo import ensure_user_exists, set_premium_normalized, revoke_premium, get_vuser_by_tid

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

def _is_admin(uid: int) -> bool:
    return uid in _admin_ids()

async def cmd_setpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setpremium command with duration normalization"""
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_admin(uid):
        await update.message.reply_text(f"❌ Admin only. Your ID: {uid}")
        return

    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "❌ **Usage:** `/setpremium <telegram_id> <duration>`\n\n"
            "**Duration formats:**\n"
            "• `lifetime` - Lifetime premium\n"
            "• `30d` or `30` - 30 days\n"
            "• `2m` - 2 months\n\n"
            "**Examples:**\n"
            "• `/setpremium 123456789 lifetime`\n"
            "• `/setpremium 123456789 30d`\n"
            "• `/setpremium 123456789 2m`",
            parse_mode='Markdown'
        )
        return

    try:
        tg_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Telegram ID must be a number!")
        return

    duration = args[1]

    try:
        # Ensure user exists even if they haven't /start
        ensure_user_exists(tg_id)
        
        # Set premium with normalized duration
        v = set_premium_normalized(tg_id, duration)
        
        premium_status = "✅ ACTIVE" if v.get('premium_active') else "❌ INACTIVE"
        lifetime_status = "🌟 LIFETIME" if v.get('is_lifetime') else "⏰ TIMED"
        
        await update.message.reply_text(
            f"✅ **Premium updated successfully!**\n\n"
            f"👤 **User ID**: `{tg_id}`\n"
            f"📊 **Premium Status**: {premium_status}\n"
            f"💎 **Type**: {lifetime_status}\n"
            f"📅 **Until**: {v.get('premium_until') or 'No expiry'}\n\n"
            f"🔍 **Raw Data:**\n"
            f"• is_premium: {v.get('is_premium')}\n"
            f"• is_lifetime: {v.get('is_lifetime')}\n"
            f"• premium_active: {v.get('premium_active')}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ **setpremium failed:** {str(e)}")

async def cmd_revoke_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /revoke_premium command"""
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_admin(uid):
        await update.message.reply_text(f"❌ Admin only. Your ID: {uid}")
        return

    args = context.args or []
    if len(args) < 1:
        await update.message.reply_text(
            "❌ **Usage:** `/revoke_premium <telegram_id>`\n\n"
            "**Example:** `/revoke_premium 123456789`",
            parse_mode='Markdown'
        )
        return
        
    try:
        tg_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Telegram ID must be a number!")
        return

    try:
        v = revoke_premium(tg_id)
        
        await update.message.reply_text(
            f"✅ **Premium revoked successfully!**\n\n"
            f"👤 **User ID**: `{tg_id}`\n"
            f"📊 **Premium Status**: ❌ REVOKED\n\n"
            f"🔍 **Raw Data:**\n"
            f"• is_premium: {v.get('is_premium')}\n"
            f"• is_lifetime: {v.get('is_lifetime')}\n"
            f"• premium_active: {v.get('premium_active')}\n"
            f"• premium_until: {v.get('premium_until')}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ **revoke_premium failed:** {str(e)}")

async def cmd_whois(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /whois command to check user status from v_users"""
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_admin(uid):
        await update.message.reply_text(f"❌ Admin only. Your ID: {uid}")
        return

    args = context.args or []
    if len(args) < 1:
        await update.message.reply_text(
            "❌ **Usage:** `/whois <telegram_id>`\n\n"
            "**Example:** `/whois 123456789`",
            parse_mode='Markdown'
        )
        return
        
    try:
        tg_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Telegram ID must be a number!")
        return

    try:
        v = get_vuser_by_tid(tg_id) or {}
        
        if not v:
            await update.message.reply_text(f"❌ User {tg_id} not found in database")
            return
            
        premium_status = "✅ ACTIVE" if v.get('premium_active') else "❌ INACTIVE"
        lifetime_status = "🌟 LIFETIME" if v.get('is_lifetime') else "⏰ TIMED"
        
        await update.message.reply_text(
            f"👤 **User Status from v_users**\n\n"
            f"🆔 **Telegram ID**: `{tg_id}`\n"
            f"👤 **Name**: {v.get('first_name', 'Unknown')}\n"
            f"📊 **Premium Status**: {premium_status}\n"
            f"💎 **Type**: {lifetime_status}\n"
            f"💳 **Credits**: {v.get('credits', 0)}\n"
            f"📅 **Premium Until**: {v.get('premium_until') or 'No expiry'}\n\n"
            f"🔍 **Raw Premium Data:**\n"
            f"• is_premium: {v.get('is_premium')}\n"
            f"• is_lifetime: {v.get('is_lifetime')}\n"
            f"• premium_active: {v.get('premium_active')}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ **whois failed:** {str(e)}")
