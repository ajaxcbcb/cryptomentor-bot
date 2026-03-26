"""
Basic handlers untuk Whitelabel Bot - /start, /help, dll
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import BOT_NAME, BOT_TAGLINE, ADMIN_IDS

logger = logging.getLogger(__name__)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /start command - sama seperti bot pusat"""
    user = update.effective_user
    
    # Register user di database with welcome credits
    try:
        from app.supabase_repo import upsert_user_with_welcome
        from config import WELCOME_CREDITS
        result = upsert_user_with_welcome(
            user.id, 
            user.username, 
            user.first_name, 
            user.last_name,
            WELCOME_CREDITS
        )
        is_new_user = result.get('is_new', False)
    except Exception as e:
        logger.warning(f"Failed to register user: {e}")
        is_new_user = False
    
    # Check if user already has Bitunix API key
    has_api_key = False
    try:
        from app.handlers_autotrade import get_user_api_keys
        keys = get_user_api_keys(user.id)
        has_api_key = keys is not None
    except Exception:
        has_api_key = False

    if has_api_key:
        # User already set up — go straight to autotrade dashboard
        from app.handlers_autotrade import cmd_autotrade
        await cmd_autotrade(update, context)
    else:
        # New user — show auto trading intro
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 Start Auto Trading", callback_data="start_autotrade")],
            [InlineKeyboardButton("❓ Help", callback_data="show_help")],
        ])
        
        welcome_msg = f"👋 <b>Welcome, {user.first_name}!</b>\n\n"
        if is_new_user:
            welcome_msg += f"🎁 You received {WELCOME_CREDITS} welcome credits!\n\n"
        
        welcome_msg += (
            f"Welcome to <b>{BOT_NAME}</b> — your 24/7 automated crypto trading bot.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 <b>WHAT IS AUTO TRADING?</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "This bot trades <b>futures automatically</b> on Bitunix exchange using AI signals — "
            "no need to watch charts all day.\n\n"
            "⚡ <b>What the bot does for you:</b>\n"
            "• Analyzes the market & detects entry/exit signals\n"
            "• Opens & closes futures positions automatically\n"
            "• Manages risk with stop loss & take profit\n"
            "• Runs 24 hours a day, 7 days a week\n\n"
            "🔧 <b>How to get started (3 steps):</b>\n"
            "1️⃣ Register a Bitunix account via our referral link\n"
            "2️⃣ Create an API key on Bitunix & connect it to the bot\n"
            "3️⃣ Set your capital & leverage — the bot starts immediately!\n\n"
            "Click the button below to begin setup. 👇"
        )
        
        await update.message.reply_text(
            welcome_msg,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    logger.info(f"User {user.id} ({user.username}) started the bot")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /help command"""
    user = update.effective_user
    is_admin = user.id in ADMIN_IDS
    
    help_text = (
        f"📚 *{BOT_NAME} - Help*\n\n"
        f"🤖 *Available Commands:*\n\n"
        f"/start - Start the bot & setup\n"
        f"/autotrade - AutoTrade dashboard\n"
        f"/help - Show this help message\n"
        f"/status - Check bot status\n"
    )
    
    if is_admin:
        help_text += f"/license_status - Check license & balance (admin)\n"
    
    help_text += (
        f"\n💡 *How to use:*\n"
        f"1. Use /autotrade to setup your Bitunix API keys\n"
        f"2. Configure your trading parameters (capital & leverage)\n"
        f"3. Start automated trading — bot runs 24/7\n\n"
        f"📊 *Features:*\n"
        f"• Automated futures trading on Bitunix\n"
        f"• AI-powered entry/exit signals\n"
        f"• Real-time PnL tracking\n"
        f"• Risk management with SL/TP\n\n"
        f"Need help? Contact admin for support."
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown"
    )


async def callback_start_autotrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback handler untuk button 'Start Auto Trading'"""
    query = update.callback_query
    await query.answer()
    
    # Redirect to autotrade command
    from app.handlers_autotrade import cmd_autotrade
    # Create fake update for command
    update._effective_message = query.message
    await cmd_autotrade(update, context)


async def callback_show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback handler untuk button 'Help'"""
    query = update.callback_query
    await query.answer()
    
    help_text = (
        f"📚 *{BOT_NAME} - Help*\n\n"
        f"🤖 *Available Commands:*\n\n"
        f"/start - Start the bot & setup\n"
        f"/autotrade - AutoTrade dashboard\n"
        f"/help - Show this help message\n"
        f"/status - Check bot status\n\n"
        f"💡 *How to use:*\n"
        f"1. Use /autotrade to setup your Bitunix API keys\n"
        f"2. Configure your trading parameters\n"
        f"3. Start automated trading\n\n"
        f"Need help? Contact admin for support."
    )
    
    await query.edit_message_text(
        help_text,
        parse_mode="Markdown"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /status command - show bot status"""
    user = update.effective_user
    
    status_text = (
        f"✅ *Bot Status*\n\n"
        f"🤖 Bot: Online\n"
        f"👤 User ID: `{user.id}`\n"
        f"📊 Trading: Use /autotrade to setup\n"
    )
    
    await update.message.reply_text(
        status_text,
        parse_mode="Markdown"
    )


async def cmd_license_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /license_status - show license info (admin only)"""
    user = update.effective_user
    
    # Check if user is admin
    if user.id not in ADMIN_IDS:
        await update.message.reply_text(
            "⚠️ Command ini hanya untuk admin bot.",
            parse_mode="Markdown"
        )
        return
    
    # Get license info
    try:
        import httpx
        import os
        
        wl_id = os.getenv("WL_ID", "")
        secret_key = os.getenv("WL_SECRET_KEY", "")
        api_url = os.getenv("LICENSE_API_URL", "").rstrip("/")
        deposit_address = os.getenv("DEPOSIT_ADDRESS", "0xff680baa2BaaD50f3756efF778eF673d0fd8cAF9")
        
        if not api_url or not wl_id or not secret_key:
            await update.message.reply_text(
                "❌ License configuration not found.\n\n"
                "Set WL_ID, WL_SECRET_KEY, and LICENSE_API_URL in .env",
                parse_mode="Markdown"
            )
            return
        
        # Call license API
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{api_url}/api/license/check",
                json={"wl_id": wl_id, "secret_key": secret_key}
            )
        
        if resp.status_code != 200:
            await update.message.reply_text(
                f"❌ Failed to check license: HTTP {resp.status_code}",
                parse_mode="Markdown"
            )
            return
        
        data = resp.json()
        
        # Format response
        status = data.get("status", "unknown")
        balance = data.get("balance", 0)
        expires_in_days = data.get("expires_in_days", 0)
        valid = data.get("valid", False)
        
        status_emoji = "✅" if valid else "🚫"
        status_label = status.upper()
        
        msg = (
            f"{status_emoji} *License Status*\n\n"
            f"📊 Status: *{status_label}*\n"
            f"💰 Balance: *${balance:.2f} USDT*\n"
            f"📅 Expires in: *{expires_in_days} days*\n"
            f"💵 Monthly fee: *$10 USDT*\n\n"
        )
        
        if not valid or status == "suspended":
            msg += (
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ *ACTION REQUIRED*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Bot suspended - users cannot access.\n\n"
                "💳 *Top-up via BSC Network:*\n"
                f"`{deposit_address}`\n\n"
                "Minimum: $10 (1 month)\n"
                "Recommended: $50 (5 months)\n\n"
                "✅ Auto-activation in 5-10 minutes"
            )
        elif expires_in_days < 5:
            msg += (
                "━━━━━━━━━━━━━━━━━━━━\n"
                "⚠️ *LOW BALANCE WARNING*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"License will expire in {expires_in_days} days.\n"
                "Top-up soon to avoid suspension.\n\n"
                "💳 *Deposit Address (BSC):*\n"
                f"`{deposit_address}`"
            )
        else:
            msg += "✅ License active - all systems operational"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error checking license status: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)[:200]}",
            parse_mode="Markdown"
        )
