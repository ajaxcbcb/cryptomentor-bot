#!/usr/bin/env python3
"""
Button-Based Menu System for CryptoMentor AI Bot
InlineKeyboard UI for all commands with fallback to slash commands
Uses python-telegram-bot framework
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# CALLBACK DATA CONSTANTS (for routing)
# =============================================================================

# Main menu
MAIN_MENU = "main_menu"

# Categories
PRICE_MARKET = "price_market"
TRADING_ANALYSIS = "trading_analysis"
FUTURES_SIGNALS = "futures_signals"
PORTFOLIO_CREDITS = "portfolio_credits"
PREMIUM_REFERRAL = "premium_referral"
ASK_AI = "ask_ai"
SETTINGS = "settings"

# Price & Market submenu
CHECK_PRICE = "check_price"
MARKET_OVERVIEW = "market_overview"

# Trading Analysis submenu
SPOT_ANALYSIS = "spot_analysis"
FUTURES_ANALYSIS = "futures_analysis"

# Futures Signals submenu
MULTI_COIN_SIGNALS = "multi_coin_signals"
AUTO_SIGNAL_INFO = "auto_signal_info"

# Portfolio & Credits submenu
MY_PORTFOLIO = "my_portfolio"
ADD_COIN = "add_coin"
CHECK_CREDITS = "check_credits"
UPGRADE_PREMIUM = "upgrade_premium"

# Premium & Referral submenu
REFERRAL_PROGRAM = "referral_program"
PREMIUM_EARNINGS = "premium_earnings"

# Ask AI submenu
ASK_CRYPTOMENTOR = "ask_cryptomentor"

# Settings submenu
CHANGE_LANGUAGE = "change_language"

# Input states for ConversationHandler
INPUT_SYMBOL = 1
INPUT_AMOUNT = 2
INPUT_QUESTION = 3

# =============================================================================
# MENU BUILDERS
# =============================================================================

def build_main_menu() -> InlineKeyboardMarkup:
    """Build main menu with 7 categories"""
    keyboard = [
        [
            InlineKeyboardButton("📈 Price & Market", callback_data=PRICE_MARKET),
            InlineKeyboardButton("🧠 Trading Analysis", callback_data=TRADING_ANALYSIS),
        ],
        [
            InlineKeyboardButton("🚀 Futures Signals", callback_data=FUTURES_SIGNALS),
            InlineKeyboardButton("💼 Portfolio", callback_data=PORTFOLIO_CREDITS),
        ],
        [
            InlineKeyboardButton("👑 Premium & Referral", callback_data=PREMIUM_REFERRAL),
            InlineKeyboardButton("🤖 Ask AI", callback_data=ASK_AI),
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data=SETTINGS),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_price_market_menu() -> InlineKeyboardMarkup:
    """Build Price & Market submenu"""
    keyboard = [
        [InlineKeyboardButton("🔹 Check Price", callback_data=CHECK_PRICE)],
        [InlineKeyboardButton("🌍 Market Overview", callback_data=MARKET_OVERVIEW)],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_trading_analysis_menu() -> InlineKeyboardMarkup:
    """Build Trading Analysis submenu"""
    keyboard = [
        [InlineKeyboardButton("📊 Spot Analysis (SnD)", callback_data=SPOT_ANALYSIS)],
        [InlineKeyboardButton("📉 Futures Analysis (SnD)", callback_data=FUTURES_ANALYSIS)],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_futures_signals_menu() -> InlineKeyboardMarkup:
    """Build Futures Signals submenu"""
    keyboard = [
        [InlineKeyboardButton("🔥 Multi-Coin Signals", callback_data=MULTI_COIN_SIGNALS)],
        [InlineKeyboardButton("👑 Auto Signals (Lifetime)", callback_data=AUTO_SIGNAL_INFO)],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_portfolio_menu() -> InlineKeyboardMarkup:
    """Build Portfolio & Credits submenu"""
    keyboard = [
        [InlineKeyboardButton("📂 My Portfolio", callback_data=MY_PORTFOLIO)],
        [InlineKeyboardButton("➕ Add Coin", callback_data=ADD_COIN)],
        [InlineKeyboardButton("💳 Check Credits", callback_data=CHECK_CREDITS)],
        [InlineKeyboardButton("⭐ Upgrade Premium", callback_data=UPGRADE_PREMIUM)],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_premium_referral_menu() -> InlineKeyboardMarkup:
    """Build Premium & Referral submenu"""
    keyboard = [
        [InlineKeyboardButton("🎁 Referral Program", callback_data=REFERRAL_PROGRAM)],
        [InlineKeyboardButton("💰 Premium Earnings", callback_data=PREMIUM_EARNINGS)],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_ask_ai_menu() -> InlineKeyboardMarkup:
    """Build Ask AI submenu"""
    keyboard = [
        [InlineKeyboardButton("💬 Ask CryptoMentor AI", callback_data=ASK_CRYPTOMENTOR)],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_settings_menu() -> InlineKeyboardMarkup:
    """Build Settings submenu"""
    keyboard = [
        [InlineKeyboardButton("🌐 Change Language", callback_data=CHANGE_LANGUAGE)],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_symbol_input_keyboard() -> InlineKeyboardMarkup:
    """Quick symbol input keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("₿ BTC", callback_data="symbol_BTC"),
            InlineKeyboardButton("Ξ ETH", callback_data="symbol_ETH"),
            InlineKeyboardButton("BNB", callback_data="symbol_BNB"),
        ],
        [
            InlineKeyboardButton("SOL", callback_data="symbol_SOL"),
            InlineKeyboardButton("XRP", callback_data="symbol_XRP"),
            InlineKeyboardButton("ADA", callback_data="symbol_ADA"),
        ],
        [InlineKeyboardButton("⌨️ Type Custom", callback_data="symbol_custom")],
        [InlineKeyboardButton("❌ Cancel", callback_data=MAIN_MENU)],
    ]
    return InlineKeyboardMarkup(keyboard)


# =============================================================================
# CALLBACK HANDLERS (Map to existing command functions)
# =============================================================================

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="🎯 **CryptoMentor AI - Main Menu**\n\nChoose a category:",
        reply_markup=build_main_menu(),
        parse_mode='Markdown'
    )


async def price_market_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Price & Market submenu"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="📈 **Price & Market**\n\nSelect an option:",
        reply_markup=build_price_market_menu(),
        parse_mode='Markdown'
    )


async def check_price_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for symbol to check price"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="🔹 **Check Price**\n\nSelect a symbol or type a custom one:\n(e.g., BTC, ETH, BTCUSDT)",
        reply_markup=build_symbol_input_keyboard(),
        parse_mode='Markdown'
    )
    
    context.user_data['action'] = 'price'


async def market_overview_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger /market command"""
    query = update.callback_query
    await query.answer()
    
    # Remove inline keyboard and show market data
    await query.edit_message_text(
        text="🌍 **Market Overview**\n\nFetching market data...",
        reply_markup=None
    )
    
    # Simulate calling the /market command handler
    # In actual implementation, you'd call: await handle_market(update, context)
    context.user_data['action'] = 'market'


async def trading_analysis_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Trading Analysis submenu"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="🧠 **Trading Analysis (Supply & Demand)**\n\nSelect an option:",
        reply_markup=build_trading_analysis_menu(),
        parse_mode='Markdown'
    )


async def spot_analysis_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for symbol to analyze (spot)"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="📊 **Spot Analysis (Supply & Demand)**\n\nSelect a symbol:\n(20 credits required)",
        reply_markup=build_symbol_input_keyboard(),
        parse_mode='Markdown'
    )
    
    context.user_data['action'] = 'analyze'


async def futures_analysis_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for symbol to analyze (futures)"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="📉 **Futures Analysis (Supply & Demand)**\n\nSelect a symbol:\n(20 credits required)",
        reply_markup=build_symbol_input_keyboard(),
        parse_mode='Markdown'
    )
    
    context.user_data['action'] = 'futures'


async def futures_signals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Futures Signals submenu"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="🚀 **Futures Signals**\n\nSelect an option:",
        reply_markup=build_futures_signals_menu(),
        parse_mode='Markdown'
    )


async def multi_coin_signals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger /futures_signals command"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="🔥 **Multi-Coin Futures Signals**\n\nScanning market for signals...",
        reply_markup=None
    )
    
    context.user_data['action'] = 'futures_signals'


async def auto_signal_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show auto signal info"""
    query = update.callback_query
    await query.answer()
    
    info_text = """👑 **Auto Signal Scanner (Lifetime Premium)**

🔄 **How It Works:**
• Automatic scanning every 30 minutes
• Supply & Demand zone detection
• Multi-timeframe analysis (1H + 4H)
• Curated top 3 signals per cycle

📊 **Entry Signals:**
• BUY: Price revisits demand zone
• SELL: Price revisits supply zone

✅ **Available For:**
• Admin users
• Lifetime premium members

📱 **Notifications:**
You'll receive instant signals in DM

💡 **Tip:** Upgrade to Lifetime Premium for automatic signal notifications!"""
    
    keyboard = [[InlineKeyboardButton("⭐ Upgrade Premium", callback_data=UPGRADE_PREMIUM)],
                [InlineKeyboardButton("🔙 Back", callback_data=FUTURES_SIGNALS)]]
    
    await query.edit_message_text(
        text=info_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def portfolio_credits_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Portfolio & Credits submenu"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="💼 **Portfolio & Credits**\n\nSelect an option:",
        reply_markup=build_portfolio_menu(),
        parse_mode='Markdown'
    )


async def my_portfolio_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger /portfolio command"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="📂 **My Portfolio**\n\nLoading your portfolio...",
        reply_markup=None
    )
    
    context.user_data['action'] = 'portfolio'


async def add_coin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Add Coin flow (step 1: symbol)"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="➕ **Add Coin to Portfolio**\n\n**Step 1:** Select a symbol:",
        reply_markup=build_symbol_input_keyboard(),
        parse_mode='Markdown'
    )
    
    context.user_data['action'] = 'add_coin'
    context.user_data['step'] = 'symbol'


async def check_credits_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger /credits command"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="💳 **Check Credits**\n\nLoading credit information...",
        reply_markup=None
    )
    
    context.user_data['action'] = 'credits'


async def upgrade_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger /subscribe command"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="⭐ **Upgrade to Premium**\n\nLoading subscription options...",
        reply_markup=None
    )
    
    context.user_data['action'] = 'subscribe'


async def premium_referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Premium & Referral submenu"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="👑 **Premium & Referral**\n\nSelect an option:",
        reply_markup=build_premium_referral_menu(),
        parse_mode='Markdown'
    )


async def referral_program_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger /referral command"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="🎁 **Referral Program**\n\nLoading your referral details...",
        reply_markup=None
    )
    
    context.user_data['action'] = 'referral'


async def premium_earnings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger /premium_earnings command"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="💰 **Premium Earnings**\n\nLoading earnings report...",
        reply_markup=None
    )
    
    context.user_data['action'] = 'premium_earnings'


async def ask_ai_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Ask AI submenu"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="🤖 **Ask CryptoMentor AI**\n\nSelect an option:",
        reply_markup=build_ask_ai_menu(),
        parse_mode='Markdown'
    )


async def ask_cryptomentor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for AI question"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="💬 **Ask CryptoMentor AI**\n\nType your question below:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=ASK_AI)]])
    )
    
    context.user_data['action'] = 'ask_ai'
    context.user_data['awaiting_input'] = True


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Settings submenu"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="⚙️ **Settings**\n\nSelect an option:",
        reply_markup=build_settings_menu(),
        parse_mode='Markdown'
    )


async def change_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language options"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
            InlineKeyboardButton("🇮🇩 Bahasa", callback_data="lang_id"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data=SETTINGS)],
    ]
    
    await query.edit_message_text(
        text="🌐 **Choose Language:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


# =============================================================================
# SYMBOL SELECTION CALLBACK
# =============================================================================

async def symbol_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle symbol selection from buttons"""
    query = update.callback_query
    symbol = query.data.replace("symbol_", "").upper()
    
    if symbol == "CUSTOM":
        await query.answer("Type the symbol (e.g., BTCUSDT):")
        context.user_data['awaiting_symbol'] = True
        return
    
    await query.answer(f"Selected: {symbol}")
    
    action = context.user_data.get('action')
    step = context.user_data.get('step')
    
    # Different flows based on action
    if action == 'price':
        await query.edit_message_text(text=f"📈 Fetching price for {symbol}...", reply_markup=None)
        context.user_data['symbol'] = symbol
        # Would call: await handle_price(update, context, symbol)
        
    elif action == 'analyze':
        await query.edit_message_text(text=f"📊 Analyzing {symbol}...", reply_markup=None)
        context.user_data['symbol'] = symbol
        # Would call: await handle_analyze(update, context, symbol)
        
    elif action == 'futures':
        await query.edit_message_text(text=f"📉 Analyzing futures for {symbol}...", reply_markup=None)
        context.user_data['symbol'] = symbol
        # Would call: await handle_futures(update, context, symbol)
        
    elif action == 'add_coin' and step == 'symbol':
        # Next step: ask for amount
        await query.edit_message_text(
            text=f"➕ **Add {symbol}**\n\n**Step 2:** How much {symbol} do you have?\n\nEnter amount (e.g., 1.5)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data=MAIN_MENU)]])
        )
        context.user_data['symbol'] = symbol
        context.user_data['step'] = 'amount'
        context.user_data['awaiting_amount'] = True


# =============================================================================
# HANDLER REGISTRATION (Add to bot.py)
# =============================================================================

def register_menu_handlers(application):
    """
    Register all menu callbacks with the Telegram application
    
    Call this function in your bot.py main setup:
    
    Example:
        from menu_handler import register_menu_handlers
        
        application = Application.builder().token(TOKEN).build()
        register_menu_handlers(application)
    """
    
    # Main callbacks
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern=f"^{MAIN_MENU}$"))
    
    # Category callbacks
    application.add_handler(CallbackQueryHandler(price_market_callback, pattern=f"^{PRICE_MARKET}$"))
    application.add_handler(CallbackQueryHandler(trading_analysis_callback, pattern=f"^{TRADING_ANALYSIS}$"))
    application.add_handler(CallbackQueryHandler(futures_signals_callback, pattern=f"^{FUTURES_SIGNALS}$"))
    application.add_handler(CallbackQueryHandler(portfolio_credits_callback, pattern=f"^{PORTFOLIO_CREDITS}$"))
    application.add_handler(CallbackQueryHandler(premium_referral_callback, pattern=f"^{PREMIUM_REFERRAL}$"))
    application.add_handler(CallbackQueryHandler(ask_ai_callback, pattern=f"^{ASK_AI}$"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern=f"^{SETTINGS}$"))
    
    # Price & Market
    application.add_handler(CallbackQueryHandler(check_price_callback, pattern=f"^{CHECK_PRICE}$"))
    application.add_handler(CallbackQueryHandler(market_overview_callback, pattern=f"^{MARKET_OVERVIEW}$"))
    
    # Trading Analysis
    application.add_handler(CallbackQueryHandler(spot_analysis_callback, pattern=f"^{SPOT_ANALYSIS}$"))
    application.add_handler(CallbackQueryHandler(futures_analysis_callback, pattern=f"^{FUTURES_ANALYSIS}$"))
    
    # Futures Signals
    application.add_handler(CallbackQueryHandler(multi_coin_signals_callback, pattern=f"^{MULTI_COIN_SIGNALS}$"))
    application.add_handler(CallbackQueryHandler(auto_signal_info_callback, pattern=f"^{AUTO_SIGNAL_INFO}$"))
    
    # Portfolio & Credits
    application.add_handler(CallbackQueryHandler(my_portfolio_callback, pattern=f"^{MY_PORTFOLIO}$"))
    application.add_handler(CallbackQueryHandler(add_coin_callback, pattern=f"^{ADD_COIN}$"))
    application.add_handler(CallbackQueryHandler(check_credits_callback, pattern=f"^{CHECK_CREDITS}$"))
    application.add_handler(CallbackQueryHandler(upgrade_premium_callback, pattern=f"^{UPGRADE_PREMIUM}$"))
    
    # Premium & Referral
    application.add_handler(CallbackQueryHandler(referral_program_callback, pattern=f"^{REFERRAL_PROGRAM}$"))
    application.add_handler(CallbackQueryHandler(premium_earnings_callback, pattern=f"^{PREMIUM_EARNINGS}$"))
    
    # Ask AI
    application.add_handler(CallbackQueryHandler(ask_cryptomentor_callback, pattern=f"^{ASK_CRYPTOMENTOR}$"))
    
    # Settings
    application.add_handler(CallbackQueryHandler(change_language_callback, pattern=f"^{CHANGE_LANGUAGE}$"))
    
    # Symbol selection
    application.add_handler(CallbackQueryHandler(symbol_callback, pattern=r"^symbol_"))
    
    logger.info("✅ Menu handlers registered successfully")
