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
TIME_SETTINGS = "time_settings"

# Timezone definitions
TIMEZONES = {
    'WIB': {'offset': 7, 'name': '🇮🇩 WIB (Jakarta)', 'city': 'Jakarta'},
    'WITA': {'offset': 8, 'name': '🇮🇩 WITA (Makassar)', 'city': 'Makassar'},
    'WIT': {'offset': 9, 'name': '🇮🇩 WIT (Papua)', 'city': 'Jayapura'},
    'SGT': {'offset': 8, 'name': '🇸🇬 Singapore', 'city': 'Singapore'},
    'MYT': {'offset': 8, 'name': '🇲🇾 Malaysia', 'city': 'Kuala Lumpur'},
    'GST': {'offset': 4, 'name': '🇦🇪 Dubai (GST)', 'city': 'Dubai'},
    'GMT': {'offset': 0, 'name': '🇬🇧 UK (GMT)', 'city': 'London'},
    'EST': {'offset': -5, 'name': '🇺🇸 US East (EST)', 'city': 'New York'},
    'PST': {'offset': -8, 'name': '🇺🇸 US West (PST)', 'city': 'Los Angeles'},
}

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
            [InlineKeyboardButton("🕐 Time Settings", callback_data=TIME_SETTINGS)],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data=MAIN_MENU)]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def build_timezone_menu() -> InlineKeyboardMarkup:
        """Build timezone selection menu"""
        keyboard = [
            [InlineKeyboardButton("🇮🇩 WIB (Jakarta)", callback_data="set_tz_WIB"),
             InlineKeyboardButton("🇮🇩 WITA (Makassar)", callback_data="set_tz_WITA")],
            [InlineKeyboardButton("🇮🇩 WIT (Papua)", callback_data="set_tz_WIT"),
             InlineKeyboardButton("🇸🇬 Singapore", callback_data="set_tz_SGT")],
            [InlineKeyboardButton("🇲🇾 Malaysia", callback_data="set_tz_MYT"),
             InlineKeyboardButton("🇦🇪 Dubai", callback_data="set_tz_GST")],
            [InlineKeyboardButton("🇬🇧 UK (GMT)", callback_data="set_tz_GMT"),
             InlineKeyboardButton("🇺🇸 US East", callback_data="set_tz_EST")],
            [InlineKeyboardButton("🇺🇸 US West", callback_data="set_tz_PST")],
            [InlineKeyboardButton("🔙 Back to Settings", callback_data=SETTINGS_MENU)]
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

def get_menu_text(menu_key: str, user_lang: str = 'en') -> str:
    """Get menu text by key with language support"""
    if user_lang == 'id':
        texts = {
            MAIN_MENU: """🤖 **CryptoMentor AI 2.0**

Selamat datang di platform analisis cryptocurrency canggih!

Pilih opsi di bawah untuk memulai:""",

            PRICE_MARKET: """📊 **Analisis Harga & Pasar**

Dapatkan harga cryptocurrency real-time dan insight pasar komprehensif.""",

            TRADING_ANALYSIS: """🧠 **Analisis Trading AI**

Analisis teknis canggih yang didukung algoritma Supply & Demand.""",

            FUTURES_SIGNALS: """⚡ **Sinyal Trading Futures**

Sinyal trading futures profesional dengan titik entry/exit yang presisi.""",

            PORTFOLIO_CREDITS: """💼 **Portfolio & Kredit**

Kelola portfolio crypto Anda dan cek saldo kredit.""",

            PREMIUM_REFERRAL: """👑 **Premium & Referral**

Upgrade ke premium dan dapatkan penghasilan melalui program referral.""",

            ASK_AI_MENU: """🤖 **Asisten AI**

Dapatkan insight ahli dan jawaban untuk pertanyaan cryptocurrency Anda.""",

            SETTINGS_MENU: """⚙️ **Pengaturan**

Sesuaikan pengalaman CryptoMentor AI Anda."""
        }
    else:
        texts = {
            MAIN_MENU: """🤖 **CryptoMentor AI 2.0**

Welcome to the advanced cryptocurrency analysis platform!

Choose an option below to get started:""",

            PRICE_MARKET: """📊 **Price & Market Analysis**

Get real-time cryptocurrency prices and comprehensive market insights.""",

            TRADING_ANALYSIS: """🧠 **AI Trading Analysis**

Advanced technical analysis powered by Supply & Demand algorithms.""",

            FUTURES_SIGNALS: """⚡ **Futures Trading Signals**

Professional futures trading signals with precise entry/exit points.""",

            PORTFOLIO_CREDITS: """💼 **Portfolio & Credits**

Manage your crypto portfolio and check your credit balance.""",

            PREMIUM_REFERRAL: """👑 **Premium & Referral**

Upgrade to premium and earn through our referral program.""",

            ASK_AI_MENU: """🤖 **AI Assistant**

Get expert insights and answers to your cryptocurrency questions.""",

            SETTINGS_MENU: """⚙️ **Settings**

Customize your CryptoMentor AI experience."""
        }

    return texts.get(menu_key, "Menu not found")

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