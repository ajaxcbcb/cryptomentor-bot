import os
import logging
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file (if exists) and system environment
load_dotenv()

# Check deployment environment (Replit environments) - simplified for consistency
IS_DEPLOYMENT = (
    os.getenv('REPLIT_DEPLOYMENT') == '1' or 
    os.getenv('REPL_DEPLOYMENT') == '1'
)

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduced logging to save memory
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from telegram.constants import ParseMode

from database import Database
from crypto_api import CryptoAPI
from ai_assistant import AIAssistant

class TelegramBot:
    def __init__(self):
        # Get bot token from environment (Replit Secrets or .env)
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')

        # Get admin ID with better error handling
        admin_id_str = os.getenv('ADMIN_USER_ID', '0')
        try:
            self.admin_id = int(admin_id_str)
        except ValueError:
            logger.warning(f"Invalid ADMIN_USER_ID: {admin_id_str}, using default 0")
            self.admin_id = 0

        # Initialize components
        self.db = Database()
        self.crypto_api = CryptoAPI()
        self.ai = AIAssistant()

        # Initialize broadcast system
        self.pending_broadcast = None
        self.broadcast_in_progress = False

        # Validate token before creating application
        if not self.token:
            logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
            logger.error("💡 Please set TELEGRAM_BOT_TOKEN in Replit Secrets")
            logger.error("📝 Go to Secrets tab and add your bot token")
            sys.exit(1)

        # Initialize application with token
        try:
            self.application = Application.builder().token(self.token).build()
            logger.info("✅ Bot initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot: {e}")
            sys.exit(1)

    async def run_bot(self):
        """Main method to run the bot"""
        try:
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("price", self.price_command))
            self.application.add_handler(CommandHandler("analyze", self.analyze_command))
            self.application.add_handler(CommandHandler("portfolio", self.portfolio_command))
            self.application.add_handler(CommandHandler("add_coin", self.add_coin_command))
            self.application.add_handler(CommandHandler("market", self.market_command))
            self.application.add_handler(CommandHandler("futures_signals", self.futures_signals_command))
            self.application.add_handler(CommandHandler("futures", self.futures_command))
            self.application.add_handler(CommandHandler("credits", self.credits_command))
            self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
            self.application.add_handler(CommandHandler("referral", self.referral_command))
            self.application.add_handler(CommandHandler("language", self.language_command))
            self.application.add_handler(CommandHandler("ask_ai", self.handle_ask_ai))
            

            # Admin commands
            self.application.add_handler(CommandHandler("admin", self.admin_command))
            self.application.add_handler(CommandHandler("grant_premium", self.grant_premium_command))
            self.application.add_handler(CommandHandler("revoke_premium", self.revoke_premium_command))
            self.application.add_handler(CommandHandler("grant_credits", self.grant_credits_command))
            self.application.add_handler(CommandHandler("fix_all_credits", self.fix_all_credits_command))
            self.application.add_handler(CommandHandler("broadcast", self.broadcast_command))
            self.application.add_handler(CommandHandler("confirm_broadcast", self.confirm_broadcast_command))
            self.application.add_handler(CommandHandler("cancel_broadcast", self.cancel_broadcast_command))
            self.application.add_handler(CommandHandler("check_admin", self.check_admin_command))

            # Add callback query handler
            self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))

            # Add message handler for regular text (should be last)
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

            print("🤖 Bot handlers registered successfully")
            mode_text = "🌐 DEPLOYMENT MODE (Always On)" if IS_DEPLOYMENT else "🔧 DEVELOPMENT MODE (Workspace)"
            print(f"🌍 Environment: {mode_text}")
            print(f"🔑 API Status: BIN=✅, CG=✅, CN=✅ (Binance Primary + CoinGecko + CryptoNews)")
            print("🚀 Starting bot polling with Binance Advanced API integration...")

            # Start the bot with optimized polling for deployment
            print("✅ Bot is now running and polling for updates...")
            await self.application.run_polling(
                drop_pending_updates=True,  # Drop old updates on start
                pool_timeout=60,           # Longer pool timeout for deployment
                read_timeout=60,           # Longer read timeout 
                write_timeout=60,          # Longer write timeout
                connect_timeout=60,        # Longer connect timeout
                allowed_updates=['message', 'callback_query'],  # Only handle needed updates
                close_loop=False           # Don't close event loop
            )

        except Exception as e:
            # Handle specific Telegram conflicts
            if "terminated by other getUpdates request" in str(e) or "Conflict" in str(e):
                logger.error("❌ Bot conflict detected - forcing cleanup")
                print("⚠️  CONFLICT: Another bot instance detected!")
                print("🔄 Attempting automatic cleanup...")

                # Clear any pending broadcast to prevent errors
                self.pending_broadcast = None
                self.broadcast_in_progress = False

                # Force cleanup of conflicting instances
                try:
                    import subprocess
                    import signal
                    import psutil

                    # Kill any python processes running main.py
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if proc.info['name'] == 'python3' or proc.info['name'] == 'python':
                                cmdline = ' '.join(proc.info['cmdline'] or [])
                                if 'main.py' in cmdline and proc.pid != os.getpid():
                                    print(f"🛑 Terminating conflicting process: {proc.pid}")
                                    proc.terminate()
                                    proc.wait(timeout=3)
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                            pass

                    import time
                    time.sleep(5)  # Wait for cleanup
                    print("✅ Cleanup completed, restarting...")

                    # Force exit to restart cleanly
                    if IS_DEPLOYMENT:
                        print("🔄 Deployment will restart automatically...")
                        sys.exit(1)
                    else:
                        # Restart in development
                        print("🔄 Restarting bot...")
                        raise

                except ImportError:
                    print("⚠️ psutil not available, manual restart required")
                    if IS_DEPLOYMENT:
                        sys.exit(1)
                    else:
                        raise
                except Exception as cleanup_error:
                    print(f"⚠️ Cleanup failed: {cleanup_error}")
                    if IS_DEPLOYMENT:
                        sys.exit(1)
                    else:
                        raise
            else:
                logger.error(f"❌ Error running bot: {e}")
                raise
        finally:
            # Cleanup
            try:
                if self.application:
                    await self.application.stop()
                    await self.application.shutdown()
                print("🛑 Bot stopped gracefully")
            except Exception as e:
                logger.error(f"Error during bot shutdown: {e}")

    async def start_command(self, update: Update, context: CallbackContext):
        """Handle /start command"""
        user = update.effective_user

        try:
            # Check if user exists
            existing_user = self.db.get_user(user.id)

            if not existing_user:
                # Create new user with proper error handling
                success = self.db.create_user(
                    telegram_id=user.id,
                    username=user.username or 'no_username',
                    first_name=user.first_name or 'Unknown',
                    last_name=user.last_name,
                    language_code=user.language_code or 'id'
                )

                if success:
                    print(f"✅ New user created: {user.id} ({user.first_name})")
                    # Log user registration
                    self.db.log_user_activity(user.id, "user_registered", f"New user: {user.first_name}")
                else:
                    print(f"❌ Failed to create user: {user.id}")

            else:
                print(f"👤 Existing user: {user.id} ({existing_user.get('first_name')})")
                # Log user return
                self.db.log_user_activity(user.id, "user_returned", "User started bot again")

        except Exception as e:
            print(f"❌ Error in start command: {e}")
            # Continue anyway to not break user experience

        # Welcome message
        language = user.language_code or 'id'

        if language == 'id':
            welcome_text = f"""🎉 **Selamat datang di CryptoMentor AI, {user.first_name}!**

🤖 Saya adalah AI assistant crypto trading terlengkap dengan data real-time dari multiple API.

🚀 **Fitur Premium:**
• Analisis teknikal mendalam
• Signal futures real-time  
• Data multi-API (Binance + CoinGecko + CryptoNews)
• Portfolio tracker advanced
• Unlimited analysis

💎 **Credits System:**
• Analisis: 5 credits
• Market overview: 3 credits  
• Futures signals: 5 credits
• Premium users: Unlimited

📋 **Quick Start:**
• `/price btc` - Cek harga Bitcoin
• `/analyze eth` - Analisis Ethereum
• `/market` - Overview pasar
• `/help` - Panduan lengkap

Ketik command untuk memulai trading journey Anda! 📈"""

        else:
            welcome_text = f"""🎉 **Welcome to CryptoMentor AI, {user.first_name}!**

🤖 I'm your comprehensive crypto trading AI assistant with real-time multi-API data.

🚀 **Premium Features:**
• In-depth technical analysis
• Real-time futures signals
• Multi-API data (Binance + CoinGecko + CryptoNews)  
• Advanced portfolio tracker
• Unlimited analysis

💎 **Credits System:**
• Analysis: 5 credits
• Market overview: 3 credits
• Futures signals: 5 credits
• Premium users: Unlimited

📋 **Quick Start:**
• `/price btc` - Check Bitcoin price
• `/analyze eth` - Analyze Ethereum
• `/market` - Market overview
• `/help` - Complete guide

Type a command to start your trading journey! 📈"""

        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: CallbackContext):
        """Handle /help command"""
        help_text = """🤖 **CryptoMentor AI Bot - Help**

📊 **Harga & Data Pasar:**
• `/price <symbol>` - Harga real-time
• `/market` - Overview pasar komprehensif

📈 **Analisis Trading:**
• `/analyze <symbol>` - Analisis mendalam (20 credit)
• `/futures <symbol>` - Analisis futures dengan timeframe (20 credit)
• `/futures_signals` - Sinyal futures lengkap (30 credit)

💼 **Portfolio & Credit:**
• `/portfolio` - Lihat portfolio
• `/add_coin <symbol> <amount>` - Tambah ke portfolio
• `/credits` - Cek sisa credit
• `/subscribe` - Upgrade premium

🎯 **Lainnya:**
• `/ask_ai <pertanyaan>` - Tanya AI crypto
• `/referral` - Program referral
• `/language` - Ubah bahasa

💡 **Tips:**
- Ketik nama crypto langsung untuk harga cepat
- Fitur premium = unlimited access
- Gunakan referral untuk bonus credit

🔥 **New**: Analisis futures dengan entry point, TP, dan SL!"""
        try:
            await update.message.reply_text(help_text, parse_mode='Markdown')
        except Exception as e:
            # If markdown parsing fails, send without markdown
            await update.message.reply_text(help_text)
            print(f"Help command markdown error: {e}")

    async def price_command(self, update: Update, context: CallbackContext):
        """Handle /price command with enhanced real-time data"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/price <symbol>`\nContoh: `/price btc`", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()

        # Show loading with consistent status
        mode_text = "🌐 DEPLOYMENT" if IS_DEPLOYMENT else "🔧 DEVELOPMENT"
        loading_msg = await update.message.reply_text(f"⏳ Mengambil data real-time {symbol}... ({mode_text})")

        # Get comprehensive real-time data with API priority
        print(f"🔄 Fetching real-time data for {symbol} from multiple sources...")

        # Primary: Binance API for most accurate real-time prices
        price_data = self.crypto_api.get_binance_price(symbol)
        coingecko_data = None
        news_data = None

        # Secondary: CoinGecko for additional market data
        try:
            coingecko_data = self.crypto_api.get_price(symbol, force_refresh=True)
        except:
            pass

        # Tertiary: Get relevant news for context
        try:
            news_data = self.crypto_api.get_crypto_news(limit=1)
        except:
            pass

        if price_data and 'error' not in price_data and price_data.get('price', 0) > 0:
            source = price_data.get('source', 'unknown')

            # Enhanced source indicators with API health
            source_emoji = {
                'binance': '🟢 Binance API (Real-Time)',
                'binance_simple': '🟡 Binance Simple (Real-Time)', 
                'coingecko': '🔵 CoinGecko Pro (Real-Time)',
                'coingecko_free': '🔵 CoinGecko Free (Real-Time)',
                'mock_realtime': '🔄 Enhanced Market Simulation'
            }.get(source, '🔄 Market Data')

            is_real_api = source in ['binance', 'binance_simple', 'coingecko', 'coingecko_free']

            # Smart price formatting using crypto_api formatting function
            current_price = price_data.get('price', 0)
            price_format = self.crypto_api._format_price_display(current_price)

            change_24h = price_data.get('change_24h', 0)
            change_emoji = "📈" if change_24h >= 0 else "📉"
            change_color = "+" if change_24h >= 0 else ""

            message = f"""
📊 **{symbol} Real-Time Market Data**

💰 **Harga**: {price_format}
{change_emoji} **Perubahan 24j**: {change_color}{change_24h:.2f}%
"""

            # Enhanced data display
            if price_data.get('volume_24h', 0) > 0:
                volume = price_data.get('volume_24h', 0)
                if volume > 1000000000:
                    volume_format = f"${volume/1000000000:.2f}B"
                elif volume > 1000000:
                    volume_format = f"${volume/1000000:.1f}M"
                else:
                    volume_format = f"${volume:,.0f}"
                message += f"📊 **Volume 24j**: {volume_format}\n"

            # Add high/low if available
            if price_data.get('high_24h', 0) > 0 and price_data.get('low_24h', 0) > 0:
                high_24h = price_data.get('high_24h', 0)
                low_24h = price_data.get('low_24h', 0)
                if high_24h < 100:
                    high_format = f"${high_24h:.4f}"
                    low_format = f"${low_24h:.4f}"
                else:
                    high_format = f"${high_24h:,.2f}"
                    low_format = f"${low_24h:,.2f}"
                message += f"🔺 **High 24j**: {high_format}\n🔻 **Low 24j**: {low_format}\n"

            # API Status and timing
            current_time = datetime.now().strftime('%H:%M:%S WIB')
            message += f"""
⏰ **Update**: {current_time}
🔄 **Sumber**: {source_emoji}
"""

            # Multi-API status
            api_status = []
            if is_real_api:
                api_status.append("✅ Binance/CoinGecko")
            else:
                api_status.append("🔄 Real-time Simulation")

            if coingecko_data and coingecko_data.get('source') in ['coingecko', 'coingecko_free']:
                api_status.append("✅ CoinGecko")

            if news_data and len(news_data) > 0:
                api_status.append("✅ CryptoNews")

            message += f"🌐 **API Status**: {' | '.join(api_status)}\n"

            # Add latest crypto news context if available
            if news_data and len(news_data) > 0:
                latest_news = news_data[0]
                news_title = latest_news.get('title', '')[:60] + '...' if len(latest_news.get('title', '')) > 60 else latest_news.get('title', '')
                message += f"📰 **Crypto News**: {news_title}\n"

            message += f"🔗 **Mode**: {'🌐 Always On (Deployment)' if IS_DEPLOYMENT else '🔧 Development Workspace'}"
        else:
            message = f"❌ Tidak dapat menemukan data untuk {symbol}"

        await loading_msg.edit_text(message, parse_mode='Markdown')

    async def analyze_command(self, update: Update, context: CallbackContext):
        """Handle /analyze command - comprehensive analysis with news integration"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/analyze <symbol>`\nContoh: `/analyze btc`", parse_mode='Markdown')
            return

        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = user_id == self.admin_id

        # Check credits for non-premium, non-admin users
        if not is_premium and not is_admin and credits < 20:
            await update.message.reply_text("❌ Credit tidak cukup! Analisis komprehensif membutuhkan 20 credit. Gunakan `/credits` untuk melihat sisa credit Anda.", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()

        # Show loading message
        loading_msg = await update.message.reply_text("⏳ Menganalisis data komprehensif + berita crypto...")

        try:
            # Get price and futures data for comprehensive analysis
            price_data = self.crypto_api.get_price(symbol)
            futures_data = self.crypto_api.get_futures_data(symbol)

            # Use comprehensive analysis function with crypto_api for news
            analysis = self.ai.get_comprehensive_analysis(symbol, futures_data, price_data, 'id', self.crypto_api)

            # Deduct credit only for non-premium, non-admin users (20 credits for comprehensive analysis)
            if not is_premium and not is_admin:
                self.db.deduct_credit(user_id, 20)
                remaining_credits = self.db.get_user_credits(user_id)
                analysis += f"\n\n💳 Credit tersisa: {remaining_credits} (Analisis komprehensif: -20 credit)"
            elif is_premium:
                analysis += f"\n\n⭐ **Status Premium** - Unlimited Access"
            elif is_admin:
                analysis += f"\n\n👑 **Admin Access** - Unlimited"

            # Edit the loading message with the analysis
            await loading_msg.edit_text(analysis, parse_mode='Markdown')

        except Exception as e:
            await loading_msg.edit_text(f"❌ Terjadi kesalahan: {str(e)}")
            print(f"Error in analyze command: {e}")

    async def portfolio_command(self, update: Update, context: CallbackContext):
        """Handle /portfolio command"""
        user_id = update.message.from_user.id
        portfolio = self.db.get_user_portfolio(user_id)

        if not portfolio:
            message = """
💼 **Portfolio Anda kosong**

Gunakan `/add_coin <symbol> <amount>` untuk menambah koin ke portfolio.
Contoh: `/add_coin btc 0.5`
            """
        else:
            message = "💼 **Portfolio Anda:**\n\n"
            total_value = 0

            for coin in portfolio:
                symbol = coin['symbol']
                amount = coin['amount']
                price_data = self.crypto_api.get_price(symbol)

                if price_data:
                    current_price = price_data.get('price', 0)
                    value = amount * current_price
                    total_value += value

                    message += f"• {symbol}: {amount} koin (${value:,.2f})\n"

            message += f"\n💰 **Total Value: ${total_value:,.2f}**"

        await update.message.reply_text(message, parse_mode='Markdown')

    async def add_coin_command(self, update: Update, context: CallbackContext):
        """Handle /add_coin command"""
        if len(context.args) < 2:
            await update.message.reply_text("❌ Gunakan format: `/add_coin <symbol> <amount>`\nContoh: `/add_coin btc 0.5`")
            return

        user_id = update.message.from_user.id
        symbol = context.args[0].upper()

        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Amount harus berupa angka!")
            return

        # Add to portfolio
        self.db.add_to_portfolio(user_id, symbol, amount)

        message = f"✅ Berhasil menambahkan {amount} {symbol} ke portfolio Anda!"
        await update.message.reply_text(message)

    async def market_command(self, update: Update, context: CallbackContext):
        """Handle /market command"""
        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = user_id == self.admin_id

        # Check credits for non-premium, non-admin users
        if not is_premium and not is_admin and credits < 20:
            await update.message.reply_text("❌ Credit tidak cukup! Overview pasar membutuhkan 20 credit. Gunakan `/credits` untuk melihat sisa credit Anda.", parse_mode='Markdown')
            return

        # Show loading message for comprehensive analysis
        loading_msg = await update.message.reply_text("⏳ Menganalisis overview pasar crypto real-time...")

        try:
            # Get comprehensive market overview with real-time data
            market_data = self.ai.get_market_sentiment('id', self.crypto_api)

            # Deduct credit only for non-premium, non-admin users (20 credits for market overview)
            if not is_premium and not is_admin:
                self.db.deduct_credit(user_id, 20)
                remaining_credits = self.db.get_user_credits(user_id)
                market_data += f"\n\n💳 Credit tersisa: {remaining_credits} (Overview pasar: -20 credit)"
            elif is_premium:
                market_data += f"\n\n⭐ **Status Premium** - Unlimited Access"
            elif is_admin:
                market_data += f"\n\n👑 **Admin Access** - Unlimited"

            # Edit loading message with the comprehensive overview
            await loading_msg.edit_text(market_data, parse_mode='Markdown')

        except Exception as e:
            await loading_msg.edit_text(f"❌ Terjadi kesalahan saat menganalisis pasar: {str(e)}")
            print(f"Error in market command: {e}")

    async def futures_signals_command(self, update: Update, context: CallbackContext):
        """Handle /futures_signals command with real-time data"""
        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = user_id == self.admin_id

        # Check credits for non-premium, non-admin users
        if not is_premium and not is_admin and credits < 30:
            await update.message.reply_text("❌ Credit tidak cukup! Sinyal futures membutuhkan 30 credit. Gunakan `/credits` untuk melihat sisa credit Anda.", parse_mode='Markdown')
            return

        # Show loading message
        loading_msg = await update.message.reply_text("⏳ Menganalisis sinyal futures real-time...")

        try:
            # Verify API connection first
            if not self.crypto_api:
                await loading_msg.edit_text("❌ API tidak tersedia. Silakan coba lagi nanti.")
                return

            print(f"🔄 Generating futures signals for user {user_id}")

            # Generate signals with proper error handling
            signals = self.ai.generate_futures_signals('id', self.crypto_api)

            if not signals or len(signals.strip()) < 50:
                await loading_msg.edit_text("❌ Gagal mengambil data sinyal futures. Silakan coba lagi dalam beberapa menit.")
                return

            # Deduct credit only for non-premium, non-admin users (30 credits for futures signals)
            if not is_premium and not is_admin:
                self.db.deduct_credit(user_id, 30)
                remaining_credits = self.db.get_user_credits(user_id)
                signals += f"\n\n💳 Credit tersisa: {remaining_credits} (Sinyal futures: -30 credit)"
            elif is_premium:
                signals += f"\n\n⭐ **Status Premium** - Unlimited Access"
            elif is_admin:
                signals += f"\n\n👑 **Admin Access** - Unlimited"

            print(f"✅ Futures signals generated successfully for user {user_id}")

            # Split long messages if needed
            if len(signals) > 4000:
                # Split into chunks
                chunks = [signals[i:i+4000] for i in range(0, len(signals), 4000)]
                await loading_msg.edit_text(chunks[0], parse_mode='Markdown')

                for chunk in chunks[1:]:
                    await update.message.reply_text(chunk, parse_mode='Markdown')
            else:
                # Edit the loading message with the signals
                await loading_msg.edit_text(signals, parse_mode='Markdown')

        except Exception as e:
            error_msg = f"❌ Terjadi kesalahan saat menganalisis sinyal futures: {str(e)[:100]}"
            await loading_msg.edit_text(error_msg)
            print(f"Error in futures_signals command: {e}")
            import traceback
            traceback.print_exc()

    async def futures_command(self, update: Update, context: CallbackContext):
        """Handle /futures command with timeframe selection"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/futures <symbol>`\nContoh: `/futures btc`", parse_mode='Markdown')
            return

        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = user_id == self.admin_id

        # Check credits for non-premium, non-admin users (20 credits for futures analysis)
        if not is_premium and not is_admin and credits < 20:
            await update.message.reply_text("❌ Credit tidak cukup! Analisis futures membutuhkan 20 credit. Gunakan `/credits` untuk melihat sisa credit Anda.", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()

        # Show timeframe selection with inline keyboard
        keyboard = [
            [InlineKeyboardButton("⚡ 15m", callback_data=f'futures_tf_{symbol}_15m'),
             InlineKeyboardButton("🔥 30m", callback_data=f'futures_tf_{symbol}_30m')],
            [InlineKeyboardButton("📈 1h", callback_data=f'futures_tf_{symbol}_1h'),
             InlineKeyboardButton("🚀 4h", callback_data=f'futures_tf_{symbol}_4h')],
            [InlineKeyboardButton("💎 1d", callback_data=f'futures_tf_{symbol}_1d'),
             InlineKeyboardButton("🌟 1w", callback_data=f'futures_tf_{symbol}_1w')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📊 **Analisis Futures {symbol}**\n\n"
            "Pilih timeframe untuk analisis teknikal advance:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def credits_command(self, update: Update, context: CallbackContext):
        """Handle /credits command"""
        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = user_id == self.admin_id

        if is_admin:
            message = f"""
💳 **Credit Information - Admin**

👑 Status: **ADMIN** 
♾️ Credit: **UNLIMITED**
🛠️ Akses penuh semua fitur dan kontrol bot!

Selamat mengelola CryptoMentor AI!
            """
        elif is_premium:
            message = f"""
💳 **Credit Information - Premium User**

⭐ Status: **PREMIUM** 
♾️ Credit: **UNLIMITED**
🚀 Akses penuh semua fitur!

Terima kasih telah menjadi member premium!
            """
        else:
            message = f"""
💳 **Credit Information - Free User**

💰 Credit tersisa: **{credits}**
📊 **Biaya per fitur:**
• `/analyze` - 20 credit (analisis komprehensif)
• `/futures` - 20 credit (analisis futures 1 coin)
• `/futures_signals` - 30 credit (sinyal futures lengkap)
• `/market` - 20 credit (overview pasar)
• Fitur lain - Gratis
🎁 User baru mendapat 10 credit gratis

💡 **Cara mendapat lebih banyak credit:**
• `/referral` - Ajak teman (10 credit/referral)
• `/subscribe` - Upgrade ke Premium (unlimited)

Gunakan credit dengan bijak!
            """
        await update.message.reply_text(message, parse_mode='Markdown')

    async def subscribe_command(self, update: Update, context: CallbackContext):
        """Handle /subscribe command"""
        user_id = update.message.from_user.id
        username = update.message.from_user.username or "Tidak ada username"
        first_name = update.message.from_user.first_name or ""

        message = f"""⭐ **Upgrade ke Premium**

👤 **Informasi Anda:**
• **User ID:** {user_id}
• **Username:** @{username}
• **Nama:** {first_name}

🚀 **Fitur Premium:**
• ♾️ Unlimited analisis
• 📊 Analisis futures lengkap
• 🚨 Alert harga real-time
• 📈 Sinyal trading premium
• 🎯 Support prioritas
• 🔔 Notifikasi breakout otomatis

💰 **Harga Premium:**
• Rp 320.000 (per bulan)

💳 **Metode Pembayaran:**

🏦 **Transfer Bank:**
• Bank Mandiri
• A/N: NABIL FARREL AL FARI
• No. Rek: 1560018407074

📱 **E-Wallet:**
• Shopee Pay / Dana / GO-PAY
• No. HP: 087779274400

📋 **Cara Upgrade:**
1. Transfer Rp 320.000
2. Kirim bukti pembayaran ke admin @Billfarr
3. Sertakan informasi ini:
   • User ID: {user_id}
   • Username: @{username}
   • Nama: {first_name}
4. Tunggu konfirmasi aktivasi (maks 24 jam)

⚡ **Promo Khusus:**
Daftar sekarang dan dapatkan 7 hari trial GRATIS!

💬 **Butuh bantuan?** Chat admin @Billfarr

ℹ️ **Catatan Penting:** 
Pastikan menyertakan User ID ({user_id}) dalam pesan ke admin untuk mempercepat proses aktivasi premium."""
        
        try:
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            # If markdown parsing fails, send without markdown
            await update.message.reply_text(message)
            print(f"Subscribe command markdown error: {e}")

    async def referral_command(self, update: Update, context: CallbackContext):
        """Handle /referral command"""
        user_id = update.message.from_user.id
        username = update.message.from_user.username or "no_username"

        message = f"""🎁 **Program Referral**

👤 **Link Referral Anda:**
`https://t.me/YourBotUsername?start=ref_{user_id}`

💰 **Keuntungan:**
• Dapatkan 10 credit untuk setiap referral berhasil
• Teman Anda juga mendapat bonus 5 credit
• Unlimited referrals!

📊 **Status Referral:**
• Total Referrals: 0
• Credit Earned: 0

Bagikan link Anda dan mulai earning!"""
        
        await update.message.reply_text(message, parse_mode='Markdown')

    async def language_command(self, update: Update, context: CallbackContext):
        """Handle /language command"""
        keyboard = [
            [InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data='lang_id')],
            [InlineKeyboardButton("🇺🇸 English", callback_data='lang_en')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🌍 **Pilih Bahasa / Choose Language**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def grant_premium_command(self, update: Update, context: CallbackContext):
        """Handle /grant_premium command"""
        user_id = update.message.from_user.id

        # Enhanced admin check
        if user_id != self.admin_id:
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if len(context.args) < 1:
            await update.message.reply_text(
                "❌ **Format salah!**\n\n"
                "Gunakan: `/grant_premium <user_id> [days]`\n\n"
                "**Contoh:**\n"
                "• `/grant_premium 123456789 30` - Premium 30 hari\n"
                "• `/grant_premium 123456789 0` - Premium permanent\n"
                "• `/grant_premium 123456789` - Premium 30 hari (default)",
                parse_mode='Markdown'
            )
            return

        try:
            target_user_id = int(context.args[0])
            days = int(context.args[1]) if len(context.args) > 1 else 30
        except ValueError:
            await update.message.reply_text("❌ User ID dan days harus berupa angka!\n\nContoh: `/grant_premium 123456789 30`")
            return

        # Validate user ID
        if target_user_id <= 0:
            await update.message.reply_text("❌ User ID tidak valid!")
            return

        # Check if user exists in database
        existing_user = self.db.get_user(target_user_id)
        if not existing_user:
            await update.message.reply_text(
                f"⚠️ **User {target_user_id} belum terdaftar!**\n\n"
                "User harus menggunakan bot terlebih dahulu dengan command `/start` sebelum bisa diberi premium."
            )
            return

        # Show current status
        is_currently_premium = self.db.is_user_premium(target_user_id)
        current_credits = self.db.get_user_credits(target_user_id)

        # Grant premium status
        try:
            if days == 0:
                success = self.db.grant_permanent_premium(target_user_id)
                premium_type = "permanent"
            else:
                success = self.db.grant_premium(target_user_id, days)
                premium_type = f"{days} hari"

            if success:
                # Get user info for confirmation
                user_info = self.db.get_user(target_user_id)
                username = user_info.get('username', 'No username')
                first_name = user_info.get('first_name', 'Unknown')

                message = f"""✅ **Premium berhasil diberikan!**

👤 **User Info:**
• **ID**: {target_user_id}
• **Name**: {first_name}
• **Username**: @{username}

⭐ **Premium Status:**
• **Type**: {premium_type}
• **Previous**: {"Premium" if is_currently_premium else "Free"}
• **Current Credits**: {current_credits}

🎉 User sekarang memiliki akses unlimited ke semua fitur premium!"""

                # Log admin action
                self.db.log_user_activity(
                    user_id, 
                    "admin_grant_premium", 
                    f"Granted {premium_type} premium to user {target_user_id}"
                )

            else:
                message = f"""❌ **Gagal memberikan premium!**

🔍 **Troubleshooting:**
• Pastikan User ID benar: {target_user_id}
• User harus sudah menggunakan `/start` di bot
• Cek koneksi database

⚠️ Coba lagi atau hubungi developer."""

        except Exception as e:
            message = f"""❌ **Error sistem saat memberikan premium!**

**Error**: {str(e)}
**User ID**: {target_user_id}

🔧 Silakan coba lagi atau restart bot."""
            print(f"Error in grant_premium_command: {e}")

        await update.message.reply_text(message, parse_mode='Markdown')

    async def revoke_premium_command(self, update: Update, context: CallbackContext):
        """Handle /revoke_premium command"""
        user_id = update.message.from_user.id

        if user_id != self.admin_id:
            return

        if len(context.args) < 1:
            await update.message.reply_text("❌ Gunakan format: `/revoke_premium <user_id>`", parse_mode='Markdown')
            return

        try:
            target_user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ User ID harus berupa angka!")
            return

        # Revoke premium status
        success = self.db.revoke_premium(target_user_id)
        
        if success:
            message = f"✅ Berhasil mencabut premium dari user {target_user_id}"
        else:
            message = f"❌ Gagal mencabut premium dari user {target_user_id}"

        await update.message.reply_text(message)

    async def grant_credits_command(self, update: Update, context: CallbackContext):
        """Handle /grant_credits command"""
        user_id = update.message.from_user.id

        if user_id != self.admin_id:
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ **Format salah!**\n\n"
                "Gunakan: `/grant_credits <user_id> <amount>`\n\n"
                "**Contoh:**\n"
                "• `/grant_credits 123456789 50`\n"
                "• `/grant_credits 123456789 100`",
                parse_mode='Markdown'
            )
            return

        try:
            target_user_id = int(context.args[0])
            amount = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ User ID dan amount harus berupa angka!")
            return

        # Validate inputs
        if target_user_id <= 0:
            await update.message.reply_text("❌ User ID tidak valid!")
            return

        if amount <= 0:
            await update.message.reply_text("❌ Amount harus lebih dari 0!")
            return

        # Check if user exists
        existing_user = self.db.get_user(target_user_id)
        if not existing_user:
            await update.message.reply_text(
                f"⚠️ **User {target_user_id} belum terdaftar!**\n\n"
                "User harus menggunakan bot terlebih dahulu dengan command `/start`."
            )
            return

        # Get current credits
        current_credits = self.db.get_user_credits(target_user_id)

        # Grant credits
        success = self.db.add_credits(target_user_id, amount)
        
        if success:
            new_credits = self.db.get_user_credits(target_user_id)
            user_info = self.db.get_user(target_user_id)
            username = user_info.get('username', 'No username')
            first_name = user_info.get('first_name', 'Unknown')

            message = f"""✅ **Credits berhasil diberikan!**

👤 **User Info:**
• **ID**: {target_user_id}
• **Name**: {first_name}
• **Username**: @{username}

💰 **Credits Update:**
• **Previous**: {current_credits} credits
• **Added**: +{amount} credits
• **New Total**: {new_credits} credits"""

            # Log admin action
            self.db.log_user_activity(
                user_id, 
                "admin_grant_credits", 
                f"Granted {amount} credits to user {target_user_id}"
            )
        else:
            message = f"""❌ **Gagal memberikan credits!**

🔍 **Troubleshooting:**
• Pastikan User ID benar: {target_user_id}
• User harus sudah terdaftar di bot
• Cek koneksi database

⚠️ Coba lagi atau hubungi developer."""

        await update.message.reply_text(message, parse_mode='Markdown')

    async def fix_all_credits_command(self, update: Update, context: CallbackContext):
        """Handle /fix_all_credits command"""
        user_id = update.message.from_user.id

        if user_id != self.admin_id:
            return

        try:
            # Fix all users with 0 or negative credits
            fixed_count = self.db.fix_user_credits()
            message = f"✅ Berhasil memperbaiki credit untuk {fixed_count} user"
        except Exception as e:
            message = f"❌ Gagal memperbaiki credit: {str(e)}"

        await update.message.reply_text(message)

    async def broadcast_command(self, update: Update, context: CallbackContext):
        """Handle /broadcast command"""
        user_id = update.message.from_user.id

        if user_id != self.admin_id:
            return

        if not context.args:
            await update.message.reply_text(
                "📢 **Broadcast Command**\n\n"
                "Gunakan format: `/broadcast <message>`\n\n"
                "Contoh:\n"
                "`/broadcast 🚀 Update Fitur Baru!\n\n"
                "✅ Analisis real-time telah ditingkatkan\n"
                "📊 Dashboard baru tersedia\n\n"
                "Terima kasih telah menggunakan CryptoMentor AI!`\n\n"
                "💡 **Tips:**\n"
                "• Ketik pesan natural dengan enter untuk baris baru\n"
                "• Gunakan **text** untuk bold\n"
                "• Format akan dipertahankan seperti yang Anda ketik\n"
                "• Gunakan emoji untuk menarik perhatian",
                parse_mode='Markdown'
            )
            return

        # Get the original message text after "/broadcast "
        original_text = update.message.text
        if original_text and original_text.startswith('/broadcast '):
            message = original_text[11:]  # Remove "/broadcast " prefix
        else:
            message = " ".join(context.args)

        # Validate message length
        if len(message.strip()) == 0:
            await update.message.reply_text("❌ Pesan broadcast tidak boleh kosong!")
            return

        if len(message) > 4000:
            await update.message.reply_text("❌ Pesan terlalu panjang! Maksimal 4000 karakter.")
            return

        # Store broadcast message temporarily with admin ID
        self.pending_broadcast = {
            'message': message,
            'admin_id': user_id,
            'timestamp': datetime.now()
        }

        # Escape markdown characters in user message to prevent parsing errors
        def escape_markdown(text):
            """Escape markdown special characters"""
            escape_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in escape_chars:
                text = text.replace(char, f'\\{char}')
            return text

        escaped_message = escape_markdown(message)

        confirmation_message = f"""📢 **Konfirmasi Broadcast**

**Pesan yang akan dikirim:**
```
{escaped_message}
```

**Warning:** Pesan ini akan dikirim ke SEMUA user bot!

Gunakan:
• `/confirm_broadcast` untuk mengirim
• `/cancel_broadcast` untuk membatalkan

⏰ **Timeout:** Konfirmasi akan expired dalam 10 menit."""

        await update.message.reply_text(confirmation_message, parse_mode='MarkdownV2')

    async def confirm_broadcast_command(self, update: Update, context: CallbackContext):
        """Handle /confirm_broadcast command"""
        user_id = update.message.from_user.id

        if user_id != self.admin_id:
            await update.message.reply_text("❌ Perintah ini hanya untuk admin!")
            return

        if not self.pending_broadcast:
            await update.message.reply_text("❌ Tidak ada broadcast yang tertunda!")
            return

        # Check if the admin who created the broadcast is the same as confirming
        if self.pending_broadcast.get('admin_id') != user_id:
            await update.message.reply_text("❌ Hanya admin yang membuat broadcast yang bisa mengkonfirmasi!")
            return

        # Check timeout (10 minutes)
        broadcast_time = self.pending_broadcast.get('timestamp')
        if broadcast_time and (datetime.now() - broadcast_time).total_seconds() > 600:
            self.pending_broadcast = None
            await update.message.reply_text("❌ Broadcast expired! Silakan buat broadcast baru.")
            return

        # Set broadcast in progress
        self.broadcast_in_progress = True
        broadcast_message = self.pending_broadcast['message']

        try:
            # Get all users with better error handling
            all_users = self.db.get_all_users()

            if not all_users:
                self.pending_broadcast = None
                self.broadcast_in_progress = False
                await update.message.reply_text("❌ Tidak ada user yang ditemukan di database!")
                return

            success_count = 0
            fail_count = 0
            blocked_count = 0
            total_users = len(all_users)

            status_msg = await update.message.reply_text(f"📢 Memulai broadcast ke {total_users} user...")
            print(f"🔄 Starting broadcast to {total_users} users")
            print(f"📝 Broadcast message: {broadcast_message[:100]}...")

            # Enhanced broadcast with better error handling and rate limiting
            for i, user in enumerate(all_users):
                user_id_target = user.get('user_id')
                if not user_id_target or not isinstance(user_id_target, int):
                    fail_count += 1
                    print(f"❌ Invalid user_id: {user_id_target}")
                    continue

                try:
                    # Clean the message to avoid any encoding issues
                    clean_message = str(broadcast_message).strip()
                    if not clean_message:
                        clean_message = "📢 Pesan broadcast dari admin"

                    # Send message with safer parameters
                    await context.bot.send_message(
                        chat_id=int(user_id_target),
                        text=clean_message,
                        parse_mode=None,  # No markdown to avoid parsing errors
                        disable_web_page_preview=True,
                        disable_notification=False,
                        read_timeout=60,     # Increased timeout
                        write_timeout=60,    # Increased timeout
                        connect_timeout=60   # Increased timeout
                    )
                    success_count += 1
                    print(f"✅ Sent to user {user_id_target} ({success_count}/{total_users})")

                    # Update progress every 20 users or at key milestones
                    if (i + 1) % 20 == 0 or (i + 1) in [5, 10, 25, 50, 100]:
                        try:
                            progress_text = f"📢 Broadcast progress: {i + 1}/{total_users}\n✅ Berhasil: {success_count} | 🚫 Blocked: {blocked_count} | ❌ Error: {fail_count}"
                            await status_msg.edit_text(progress_text)
                        except Exception as edit_error:
                            print(f"Progress update failed: {edit_error}")

                    # Improved rate limiting - slower but more reliable
                    await asyncio.sleep(0.5)  # 500ms delay for better Telegram compliance

                except Exception as e:
                    error_str = str(e).lower()
                    print(f"❌ Broadcast failed for user {user_id_target}: {e}")

                    # Enhanced error categorization
                    if any(keyword in error_str for keyword in [
                        'blocked', 'forbidden', 'chat not found', 
                        'user is deactivated', 'bot was kicked',
                        'user has deleted their account',
                        'user_deactivated', 'chat_not_found'
                    ]):
                        blocked_count += 1
                        print(f"🚫 User {user_id_target} blocked/deleted/deactivated")
                    elif any(keyword in error_str for keyword in [
                        'flood control', 'too many requests', 'retry after', 'rate limit'
                    ]):
                        print(f"⏳ Rate limited, waiting longer...")
                        await asyncio.sleep(5)  # Wait 5 seconds for rate limits
                        # Retry once with longer delay
                        try:
                            await context.bot.send_message(
                                chat_id=int(user_id_target),
                                text=clean_message,
                                parse_mode=None,
                                disable_web_page_preview=True,
                                read_timeout=60,
                                write_timeout=60,
                                connect_timeout=60
                            )
                            success_count += 1
                            print(f"✅ Retry successful for user {user_id_target}")
                            await asyncio.sleep(1)  # Extra delay after retry
                        except Exception as retry_error:
                            fail_count += 1
                            print(f"❌ Retry failed for user {user_id_target}: {retry_error}")
                    else:
                        fail_count += 1
                        print(f"❌ Unknown error for user {user_id_target}: {error_str}")

            # Calculate final statistics
            total_attempted = success_count + fail_count + blocked_count
            success_rate = (success_count / total_attempted * 100) if total_attempted > 0 else 0

            result_message = f"""✅ **Broadcast Selesai!**

📊 **Statistik Lengkap:**
• ✅ **Berhasil terkirim**: {success_count} user
• 🚫 **User blocked/inactive**: {blocked_count} user  
• ❌ **Error/timeout**: {fail_count} user
• 📊 **Total user database**: {total_users} user
• 📈 **Success rate**: {success_rate:.1f}%

⏰ **Selesai**: {datetime.now().strftime('%H:%M:%S WIB')}

💡 **Catatan**: Success rate 60%+ adalah normal karena banyak user inactive/blocked bot."""

            print(f"📊 Broadcast completed: {success_count}/{total_users} successful ({success_rate:.1f}%)")

            try:
                await status_msg.edit_text(result_message, parse_mode='Markdown')
            except Exception as e:
                print(f"Failed to edit status message: {e}")
                # Send new message if edit fails
                try:
                    await update.message.reply_text(result_message, parse_mode='Markdown')
                except Exception as e2:
                    print(f"Failed to send result message: {e2}")
                    # Final fallback - plain text
                    await update.message.reply_text(f"Broadcast selesai: {success_count}/{total_users} berhasil")

        except Exception as e:
            error_message = f"❌ Critical error during broadcast: {str(e)}"
            print(f"Critical broadcast error: {e}")
            import traceback
            traceback.print_exc()
            try:
                await update.message.reply_text(error_message)
            except Exception:
                print(f"Failed to send error message: {error_message}")
        finally:
            # Always clear broadcast state
            self.pending_broadcast = None
            self.broadcast_in_progress = False
            print("🔄 Broadcast state cleared")

    async def cancel_broadcast_command(self, update: Update, context: CallbackContext):
        """Handle /cancel_broadcast command"""
        user_id = update.message.from_user.id

        if user_id != self.admin_id:
            await update.message.reply_text("❌ Perintah ini hanya untuk admin!")
            return

        if not self.pending_broadcast:
            await update.message.reply_text("❌ Tidak ada broadcast yang tertunda!")
            return

        # Check if the admin who created the broadcast is the same as canceling
        if self.pending_broadcast.get('admin_id') != user_id:
            await update.message.reply_text("❌ Hanya admin yang membuat broadcast yang bisa membatalkan!")
            return

        # Clear broadcast
        self.pending_broadcast = None
        await update.message.reply_text("✅ Broadcast dibatalkan!")

    async def handle_ask_ai(self, update: Update, context: CallbackContext):
        """Handle /ask_ai command"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/ask_ai <pertanyaan>`\nContoh: `/ask_ai apa itu bitcoin`", parse_mode='Markdown')
            return

        user_id = update.message.from_user.id

        # Get user language preference (default to Indonesian)
        user_data = self.db.get_user(user_id)
        language = user_data.get('language', 'id') if user_data else 'id'

        question = " ".join(context.args)
        response = self.ai.get_ai_response(question, language)

        await update.message.reply_text(response, parse_mode='Markdown')

    

    async def handle_callback_query(self, update: Update, context: CallbackContext):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        data = query.data

        if data.startswith('lang_'):
            # Language selection
            language = data.split('_')[1]
            self.db.set_user_language(user_id, language)

            if language == 'id':
                await query.edit_message_text("✅ Bahasa berhasil diubah ke Bahasa Indonesia!")
            else:
                await query.edit_message_text("✅ Language successfully changed to English!")

        elif data == 'make_premium' and user_id == self.admin_id:
            await query.edit_message_text(
                "👑 **Grant Premium Access**\n\n"
                "Gunakan command: `/grant_premium <user_id> [days]`\n"
                "Contoh: `/grant_premium 123456789 30`",
                parse_mode='Markdown'
            )

        elif data == 'grant_credits' and user_id == self.admin_id:
            await query.edit_message_text(
                "💰 **Grant Credits**\n\n"
                "Gunakan command: `/grant_credits <user_id> <amount>`\n"
                "Contoh: `/grant_credits 123456789 50`",
                parse_mode='Markdown'
            )

        elif data == 'broadcast_help' and user_id == self.admin_id:
            await query.edit_message_text(
                "📢 **Broadcast Message**\n\n"
                "Gunakan command: `/broadcast <message>`\n"
                "Contoh: `/broadcast Update fitur baru!`",
                parse_mode='Markdown'
            )

        elif data == 'bot_stats' and user_id == self.admin_id:
            # Get bot statistics
            stats = self.db.get_bot_statistics()
            stats_message = f"""
📊 **Statistik Bot**

👥 **Users:**
• Total Users: {stats.get('total_users', 0)}
• Premium Users: {stats.get('premium_users', 0)}
• Active Today: {stats.get('active_today', 0)}

💳 **Credits:**
• Total Credits Distributed: {stats.get('total_credits', 0)}
• Average Credits per User: {stats.get('avg_credits', 0):.1f}

📈 **Usage:**
• Commands Today: {stats.get('commands_today', 0)}
• Analyses Run: {stats.get('analyses_count', 0)}
            """
            await query.edit_message_text(stats_message, parse_mode='Markdown')

        elif data == 'activity_log' and user_id == self.admin_id:
            # Get recent activity
            recent_activity = self.db.get_recent_activity(10)
            activity_message = "📝 **Recent Activity:**\n\n"

            for activity in recent_activity:
                activity_message += f"• {activity['action']}: User {activity['user_id']}\n"

            await query.edit_message_text(activity_message, parse_mode='Markdown')

        elif data == 'api_health' and user_id == self.admin_id:
            # Check API health
            api_status = self.crypto_api.check_api_status()
            health_message = f"""
🔍 **API Health Report**

📊 **CoinGecko API:** {'✅ Online' if api_status.get('coingecko', False) else '❌ Offline'}
🔮 **Coinglass API:** {'✅ Online' if api_status.get('coinglass', False) else '❌ Offline'}
📰 **News API:** {'✅ Online' if api_status.get('news', False) else '❌ Offline'}

🔄 **Last Check:** {datetime.now().strftime('%H:%M:%S')}
            """
            await query.edit_message_text(health_message, parse_mode='Markdown')

        elif data == 'restart_bot' and user_id == self.admin_id:
            await query.edit_message_text("🔄 Bot restart initiated... Please wait.")
            # Note: Actual restart would need to be implemented based on deployment environment

        # Handle futures timeframe analysis callbacks
        elif data.startswith('futures_tf_'):
            parts = data.split('_')
            symbol = parts[2]
            timeframe = parts[3]
            await self._handle_futures_timeframe_analysis(query, symbol, timeframe)

        # Handle futures menu callback (return to timeframe selection)
        elif data.startswith('futures_menu_'):
            symbol = data.split('_')[-1]
            keyboard = [
                [InlineKeyboardButton("⚡ 15m", callback_data=f'futures_tf_{symbol}_15m'),
                 InlineKeyboardButton("🔥 30m", callback_data=f'futures_tf_{symbol}_30m')],
                [InlineKeyboardButton("📈 1h", callback_data=f'futures_tf_{symbol}_1h'),
                 InlineKeyboardButton("🚀 4h", callback_data=f'futures_tf_{symbol}_4h')],
                [InlineKeyboardButton("💎 1d", callback_data=f'futures_tf_{symbol}_1d'),
                 InlineKeyboardButton("🌟 1w", callback_data=f'futures_tf_{symbol}_1w')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"📊 **Analisis Futures {symbol}**\n\n"
                "Pilih timeframe untuk analisis teknikal advance:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        

    async def handle_message(self, update: Update, context: CallbackContext):
        """Handle regular text messages (not commands)"""
        user_id = update.message.from_user.id
        text = update.message.text.lower()

        # Get user language preference
        user_data = self.db.get_user(user_id)
        language = user_data.get('language', 'id') if user_data else 'id'

        # Check if message contains crypto-related queries
        crypto_keywords = ['harga', 'price', 'bitcoin', 'btc', 'ethereum', 'eth', 'bnb', 'ada', 'sol', 'doge', 
                          'analisis', 'analyze', 'futures', 'trading', 'crypto', 'coin', 'pasar', 'market',
                          'bagaimana', 'how about', 'gimana', 'berapa', 'how much']

        crypto_symbols = ['btc', 'eth', 'bnb', 'ada', 'sol', 'doge', 'xrp', 'dot', 'matic', 'avax', 'link', 'ltc', 'ondo', 'sei', 'pepe', 'moodeng', 'shib', 'floki', 'wif', 'bonk', 'jup', 'pyth', 'render', 'inj', 'sui', 'apt', 'op', 'arb', 'tia', 'hyperliquid', 'popcat', 'pendle', 'eigen']

        # Check if text contains crypto keywords or symbols
        is_crypto_query = any(keyword in text for keyword in crypto_keywords) or any(symbol in text for symbol in crypto_symbols)

        if is_crypto_query:
            # Try to extract crypto symbol from text
            detected_symbol = None
            for symbol in crypto_symbols:
                if symbol in text:
                    detected_symbol = symbol.upper()
                    break

            # If asking about price
            if any(word in text for word in ['harga', 'price', 'berapa']):
                if detected_symbol:
                    # Show loading message
                    loading_msg = await update.message.reply_text(f"⏳ Mengecek harga {detected_symbol}...")

                    # Get price data
                    price_data = self.crypto_api.get_price(detected_symbol, force_refresh=True)

                    if price_data and 'error' not in price_data:
                        source = price_data.get('source', 'unknown')
                        is_real_data = source in ['binance', 'binance_simple', 'coingecko', 'coingecko_free']

                        response = f"""💰 **Harga {detected_symbol} saat ini**: ${price_data.get('price', 0):,.2f}

📈 Perubahan 24h: {price_data.get('change_24h', 0):+.2f}%
{"📊 Volume 24h: $" + f"{price_data.get('volume_24h', 0):,.0f}" if price_data.get('volume_24h', 0) > 0 else ""}
🕐 Update: {datetime.now().strftime('%H:%M:%S WIB')}
🔄 {"Data real-time dari " + source.title() if is_real_data else "Data real-time"}"""
                    else:
                        response = f"❌ Maaf, tidak dapat menemukan data harga untuk {detected_symbol}"

                    await loading_msg.edit_text(response, parse_mode='Markdown')
                    return
                else:
                    response = "💡 Untuk cek harga, sebutkan nama crypto seperti: 'harga bitcoin' atau 'berapa harga eth'"

            # If asking for analysis
            elif any(word in text for word in ['analisis', 'analyze', 'gimana', 'bagaimana']):
                if detected_symbol:
                    # Check credits first
                    credits = self.db.get_user_credits(user_id)
                    is_premium = self.db.is_user_premium(user_id)
                    is_admin = user_id == self.admin_id

                    if not is_premium and not is_admin and credits < 20:
                        response = "❌ Credit tidak cukup untuk analisis mendalam. Gunakan `/credits` untuk melihat sisa credit Anda."
                    else:
                        loading_msg = await update.message.reply_text(f"⏳ Menganalisis {detected_symbol}...")

                        try:
                            price_data = self.crypto_api.get_price(detected_symbol)
                            futures_data = self.crypto_api.get_futures_data(detected_symbol)

                            analysis = self.ai.get_comprehensive_analysis(detected_symbol, futures_data, price_data, 'id', self.crypto_api)

                            # Deduct credit if needed
                            if not is_premium and not is_admin:
                                self.db.deduct_credit(user_id, 20)
                                remaining_credits = self.db.get_user_credits(user_id)
                                analysis += f"\n\n💳 Credit tersisa: {remaining_credits}"

                            await loading_msg.edit_text(analysis, parse_mode='Markdown')
                            return
                        except Exception as e:
                            await loading_msg.edit_text(f"❌ Terjadi kesalahan saat analisis: {str(e)}")
                            return
                else:
                    response = "💡 Untuk analisis, sebutkan crypto seperti: 'analisis bitcoin' atau 'gimana eth'"

            # If asking about futures
            elif 'futures' in text or 'sinyal' in text:
                if detected_symbol:
                    # Check credits first
                    credits = self.db.get_user_credits(user_id)
                    is_premium = self.db.is_user_premium(user_id)
                    is_admin = user_id == self.admin_id

                    if not is_premium and not is_admin and credits < 20:
                        response = "❌ Credit tidak cukup untuk analisis futures. Gunakan `/credits` untuk melihat sisa credit Anda."
                    else:
                        loading_msg = await update.message.reply_text(f"⏳ Menganalisis futures {detected_symbol}...")

                        try:
                            signals = self.ai.generate_single_futures_signal(detected_symbol, 'id', self.crypto_api)

                            # Deduct credit if needed
                            if not is_premium and not is_admin:
                                self.db.deduct_credit(user_id, 20)
                                remaining_credits = self.db.get_user_credits(user_id)
                                signals += f"\n\n💳 Credit tersisa: {remaining_credits}"

                            await loading_msg.edit_text(signals, parse_mode='Markdown')
                            return
                        except Exception as e:
                            await loading_msg.edit_text(f"❌ Terjadi kesalahan: {str(e)}")
                            return
                else:
                    response = "💡 Untuk analisis futures, sebutkan crypto seperti: 'futures bitcoin' atau 'sinyal eth'"

            # If asking about market
            elif any(word in text for word in ['pasar', 'market', 'overview']):
                # Check credits first
                credits = self.db.get_user_credits(user_id)
                is_premium = self.db.is_user_premium(user_id)
                is_admin = user_id == self.admin_id

                if not is_premium and not is_admin and credits < 20:
                    response = "❌ Credit tidak cukup untuk overview pasar. Gunakan `/credits` untuk melihat sisa credit Anda."
                else:
                    loading_msg = await update.message.reply_text("⏳ Menganalisis kondisi pasar...")

                    try:
                        market_data = self.ai.get_market_sentiment('id', self.crypto_api)

                        # Deduct credit if needed
                        if not is_premium and not is_admin:
                            self.db.deduct_credit(user_id, 20)
                            remaining_credits = self.db.get_user_credits(user_id)
                            market_data += f"\n\n💳 Credit tersisa: {remaining_credits}"

                        await loading_msg.edit_text(market_data, parse_mode='Markdown')
                        return
                    except Exception as e:
                        await loading_msg.edit_text(f"❌ Terjadi kesalahan: {str(e)}")
                        return
            else:
                # General crypto response
                response = """💡 **Cara menggunakan CryptoMentor AI:**

📊 **Cek Harga**: "harga bitcoin" atau "berapa eth"
📈 **Analisis**: "analisis btc" atau "gimana ethereum"  
⚡ **Futures**: "futures bitcoin" atau "sinyal eth"
🌍 **Pasar**: "kondisi pasar" atau "overview market"

Atau gunakan command seperti `/price btc`, `/analyze eth`, `/futures sol`"""
        else:
            # Use AI assistant for general questions
            response = self.ai.get_ai_response(update.message.text, language)

        await update.message.reply_text(response, parse_mode='Markdown')

    async def _handle_futures_timeframe_analysis(self, query, symbol, timeframe):
        """Handle futures timeframe analysis callback"""
        user_id = query.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = user_id == self.admin_id

        # Check credits again for non-premium users
        if not is_premium and not is_admin and credits < 20:
            await query.edit_message_text("❌ Credit tidak cukup untuk analisis futures!")
            return

        # Show loading message
        await query.edit_message_text(f"⏳ Menganalisis {symbol} pada timeframe {timeframe}...")

        try:
            # Get comprehensive timeframe analysis with trading signals
            analysis = self.ai.get_futures_trading_signals(symbol, timeframe, self.crypto_api)

            # Deduct credits for non-premium users
            if not is_premium and not is_admin:
                self.db.deduct_credit(user_id, 20)
                remaining_credits = self.db.get_user_credits(user_id)
                analysis += f"\n\n💳 Credit tersisa: {remaining_credits} (Analisis futures: -20 credit)"
            elif is_premium:
                analysis += f"\n\n⭐ **Status Premium** - Unlimited Access"
            elif is_admin:
                analysis += f"\n\n👑 **Admin Access** - Unlimited"

            # Add menu options
            keyboard = [
                [InlineKeyboardButton("🔄 Ganti Timeframe", callback_data=f'futures_menu_{symbol}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Split long messages if needed
            if len(analysis) > 4000:
                chunks = [analysis[i:i+4000] for i in range(0, len(analysis), 4000)]
                await query.edit_message_text(chunks[0], parse_mode='Markdown')

                # Send additional chunks
                for chunk in chunks[1:-1]:
                    await query.message.reply_text(chunk, parse_mode='Markdown')
                
                # Last chunk with keyboard
                await query.message.reply_text(chunks[-1], reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await query.edit_message_text(analysis, reply_markup=reply_markup, parse_mode='Markdown')

        except Exception as e:
            await query.edit_message_text(f"❌ Terjadi kesalahan: {str(e)[:100]}")
            print(f"Futures timeframe analysis error: {e}")

    

    async def admin_command(self, update: Update, context: CallbackContext):
        """Admin panel command"""
        user_id = update.message.from_user.id

        # Strict admin check - only respond to admin, ignore others completely
        if user_id != self.admin_id:
            # Don't send any response to non-admin users
            return

        keyboard = [
            [InlineKeyboardButton("👑 Buat User Premium", callback_data='make_premium')],
            [InlineKeyboardButton("💰 Berikan Credits", callback_data='grant_credits')],
            [InlineKeyboardButton("📢 Broadcast Message", callback_data='broadcast_help')],
            [InlineKeyboardButton("📊 Statistik Bot", callback_data='bot_stats')],
            [InlineKeyboardButton("📝 Log Aktivitas", callback_data='activity_log')],
            [InlineKeyboardButton("🔍 API Health Report", callback_data='api_health')],
            [InlineKeyboardButton("🔄 Restart Bot", callback_data='restart_bot')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🛠 **Panel Admin CryptoMentor**\n\n"
            "Pilih opsi yang tersedia:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def admin_stats(self, update: Update, context: CallbackContext):
        """Admin command to view bot statistics"""
        user_id = update.effective_user.id

        if user_id != self.admin_id:
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        try:
            # Get comprehensive statistics
            stats = self.db.get_bot_statistics()

            # Check API health
            api_status = self.crypto_api.check_api_status()
            api_health = "✅ All Connected" if api_status.get('overall_health', False) else "⚠️ Partial"

            # Additional database checks
            try:
                self.db.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NULL OR telegram_id = 0")
                invalid_users = self.db.cursor.fetchone()[0]

                self.db.cursor.execute("SELECT COUNT(*) FROM users WHERE credits < 0")
                negative_credits = self.db.cursor.fetchone()[0]
            except:
                invalid_users = 0
                negative_credits = 0

            message = f"""📊 **CryptoMentor AI - Bot Statistics**

👥 **Users:**
• Total Users: {stats['total_users']}
• Premium Users: {stats['premium_users']}
• Active Today: {stats['active_today']}

💰 **Credits:**
• Total Credits: {stats['total_credits']:,}
• Average Credits/User: {stats['avg_credits']:.1f}
• Commands Today: {stats['commands_today']}

📈 **Activity:**
• Total Analyses: {stats['analyses_count']}
• API Status: {api_health}
• Bot Uptime: {datetime.now().strftime('%H:%M:%S')}

🔧 **Database Health:**
• Invalid Users: {invalid_users}
• Negative Credits: {negative_credits}
• DB Status: {"🟢 Healthy" if invalid_users == 0 and negative_credits == 0 else "🟡 Needs Attention"}

**Admin Commands:**
• `/grant_premium <user_id>` - Grant premium
• `/revoke_premium <user_id>` - Revoke premium  
• `/broadcast <message>` - Send to all users

System Status: 🟢 Operational"""

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching stats: {str(e)}")
            print(f"Admin stats error: {e}")

    async def check_admin_command(self, update: Update, context: CallbackContext):
        """Check admin status - debugging command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "No username"
        first_name = update.effective_user.first_name or "Unknown"

        message = f"""🔍 **Admin Status Check**

👤 **Your Info:**
• **User ID**: {user_id}
• **Username**: @{username}
• **Name**: {first_name}

🛠 **Bot Config:**
• **Admin ID**: {self.admin_id}
• **Match**: {"✅ YES" if user_id == self.admin_id else "❌ NO"}

💡 **To fix admin access:**
1. Set ADMIN_USER_ID in Secrets
2. Use your Telegram User ID: {user_id}
3. Restart bot

🔧 **Commands available:**
• `/grant_premium <user_id> [days]`
• `/grant_credits <user_id> <amount>`
• `/admin` - Admin panel"""

        await update.message.reply_text(message, parse_mode='Markdown')

# News command will be integrated in main bot class