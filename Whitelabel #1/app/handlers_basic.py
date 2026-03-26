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
    help_text = (
        f"📚 *{BOT_NAME} - Help*\n\n"
        f"🤖 *Available Commands:*\n\n"
        f"/start - Start the bot & setup\n"
        f"/autotrade - AutoTrade dashboard\n"
        f"/help - Show this help message\n"
        f"/status - Check bot status\n\n"
        f"💡 *How to use:*\n"
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
