
# -*- coding: utf-8 -*-
"""
CryptoMentor AI 2.0 - Button-Based Menu System
Complete InlineKeyboard system that maps all existing commands
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, List

# Menu Constants
MAIN_MENU = "main_menu"
PRICE_MARKET = "price_market"
TRADING_ANALYSIS = "trading_analysis"
FUTURES_SIGNALS = "futures_signals"
PORTFOLIO_CREDITS = "portfolio_credits"
PREMIUM_REFERRAL = "premium_referral"
ASK_AI_MENU = "ask_ai_menu"
SETTINGS_MENU = "settings_menu"

# Action Constants
CHECK_PRICE = "check_price"
MARKET_OVERVIEW = "market_overview"
SPOT_ANALYSIS = "spot_analysis"
FUTURES_ANALYSIS = "futures_analysis"
MULTI_COIN_SIGNALS = "multi_coin_signals"
AUTO_SIGNAL_INFO = "auto_signal_info"
MY_PORTFOLIO = "my_portfolio"
ADD_COIN = "add_coin"
CHECK_CREDITS = "check_credits"
UPGRADE_PREMIUM = "upgrade_premium"
REFERRAL_PROGRAM = "referral_program"
PREMIUM_EARNINGS = "premium_earnings"
ASK_AI = "ask_ai"
CHANGE_LANGUAGE = "change_language"

# Popular symbols for quick selection
POPULAR_SYMBOLS = ["BTC", "ETH", "SOL", "ADA", "DOT", "MATIC", "AVAX", "UNI"]

class MenuBuilder:
    """Builds InlineKeyboard menus for CryptoMentor AI"""
    
    @staticmethod
    def build_main_menu() -> InlineKeyboardMarkup:
        """Build the main menu with 7 categories"""
        keyboard = [
            [InlineKeyboardButton("📈 Price & Market", callback_data=PRICE_MARKET)],
            [InlineKeyboardButton("🧠 Trading Analysis", callback_data=TRADING_ANALYSIS)],
            [InlineKeyboardButton("🚀 Futures Signals", callback_data=FUTURES_SIGNALS)],
            [InlineKeyboardButton("💼 Portfolio & Credits", callback_data=PORTFOLIO_CREDITS)],
            [InlineKeyboardButton("👑 Premium & Referral", callback_data=PREMIUM_REFERRAL)],
            [InlineKeyboardButton("🤖 Ask AI", callback_data=ASK_AI_MENU)],
            [InlineKeyboardButton("⚙️ Settings", callback_data=SETTINGS_MENU)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_price_market_menu() -> InlineKeyboardMarkup:
        """Build Price & Market submenu"""
        keyboard = [
            [InlineKeyboardButton("🔹 Check Price (FREE)", callback_data=CHECK_PRICE)],
            [InlineKeyboardButton("🌍 Market Overview (FREE)", callback_data=MARKET_OVERVIEW)],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_trading_analysis_menu() -> InlineKeyboardMarkup:
        """Build Trading Analysis submenu"""
        keyboard = [
            [InlineKeyboardButton("📊 Spot Analysis (SnD) - 20 Credits", callback_data=SPOT_ANALYSIS)],
            [InlineKeyboardButton("📉 Futures Analysis (SnD) - 20 Credits", callback_data=FUTURES_ANALYSIS)],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_futures_signals_menu() -> InlineKeyboardMarkup:
        """Build Futures Signals submenu"""
        keyboard = [
            [InlineKeyboardButton("🔥 Multi-Coin Signals - 60 Credits", callback_data=MULTI_COIN_SIGNALS)],
            [InlineKeyboardButton("👑 Auto Signal Info (Lifetime)", callback_data=AUTO_SIGNAL_INFO)],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_portfolio_credits_menu() -> InlineKeyboardMarkup:
        """Build Portfolio & Credits submenu"""
        keyboard = [
            [InlineKeyboardButton("📂 My Portfolio (FREE)", callback_data=MY_PORTFOLIO)],
            [InlineKeyboardButton("➕ Add Coin (FREE)", callback_data=ADD_COIN)],
            [InlineKeyboardButton("💳 Check Credits (FREE)", callback_data=CHECK_CREDITS)],
            [InlineKeyboardButton("⭐ Upgrade Premium", callback_data=UPGRADE_PREMIUM)],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_premium_referral_menu() -> InlineKeyboardMarkup:
        """Build Premium & Referral submenu"""
        keyboard = [
            [InlineKeyboardButton("🎁 Referral Program (FREE)", callback_data=REFERRAL_PROGRAM)],
            [InlineKeyboardButton("💰 Premium Earnings", callback_data=PREMIUM_EARNINGS)],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_ask_ai_menu() -> InlineKeyboardMarkup:
        """Build Ask AI submenu"""
        keyboard = [
            [InlineKeyboardButton("💬 Ask CryptoMentor AI", callback_data=ASK_AI)],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_settings_menu() -> InlineKeyboardMarkup:
        """Build Settings submenu"""
        keyboard = [
            [InlineKeyboardButton("🌐 Change Language", callback_data=CHANGE_LANGUAGE)],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_symbol_selection() -> InlineKeyboardMarkup:
        """Build popular symbol selection keyboard"""
        keyboard = []
        
        # Group symbols in pairs for better layout
        for i in range(0, len(POPULAR_SYMBOLS), 2):
            row = []
            if i < len(POPULAR_SYMBOLS):
                row.append(InlineKeyboardButton(f"₿ {POPULAR_SYMBOLS[i]}", callback_data=f"symbol_{POPULAR_SYMBOLS[i]}"))
            if i + 1 < len(POPULAR_SYMBOLS):
                row.append(InlineKeyboardButton(f"₿ {POPULAR_SYMBOLS[i+1]}", callback_data=f"symbol_{POPULAR_SYMBOLS[i+1]}"))
            keyboard.append(row)
        
        # Add manual input option and back button
        keyboard.append([InlineKeyboardButton("⌨️ Type Symbol Manually", callback_data="manual_symbol")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=MAIN_MENU)])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_timeframe_selection(symbol: str) -> InlineKeyboardMarkup:
        """Build timeframe selection for futures analysis"""
        keyboard = [
            [InlineKeyboardButton("⚡ 15M", callback_data=f'futures_{symbol}_15m'),
             InlineKeyboardButton("🔥 30M", callback_data=f'futures_{symbol}_30m')],
            [InlineKeyboardButton("📈 1H", callback_data=f'futures_{symbol}_1h'),
             InlineKeyboardButton("🚀 4H", callback_data=f'futures_{symbol}_4h')],
            [InlineKeyboardButton("💎 1D", callback_data=f'futures_{symbol}_1d'),
             InlineKeyboardButton("🌟 1W", callback_data=f'futures_{symbol}_1w')],
            [InlineKeyboardButton("🔙 Back", callback_data=TRADING_ANALYSIS)]
        ]
        return InlineKeyboardMarkup(keyboard)

def get_menu_text(menu_type: str, user_data: Dict = None) -> str:
    """Get appropriate text for each menu type"""
    
    menu_texts = {
        MAIN_MENU: """🤖 **CryptoMentor AI 2.0 - Main Menu**

Welcome! Choose from the options below:

📈 **Price & Market** - Check real-time prices and market overview
🧠 **Trading Analysis** - Advanced SnD analysis for spot and futures
🚀 **Futures Signals** - Professional trading signals
💼 **Portfolio & Credits** - Manage your portfolio and account
👑 **Premium & Referral** - Premium features and earnings
🤖 **Ask AI** - Chat with our AI assistant
⚙️ **Settings** - Language and preferences

💡 **Tip**: Advanced users can still use slash commands like `/price btc`""",

        PRICE_MARKET: """📈 **Price & Market**

Get real-time cryptocurrency data:

🔹 **Check Price** - Real-time prices from CoinAPI (FREE)
🌍 **Market Overview** - Global market stats and trends (FREE)

💰 Both features are completely free to use!""",

        TRADING_ANALYSIS: """🧠 **Trading Analysis with Supply & Demand**

Professional trading analysis:

📊 **Spot Analysis** - Comprehensive analysis with SnD zones (20 credits)
📉 **Futures Analysis** - Futures trading signals with SnD (20 credits)

⚡ Features real-time CoinAPI data + advanced SnD algorithms""",

        FUTURES_SIGNALS: """🚀 **Futures Trading Signals**

Professional futures trading tools:

🔥 **Multi-Coin Signals** - Scan 25+ coins for trading opportunities (60 credits)
👑 **Auto Signals** - Automated signals for Lifetime premium users only

💎 All signals include precise entry, TP, and SL levels""",

        PORTFOLIO_CREDITS: """💼 **Portfolio & Credits Management**

Manage your account and investments:

📂 **My Portfolio** - View your crypto holdings (FREE)
➕ **Add Coin** - Add coins to track performance (FREE)
💳 **Check Credits** - View your current credit balance (FREE)
⭐ **Upgrade Premium** - Unlock unlimited features

💡 New users start with 100 free credits!""",

        PREMIUM_REFERRAL: """👑 **Premium & Referral Program**

Maximize your earnings:

🎁 **Referral Program** - Earn credits and money from referrals (FREE)
💰 **Premium Earnings** - View your referral earnings dashboard

💎 Premium users earn money from premium referrals!""",

        ASK_AI_MENU: """🤖 **AI Assistant**

Chat with CryptoMentor AI:

💬 **Ask AI** - Get expert answers about crypto and trading

📚 Examples: "What is DeFi?", "Explain Bitcoin halving", "Trading tips"

🎯 Free for basic questions, premium for advanced analysis""",

        SETTINGS_MENU: """⚙️ **Settings**

Customize your experience:

🌐 **Change Language** - Switch between Indonesian and English

🔧 More settings coming soon in future updates!"""
    }
    
    return menu_texts.get(menu_type, "Menu not found")

# Export all components
__all__ = [
    'MenuBuilder',
    'get_menu_text',
    'MAIN_MENU',
    'PRICE_MARKET',
    'TRADING_ANALYSIS',
    'FUTURES_SIGNALS',
    'PORTFOLIO_CREDITS',
    'PREMIUM_REFERRAL',
    'ASK_AI_MENU',
    'SETTINGS_MENU',
    'POPULAR_SYMBOLS'
]
