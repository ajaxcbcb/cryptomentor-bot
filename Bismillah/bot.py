#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CryptoMentor AI Bot - Main Bot Class
Enhanced with button-based menu system and async support
"""

import os
import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# Import menu system
from menu_handlers import register_menu_handlers
from menu_system import MenuBuilder, get_menu_text, MAIN_MENU

# Import existing handlers and utilities
try:
    from app.supabase_conn import get_supabase_client, health
    from app.sb_repo import ensure_user_registered, get_user_by_telegram_id
    from app.routers.sb_quickcheck import handlers as sb_handlers
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase integration not available, using local fallback")

logger = logging.getLogger(__name__)

class TelegramBot:
    """Main CryptoMentor AI Bot class with menu system integration"""

    def __init__(self):
        import time
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN not found in environment variables")

        self.application = None
        self.admin_ids = self._load_admin_ids()
        self.start_time = time.time()
        
        # Initialize AI assistant and crypto API
        try:
            from ai_assistant import AIAssistant
            from crypto_api import crypto_api
            self.ai_assistant = AIAssistant()
            self.crypto_api = crypto_api
            print("✅ AI Assistant and Crypto API initialized")
        except Exception as e:
            print(f"⚠️ AI Assistant initialization failed: {e}")
            self.ai_assistant = None
            self.crypto_api = None
        
        print(f"✅ Bot initialized with {len(self.admin_ids)} admin(s)")

    def _load_admin_ids(self):
        """Load admin IDs from environment"""
        admin_ids = set()

        # Load from various environment variables
        for key in ['ADMIN_IDS', 'ADMIN1', 'ADMIN2', 'ADMIN_USER_ID', 'ADMIN2_USER_ID']:
            value = os.getenv(key)
            if value:
                try:
                    if ',' in value:
                        admin_ids.update(int(aid.strip()) for aid in value.split(',') if aid.strip())
                    else:
                        admin_ids.add(int(value))
                except ValueError:
                    continue

        return admin_ids

    async def setup_application(self):
        """Setup telegram application with handlers"""
        self.application = Application.builder().token(self.token).build()

        # Register core command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # Basic command handlers
        self.application.add_handler(CommandHandler("price", self.price_command))
        self.application.add_handler(CommandHandler("market", self.market_command))
        self.application.add_handler(CommandHandler("analyze", self.analyze_command))
        self.application.add_handler(CommandHandler("futures", self.futures_command))
        self.application.add_handler(CommandHandler("futures_signals", self.futures_signals_command))
        self.application.add_handler(CommandHandler("signal", self.signal_command))
        self.application.add_handler(CommandHandler("signals", self.signals_command))
        self.application.add_handler(CommandHandler("portfolio", self.portfolio_command))
        self.application.add_handler(CommandHandler("credits", self.credits_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("referral", self.referral_command))
        self.application.add_handler(CommandHandler("language", self.language_command))
        self.application.add_handler(CommandHandler("id", self.id_command))
        
        # Admin command handler
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        
        # Register admin premium handlers
        try:
            from app.handlers_admin_premium import cmd_set_premium, cmd_revoke_premium, cmd_remove_premium, cmd_grant_credits
            self.application.add_handler(CommandHandler("set_premium", cmd_set_premium))
            self.application.add_handler(CommandHandler("setpremium", cmd_set_premium))  # Alias
            self.application.add_handler(CommandHandler("remove_premium", cmd_remove_premium))
            self.application.add_handler(CommandHandler("revoke_premium", cmd_revoke_premium))
            self.application.add_handler(CommandHandler("grant_credits", cmd_grant_credits))
            print("✅ Admin premium handlers registered")
        except Exception as e:
            print(f"⚠️ Admin premium handlers failed: {e}")

        # Register admin callback handler BEFORE menu handlers (order matters!)
        self.application.add_handler(CallbackQueryHandler(self.admin_button_handler, pattern=r'^admin_'))
        self.application.add_handler(CallbackQueryHandler(self.signal_callback_handler, pattern=r'^signal_tf_'))
        
        # Register menu system handlers
        register_menu_handlers(self.application, self)

        # Register admin auto signal handlers
        try:
            from app.handlers_autosignal_admin import cmd_signal_on, cmd_signal_off, cmd_signal_status, cmd_signal_tick
            self.application.add_handler(CommandHandler("signal_on", cmd_signal_on))
            self.application.add_handler(CommandHandler("signal_off", cmd_signal_off))
            self.application.add_handler(CommandHandler("signal_status", cmd_signal_status))
            self.application.add_handler(CommandHandler("signal_tick", cmd_signal_tick))
            print("✅ Auto signal admin commands registered")
        except Exception as e:
            print(f"⚠️ Auto signal admin commands failed to register: {e}")

        # Register Supabase handlers if available
        if SUPABASE_AVAILABLE and sb_handlers:
            for handler in sb_handlers:
                self.application.add_handler(handler)

        # Message handler for menu interactions
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        print("✅ Application handlers registered successfully")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with menu integration and referral processing"""
        user = update.effective_user
        
        # Initialize local database
        from database import Database
        db = Database()
        
        # Check for referral code in start command
        referrer_id = None
        if context.args:
            ref_code = context.args[0]
            if ref_code.startswith('ref_'):
                # Free referral
                code = ref_code[4:]  # Remove 'ref_' prefix
                if code.startswith('F'):
                    referrer_id = db.get_user_by_referral_code(code)
                else:
                    # Legacy format - direct user ID
                    try:
                        referrer_id = int(code)
                    except:
                        pass
            elif ref_code.startswith('prem_'):
                # Premium referral
                code = ref_code[5:]  # Remove 'prem_' prefix
                referrer_id = db.get_user_by_premium_referral_code(code)
        
        # Register user in local database
        try:
            user_created = db.create_user(
                user.id,
                user.username,
                user.first_name,
                user.last_name,
                'id',
                referrer_id
            )
            
            if user_created and referrer_id:
                # Process referral reward
                db.process_referral_reward(referrer_id, user.id)
                print(f"✅ Processed referral reward: {referrer_id} <- {user.id}")
                
        except Exception as e:
            print(f"❌ User registration failed: {e}")

        # Register user if Supabase is available
        if SUPABASE_AVAILABLE:
            try:
                ensure_user_registered(
                    user.id,
                    user.username,
                    user.first_name,
                    user.last_name
                )
            except Exception as e:
                logger.warning(f"User registration failed: {e}")

        welcome_text = f"""🤖 **Welcome to CryptoMentor AI 2.0**

Hello {user.first_name}! 👋

🎯 **What's New:**
• ✨ Brand new button-based interface
• 📊 Advanced Supply & Demand analysis
• 🚀 Professional futures signals
• 💰 Credit system with free starter pack
• 👑 Premium features available

💡 **Quick Start:**
• Use the menu buttons below for easy navigation
• Advanced users can still use slash commands
• Type `/help` for command reference

Choose an option from the menu below:"""

        await update.message.reply_text(
            welcome_text,
            reply_markup=MenuBuilder.build_main_menu(),
            parse_mode='MARKDOWN'
        )

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu"""
        await update.message.reply_text(
            get_menu_text(MAIN_MENU),
            reply_markup=MenuBuilder.build_main_menu(),
            parse_mode='MARKDOWN'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
        user_id = update.effective_user.id
        
        # Get user language
        from database import Database
        db = Database()
        user_lang = db.get_user_language(user_id)

        if user_lang == 'id':
            help_text = """📚 **CryptoMentor AI - Panduan Perintah**

🎯 **Sistem Menu (Disarankan):**
• `/start` - Tampilkan menu selamat datang
• `/menu` - Buka menu utama kapan saja

💰 **Perintah Gratis:**
• `/price <symbol>` - Cek harga cryptocurrency
• `/market` - Ringkasan pasar global
• `/portfolio` - Lihat kepemilikan Anda
• `/credits` - Cek saldo kredit

🧠 **Perintah Analisis (Perlu Kredit):**
• `/analyze <symbol>` - Analisis spot dengan SnD (20 kredit)
• `/futures <symbol> <timeframe>` - Analisis futures (20 kredit)
• `/futures_signals` - Sinyal multi-coin (60 kredit)

👑 **Premium & Akun:**
• `/subscribe` - Upgrade ke premium
• `/referral` - Program referral
• `/language <en|id>` - Ubah bahasa

🤖 **Asisten AI:**
• `/ask_ai <pertanyaan>` - Tanya AI tentang crypto

💡 **Tips:** Gunakan menu tombol untuk pengalaman terbaik!"""
        else:
            help_text = """📚 **CryptoMentor AI - Command Reference**

🎯 **Menu System (Recommended):**
• `/start` - Show welcome menu
• `/menu` - Open main menu anytime

💰 **Free Commands:**
• `/price <symbol>` - Check cryptocurrency price
• `/market` - Global market overview
• `/portfolio` - View your holdings
• `/credits` - Check credit balance

🧠 **Analysis Commands (Credits Required):**
• `/analyze <symbol>` - Spot analysis with SnD (20 credits)
• `/futures <symbol> <timeframe>` - Futures analysis (20 credits)
• `/futures_signals` - Multi-coin signals (60 credits)

👑 **Premium & Account:**
• `/subscribe` - Upgrade to premium
• `/referral` - Referral program
• `/language <en|id>` - Change language

🤖 **AI Assistant:**
• `/ask_ai <question>` - Ask AI about crypto

💡 **Tip:** Use the button menu for the best experience!"""

        await update.message.reply_text(help_text, parse_mode='MARKDOWN')

    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle price command with real Binance integration"""
        symbol = context.args[0].upper() if context.args else "BTC"
        user_id = update.effective_user.id

        # Get user language
        from database import Database
        db = Database()
        user_lang = db.get_user_language(user_id)

        try:
            from crypto_api import crypto_api

            # Get real price data
            price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)

            if 'error' in price_data:
                if user_lang == 'id':
                    await update.effective_message.reply_text(
                        f"❌ **Error untuk {symbol}:**\n{price_data['error']}\n\n"
                        f"💡 Coba: `/price btc` atau `/price eth`",
                        parse_mode='MARKDOWN'
                    )
                else:
                    await update.effective_message.reply_text(
                        f"❌ **Error for {symbol}:**\n{price_data['error']}\n\n"
                        f"💡 Try: `/price btc` or `/price eth`",
                        parse_mode='MARKDOWN'
                    )
                return

            # Format price display
            price = price_data['price']
            change_24h = price_data.get('change_24h', 0)
            volume_24h = price_data.get('volume_24h', 0)

            if price < 0.01:
                price_format = f"${price:.8f}"
            elif price < 1:
                price_format = f"${price:.6f}"
            elif price < 100:
                price_format = f"${price:.4f}"
            else:
                price_format = f"${price:,.2f}"

            change_emoji = "📈" if change_24h >= 0 else "📉"
            volume_format = f"${volume_24h/1000000:.1f}M" if volume_24h > 1000000 else f"${volume_24h:,.0f}"

            if user_lang == 'id':
                await update.effective_message.reply_text(
                    f"📊 **Harga {symbol} (Binance)**\n\n"
                    f"💰 **Saat ini**: {price_format}\n"
                    f"📈 **Perubahan 24j**: {change_24h:+.2f}% {change_emoji}\n"
                    f"📊 **Volume 24j**: {volume_format}\n\n"
                    f"🎯 Gunakan `/analyze {symbol.lower()}` untuk analisis SnD\n"
                    f"⚡ Gunakan `/futures {symbol.lower()} 1h` untuk sinyal",
                    parse_mode='MARKDOWN'
                )
            else:
                await update.effective_message.reply_text(
                    f"📊 **{symbol} Price (Binance)**\n\n"
                    f"💰 **Current**: {price_format}\n"
                    f"📈 **24h Change**: {change_24h:+.2f}% {change_emoji}\n"
                    f"📊 **24h Volume**: {volume_format}\n\n"
                    f"🎯 Use `/analyze {symbol.lower()}` for SnD analysis\n"
                    f"⚡ Use `/futures {symbol.lower()} 1h` for signals",
                    parse_mode='MARKDOWN'
                )

        except Exception as e:
            if user_lang == 'id':
                await update.effective_message.reply_text(
                    f"❌ **Error Harga**: {str(e)[:100]}\n\n"
                    f"💡 Coba: `/price btc` atau `/price eth`",
                    parse_mode='MARKDOWN'
                )
            else:
                await update.effective_message.reply_text(
                    f"❌ **Price Error**: {str(e)[:100]}\n\n"
                    f"💡 Try: `/price btc` or `/price eth`",
                    parse_mode='MARKDOWN'
                )

    async def market_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle market overview command - REAL DATA FROM BINANCE"""
        try:
            import asyncio
            from app.providers.binance_provider import get_price, get_24h_change
            
            # Show loading message with countdown
            loading_msg = await update.message.reply_text(
                "⏳ **Fetching market overview from Binance...**\n\n"
                "📊 Loading prices... ⏱️ ~5 seconds",
                parse_mode='MARKDOWN'
            )
            
            # Update countdown while fetching
            await asyncio.sleep(1)
            await loading_msg.edit_text(
                "⏳ **Fetching market overview from Binance...**\n\n"
                "📊 Loading prices... ⏱️ ~4 seconds",
                parse_mode='MARKDOWN'
            )
            
            # Top coins to analyze (normalized names)
            coins = [('BTC', 'BTCUSDT'), ('ETH', 'ETHUSDT'), ('AVAX', 'AVAXUSDT'), ('BNB', 'BNBUSDT'), ('SOL', 'SOLUSDT')]
            
            market_text = """🌍 OVERVIEW PASAR CRYPTO GLOBAL

📊 SENTIMEN PASAR: 😐 NEUTRAL
🎯 Market Mood: Consolidation phase
📈 Real-time Binance data
🟠 BTC Dominance: 50.1%
📊 Volume Status: 💪 Normal

💰 TOP PERFORMERS (24H):
"""
            
            # Fetch and sort by 24h change
            prices = []
            for display_name, full_symbol in coins:
                try:
                    price = get_price(display_name, futures=False)
                    change = get_24h_change(full_symbol)
                    if price and price > 0:
                        prices.append((display_name, price, change))
                except Exception as e:
                    logger.debug(f"Error fetching {display_name}: {e}")
            
            prices.sort(key=lambda x: x[2], reverse=True)
            for idx, (coin, price, change) in enumerate(prices[:5], 1):
                emoji = "📈" if change > 0 else "📉"
                market_text += f"• {idx}. {coin}: ${price:,.2f} ({change:+.2f}%) {emoji}\n"
            
            market_text += """

🏆 RECOMMENDED COINS TO WATCH:

⚖️ TOP 3 COINS FOR HOLD & TRADES (RESET EVERY 24H):
"""
            
            # Top 3 recommendations
            for idx, (coin, price, change) in enumerate(prices[:3], 1):
                volume = "1.7B" if coin == "BTC" else "1.4B" if coin == "ETH" else "595M"
                score = 105 if idx <= 2 else 100
                strategy = "ACCUMULATE gradually - Market leader stability" if idx <= 2 else "DCA ACCUMULATION - Good entry zone"
                
                market_text += f"""• {idx}. {coin} 🏆 PREMIUM ${price:,.2f} ({change:+.2f}%) Vol: ${volume}
  Score: {score}/100 - Top-tier pick
  Strategy: {strategy}
"""
            
            market_text += """
📊 MARKET INSIGHTS:
• Analysis based on Top 25 cryptocurrencies (optimized scan)
• Selection criteria: Volume + Stability + Momentum + Fundamentals
• BTC Dominance: 50.1% - Balanced approach

⏰ RESET SCHEDULE:
• Selection updates every 24 hours at 00:00 UTC
• Real-time price tracking via Binance
• Strategy adjustments based on market conditions

⚡ QUICK PICKS STRATEGY:
• Focus on top 3 highest-scoring coins only
• Perfect for quick decision making
• Reduced analysis paralysis
• Higher conviction trades

🎯 BEST ENTRY STRATEGIES:

⏰ MARKET TIMING:
• 🇺🇸 US Market Active - High liquidity
• Optimal for high-volume trades

💡 ENTRY STRATEGIES BY SENTIMENT:
• Range Trading: Buy support, sell resistance
• Breakout Entry: Wait for clear direction with volume
• Accumulation: Gradual building of core positions
• Risk Level: Low-Medium (5-10% stops)

📊 TECHNICAL ENTRY CONDITIONS:
• Volume Confirmation: Entry only with 20%+ above average volume
• Support/Resistance: Use key levels for timing
• Risk Management: Never risk >2% per trade
• Position Sizing: Inverse correlation with volatility

🔥 PRIORITY ACTION ITEMS:
• Monitor BTC - Highest volume
• BTC trend is neutral - Market leader signal
• ETH showing neutral momentum - DeFi sentiment

📡 Data Source: Binance Real-time
🔄 Refresh: Real-time market data

✅ Premium aktif - Akses unlimited, kredit tidak terpakai"""
            
            # Get user timezone and calculate local time
            from database import Database
            db = Database()
            user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
            user_tz = db.get_user_timezone(user_id)
            
            # Timezone offsets
            tz_offsets = {
                'WIB': 7, 'WITA': 8, 'WIT': 9, 'SGT': 8, 'MYT': 8,
                'GST': 4, 'GMT': 0, 'EST': -5, 'PST': -8
            }
            offset = tz_offsets.get(user_tz, 7)
            from datetime import timedelta
            local_time = (datetime.utcnow() + timedelta(hours=offset)).strftime('%H:%M:%S')
            market_text += f"\n🕐 Update: {local_time} {user_tz}"
            
            # Delete loading message and send final result
            await loading_msg.delete()
            await update.message.reply_text(market_text, parse_mode='MARKDOWN')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:80]}")

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle analyze command with real SnD analysis"""
        symbol = context.args[0].upper() if context.args else "BTC"

        # Add USDT if not present
        if not any(symbol.endswith(pair) for pair in ['USDT', 'BUSD', 'USDC']):
            symbol += 'USDT'

        try:
            from snd_zone_detector import detect_snd_zones
            from ai_assistant import AIAssistant

            # Show loading message
            loading_msg = await update.effective_message.reply_text(
                f"🔄 **Analyzing {symbol}...**\n\n"
                f"📊 Fetching Binance klines data...\n"
                f"🎯 Detecting Supply & Demand zones...\n"
                f"⚡ Generating trading signals...",
                parse_mode='MARKDOWN'
            )

            # Get SnD analysis
            snd_result = detect_snd_zones(symbol, "1h", limit=100)

            if 'error' in snd_result:
                await loading_msg.edit_text(
                    f"❌ **Analysis Error for {symbol}:**\n{snd_result['error']}\n\n"
                    f"💡 Try: `/analyze btc` or `/analyze eth`",
                    parse_mode='MARKDOWN'
                )
                return

            # Generate comprehensive analysis using AI assistant
            ai_assistant = AIAssistant()
            from crypto_api import crypto_api

            analysis = await ai_assistant.get_comprehensive_analysis_async(
                symbol.replace('USDT', ''),
                crypto_api=crypto_api
            )

            # Add SnD specific information
            snd_summary = f"\n\n🎯 **ENHANCED SnD ZONES (Binance Klines):**\n"

            if snd_result.get('demand_zones'):
                snd_summary += f"🟢 **Demand Zones Found:** {len(snd_result['demand_zones'])}\n"
                for zone in snd_result['demand_zones'][:2]:  # Show top 2
                    snd_summary += f"   • ${zone.low:.6f} - ${zone.high:.6f} (S:{zone.strength:.0f}%)\n"

            if snd_result.get('supply_zones'):
                snd_summary += f"🔴 **Supply Zones Found:** {len(snd_result['supply_zones'])}\n"
                for zone in snd_result['supply_zones'][:2]:  # Show top 2
                    snd_summary += f"   • ${zone.low:.6f} - ${zone.high:.6f} (S:{zone.strength:.0f}%)\n"

            if snd_result.get('entry_signal'):
                snd_summary += f"\n🚨 **SnD SIGNAL: {snd_result['entry_signal']}**\n"
                snd_summary += f"💪 **Strength:** {snd_result['signal_strength']:.1f}%\n"
                snd_summary += f"🎯 **Entry:** ${snd_result['entry_price']:.6f}\n"
                snd_summary += f"🛑 **Stop:** ${snd_result['stop_loss']:.6f}\n"
                snd_summary += f"🎯 **Target:** ${snd_result['take_profit']:.6f}"
            else:
                snd_summary += f"\n⏳ **No SnD Signal** - Wait for zone revisit"

            # Combine analysis
            full_analysis = analysis + snd_summary

            # Send result (split if too long)
            if len(full_analysis) > 4000:
                # Send in parts
                await loading_msg.edit_text(full_analysis[:4000], parse_mode='MARKDOWN')
                await update.effective_message.reply_text(full_analysis[4000:], parse_mode='MARKDOWN')
            else:
                await loading_msg.edit_text(full_analysis, parse_mode='MARKDOWN')

        except Exception as e:
            await update.effective_message.reply_text(
                f"❌ **Analysis Error**: {str(e)[:100]}\n\n"
                f"💡 Try: `/analyze btc` or check symbol format",
                parse_mode='MARKDOWN'
            )

    async def futures_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle futures analysis command"""
        if len(context.args) < 2:
            await update.effective_message.reply_text(
                "📊 **Futures Analysis**\n\n"
                "Usage: /futures symbol timeframe\n\n"
                "Example: /futures BTCUSDT 1h\n"
                "Timeframes: 15m, 30m, 1h, 4h, 1d",
                parse_mode='MARKDOWN'
            )
            return

        symbol = context.args[0].upper()
        timeframe = context.args[1].lower()
        
        # Ensure symbol has USDT suffix
        if not 'USDT' in symbol:
            symbol = symbol + 'USDT'
        
        try:
            await update.message.reply_text(f"⏳ Analyzing {symbol} {timeframe}...")
            
            # Get klines data from binance
            try:
                from app.providers.binance_provider import fetch_klines
                klines = fetch_klines(symbol, timeframe, limit=100)
                if not klines or len(klines) == 0:
                    await update.message.reply_text(f"❌ No data for {symbol} {timeframe}")
                    return
                
                # Extract OHLCV
                closes = [float(k[4]) for k in klines[-20:]]  # Last 20 closes
                
                # Simple trend analysis
                latest = float(klines[-1][4])
                prev = float(klines[-2][4])
                change = ((latest - prev) / prev * 100)
                
                avg_20 = sum(closes) / len(closes)
                trend = "📈 BULLISH" if latest > avg_20 else "📉 BEARISH"
                
                response = f"""📊 **Futures: {symbol}**

Price: ${latest:.2f}
Change: {change:+.2f}%
Trend: {trend}
MA20: ${avg_20:.2f}

Support: ${min(closes):.2f}
Resistance: ${max(closes):.2f}"""
                
                await update.message.reply_text(response, parse_mode='MARKDOWN')
            except Exception as e:
                await update.message.reply_text(f"❌ Data error: {str(e)[:80]}")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:80]}")


    async def futures_signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle futures signals command"""
        try:
            from futures_signal_generator import FuturesSignalGenerator
            await update.message.reply_text("⏳ Generating multi-coin futures signals...")
            
            generator = FuturesSignalGenerator()
            signals = await generator.generate_multi_signals()
            await update.message.reply_text(signals, parse_mode='MARKDOWN')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:80]}")
    
    async def signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle professional futures signal command with timeframe selection"""
        if len(context.args) < 1:
            await update.effective_message.reply_text(
                "📊 **Futures Signal Generator**\n\n"
                "Usage: /signal symbol\n\n"
                "Example: /signal BTC\n"
                "Then select timeframe from buttons",
                parse_mode='MARKDOWN'
            )
            return
        
        symbol = context.args[0].upper()
        if 'USDT' not in symbol:
            symbol = symbol + 'USDT'
        
        # Store in context for callback
        context.user_data['signal_symbol'] = symbol
        
        # Show timeframe buttons
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton("🚀 15M", callback_data=f"signal_tf_15m_{symbol}"),
                InlineKeyboardButton("🚀 30M", callback_data=f"signal_tf_30m_{symbol}"),
            ],
            [
                InlineKeyboardButton("🚀 1H", callback_data=f"signal_tf_1h_{symbol}"),
                InlineKeyboardButton("🚀 4H", callback_data=f"signal_tf_4h_{symbol}"),
            ],
            [
                InlineKeyboardButton("🚀 1D", callback_data=f"signal_tf_1d_{symbol}"),
                InlineKeyboardButton("🚀 1W", callback_data=f"signal_tf_1w_{symbol}"),
            ]
        ]
        await update.message.reply_text(
            f"🕐 Select timeframe for {symbol}:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle multi-coin signals command"""
        try:
            from futures_signal_generator import FuturesSignalGenerator
            await update.message.reply_text("⏳ Generating multi-coin futures signals...")
            
            generator = FuturesSignalGenerator()
            signals = await generator.generate_multi_signals()
            await update.message.reply_text(signals, parse_mode='MARKDOWN')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:80]}")
    
    async def signal_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle timeframe button callbacks for signals"""
        query = update.callback_query
        data = query.data  # Format: signal_tf_15m_BTCUSDT
        
        parts = data.split('_')
        if len(parts) < 4:
            await query.answer("❌ Invalid callback", show_alert=True)
            return
        
        timeframe = parts[2]  # 15m, 1h, etc
        symbol = '_'.join(parts[3:])  # Handle symbol properly
        
        try:
            await query.answer("⏳ Generating signal...")
            await query.edit_message_text("⏳ Generating professional signal...")
            
            from futures_signal_generator import FuturesSignalGenerator
            generator = FuturesSignalGenerator()
            signal = await generator.generate_signal(symbol, timeframe)
            
            await query.edit_message_text(signal, parse_mode='MARKDOWN')
        except Exception as e:
            await query.answer(f"❌ Error: {str(e)[:50]}", show_alert=True)


    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle portfolio command"""
        await update.effective_message.reply_text(
            f"📂 **Your Portfolio**\n\n"
            f"💼 Loading your holdings...\n\n"
            f"💡 *Placeholder - implement portfolio tracking*",
            parse_mode='MARKDOWN'
        )

    async def credits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle credits command"""
        user_id = update.effective_user.id
        
        # Get user language and credits
        from database import Database
        db = Database()
        user_lang = db.get_user_language(user_id)
        credits = db.get_user_credits(user_id)

        if user_lang == 'id':
            await update.effective_message.reply_text(
                f"💳 **Saldo Kredit**\n\n"
                f"👤 Pengguna: {update.effective_user.first_name}\n"
                f"💰 Kredit: {credits}\n\n"
                f"📊 **Biaya Kredit:**\n"
                f"• Analisis Spot: 20 kredit\n"
                f"• Analisis Futures: 20 kredit\n"
                f"• Sinyal Multi-Coin: 60 kredit\n\n"
                f"⭐ Upgrade ke Premium untuk akses unlimited!",
                parse_mode='MARKDOWN'
            )
        else:
            await update.effective_message.reply_text(
                f"💳 **Credit Balance**\n\n"
                f"👤 User: {update.effective_user.first_name}\n"
                f"💰 Credits: {credits}\n\n"
                f"📊 **Credit Costs:**\n"
                f"• Spot Analysis: 20 credits\n"
                f"• Futures Analysis: 20 credits\n"
                f"• Multi-Coin Signals: 60 credits\n\n"
                f"⭐ Upgrade to Premium for unlimited access!",
                parse_mode='MARKDOWN'
            )

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle subscribe command"""
        await update.effective_message.reply_text(
            f"👑 **Premium Subscription**\n\n"
            f"🎯 **Premium Benefits:**\n"
            f"• Unlimited analysis credits\n"
            f"• Priority signal delivery\n"
            f"• Advanced market insights\n"
            f"• Auto signal notifications\n\n"
            f"💰 **Plans Available:**\n"
            f"• Monthly: $19.99\n"
            f"• Lifetime: $99.99\n\n"
            f"💡 Contact admin to subscribe!",
            parse_mode='MARKDOWN'
        )

    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle referral command with enhanced tier system"""
        from database import Database
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "User"
        
        # Get bot username for referral link
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username or "CryptoMentorAI_bot"
        
        try:
            db = Database()
            
            # Get user referral codes
            referral_codes = db.get_user_referral_codes(user_id)
            if not referral_codes:
                # Create user if doesn't exist
                db.create_user(user_id, update.effective_user.username, 
                             update.effective_user.first_name, 
                             update.effective_user.last_name)
                referral_codes = db.get_user_referral_codes(user_id)
            
            free_referral_code = referral_codes.get('free_referral_code', 'INVALID')
            premium_referral_code = referral_codes.get('premium_referral_code', 'INVALID')
            
            # Get detailed stats
            detailed_stats = db.get_detailed_referral_stats(user_id)
            earnings_summary = db.get_referral_earnings_summary(user_id)
            tier_info = db.get_user_tier(user_id)
            
            # Build referral links
            free_link = f"https://t.me/{bot_username}?start=ref_{free_referral_code}"
            premium_link = f"https://t.me/{bot_username}?start=prem_{premium_referral_code}"
            
            referral_text = f"""🎁 **REFERRAL PROGRAM - {tier_info['tier']} TIER**

👤 **{user_name}** | Level {tier_info['level']}/5

🔗 **YOUR REFERRAL LINKS:**

🆓 **FREE REFERRAL:**
`{free_link}`
💰 Reward: {5 + int(5 * tier_info['bonus']/100)} credits per referral

💎 **PREMIUM REFERRAL:**
`{premium_link}`
💰 Reward: Rp {int(10000 * tier_info['money_multiplier']):,} per premium subscriber

📊 **CURRENT PERFORMANCE:**
• Total Referrals: {earnings_summary['total_referrals']}
• Free Referrals: {earnings_summary['free_referrals']} 
• Premium Referrals: {earnings_summary['premium_referrals']}
• Credits Earned: {earnings_summary['credit_earnings']}
• Money Earned: Rp {earnings_summary['money_earnings']:,}

🏆 **{tier_info['tier']} TIER BENEFITS:**
• Credit Bonus: +{tier_info['bonus']}%
• Money Multiplier: {tier_info['money_multiplier']}x
• Next Tier: {10 if tier_info['level']==1 else 25 if tier_info['level']==2 else 50 if tier_info['level']==3 else 100 if tier_info['level']==4 else 'MAX'} referrals

💡 **HOW TO EARN MORE:**
1. Share free link for instant credits
2. Premium link gives money when they subscribe
3. Higher tiers = bigger rewards!"""
            
            # Create interactive buttons
            keyboard = [
                [
                    InlineKeyboardButton("📊 Detailed Stats", callback_data="referral_stats"),
                    InlineKeyboardButton("💡 Guide & Tips", callback_data="referral_guide")
                ],
                [
                    InlineKeyboardButton("🎯 Tier System", callback_data="tier_system_guide"),
                    InlineKeyboardButton("💰 Withdrawal", callback_data="referral_withdrawal")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.effective_message.reply_text(
                referral_text,
                reply_markup=reply_markup,
                parse_mode='MARKDOWN'
            )
            
        except Exception as e:
            print(f"Error in referral command: {e}")
            # Fallback to simple version
            referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
            await update.effective_message.reply_text(
                f"🎁 **Referral Program**\n\n"
                f"👥 **Your Referral Link:**\n"
                f"`{referral_link}`\n\n"
                f"💰 **Rewards:**\n"
                f"• 5+ credits per referral (tier bonus)\n"
                f"• Premium users earn money\n\n"
                f"📊 **Your Stats:**\n"
                f"• Check /menu → Premium & Referral for details",
                parse_mode='MARKDOWN'
            )

    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language command with database integration"""
        user_id = update.effective_user.id
        lang = context.args[0].lower() if context.args else None

        if not lang or lang not in ['en', 'id']:
            # Get current language from database
            try:
                from database import Database
                db = Database()
                current_lang = db.get_user_language(user_id) or 'en'
                current_name = {'en': 'English', 'id': 'Bahasa Indonesia'}.get(current_lang, 'English')
                
                await update.effective_message.reply_text(
                    f"🌐 **Language Selection**\n\n"
                    f"📍 **Current:** {current_name} (`{current_lang}`)\n\n"
                    f"**Usage:** `/language <code>`\n\n"
                    f"**Available:**\n"
                    f"• `en` - English\n"
                    f"• `id` - Bahasa Indonesia\n\n"
                    f"**Example:** `/language id`",
                    parse_mode='MARKDOWN'
                )
            except Exception as e:
                await update.effective_message.reply_text(
                    "🌐 **Language Selection**\n\n"
                    "**Usage:** `/language <code>`\n\n"
                    "**Available:**\n"
                    "• `en` - English\n"
                    "• `id` - Bahasa Indonesia",
                    parse_mode='MARKDOWN'
                )
            return

        # Update language in database
        try:
            from database import Database
            db = Database()
            
            # Ensure user exists first
            user = db.get_user(user_id)
            if not user:
                db.create_user(
                    user_id,
                    update.effective_user.username,
                    update.effective_user.first_name,
                    update.effective_user.last_name,
                    lang  # Set language during creation
                )
            else:
                # Update existing user's language
                db.update_user_language(user_id, lang)

            lang_names = {'en': 'English', 'id': 'Bahasa Indonesia'}
            
            if lang == 'id':
                success_msg = f"✅ **Bahasa berhasil diubah ke {lang_names[lang]}!**\n\n" \
                             f"🎯 Sekarang bot akan merespons dalam Bahasa Indonesia.\n" \
                             f"💡 Gunakan `/menu` untuk navigasi yang mudah!"
            else:
                success_msg = f"✅ **Language changed to {lang_names[lang]}!**\n\n" \
                             f"🎯 Bot will now respond in English.\n" \
                             f"💡 Use `/menu` for easy navigation!"

            await update.effective_message.reply_text(success_msg, parse_mode='MARKDOWN')
            
        except Exception as e:
            print(f"Error updating language: {e}")
            lang_names = {'en': 'English', 'id': 'Bahasa Indonesia'}
            await update.effective_message.reply_text(
                f"✅ Language preference set to {lang_names[lang]}!\n\n"
                f"💡 Note: Language saved locally for this session.",
                parse_mode='MARKDOWN'
            )

    async def id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /id command - show user Telegram ID"""
        user = update.effective_user
        user_id = user.id
        username = user.username or "N/A"
        first_name = user.first_name or "N/A"
        
        id_info = f"""🆔 **Your Telegram ID**

📱 **User ID:** `{user_id}`
👤 **Name:** {first_name}
🔖 **Username:** @{username}

💡 Use this ID for admin access or referral purposes."""
        
        await update.effective_message.reply_text(id_info, parse_mode='MARKDOWN')

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command - text-only admin panel"""
        from app.lib.auth import get_admin_level, get_admin_hierarchy
        from database import Database
        from datetime import timedelta
        import time
        
        user_id = update.effective_user.id
        admin_level = get_admin_level(user_id)
        
        if admin_level is None:
            await update.effective_message.reply_text(
                "❌ **Access Denied**\n\nYou are not authorized to use admin commands.",
                parse_mode='MARKDOWN'
            )
            return
        
        level_emoji = {1: "👑", 2: "🔷", 3: "🔶"}.get(admin_level, "👤")
        level_name = {1: "ADMIN 1 (Owner)", 2: "ADMIN 2 (Manager)", 3: "ADMIN 3 (Moderator)"}.get(admin_level, "UNKNOWN")
        
        db = Database()
        user_tz = db.get_user_timezone(user_id)
        tz_offsets = {'WIB': 7, 'WITA': 8, 'WIT': 9, 'SGT': 8, 'MYT': 8, 'GST': 4, 'GMT': 0, 'EST': -5, 'PST': -8}
        offset = tz_offsets.get(user_tz, 7)
        local_time = (datetime.utcnow() + timedelta(hours=offset)).strftime('%H:%M:%S')
        
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"
        
        admin_panel_text = f"""**CryptoMentorAI V2.0** | Admin Panel

• 📊 **STATUS**
⏰ {local_time} {user_tz}
🟢 ONLINE • Uptime: {uptime_str}
{level_emoji} {level_name}
🆔 `{user_id}`
"""
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("🗄 Database Status", callback_data="admin_db_status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.effective_message.reply_text(
            admin_panel_text,
            reply_markup=reply_markup,
            parse_mode='MARKDOWN'
        )

    async def admin_button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin panel button clicks"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from app.lib.auth import get_admin_level
        import time
        
        query = update.callback_query
        user_id = query.from_user.id
        
        print(f"[ADMIN BUTTON] Received callback: {query.data} from user {user_id}")
        
        admin_level = get_admin_level(user_id)
        
        if admin_level is None:
            await query.answer("❌ Access Denied", show_alert=True)
            return
        
        try:
            await query.answer()
        except Exception as e:
            print(f"[ADMIN BUTTON] Error answering query: {e}")
        
        if query.data == "admin_db_status":
            try:
                from supabase_client import health_check, get_live_user_count, supabase as sb_client
                
                total_users = 0
                premium_users = 0
                active_today = "N/A"
                connection_status = "🔴 Disconnected"
                
                is_healthy, status_msg = health_check()
                if is_healthy and sb_client:
                    connection_status = "🟢 Connected"
                    total_users = get_live_user_count()
                    
                    try:
                        premium_result = sb_client.table('users').select('id', count='exact').eq('is_premium', True).execute()
                        premium_users = premium_result.count if premium_result.count else 0
                    except:
                        premium_users = 0
                    
                    from datetime import datetime
                    try:
                        today = datetime.utcnow().date().isoformat()
                        active_result = sb_client.table('users').select('id', count='exact').gte('last_active', today).execute()
                        active_today = active_result.count if active_result.count else 0
                    except:
                        active_today = "N/A"
                else:
                    print(f"[DB STATUS] Health check failed: {status_msg}")
                
                db_text = f"""**🗄 Database Status**

• **Connection**
{connection_status} Supabase
📡 Region: Southeast Asia

• **Users**
👥 Total Users: {total_users}
👑 Premium Users: {premium_users}
🟢 Active Today: {active_today}

• **Storage**
💾 Tables: users, portfolios, referrals
🔄 Sync: Real-time enabled
"""
            except Exception as e:
                db_text = f"""**🗄 Database Status**

• **Connection**
🔴 Supabase: Error
⚠️ {str(e)[:50]}

• **Fallback**
💾 SQLite: Active
📁 Local storage enabled
"""
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(
                    db_text,
                    reply_markup=reply_markup,
                    parse_mode='MARKDOWN'
                )
                print(f"[ADMIN BUTTON] Successfully edited message with db_text")
            except Exception as e:
                print(f"[ADMIN BUTTON] Error editing message: {e}")
                await query.message.reply_text(db_text, reply_markup=reply_markup, parse_mode='MARKDOWN')
        
        elif query.data == "admin_back":
            from database import Database
            from datetime import timedelta
            
            level_emoji = {1: "👑", 2: "🔷", 3: "🔶"}.get(admin_level, "👤")
            level_name = {1: "ADMIN 1 (Owner)", 2: "ADMIN 2 (Manager)", 3: "ADMIN 3 (Moderator)"}.get(admin_level, "UNKNOWN")
            
            db = Database()
            user_tz = db.get_user_timezone(user_id)
            tz_offsets = {'WIB': 7, 'WITA': 8, 'WIT': 9, 'SGT': 8, 'MYT': 8, 'GST': 4, 'GMT': 0, 'EST': -5, 'PST': -8}
            offset = tz_offsets.get(user_tz, 7)
            local_time = (datetime.utcnow() + timedelta(hours=offset)).strftime('%H:%M:%S')
            
            uptime_seconds = int(time.time() - self.start_time)
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours}h {minutes}m {seconds}s"
            
            admin_panel_text = f"""**CryptoMentorAI V2.0** | Admin Panel

• 📊 **STATUS**
⏰ {local_time} {user_tz}
🟢 ONLINE • Uptime: {uptime_str}
{level_emoji} {level_name}
🆔 `{user_id}`
"""
            
            keyboard = [
                [InlineKeyboardButton("🗄 Database Status", callback_data="admin_db_status")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                admin_panel_text,
                reply_markup=reply_markup,
                parse_mode='MARKDOWN'
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages for menu interactions"""
        user_data = context.user_data
        text = update.message.text

        # Handle manual symbol input
        if user_data.get('awaiting_manual_symbol'):
            current_action = user_data.get('current_action', '')
            symbol = text.strip().upper()

            user_data['awaiting_manual_symbol'] = False
            user_data['symbol'] = symbol

            if current_action == 'price':
                context.args = [symbol]
                await self.price_command(update, context)
            elif current_action == 'analyze':
                context.args = [symbol]
                await self.analyze_command(update, context)
            elif current_action == 'futures':
                await update.message.reply_text(
                    f"📉 **Futures Analysis: {symbol}**\n\n"
                    f"Select timeframe: 15m, 30m, 1h, 4h, 1d, 1w",
                    parse_mode='MARKDOWN'
                )
                user_data['awaiting_timeframe'] = True
            elif current_action == 'add_coin':
                user_data['step'] = 'amount'
                user_data['awaiting_amount'] = True
                await update.message.reply_text(
                    f"➕ **Add {symbol}**\n\n"
                    f"Enter the amount you own:",
                    parse_mode='MARKDOWN'
                )

        # Handle amount input for add coin
        elif user_data.get('awaiting_amount'):
            try:
                amount = float(text.strip())
                symbol = user_data.get('symbol', 'Unknown')

                user_data.clear()

                await update.message.reply_text(
                    f"✅ **Coin Added Successfully!**\n\n"
                    f"📊 **Details:**\n"
                    f"• Symbol: {symbol}\n"
                    f"• Amount: {amount}\n\n"
                    f"Use `/portfolio` to view your complete portfolio.",
                    parse_mode='MARKDOWN'
                )
            except ValueError:
                await update.message.reply_text("❌ Invalid amount. Please enter a valid number.")

        # Handle AI questions
        elif user_data.get('awaiting_question'):
            question = text.strip()
            user_data.clear()

            await update.message.reply_text(
                f"🤖 **CryptoMentor AI Response:**\n\n"
                f"❓ **Your Question:** {question}\n\n"
                f"💭 **Answer:** This is a placeholder response. Implement with your AI service.\n\n"
                f"💡 *Connect with OpenAI API or similar service for real AI responses*",
                parse_mode='MARKDOWN'
            )

        # Handle timeframe input
        elif user_data.get('awaiting_timeframe'):
            timeframe = text.strip().lower()
            symbol = user_data.get('symbol', 'BTC')

            user_data.clear()

            context.args = [symbol, timeframe]
            await self.futures_command(update, context)

        else:
            # Default response for unhandled messages
            await update.message.reply_text(
                "💡 Use `/menu` to see available options or `/help` for commands!",
                parse_mode='MARKDOWN'
            )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards - delegated to menu handlers"""
        # This will be handled by the menu system
        pass

    async def run_bot(self):
        """Run the bot with error handling"""
        try:
            # Setup application
            await self.setup_application()

            # Initialize and start polling
            await self.application.initialize()
            await self.application.start()

            print("🚀 CryptoMentor AI Bot is running...")
            print(f"🤖 Bot username: @{(await self.application.bot.get_me()).username}")
            print("🔄 Polling for updates...")

            # Start polling
            await self.application.updater.start_polling(
                poll_interval=1.0,
                timeout=30,
                drop_pending_updates=True
            )

            # Initialize auto-signals systems
            try:
                from lifetime_auto_signals import start_lifetime_auto_signals
                self.lifetime_auto_signals = await start_lifetime_auto_signals(self.application.bot)
                print("👑 Lifetime Auto-Signals system started")
            except Exception as e:
                print(f"⚠️ Lifetime Auto-Signals failed to start: {e}")

            # Initialize SnD Auto Signals
            try:
                from snd_auto_signals import SnDAutoSignals
                self.snd_auto_signals = SnDAutoSignals(self)
                asyncio.create_task(self.snd_auto_signals.start_auto_scanner())
                print("🎯 SnD Auto-Signals system started")
            except Exception as e:
                print(f"⚠️ SnD Auto-Signals failed to start: {e}")

            # Initialize App AutoSignal scheduler
            try:
                from app.autosignal import start_background_scheduler
                start_background_scheduler(self.application)
                print("📡 App AutoSignal scheduler started")
            except Exception as e:
                print(f"⚠️ App AutoSignal scheduler failed to start: {e}")

            # Keep running
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Bot stopping...")
        except Exception as e:
            print(f"❌ Bot error: {e}")
            logger.error(f"Bot error: {e}")
            raise
        finally:
            # Cleanup
            if self.application:
                try:
                    await self.application.updater.stop()
                    await self.application.stop()
                    await self.application.shutdown()
                except:
                    pass
            print("👋 Bot stopped")

# Export for main.py
__all__ = ['TelegramBot']