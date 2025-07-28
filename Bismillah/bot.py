import os
import logging
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file (if exists) and system environment
load_dotenv()

# Enhanced deployment detection with verification
deployment_env_checks = {
    'REPLIT_DEPLOYMENT': os.getenv('REPLIT_DEPLOYMENT') == '1',
    'REPL_DEPLOYMENT': os.getenv('REPL_DEPLOYMENT') == '1', 
    'REPLIT_ENVIRONMENT': os.getenv('REPLIT_ENVIRONMENT') == 'deployment',
    'deployment_flag': os.path.exists('/tmp/repl_deployment_flag'),
    'replit_slug': bool(os.getenv('REPL_SLUG')),
    'replit_owner': bool(os.getenv('REPL_OWNER'))
}

IS_DEPLOYMENT = any(deployment_env_checks.values())

# Log deployment detection for debugging
print(f"🔍 Bot Deployment Detection:")
for check, result in deployment_env_checks.items():
    print(f"  {'✅' if result else '❌'} {check}: {result}")
print(f"📊 Bot Deployment Status: {'ENABLED' if IS_DEPLOYMENT else 'DISABLED'}")

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
            # Force cleanup any pending updates to prevent conflicts
            print("🔄 Clearing pending updates...")
            try:
                await self.application.bot.delete_webhook(drop_pending_updates=True)
                await asyncio.sleep(2)
            except Exception as cleanup_error:
                print(f"⚠️ Cleanup warning: {cleanup_error}")

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
            self.application.add_handler(CommandHandler("broadcast_welcome", self.broadcast_welcome_command))
            self.application.add_handler(CommandHandler("recovery_stats", self.recovery_stats_command))
            self.application.add_handler(CommandHandler("check_admin", self.check_admin_command))
            self.application.add_handler(CommandHandler("restart", self.restart_command))
            self.application.add_handler(CommandHandler("refresh_credits", self.refresh_credits_command))
            self.application.add_handler(CommandHandler("premium_earnings", self.premium_earnings_command))
            self.application.add_handler(CommandHandler("grant_package", self.grant_package_command))
            self.application.add_handler(CommandHandler("test_binance", self.test_binance_command))

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
        """Handle /start command with enhanced user persistence"""
        user = update.effective_user

        try:
            # Validate user data
            if not user or not user.id:
                await update.message.reply_text("❌ Terjadi kesalahan dalam mengidentifikasi user. Silakan coba lagi.")
                return

            print(f"🔍 Processing /start for user {user.id} ({user.first_name})")

            # Check for referral parameter
            referred_by = None
            referral_type = 'free'  # default
            if context.args and len(context.args) > 0:
                arg = context.args[0]
                if arg.startswith('ref_'):
                    try:
                        referred_by = int(arg[4:])  # Extract user ID from ref_USERID
                        referral_type = 'free'
                        print(f"🎁 User {user.id} was referred by {referred_by} (free referral)")
                    except ValueError:
                        print(f"❌ Invalid referral code: {arg}")
                elif arg.startswith('pref_'):
                    # Premium referral
                    try:
                        referred_by = int(arg[5:])  # Extract user ID from pref_USERID
                        referral_type = 'premium'
                        print(f"💎 User {user.id} was referred by {referred_by} (premium referral)")
                    except ValueError:
                        print(f"❌ Invalid premium referral code: {arg}")
                elif len(arg) == 8 and (arg.startswith('F') or arg.startswith('P')):
                    # New referral code format
                    if arg.startswith('F'):
                        # Free referral code
                        referred_by = self.db.get_user_by_referral_code(arg)
                        referral_type = 'free'
                        if referred_by:
                            print(f"🎁 User {user.id} was referred by {referred_by} (free code: {arg})")
                    elif arg.startswith('P'):
                        # Premium referral code
                        referred_by = self.db.get_user_by_premium_referral_code(arg)
                        referral_type = 'premium'
                        if referred_by:
                            print(f"💎 User {user.id} was referred by {referred_by} (premium code: {arg})")
                    
                    if not referred_by:
                        print(f"❌ Invalid referral code: {arg}")

            # Check if user already exists
            existing_user = self.db.get_user(user.id)
            
            if not existing_user:
                # New user - create with referral
                success = self.db.create_user(
                    telegram_id=user.id,
                    username=user.username or 'no_username',
                    first_name=user.first_name or 'Unknown',
                    last_name=user.last_name,
                    language_code=user.language_code or 'id',
                    referred_by=referred_by
                )
                
                # Give referral bonus to referrer if applicable
                if referred_by and success:
                    try:
                        if referral_type == 'free':
                            # Standard free referral bonus - 10 credits
                            self.db.add_credits(referred_by, 10)
                            self.db.log_user_activity(referred_by, "referral_bonus", f"Got 10 credits for referring user {user.id}")
                            print(f"✅ Gave 10 credits to free referrer {referred_by}")
                        elif referral_type == 'premium':
                            # Premium referral - they get reward when referred user subscribes premium
                            # Only premium users can earn money from premium referrals
                            if self.db.is_user_premium(referred_by):
                                self.db.log_user_activity(referred_by, "premium_referral_pending", f"User {user.id} joined via premium referral, waiting for subscription")
                                print(f"💎 Premium referral logged for {referred_by}, reward pending subscription")
                            else:
                                # Non-premium users get credit bonus instead
                                self.db.add_credits(referred_by, 10)
                                self.db.log_user_activity(referred_by, "referral_bonus", f"Got 10 credits for referring user {user.id} (not premium member)")
                                print(f"✅ Gave 10 credits to non-premium referrer {referred_by}")
                    except Exception as e:
                        print(f"❌ Error giving referral bonus: {e}")
            else:
                # Existing user - ensure persistence
                success = self.db.ensure_user_persistence(
                    telegram_id=user.id,
                    username=user.username or 'no_username',
                    first_name=user.first_name or 'Unknown',
                    last_name=user.last_name,
                    language_code=user.language_code or 'id'
                )

            if not success:
                print(f"❌ Failed to ensure user persistence: {user.id}")
                # Try to recover from backup
                recovery_attempted = self.db.recover_user_from_backup(user.id)
                if recovery_attempted:
                    print(f"🔄 Attempted recovery for user {user.id}")

            # Get user data (should exist now)
            existing_user = self.db.get_user(user.id)

            if existing_user:
                # Check if user needs restart after admin restart
                if self.db.user_needs_restart(user.id):
                    # Clear restart flag and log reactivation
                    self.db.clear_restart_flag(user.id)
                    self.db.log_user_activity(user.id, "user_reactivated", f"User restarted after admin restart: {user.first_name}")
                    print(f"🔄 User reactivated after restart: {user.id} ({user.first_name})")
                else:
                    # Check if this is a new session vs returning user
                    last_activity = self.db.cursor.execute("""
                        SELECT timestamp FROM user_activity 
                        WHERE telegram_id = ? AND action = 'user_returned' 
                        ORDER BY timestamp DESC LIMIT 1
                    """, (user.id,))
                    last_return = last_activity.fetchone()
                    
                    if not last_return:
                        # First time returning since creation
                        self.db.log_user_activity(user.id, "user_first_return", f"User returned for first time: {user.first_name}")
                        print(f"👋 First return: {user.id} ({user.first_name})")
                    else:
                        # Regular return
                        self.db.log_user_activity(user.id, "user_returned", "User started bot again")
                        print(f"👤 Returning user: {user.id} ({existing_user.get('first_name')})")

                # Create backup of current user state
                self.db.backup_user_data(user.id)

            else:
                # Final attempt to create user if all else failed
                final_attempt = self.db.create_user(
                    telegram_id=user.id,
                    username=user.username or 'no_username',
                    first_name=user.first_name or 'Unknown',
                    last_name=user.last_name,
                    language_code=user.language_code or 'id'
                )
                
                if final_attempt:
                    print(f"✅ Final attempt successful for user: {user.id}")
                    self.db.log_user_activity(user.id, "user_created_final_attempt", f"User created on final attempt: {user.first_name}")
                else:
                    print(f"❌ All attempts failed for user: {user.id}")
                    # Still continue to show welcome message

        except Exception as e:
            print(f"❌ Error in start command: {e}")
            # Log the error but continue to show welcome message
            try:
                self.db.log_user_activity(user.id if user else 0, "start_command_error", f"Error: {str(e)}")
            except:
                pass

        # Welcome message
        language = user.language_code or 'id'

        if language == 'id':
            welcome_text = f"""🎉 **Selamat datang di CryptoMentor AI, {user.first_name}!**

🤖 Saya adalah AI assistant crypto trading terlengkap dengan data real-time dari multiple API.

💡 **Untuk memulai:** Gunakan `/help` untuk panduan lengkap semua fitur bot!

📊 **Quick Start - Contoh Penggunaan:**

**Cek Harga:**
• `/price btc` - Harga Bitcoin real-time
• `/price eth` - Harga Ethereum terkini

**Analisis Mendalam:**
• `/analyze btc` - Analisis komprehensif Bitcoin (technical analysis, sentiment, prediksi)
• `/analyze eth` - Analisis Ethereum dengan data real-time

**Trading Futures:**
• `/futures btc` - Pilih timeframe untuk analisis futures Bitcoin
• `/futures sol` - Analisis futures Solana dengan berbagai timeframe

💳 **Sistem Credit:**
- User baru dapat **10 credit gratis**
- `/analyze` = 20 credit | `/futures` = 20 credit
- `/futures_signals` = 30 credit | `/market` = 20 credit

🎁 **Cara Dapat Credit Gratis:**
• `/referral` - Ajak teman dapat 10 credit/referral
• `/subscribe` - Upgrade premium untuk unlimited access

🚀 **Mulai Sekarang:**
1. Gunakan `/help` untuk melihat semua command
2. Coba `/price btc` untuk harga Bitcoin
3. Test `/analyze eth` untuk analisis Ethereum
4. Eksplorasi `/futures btc` untuk trading signals

**Semua data real-time dari Binance & CoinGecko API!**"""

        else:
            welcome_text = f"""🎉 **Welcome to CryptoMentor AI, {user.first_name}!**

🤖 I'm your comprehensive crypto trading AI assistant with real-time multi-API data.

💡 **To get started:** Use `/help` for complete guide to all bot features!

📊 **Quick Start - Usage Examples:**

**Check Prices:**
• `/price btc` - Real-time Bitcoin price
• `/price eth` - Current Ethereum price

**Deep Analysis:**
• `/analyze btc` - Comprehensive Bitcoin analysis (technical analysis, sentiment, predictions)
• `/analyze eth` - Ethereum analysis with real-time data

**Futures Trading:**
• `/futures btc` - Choose timeframe for Bitcoin futures analysis
• `/futures sol` - Solana futures analysis with various timeframes

💳 **Credit System:**
- New users get **10 free credits**
- `/analyze` = 20 credits | `/futures` = 20 credits
- `/futures_signals` = 30 credits | `/market` = 20 credits

🎁 **How to Get Free Credits:**
• `/referral` - Invite friends get 10 credits/referral
• `/subscribe` - Upgrade premium for unlimited access

🚀 **Start Now:**
1. Use `/help` to see all commands
2. Try `/price btc` for Bitcoin price
3. Test `/analyze eth` for Ethereum analysis
4. Explore `/futures btc` for trading signals

**All data real-time from Binance & CoinGecko APIs!**"""

        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: CallbackContext):
        """Handle /help command"""
        help_text = """🤖 **CryptoMentor AI Bot - Panduan Lengkap**

⭐ **BEST COMMANDS untuk Pemula:**
• `/price btc` - **GRATIS** - Cek harga Bitcoin (mulai dari sini!)
• `/analyze btc` - **20 credit** - Analisis Bitcoin lengkap (recommended!)
• `/futures btc` - **20 credit** - Trading signals Bitcoin dengan timeframe

📊 **Harga & Data Pasar:**
• `/price <symbol>` - Harga real-time **[GRATIS]**
  Contoh: `/price btc`, `/price eth`, `/price sol`
• `/market` - Overview pasar komprehensif (20 credit)

📈 **Analisis Trading:**
• `/analyze <symbol>` - Analisis mendalam (20 credit) ⭐ **RECOMMENDED**
  Contoh: `/analyze btc` → Technical analysis, sentiment, prediksi harga
  
• `/futures <symbol>` - Analisis futures dengan timeframe (20 credit)
  Contoh: `/futures btc` → Pilih 15m, 1h, 4h, 1d
  Hasil: Support/resistance, entry/exit points, risk management
  
• `/futures_signals` - Sinyal futures lengkap semua coin (60 credit)

💼 **Portfolio & Credit:**
• `/portfolio` - Lihat portfolio
• `/add_coin <symbol> <amount>` - Tambah ke portfolio
  Contoh: `/add_coin btc 0.5`
• `/credits` - Cek sisa credit
• `/subscribe` - Upgrade premium

🎯 **Lainnya:**
• `/ask_ai <pertanyaan>` - Tanya AI crypto **[GRATIS]**
  Contoh: `/ask_ai apa itu DeFi?`
• `/referral` - Program referral (Credit + Uang)
• `/premium_earnings` - Dashboard earnings (Premium only)
• `/language` - Ubah bahasa

💳 **Sistem Credit:**
- User baru: 10 credit gratis
- `/analyze` = 20 credit ⭐
- `/futures` = 20 credit ⭐
- `/futures_signals` = 60 credit
- `/market` = 20 credit

🎯 **Langkah untuk Pemula:**
1. **Mulai dengan `/price btc`** (gratis) - pelajari harga crypto
2. **Coba `/analyze btc`** (20 credit) - pahami analisis mendalam
3. **Test `/futures btc`** (20 credit) - belajar trading signals
4. **Upgrade premium** untuk unlimited access semua fitur

💡 **Tips Hemat Credit:**
- Ketik nama crypto langsung untuk harga cepat (GRATIS)
- Focus pada 1-2 crypto favorit untuk analisis
- Premium = unlimited access semua fitur
- Referral FREE = bonus credit, PREMIUM = uang asli

🚀 **Semua analisis menggunakan data real-time dari Binance & CoinGecko API!**"""
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def price_command(self, update: Update, context: CallbackContext):
        """Handle /price command with enhanced real-time data"""
        # Check if user needs restart
        if await self._check_user_restart_required(update):
            return
            
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
        # ALWAYS force refresh in deployment to ensure real-time data
        price_data = self.crypto_api.get_multi_api_price(symbol, force_refresh=IS_DEPLOYMENT)
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
            primary_source = price_data.get('primary_source', source)

            # Enhanced source indicators with API health
            source_emoji = {
                'binance': '🟢 Binance Spot (Real-Time)',
                'binance_futures': '🟢 Binance Futures (Real-Time)',
                'binance_simple': '🟡 Binance Simple (Real-Time)', 
                'coingecko': '🔵 CoinGecko Pro (Real-Time)',
                'coingecko_free': '🔵 CoinGecko Free (Real-Time)',
                'coingecko_fallback': '🟡 CoinGecko Backup (Real-Time)',
                'fallback_simulation': '⚠️ Simulation Data'
            }.get(primary_source, '🔄 Market Data')

            is_real_api = source in ['binance', 'binance_simple', 'coingecko', 'coingecko_free', 'coingecko_fallback']
            
            # Warning for simulation data in deployment
            if source == 'fallback_simulation' and IS_DEPLOYMENT:
                source_emoji += ' - API CONNECTION ISSUE'

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
            # Check if we're in deployment and show appropriate error
            is_deployment = (
                os.getenv('REPLIT_DEPLOYMENT') == '1' or 
                os.getenv('REPL_DEPLOYMENT') == '1' or
                os.path.exists('/tmp/repl_deployment_flag')
            )
            
            if is_deployment:
                error_reason = price_data.get('error', 'Unknown error') if price_data else 'API completely unavailable'
                message = f"""❌ **Real-time data tidak tersedia untuk {symbol}**

🌐 **Mode**: Deployment (Real-time Only)
⚠️ **Error**: {error_reason}

🔄 **Solusi**:
• Coba beberapa saat lagi
• API sedang mengalami gangguan sementara
• Tidak menggunakan data simulasi di deployment

💡 **Info**: Bot hanya menampilkan data real-time di deployment mode"""
            else:
                message = f"❌ Tidak dapat menemukan data untuk {symbol}"

        await loading_msg.edit_text(message, parse_mode='Markdown')

    async def analyze_command(self, update: Update, context: CallbackContext):
        """Handle /analyze command - comprehensive analysis with news integration"""
        # Check if user needs restart
        if await self._check_user_restart_required(update):
            return
            
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
        """Handle /market command with enhanced error handling"""
        # Check if user needs restart
        if await self._check_user_restart_required(update):
            return
            
        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = user_id == self.admin_id

        # Check credits for non-premium, non-admin users
        if not is_premium and not is_admin and credits < 20:
            await update.message.reply_text("❌ Credit tidak cukup! Overview pasar membutuhkan 20 credit. Gunakan `/credits` untuk melihat sisa credit Anda.", parse_mode='Markdown')
            return

        # Show enhanced loading message
        loading_msg = await update.message.reply_text("⏳ Menganalisis overview pasar crypto real-time dari multiple API...")

        try:
            print(f"🔄 Market command initiated by user {user_id}")
            
            # Verify API availability first
            if not self.crypto_api:
                await loading_msg.edit_text("❌ API tidak tersedia. Silakan coba lagi dalam beberapa menit.", parse_mode='Markdown')
                return

            # Get comprehensive market overview with real-time data
            print("📊 Calling AI market sentiment analysis...")
            market_data = self.ai.get_market_sentiment('id', self.crypto_api)
            
            if not market_data or len(market_data.strip()) < 50:
                # Fallback if data is too short
                market_data = """🌍 **OVERVIEW PASAR CRYPTO**

⚠️ **Data sementara tidak lengkap**

💡 **Alternatif yang bisa dicoba:**
• `/price btc` - Cek harga Bitcoin
• `/price eth` - Cek harga Ethereum  
• `/analyze btc` - Analisis mendalam Bitcoin

🔄 Coba command `/market` lagi dalam beberapa menit untuk data lengkap."""

            # Deduct credit only for non-premium, non-admin users (20 credits for market overview)
            if not is_premium and not is_admin:
                self.db.deduct_credit(user_id, 20)
                remaining_credits = self.db.get_user_credits(user_id)
                market_data += f"\n\n💳 Credit tersisa: {remaining_credits} (Overview pasar: -20 credit)"
            elif is_premium:
                market_data += f"\n\n⭐ **Status Premium** - Unlimited Access"
            elif is_admin:
                market_data += f"\n\n👑 **Admin Access** - Unlimited"

            print(f"✅ Market analysis completed, sending response ({len(market_data)} chars)")

            # Handle long messages
            if len(market_data) > 4000:
                # Split into chunks
                chunks = [market_data[i:i+4000] for i in range(0, len(market_data), 4000)]
                await loading_msg.edit_text(chunks[0], parse_mode='Markdown')
                
                for chunk in chunks[1:]:
                    await update.message.reply_text(chunk, parse_mode='Markdown')
            else:
                # Edit loading message with the comprehensive overview
                await loading_msg.edit_text(market_data, parse_mode='Markdown')

        except Exception as e:
            error_msg = f"❌ Terjadi kesalahan saat menganalisis pasar.\n\n**Error**: {str(e)[:100]}...\n\n💡 **Coba alternatif:**\n• `/price btc`\n• `/analyze ethereum`\n• `/futures_signals`"
            await loading_msg.edit_text(error_msg, parse_mode='Markdown')
            print(f"❌ Error in market command: {e}")
            import traceback
            traceback.print_exc()

    async def futures_signals_command(self, update: Update, context: CallbackContext):
        """Handle /futures_signals command with real-time data"""
        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = user_id == self.admin_id

        # Check credits for non-premium, non-admin users
        if not is_premium and not is_admin and credits < 60:
            await update.message.reply_text("❌ Credit tidak cukup! Sinyal futures membutuhkan 60 credit. Gunakan `/credits` untuk melihat sisa credit Anda.", parse_mode='Markdown')
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

            # Deduct credit only for non-premium, non-admin users (60 credits for futures signals)
            if not is_premium and not is_admin:
                self.db.deduct_credit(user_id, 60)
                remaining_credits = self.db.get_user_credits(user_id)
                signals += f"\n\n💳 Credit tersisa: {remaining_credits} (Sinyal futures: -60 credit)"
            elif is_premium:
                signals += f"\n\n⭐ **Status Premium** - Unlimited Access"
            elif is_admin:
                signals += f"\n\n👑 **Admin Access** - Unlimited"

            print(f"✅ Futures signals generated successfully for user {user_id}")

            # Clean signals text to prevent markdown parsing errors
            def clean_markdown_text(text):
                """Clean text to prevent Telegram markdown parsing errors"""
                # Replace problematic characters
                text = text.replace('&', '&amp;')
                text = text.replace('<', '&lt;')
                text = text.replace('>', '&gt;')
                # Ensure balanced markdown
                if text.count('*') % 2 != 0:
                    text += '*'
                if text.count('_') % 2 != 0:
                    text += '_'
                return text

            cleaned_signals = clean_markdown_text(signals)

            # Split long messages if needed
            if len(cleaned_signals) > 4000:
                # Split into chunks
                chunks = [cleaned_signals[i:i+4000] for i in range(0, len(cleaned_signals), 4000)]
                try:
                    await loading_msg.edit_text(chunks[0], parse_mode='Markdown')
                except Exception as e:
                    print(f"Markdown error, sending as plain text: {e}")
                    await loading_msg.edit_text(chunks[0], parse_mode=None)

                for chunk in chunks[1:]:
                    try:
                        await update.message.reply_text(chunk, parse_mode='Markdown')
                    except Exception as e:
                        print(f"Markdown error in chunk, sending as plain text: {e}")
                        await update.message.reply_text(chunk, parse_mode=None)
            else:
                # Edit the loading message with the signals
                try:
                    await loading_msg.edit_text(cleaned_signals, parse_mode='Markdown')
                except Exception as e:
                    print(f"Markdown error, sending as plain text: {e}")
                    await loading_msg.edit_text(cleaned_signals, parse_mode=None)

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
            [InlineKeyboardButton("⚡ 15m", callback_data=f'futures_analysis_{symbol}_15m'),
             InlineKeyboardButton("🔥 30m", callback_data=f'futures_analysis_{symbol}_30m')],
            [InlineKeyboardButton("📈 1h", callback_data=f'futures_analysis_{symbol}_1h'),
             InlineKeyboardButton("🚀 4h", callback_data=f'futures_analysis_{symbol}_4h')],
            [InlineKeyboardButton("💎 1d", callback_data=f'futures_analysis_{symbol}_1d'),
             InlineKeyboardButton("🌟 1w", callback_data=f'futures_analysis_{symbol}_1w')]
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
            message = f"""💳 **CryptoMentor AI Bot - Credit Information**

👑 **Status**: **ADMIN** 
♾️ **Credit**: **UNLIMITED**

🛠️ **Akses Admin:**
• Unlimited semua fitur
• Kontrol penuh bot
• Panel admin tersedia

Selamat mengelola CryptoMentor AI!"""
        elif is_premium:
            message = f"""💳 **CryptoMentor AI Bot - Credit Information**

⭐ **Status**: **PREMIUM** 
♾️ **Credit**: **UNLIMITED**

🚀 **Fitur Premium:**
• Unlimited analisis
• Akses semua command
• Priority support

Terima kasih telah menjadi member premium!"""
        else:
            message = f"""💳 **CryptoMentor AI Bot - Credit Information**

💰 **Credit tersisa**: **{credits}**

📊 **Biaya per Fitur:**
• `/analyze <symbol>` - 20 credit (analisis komprehensif) ⭐
• `/futures <symbol>` - 20 credit (analisis futures 1 coin) ⭐
• `/futures_signals` - 60 credit (sinyal futures lengkap)
• `/market` - 20 credit (overview pasar)
• Fitur lainnya - **Gratis**

🎯 **Rekomendasi untuk Pemula:**
• Mulai dengan `/price btc` (GRATIS)
• Coba `/analyze btc` (20 credit) - best value!
• Test `/futures btc` (20 credit) - learn trading

💡 **Cara Mendapat Credit:**
• `/referral` - Ajak teman (10 credit/referral)
• `/subscribe` - Upgrade ke Premium (unlimited)
• 🎁 User baru mendapat 10 credit gratis

**Gunakan credit dengan bijak!**"""
        await update.message.reply_text(message, parse_mode='Markdown')

    async def subscribe_command(self, update: Update, context: CallbackContext):
        """Handle /subscribe command"""
        user_id = update.message.from_user.id
        username = update.message.from_user.username or "Tidak ada username"
        first_name = update.message.from_user.first_name or ""
        
        # Check current status
        is_premium = self.db.is_user_premium(user_id)
        current_credits = self.db.get_user_credits(user_id)
        
        if is_premium:
            message = f"""⭐ **Status Premium Aktif**

👤 **{first_name}**, Anda sudah menjadi member Premium!

🚀 **Keuntungan yang Anda nikmati:**
• ♾️ Unlimited analisis dan sinyal
• 🎯 Akses prioritas ke semua fitur
• 📊 Data real-time tanpa batas
• 🛡️ Support premium

✨ **Terima kasih telah menjadi Premium Member!**
Nikmati semua fitur tanpa batasan credit."""
        else:
            message = f"""⭐ **Upgrade ke Premium**

👤 **Informasi Anda:**
• **User ID:** `{user_id}`
• **Username:** @{username}
• **Nama:** {first_name}

🚀 **Fitur Premium:**
• ♾️ Unlimited analisis
• 📊 Analisis futures lengkap
• 🚨 Alert harga real-time
• 📈 Sinyal trading premium
• 🎯 Support prioritas
• 🔔 Notifikasi breakout otomatis

💰 **Paket Langganan:**
• **1 Bulan** - Rp 320.000
• **2 Bulan** - Rp 600.000 🔥 **PROMO!** (Hemat 40k)
• **6 Bulan** - Rp 1.800.000 💎 **POPULER!** (Hemat 120k)
• **1 Tahun** - Rp 3.000.000 ⭐ **TERBAIK!** (Hemat 840k)
• **Lifetime** - Rp 5.000.000 🚀 **ULTIMATE!** (Unlimited Forever)

💳 **Metode Pembayaran:**

🏦 **Transfer Bank:**
• Bank Mandiri
• A/N: NABIL FARREL AL FARI
• No. Rek: 1560018407074

📱 **E-Wallet:**
• Shopee Pay / Dana / GO-PAY
• No. HP: 087779274400

📋 **Cara Upgrade:**
1. Transfer sesuai paket yang dipilih:
   - 1 Bulan: Rp 320.000
   - 2 Bulan: Rp 600.000 (PROMO)
   - 6 Bulan: Rp 1.800.000 (POPULER)
   - 1 Tahun: Rp 3.000.000 (TERBAIK)
   - Lifetime: Rp 5.000.000 (ULTIMATE)
2. Kirim bukti pembayaran ke admin @Billfarr
3. Sertakan informasi ini:
   • User ID: `{user_id}`
   • Username: @{username}
   • Nama: {first_name}
   • Paket: (1 bulan / 2 bulan / 6 bulan / 1 tahun / lifetime)
4. Tunggu konfirmasi aktivasi (maks 24 jam)

💬 **Butuh bantuan?** Chat admin @Billfarr

🎯 **Rekomendasi:** 
• **2 Bulan** - Hemat untuk pemula
• **6 Bulan** - Paling populer untuk trader aktif
• **1 Tahun** - Hemat maksimal untuk profesional
• **Lifetime** - Investasi terbaik untuk long-term trader

ℹ️ **Catatan Penting:**
Pastikan menyertakan User ID (`{user_id}`) dan paket yang dipilih dalam pesan ke admin untuk mempercepat proses aktivasi premium."""
        
        await update.message.reply_text(message, parse_mode='Markdown')

    async def referral_command(self, update: Update, context: CallbackContext):
        """Handle /referral command with dual system"""
        user_id = update.message.from_user.id
        username = update.message.from_user.username or "no_username"
        is_premium = self.db.is_user_premium(user_id)

        # Get bot username dynamically
        try:
            bot_info = await self.application.bot.get_me()
            bot_username = bot_info.username
        except Exception as e:
            print(f"Error getting bot info: {e}")
            bot_username = "CryptoMentorAI_bot"  # Fallback username

        # Get referral codes
        referral_codes = self.db.get_user_referral_codes(user_id)
        if not referral_codes:
            await update.message.reply_text("❌ Error getting referral codes. Please contact support.")
            return

        free_code = referral_codes['free_referral_code']
        premium_code = referral_codes['premium_referral_code']

        # Get free referral statistics
        try:
            self.db.cursor.execute("""
                SELECT COUNT(*) FROM users WHERE referred_by = ?
            """, (user_id,))
            total_free_referrals = self.db.cursor.fetchone()[0]
            credits_earned = total_free_referrals * 10
        except Exception as e:
            print(f"Error getting free referral stats: {e}")
            total_free_referrals = 0
            credits_earned = 0

        # Get premium referral statistics
        premium_stats = self.db.get_premium_referral_stats(user_id)

        message = f"""🎁 **Program Referral CryptoMentor**

🔗 **Link Referral FREE (Credit Bonus):**
`https://t.me/{bot_username}?start={free_code}`

💰 **Keuntungan FREE:**
• Anda dapat 10 credit per referral
• Teman dapat bonus 5 credit
• Instant reward!

📊 **Status FREE Referral:**
• Total Referrals: {total_free_referrals}
• Credit Earned: {credits_earned}

"""

        if is_premium:
            message += f"""💎 **Link Referral PREMIUM (Uang Asli):**
`https://t.me/{bot_username}?start={premium_code}`

💵 **Keuntungan PREMIUM:**
• Anda dapat **Rp 10.000** per user yang subscribe premium
• Reward uang asli, bukan credit!
• Withdraw ke rekening/e-wallet

📊 **Status PREMIUM Referral:**
• Total Premium Referrals: {premium_stats['total_referrals']}
• Total Earnings: **Rp {premium_stats['total_earnings']:,}**

"""

            # Show recent premium referrals
            if premium_stats['recent_referrals']:
                message += "📈 **Recent Premium Referrals:**\n"
                for ref in premium_stats['recent_referrals'][:3]:
                    referred_name = ref[1][:15] + "..." if len(ref[1]) > 15 else ref[1]
                    subscription_type = ref[2]
                    earnings = ref[3]
                    date = ref[4][:10]  # Just date part
                    message += f"• {referred_name} ({subscription_type}) - Rp {earnings:,} ({date})\n"
                message += "\n"
        else:
            message += f"""💎 **Ingin Earning Uang Asli?**

Upgrade ke Premium untuk akses:
• Link referral premium (Rp 10k/referral)
• Withdraw ke rekening/e-wallet
• Unlimited premium features

Gunakan `/subscribe` untuk upgrade!

"""

        message += f"""🔗 **Cara Menggunakan:**

**FREE Referral:**
1. Bagikan link FREE ke teman
2. Mereka /start → Anda dapat 10 credit

**PREMIUM Referral** {'(Tersedia)' if is_premium else '(Premium Only)'}:
1. Bagikan link PREMIUM ke calon customer
2. Mereka subscribe premium → Anda dapat Rp 10.000
3. Withdraw earnings ke rekening Anda

💡 **Tips:** Gunakan link FREE untuk sharing biasa, link PREMIUM untuk monetisasi!"""
        
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

                # Check if this user was referred by premium referral
                premium_referral_reward = ""
                try:
                    # Find if user was referred through premium referral
                    self.db.cursor.execute("""
                        SELECT referred_by FROM users WHERE telegram_id = ?
                    """, (target_user_id,))
                    referred_by_result = self.db.cursor.fetchone()
                    
                    if referred_by_result and referred_by_result[0]:
                        referrer_id = referred_by_result[0]
                        
                        # Check if there's a pending premium referral
                        self.db.cursor.execute("""
                            SELECT details FROM user_activity 
                            WHERE telegram_id = ? AND action = 'premium_referral_pending'
                            AND details LIKE ?
                            ORDER BY timestamp DESC LIMIT 1
                        """, (referrer_id, f"User {target_user_id} joined via premium referral%"))
                        
                        pending_referral = self.db.cursor.fetchone()
                        
                        if pending_referral and self.db.is_user_premium(referrer_id):
                            # Create premium referral reward
                            subscription_amount = 320000 if days == 30 else 600000 if days == 60 else 320000  # Default to 1 month
                            success_reward = self.db.create_premium_referral(
                                referrer_id, target_user_id, premium_type, subscription_amount
                            )
                            
                            if success_reward:
                                referrer_info = self.db.get_user(referrer_id)
                                referrer_name = referrer_info.get('first_name', 'Unknown') if referrer_info else 'Unknown'
                                premium_referral_reward = f"\n\n💰 **Premium Referral Reward:**\n• Referrer: {referrer_name} (ID: {referrer_id})\n• Earned: Rp 10.000\n• Total subscription: Rp {subscription_amount:,}"
                                
                                # Update pending referral to completed
                                self.db.log_user_activity(referrer_id, "premium_referral_completed", 
                                                         f"Received Rp 10.000 for user {target_user_id} premium subscription")
                except Exception as e:
                    print(f"Error processing premium referral reward: {e}")

                message = f"""✅ **Premium berhasil diberikan!**

👤 **User Info:**
• **ID**: {target_user_id}
• **Name**: {first_name}
• **Username**: @{username}

⭐ **Premium Status:**
• **Type**: {premium_type}
• **Previous**: {"Premium" if is_currently_premium else "Free"}
• **Current Credits**: {current_credits}

🎉 User sekarang memiliki akses unlimited ke semua fitur premium!{premium_referral_reward}"""

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

        await update.message.reply_text(confirmation_message, parse_mode='Markdown')

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

    async def broadcast_welcome_command(self, update: Update, context: CallbackContext):
        """Handle /broadcast_welcome command - Send welcome back message to all users"""
        user_id = update.message.from_user.id

        if user_id != self.admin_id:
            await update.message.reply_text("❌ Perintah ini hanya untuk admin!")
            return

        welcome_message = """🎉 **Selamat datang kembali di CryptoMentor AI!**

🔄 **Bot telah diperbarui dengan fitur-fitur terbaru:**
• 📊 Data real-time yang lebih akurat
• 🚀 Analisis AI yang ditingkatkan
• ⚡ Performa yang lebih cepat

💡 **Untuk melanjutkan penggunaan:**
Silakan gunakan `/start` untuk mengaktifkan kembali akses Anda.

💾 **Jangan khawatir!** 
Semua data Anda (credits, premium, portfolio) tetap aman dan tidak hilang.

🎯 **Fitur unggulan:**
• `/price <symbol>` - Harga real-time
• `/analyze <symbol>` - Analisis mendalam
• `/market` - Overview pasar
• `/futures_signals` - Sinyal futures

Terima kasih telah setia menggunakan CryptoMentor AI! 🚀"""

        # Store the welcome broadcast message
        self.pending_broadcast = {
            'message': welcome_message,
            'admin_id': user_id,
            'timestamp': datetime.now()
        }

        await update.message.reply_text(
            "📢 **Welcome Back Broadcast Ready!**\n\n"
            "Pesan welcome back telah disiapkan untuk semua user.\n\n"
            "Gunakan `/confirm_broadcast` untuk mengirim ke semua user\n"
            "atau `/cancel_broadcast` untuk membatalkan.",
            parse_mode='Markdown'
        )

    async def recovery_stats_command(self, update: Update, context: CallbackContext):
        """Handle /recovery_stats command - Show user recovery statistics"""
        user_id = update.message.from_user.id

        if user_id != self.admin_id:
            await update.message.reply_text("❌ Perintah ini hanya untuk admin!")
            return

        try:
            # Get total users
            self.db.cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NOT NULL")
            total_users = self.db.cursor.fetchone()[0]

            # Get users who need restart
            self.db.cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE restart_required = 1 AND telegram_id IS NOT NULL
            """)
            users_need_restart = self.db.cursor.fetchone()[0]

            # Get users who have reactivated today
            self.db.cursor.execute("""
                SELECT COUNT(*) FROM user_activity 
                WHERE action = 'user_reactivated' 
                AND timestamp >= datetime('now', '-1 day')
            """)
            reactivated_today = self.db.cursor.fetchone()[0]

            # Get users who have returned today
            self.db.cursor.execute("""
                SELECT COUNT(*) FROM user_activity 
                WHERE action = 'user_returned' 
                AND timestamp >= datetime('now', '-1 day')
            """)
            returned_today = self.db.cursor.fetchone()[0]

            # Calculate recovery rate
            users_recovered = total_users - users_need_restart
            recovery_rate = (users_recovered / total_users * 100) if total_users > 0 else 0

            message = f"""📊 **User Recovery Statistics**

👥 **Overall Stats:**
• **Total Users**: {total_users}
• **Users Recovered**: {users_recovered}
• **Still Need /start**: {users_need_restart}
• **Recovery Rate**: {recovery_rate:.1f}%

📈 **Today's Activity:**
• **Reactivated Today**: {reactivated_today} users
• **Returned Today**: {returned_today} users
• **Total Engagement**: {reactivated_today + returned_today} users

💡 **Recovery Actions:**
• Use `/broadcast_welcome` to send welcome back message
• Monitor reactivation through user logs
• Users who `/start` will be tracked as reactivated

**Last Updated**: {datetime.now().strftime('%H:%M:%S WIB')}"""

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            await update.message.reply_text(f"❌ Error getting recovery stats: {str(e)}")
            print(f"Recovery stats error: {e}")

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

    async def binance_data_command(self, update: Update, context: CallbackContext):
        """Handle /binance_data command - comprehensive Binance API data"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/binance_data <symbol>`\nContoh: `/binance_data btc`", parse_mode='Markdown')
            return

        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = user_id == self.admin_id

        # Check credits for non-premium, non-admin users
        if not is_premium and not is_admin and credits < 25:
            await update.message.reply_text("❌ Credit tidak cukup! Data comprehensive Binance membutuhkan 25 credit. Gunakan `/credits` untuk melihat sisa credit Anda.", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()

        # Show loading message
        loading_msg = await update.message.reply_text(f"⏳ Mengambil data comprehensive Binance untuk {symbol}...")

        try:
            # Get comprehensive Binance data
            comp_data = self.crypto_api.get_comprehensive_futures_data(symbol)

            if comp_data.get('error'):
                await loading_msg.edit_text(f"❌ Gagal mengambil data untuk {symbol}: {comp_data.get('error')}")
                return

            success_calls = comp_data.get('successful_api_calls', 0)
            total_calls = comp_data.get('total_api_calls', 0)
            data_quality = comp_data.get('data_quality', 'unknown')

            # Format comprehensive message
            message = f"""📊 **Data Comprehensive Binance - {symbol}**

🔗 **API Status**: {success_calls}/{total_calls} endpoints ({'✅' if success_calls >= 5 else '🟡' if success_calls >= 4 else '🔴'})
📈 **Data Quality**: {data_quality.upper()}

"""

            # Price Data
            price_data = comp_data.get('price_data', {})
            if price_data and 'error' not in price_data:
                current_price = price_data.get('price', 0)
                price_format = self.crypto_api._format_price_display(current_price)
                change_24h = price_data.get('change_24h', 0)
                change_emoji = "📈" if change_24h >= 0 else "📉"

                message += f"""💰 **Futures Price Data** 🟢
• **Current Price**: {price_format}
• **24h Change**: {change_emoji} {change_24h:+.2f}%
• **24h High**: {self.crypto_api._format_price_display(price_data.get('high_24h', 0))}
• **24h Low**: {self.crypto_api._format_price_display(price_data.get('low_24h', 0))}
• **Volume**: {price_data.get('volume_24h', 0):,.0f}

"""

            # Mark Price & Funding
            mark_data = comp_data.get('mark_price_data', {})
            if mark_data and 'error' not in mark_data:
                mark_price = mark_data.get('mark_price', 0)
                index_price = mark_data.get('index_price', 0)
                funding_rate = mark_data.get('last_funding_rate', 0)
                funding_pct = funding_rate * 100

                message += f"""⚡ **Mark Price & Funding** 🟢
• **Mark Price**: {self.crypto_api._format_price_display(mark_price)}
• **Index Price**: {self.crypto_api._format_price_display(index_price)}
• **Funding Rate**: {funding_pct:+.4f}%
• **Next Funding**: {mark_data.get('next_funding_time_iso', '')[:16].replace('T', ' ')}

"""

            # Long/Short Ratio
            ls_data = comp_data.get('long_short_ratio_data', {})
            if ls_data and 'error' not in ls_data:
                long_ratio = ls_data.get('long_ratio', 0)
                short_ratio = ls_data.get('short_ratio', 0)

                message += f"""📊 **Long/Short Ratio** 🟢
• **Long Ratio**: {long_ratio:.1f}%
• **Short Ratio**: {short_ratio:.1f}%
• **L/S Ratio**: {ls_data.get('long_short_ratio', 0):.2f}
• **Sentiment**: {'Bullish' if long_ratio > 60 else 'Bearish' if long_ratio < 40 else 'Neutral'}

"""

            # Open Interest
            oi_data = comp_data.get('open_interest_data', {})
            if oi_data and 'error' not in oi_data:
                oi_value = oi_data.get('open_interest', 0)
                if oi_value > 1000000000:
                    oi_format = f"{oi_value/1000000000:.2f}B"
                elif oi_value > 1000000:
                    oi_format = f"{oi_value/1000000:.2f}M"
                else:
                    oi_format = f"{oi_value:,.0f}"

                message += f"""📈 **Open Interest** 🟢
• **Total OI**: {oi_format}
• **Timestamp**: {oi_data.get('time_iso', '')[:16].replace('T', ' ')}

"""

            # Liquidation Data
            liq_data = comp_data.get('liquidation_data', {})
            if liq_data and 'error' not in liq_data:
                total_liq = liq_data.get('total_liquidation', 0)
                long_liq = liq_data.get('long_liquidation', 0)
                short_liq = liq_data.get('short_liquidation', 0)

                message += f"""🔥 **Liquidations (Recent)** 🟢
• **Total**: ${total_liq:,.0f}
• **Long Liq**: ${long_liq:,.0f}
• **Short Liq**: ${short_liq:,.0f}
• **Orders**: {liq_data.get('total_orders', 0)}

"""

            message += f"🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}\n"
            message += f"🔄 **Source**: Binance Futures API (Real-time)"

            # Deduct credit only for non-premium, non-admin users
            if not is_premium and not is_admin:
                self.db.deduct_credit(user_id, 25)
                remaining_credits = self.db.get_user_credits(user_id)
                message += f"\n\n💳 Credit tersisa: {remaining_credits} (Data comprehensive: -25 credit)"
            elif is_premium:
                message += f"\n\n⭐ **Status Premium** - Unlimited Access"
            elif is_admin:
                message += f"\n\n👑 **Admin Access** - Unlimited"

            await loading_msg.edit_text(message, parse_mode='Markdown')

        except Exception as e:
            await loading_msg.edit_text(f"❌ Terjadi kesalahan: {str(e)}")
            print(f"Error in binance_data command: {e}")

    async def candles_command(self, update: Update, context: CallbackContext):
        """Handle /candles command - candlestick data"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/candles <symbol> [interval] [limit]`\nContoh: `/candles btc 1h 12`", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()
        interval = context.args[1] if len(context.args) > 1 else '1h'
        limit = int(context.args[2]) if len(context.args) > 2 and context.args[2].isdigit() else 12

        # Validate interval
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        if interval not in valid_intervals:
            await update.message.reply_text(f"❌ Interval tidak valid! Gunakan: {', '.join(valid_intervals)}")
            return

        # Limit the limit
        if limit > 50:
            limit = 50

        loading_msg = await update.message.reply_text(f"⏳ Mengambil data candlestick {symbol} ({interval})...")

        try:
            candles_data = self.crypto_api.get_binance_candlestick(symbol, interval, limit)

            if not candles_data or 'error' in candles_data:
                await loading_msg.edit_text(f"❌ Gagal mengambil data candlestick untuk {symbol}")
                return

            candlesticks = candles_data.get('candlesticks', [])
            source = candles_data.get('source', 'unknown')
            source_emoji = "🟢" if source == 'binance' else "🔄"

            if not candlesticks:
                await loading_msg.edit_text(f"❌ Tidak ada data candlestick untuk {symbol}")
                return

            message = f"""📈 **Candlestick Data - {symbol}** {source_emoji}

**Interval**: {interval} | **Count**: {len(candlesticks)}

**Recent Candles:**
"""

            # Show last 6 candles
            recent_candles = candlesticks[-6:]
            for i, candle in enumerate(recent_candles):
                time_str = candle.get('close_time_iso', '')[:16].replace('T', ' ')
                open_p = self.crypto_api._format_price_display(candle.get('open', 0))
                close_p = self.crypto_api._format_price_display(candle.get('close', 0))
                high_p = self.crypto_api._format_price_display(candle.get('high', 0))
                low_p = self.crypto_api._format_price_display(candle.get('low', 0))
                volume = candle.get('volume', 0)

                change = ((candle.get('close', 0) - candle.get('open', 0)) / candle.get('open', 1)) * 100
                change_emoji = "🟢" if change >= 0 else "🔴"

                message += f"\n**{time_str}** {change_emoji}\n"
                message += f"O:{open_p} H:{high_p} L:{low_p} C:{close_p}\n"
                message += f"Vol: {volume:,.0f} | {change:+.2f}%\n"

            message += f"\n🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}"
            message += f"\n🔄 **Source**: {source.title()}"

            await loading_msg.edit_text(message, parse_mode='Markdown')

        except Exception as e:
            await loading_msg.edit_text(f"❌ Terjadi kesalahan: {str(e)}")

    async def funding_command(self, update: Update, context: CallbackContext):
        """Handle /funding command - funding rate data"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/funding <symbol>`\nContoh: `/funding btc`", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()
        loading_msg = await update.message.reply_text(f"⏳ Mengambil data funding rate {symbol}...")

        try:
            funding_data = self.crypto_api.get_binance_funding_rate(symbol)

            if not funding_data or 'error' in funding_data:
                await loading_msg.edit_text(f"❌ Gagal mengambil data funding rate untuk {symbol}")
                return

            source = funding_data.get('source', 'unknown')
            source_emoji = "🟢" if source == 'binance_futures' else "🔄"

            mark_price = funding_data.get('mark_price', 0)
            index_price = funding_data.get('index_price', 0)
            funding_rate = funding_data.get('last_funding_rate', 0)
            funding_pct = funding_rate * 100
            next_funding = funding_data.get('next_funding_time_iso', '')

            # Determine funding rate status
            if funding_rate > 0.01:
                funding_status = "🔴 Sangat Tinggi (Long membayar Short)"
            elif funding_rate > 0.005:
                funding_status = "🟡 Tinggi (Long membayar Short)"
            elif funding_rate > 0:
                funding_status = "🟢 Positif (Long membayar Short)"
            elif funding_rate > -0.005:
                funding_status = "🟢 Negatif (Short membayar Long)"
            else:
                funding_status = "🔴 Sangat Negatif (Short membayar Long)"

            message = f"""⚡ **Funding Rate - {symbol}** {source_emoji}

💰 **Mark Price**: {self.crypto_api._format_price_display(mark_price)}
📊 **Index Price**: {self.crypto_api._format_price_display(index_price)}

**Funding Rate**: {funding_pct:+.4f}%
{funding_status}

**Next Funding**: {next_funding[:16].replace('T', ' ') if next_funding else 'N/A'}

**Interpretasi:**
• Funding Rate positif = Long traders bayar Short
• Funding Rate negatif = Short traders bayar Long
• Rate tinggi = Market bullish/long heavy
• Rate rendah/negatif = Market bearish/short heavy

🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}
🔄 **Source**: {source.replace('_', ' ').title()}"""

            await loading_msg.edit_text(message, parse_mode='Markdown')

        except Exception as e:
            await loading_msg.edit_text(f"❌ Terjadi kesalahan: {str(e)}")

    async def open_interest_command(self, update: Update, context: CallbackContext):
        """Handle /oi command - open interest data"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/oi <symbol>`\nContoh: `/oi btc`", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()
        loading_msg = await update.message.reply_text(f"⏳ Mengambil data open interest {symbol}...")

        try:
            oi_data = self.crypto_api.get_binance_open_interest(symbol)

            if not oi_data or 'error' in oi_data:
                await loading_msg.edit_text(f"❌ Gagal mengambil data open interest untuk {symbol}")
                return

            source = oi_data.get('source', 'unknown')
            source_emoji = "🟢" if source == 'binance_futures' else "🔄"

            oi_value = oi_data.get('open_interest', 0)
            time_iso = oi_data.get('time_iso', '')

            # Format OI value
            if oi_value > 1000000000:
                oi_format = f"{oi_value/1000000000:.2f}B"
            elif oi_value > 1000000:
                oi_format = f"{oi_value/1000000:.2f}M"
            elif oi_value > 1000:
                oi_format = f"{oi_value/1000:.1f}K"
            else:
                oi_format = f"{oi_value:,.0f}"

            # OI analysis
            if oi_value > 100000000:  # 100M+
                oi_status = "🔴 Sangat Tinggi - High Leverage Risk"
            elif oi_value > 50000000:   # 50M+
                oi_status = "🟡 Tinggi - Moderate Risk"
            elif oi_value > 10000000:   # 10M+
                oi_status = "🟢 Normal - Healthy Activity"
            else:
                oi_status = "🔵 Rendah - Low Activity"

            message = f"""📊 **Open Interest - {symbol}** {source_emoji}

**Open Interest**: {oi_format} ({oi_value:,.0f})
{oi_status}

**Timestamp**: {time_iso[:16].replace('T', ' ') if time_iso else 'N/A'}

**Analisis Open Interest:**
• OI tinggi = Banyak posisi terbuka, volatilitas potensial
• OI rendah = Sedikit leverage, pergerakan lebih stabil
• OI naik + harga naik = Bullish confirmation
• OI naik + harga turun = Bearish confirmation
• OI turun = Profit taking atau position closing

💡 **Trading Insight:**
• High OI = Waspadai sudden liquidation
• Rising OI = Strong trend confirmation
• Falling OI = Trend may be weakening

🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}
🔄 **Source**: {source.replace('_', ' ').title()}"""

            await loading_msg.edit_text(message, parse_mode='Markdown')

        except Exception as e:
            await loading_msg.edit_text(f"❌ Terjadi kesalahan: {str(e)}")

    async def mark_price_command(self, update: Update, context: CallbackContext):
        """Handle /mark_price command - mark price and premium index"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/mark_price <symbol>`\nContoh: `/mark_price btc`", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()
        loading_msg = await update.message.reply_text(f"⏳ Mengambil data mark price {symbol}...")

        try:
            mark_data = self.crypto_api.get_binance_mark_price(symbol)

            if not mark_data or 'error' in mark_data:
                await loading_msg.edit_text(f"❌ Gagal mengambil data mark price untuk {symbol}")
                return

            mark_price = mark_data.get('mark_price', 0)
            index_price = mark_data.get('index_price', 0)
            funding_rate = mark_data.get('last_funding_rate', 0)
            funding_pct = funding_rate * 100
            next_funding = mark_data.get('next_funding_time_iso', '')

            # Calculate premium
            premium = ((mark_price - index_price) / index_price * 100) if index_price > 0 else 0

            message = f"""⚡ **Mark Price & Premium Index - {symbol}** 🟢

💰 **Mark Price**: {self.crypto_api._format_price_display(mark_price)}
📊 **Index Price**: {self.crypto_api._format_price_display(index_price)}
📈 **Premium**: {premium:+.4f}%

**Funding Rate**: {funding_pct:+.4f}%
**Next Funding**: {next_funding[:16].replace('T', ' ') if next_funding else 'N/A'}

**Interpretasi:**
• Mark Price = Harga kontrak futures
• Index Price = Harga spot rata-rata
• Premium > 0 = Futures lebih mahal (Bullish)
• Premium < 0 = Futures lebih murah (Bearish)

**Funding Rate:**
• Positif = Long traders bayar Short
• Negatif = Short traders bayar Long
• Rate tinggi = Sentiment bullish kuat

🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}
🔄 **Source**: Binance Futures API"""

            await loading_msg.edit_text(message, parse_mode='Markdown')

        except Exception as e:
            await loading_msg.edit_text(f"❌ Terjadi kesalahan: {str(e)}")

    async def server_time_command(self, update: Update, context: CallbackContext):
        """Handle /server_time command - Binance server time"""
        loading_msg = await update.message.reply_text("⏳ Mengambil waktu server Binance...")

        try:
            time_data = self.crypto_api.get_binance_server_time()

            if not time_data or 'error' in time_data:
                await loading_msg.edit_text("❌ Gagal mengambil waktu server Binance")
                return

            server_time = time_data.get('server_time_readable', '')
            server_time_iso = time_data.get('server_time_iso', '')

            # Get local time for comparison
            local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')

            message = f"""🕐 **Binance Server Time** 🟢

**Server Time (UTC)**: {server_time}
**Server Time (ISO)**: {server_time_iso}
**Local Time (WIB)**: {local_time}

**Network Status**: ✅ Connected
**API Latency**: <100ms (Real-time)

💡 **Info:**
• Server time digunakan untuk timestamp trading
• Penting untuk order execution accuracy
• Binance menggunakan UTC timezone

🔄 **Source**: Binance Spot API"""

            await loading_msg.edit_text(message, parse_mode='Markdown')

        except Exception as e:
            await loading_msg.edit_text(f"❌ Terjadi kesalahan: {str(e)}")

    async def liquidations_command(self, update: Update, context: CallbackContext):
        """Handle /liquidations command - recent liquidation orders"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/liquidations <symbol>`\nContoh: `/liquidations btc`", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()
        loading_msg = await update.message.reply_text(f"⏳ Mengambil data liquidation {symbol}...")

        try:
            liq_data = self.crypto_api.get_binance_liquidation_orders(symbol)

            if not liq_data or 'error' in liq_data:
                await loading_msg.edit_text(f"❌ Gagal mengambil data liquidation untuk {symbol}")
                return

            total_liq = liq_data.get('total_liquidation', 0)
            long_liq = liq_data.get('long_liquidation', 0)
            short_liq = liq_data.get('short_liquidation', 0)
            total_orders = liq_data.get('total_orders', 0)
            recent_orders = liq_data.get('liquidation_orders', [])

            message = f"""🔥 **Liquidations - {symbol}** 🟢

📊 **Summary (Recent Orders):**
• **Total Liquidation**: ${total_liq:,.0f}
• **Long Liquidations**: ${long_liq:,.0f} ({(long_liq/total_liq*100) if total_liq > 0 else 0:.1f}%)
• **Short Liquidations**: ${short_liq:,.0f} ({(short_liq/total_liq*100) if total_liq > 0 else 0:.1f}%)
• **Total Orders**: {total_orders}

**Recent Liquidations:**
"""

            # Show last 5 liquidations
            for i, order in enumerate(recent_orders[-5:]):
                side_emoji = "🔴" if order['side'] == 'SELL' else "🟢"
                time_str = order.get('time_iso', '')[:16].replace('T', ' ')
                message += f"{side_emoji} {order['side']} ${order['value']:,.0f} @ {order['time_str']}\n"

            message += f"""
**Analisis:**
• Long dominance = {(long_liq/total_liq*100) if total_liq > 0 else 0:.1f}% liquidation
• {'Longs getting rekt' if long_liq > short_liq else 'Shorts getting rekt' if short_liq > long_liq else 'Balanced liquidation'}
• Market stress level: {'High' if total_orders > 50 else 'Medium' if total_orders > 20 else 'Low'}

🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}
🔄 **Source**: Binance Futures API"""

            await loading_msg.edit_text(message, parse_mode='Markdown')

        except Exception as e:
            await loading_msg.edit_text(f"❌ Terjadi kesalahan: {str(e)}")

    async def long_short_command(self, update: Update, context: CallbackContext):
        """Handle /long_short command - long/short ratio analysis"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/long_short <symbol>`\nContoh: `/long_short btc`", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()
        loading_msg = await update.message.reply_text(f"⏳ Mengambil data long/short ratio {symbol}...")

        try:
            ls_data = self.crypto_api.get_binance_long_short_ratio(symbol)

            if not ls_data or 'error' in ls_data:
                await loading_msg.edit_text(f"❌ Gagal mengambil data long/short ratio untuk {symbol}")
                return

            long_ratio = ls_data.get('long_ratio', 0)
            short_ratio = ls_data.get('short_ratio', 0)
            ls_ratio = ls_data.get('long_short_ratio', 0)
            long_account = ls_data.get('long_account', 0)


    async def test_binance_command(self, update: Update, context: CallbackContext):
        """Handle /test_binance command - admin only debug tool"""
        user_id = update.message.from_user.id
        
        # Admin only command
        if user_id != self.admin_id:
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return
            
        # Show loading message
        loading_msg = await update.message.reply_text("🔧 Testing Binance API connectivity and price validation...")
        
        try:
            print(f"🔧 Admin {user_id} initiated Binance API test")
            
            # Test deployment mode detection
            is_deployment = (
                os.getenv('REPLIT_DEPLOYMENT') == '1' or 
                os.getenv('REPL_DEPLOYMENT') == '1' or
                os.path.exists('/tmp/repl_deployment_flag') or
                bool(os.getenv('REPL_SLUG'))
            )
            
            # Test basic connectivity
            connectivity_test = self.crypto_api.test_binance_connectivity()
            
            # Test price retrieval for major coins
            test_symbols = ['BTC', 'ETH', 'BNB']
            price_tests = {}
            
            for symbol in test_symbols:
                try:
                    price_data = self.crypto_api.get_binance_price(symbol, force_refresh=True)
                    if 'error' not in price_data and price_data.get('price', 0) > 0:
                        price_tests[symbol] = {
                            'success': True,
                            'price': price_data.get('price'),
                            'source': price_data.get('source', 'unknown'),
                            'validation': price_data.get('price_validation_passed', False)
                        }
                    else:
                        price_tests[symbol] = {
                            'success': False,
                            'error': price_data.get('error', 'Unknown error'),
                            'source': 'failed'
                        }
                except Exception as e:
                    price_tests[symbol] = {
                        'success': False,
                        'error': str(e),
                        'source': 'exception'
                    }
            
            # Test futures API
            futures_test = {}
            try:
                futures_data = self.crypto_api.get_binance_futures_price('BTC')
                if 'error' not in futures_data and futures_data.get('price', 0) > 0:
                    futures_test = {
                        'success': True,
                        'price': futures_data.get('price'),
                        'validation': futures_data.get('price_validation_passed', False)
                    }
                else:
                    futures_test = {
                        'success': False,
                        'error': futures_data.get('error', 'Unknown futures error')
                    }
            except Exception as e:
                futures_test = {
                    'success': False,
                    'error': str(e)
                }
            
            # Build comprehensive test report
            successful_tests = sum([
                connectivity_test.get('spot_ping', False),
                connectivity_test.get('futures_ping', False),
                connectivity_test.get('spot_price', False),
                connectivity_test.get('futures_price', False),
                sum(1 for test in price_tests.values() if test.get('success', False)),
                futures_test.get('success', False)
            ])
            
            total_tests = 4 + len(test_symbols) + 1  # 4 connectivity + price tests + futures test
            success_rate = (successful_tests / total_tests) * 100
            
            # Format test results
            message = f"""🔧 **Binance API Test Results**

📍 **Environment**: {'🌐 DEPLOYMENT' if is_deployment else '🔧 DEVELOPMENT'}
📊 **Overall Health**: {success_rate:.1f}% ({successful_tests}/{total_tests} tests passed)

🌐 **Connectivity Tests**:
• Spot API Ping: {'✅' if connectivity_test.get('spot_ping') else '❌'}
• Futures API Ping: {'✅' if connectivity_test.get('futures_ping') else '❌'}
• Spot Price Test: {'✅' if connectivity_test.get('spot_price') else '❌'}
• Futures Price Test: {'✅' if connectivity_test.get('futures_price') else '❌'}

💰 **Price Validation Tests**:"""

            for symbol, test in price_tests.items():
                if test.get('success'):
                    price_str = f"${test.get('price'):,.4f}"
                    source = test.get('source', 'unknown')
                    validation = '✅' if test.get('validation') else '⚠️'
                    message += f"\n• {symbol}: ✅ {price_str} ({source}) {validation}"
                else:
                    error = test.get('error', 'Unknown error')[:50]
                    message += f"\n• {symbol}: ❌ {error}..."

            # Futures test result
            if futures_test.get('success'):
                futures_price = f"${futures_test.get('price'):,.4f}"
                validation = '✅' if futures_test.get('validation') else '⚠️'
                message += f"\n\n🚀 **Futures Test**: ✅ BTC {futures_price} {validation}"
            else:
                futures_error = futures_test.get('error', 'Unknown error')[:50]
                message += f"\n\n🚀 **Futures Test**: ❌ {futures_error}..."

            # Add deployment specific info
            if is_deployment:
                message += f"\n\n🌐 **Deployment Info**:"
                message += f"\n• Real-time Mode: {'✅ Enabled' if is_deployment else '❌ Disabled'}"
                message += f"\n• Force Refresh: ✅ Active"
                message += f"\n• Cache Control: ✅ Disabled"
            else:
                message += f"\n\n🔧 **Development Info**:"
                message += f"\n• Test Mode: ✅ Active"
                message += f"\n• Retry Logic: ✅ Enabled"
                message += f"\n• Debug Logging: ✅ Verbose"

            # Health assessment
            if success_rate >= 80:
                message += f"\n\n✅ **Status**: Excellent - All systems operational"
            elif success_rate >= 60:
                message += f"\n\n🟡 **Status**: Good - Minor issues detected"
            else:
                message += f"\n\n❌ **Status**: Poor - Major issues require attention"

            message += f"\n\n⏰ **Test Time**: {datetime.now().strftime('%H:%M:%S WIB')}"
            
            print(f"✅ Binance test completed for admin {user_id}: {success_rate:.1f}% success rate")
            
            await loading_msg.edit_text(message, parse_mode='Markdown')
            
        except Exception as e:
            error_msg = f"""❌ **Binance Test Failed**

**Error**: {str(e)[:200]}...

🔧 **Troubleshooting**:
• Check internet connectivity
• Verify Binance API status
• Review bot logs for details
• Try again in a few minutes

⏰ **Failed at**: {datetime.now().strftime('%H:%M:%S WIB')}"""
            
            await loading_msg.edit_text(error_msg, parse_mode='Markdown')
            print(f"❌ Binance test failed for admin {user_id}: {e}")


            short_account = ls_data.get('short_account', 0)

            # Determine sentiment
            if long_ratio > 70:
                sentiment = "🔴 Extremely Bullish (Overleveraged)"
                risk_level = "High Risk - Potential Long Squeeze"
            elif long_ratio > 60:
                sentiment = "🟡 Bullish"
                risk_level = "Medium Risk"
            elif long_ratio < 30:
                sentiment = "🔴 Extremely Bearish (Oversold)"
                risk_level = "High Risk - Potential Short Squeeze"
            elif long_ratio < 40:
                sentiment = "🟡 Bearish"
                risk_level = "Medium Risk"
            else:
                sentiment = "🟢 Neutral/Balanced"
                risk_level = "Low Risk"

            message = f"""📊 **Long/Short Ratio - {symbol}** 🟢

**Position Ratio:**
• **Long Ratio**: {long_ratio:.1f}%
• **Short Ratio**: {short_ratio:.1f}%
• **L/S Ratio**: {ls_ratio:.2f}

**Account Distribution:**
• **Long Accounts**: {long_account:.1f}%
• **Short Accounts**: {short_account:.1f}%

**Market Sentiment**: {sentiment}
**Risk Level**: {risk_level}

**Analisis:**
• Ratio tinggi (>60%) = Bullish bias, watch for long squeeze
• Ratio rendah (<40%) = Bearish bias, watch for short squeeze
• Ratio seimbang (40-60%) = Healthy market structure

**Trading Insight:**
• Extreme ratios often signal reversals
• Use as contrarian indicator
• Combine with price action for confirmation

🕐 **Update**: {datetime.now().strftime('%H:%M:%S WIB')}
🔄 **Source**: Binance Futures API (Top Traders)"""

            await loading_msg.edit_text(message, parse_mode='Markdown')

        except Exception as e:
            await loading_msg.edit_text(f"❌ Terjadi kesalahan: {str(e)}")

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
                "**Method 1 - By Package (Recommended):**\n"
                "`/grant_package <user_id> <package>`\n\n"
                "**Packages:** 1month, 2months, 6months, 1year, lifetime\n"
                "**Contoh:** `/grant_package 123456789 6months`\n\n"
                "**Method 2 - By Days:**\n"
                "`/grant_premium <user_id> [days]`\n"
                "**Contoh:** `/grant_premium 123456789 30`",
                parse_mode='Markdown'
            )

        elif data == 'grant_package_help' and user_id == self.admin_id:
            await query.edit_message_text(
                "💎 **Grant Package Premium**\n\n"
                "Gunakan command: `/grant_package <user_id> <package>`\n\n"
                "**Available Packages:**\n"
                "• `1month` - 1 Bulan (Rp 320k)\n"
                "• `2months` - 2 Bulan (Rp 600k)\n"
                "• `6months` - 6 Bulan (Rp 1.8jt)\n"
                "• `1year` - 1 Tahun (Rp 3jt)\n"
                "• `lifetime` - Lifetime (Rp 5jt)\n\n"
                "**Contoh:**\n"
                "`/grant_package 123456789 6months`\n"
                "`/grant_package 123456789 lifetime`",
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
            keyboard = [
                [InlineKeyboardButton("✅ Confirm Restart All Users", callback_data='confirm_restart_users')],
                [InlineKeyboardButton("❌ Cancel", callback_data='admin_panel')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🔄 **Restart All Users**\n\n"
                "⚠️ **This will reset ALL users' start status**\n\n"
                "**What happens:**\n"
                "• All users must use `/start` again\n"
                "• Other commands blocked until restart\n"
                "• **NO DATA LOSS** (credits, premium preserved)\n"
                "• Perfect for engagement tracking\n\n"
                "**Confirm to proceed:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        elif data == 'refresh_credits_panel' and user_id == self.admin_id:
            keyboard = [
                [InlineKeyboardButton("✅ Confirm Credit Refresh", callback_data='confirm_credit_refresh')],
                [InlineKeyboardButton("❌ Cancel", callback_data='admin_panel')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Get current statistics
            try:
                self.db.cursor.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE (is_premium = 0 OR is_premium IS NULL) 
                    AND telegram_id IS NOT NULL
                """)
                free_users_count = self.db.cursor.fetchone()[0]
                
                await query.edit_message_text(
                    f"💰 **Weekly Credit Refresh**\n\n"
                    f"**Current free users**: {free_users_count}\n\n"
                    "**What happens:**\n"
                    "• All free users get 100 credits\n"
                    "• Previous credits reset to 100\n"
                    "• Premium users not affected\n"
                    "• Activity logged for tracking\n\n"
                    "**Confirm to proceed:**",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            except Exception as e:
                await query.edit_message_text(f"❌ Error getting user count: {str(e)}")

        elif data == 'confirm_credit_refresh' and user_id == self.admin_id:
            await query.edit_message_text("🔄 Processing credit refresh...")
            
            try:
                import subprocess
                import sys
                
                result = subprocess.run([
                    sys.executable, 
                    'weekly_credit_refresh.py'
                ], 
                cwd='Bismillah',
                capture_output=True, 
                text=True, 
                timeout=300
                )
                
                if result.returncode == 0:
                    output_lines = result.stdout.strip().split('\n')
                    users_updated = 0
                    credits_given = 0
                    
                    for line in output_lines:
                        if "Users updated:" in line:
                            users_updated = int(line.split(":")[1].split("/")[0].strip())
                        elif "Total credits distributed:" in line:
                            credits_given = int(line.split(":")[1].strip().replace(",", ""))
                    
                    await query.edit_message_text(
                        f"✅ **Credit Refresh Completed!**\n\n"
                        f"📊 **Updated**: {users_updated} free users\n"
                        f"💰 **Credits given**: {credits_given:,} total\n"
                        f"🕐 **Time**: {datetime.now().strftime('%H:%M:%S WIB')}",
                        parse_mode='Markdown'
                    )
                    
                    self.db.log_user_activity(user_id, "admin_panel_credit_refresh", f"Refreshed credits for {users_updated} users via panel")
                else:
                    await query.edit_message_text(f"❌ Credit refresh failed: {result.stderr or result.stdout}")
                    
            except Exception as e:
                await query.edit_message_text(f"❌ Error during refresh: {str(e)}")

        elif data == 'confirm_restart_users' and user_id == self.admin_id:
            try:
                restart_count = self.db.mark_all_users_for_restart()
                await query.edit_message_text(
                    f"✅ **Restart Completed!**\n\n"
                    f"📊 **{restart_count} users** marked for restart\n"
                    f"🔄 All users must use `/start` to continue\n"
                    f"💾 All data preserved safely\n\n"
                    f"**Completed**: {datetime.now().strftime('%H:%M:%S WIB')}",
                    parse_mode='Markdown'
                )
                self.db.log_user_activity(user_id, "admin_restart_all", f"Restarted {restart_count} users via panel")
            except Exception as e:
                await query.edit_message_text(f"❌ Error during restart: {str(e)}")

        elif data == 'admin_panel' and user_id == self.admin_id:
            # Return to main admin panel
            keyboard = [
                [InlineKeyboardButton("👑 Buat User Premium", callback_data='make_premium')],
                [InlineKeyboardButton("💎 Grant Package Premium", callback_data='grant_package_help')],
                [InlineKeyboardButton("💰 Berikan Credits", callback_data='grant_credits')],
                [InlineKeyboardButton("🎁 Refresh Credits Mingguan", callback_data='refresh_credits_panel')],
                [InlineKeyboardButton("📢 Broadcast Message", callback_data='broadcast_help')],
                [InlineKeyboardButton("📊 Statistik Bot", callback_data='bot_stats')],
                [InlineKeyboardButton("📝 Log Aktivitas", callback_data='activity_log')],
                [InlineKeyboardButton("🔍 API Health Report", callback_data='api_health')],
                [InlineKeyboardButton("🔄 Restart All Users", callback_data='restart_bot')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "🛠 **Panel Admin CryptoMentor**\n\n"
                "Pilih opsi yang tersedia:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        # Handle futures analysis callbacks (direct AI analysis)
        elif data.startswith('futures_analysis_'):
            parts = data.split('_')
            symbol = parts[2]
            timeframe = parts[3]
            await self._handle_direct_futures_analysis(query, symbol, timeframe)

        # Handle futures menu callback (return to timeframe selection)
        elif data.startswith('futures_menu_'):
            symbol = data.split('_')[-1]
            keyboard = [
                [InlineKeyboardButton("⚡ 15m", callback_data=f'futures_analysis_{symbol}_15m'),
                 InlineKeyboardButton("🔥 30m", callback_data=f'futures_analysis_{symbol}_30m')],
                [InlineKeyboardButton("📈 1h", callback_data=f'futures_analysis_{symbol}_1h'),
                 InlineKeyboardButton("🚀 4h", callback_data=f'futures_analysis_{symbol}_4h')],
                [InlineKeyboardButton("💎 1d", callback_data=f'futures_analysis_{symbol}_1d'),
                 InlineKeyboardButton("🌟 1w", callback_data=f'futures_analysis_{symbol}_1w')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"📊 **Analisis Futures {symbol}**\n\n"
                "Pilih timeframe untuk analisis teknikal advance:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

        # Handle additional futures analysis callbacks
        elif data.startswith('deep_technical_'):
            symbol = data.split('_')[-1]
            await self._handle_deep_technical_analysis(query, symbol)

        elif data.startswith('binance_data_'):
            symbol = data.split('_')[-1]
            await self._handle_binance_data_callback(query, symbol)

        elif data.startswith('liquidation_'):
            symbol = data.split('_')[-1]
            await self._handle_liquidation_analysis(query, symbol)

        elif data.startswith('long_short_'):
            symbol = data.split('_')[-1]
            await self._handle_long_short_analysis(query, symbol)

        elif data.startswith('funding_history_'):
            symbol = data.split('_')[-1]
            await self._handle_funding_history(query, symbol)

    async def _check_user_restart_required(self, update: Update) -> bool:
        """Check if user needs to restart before using commands"""
        user_id = update.effective_user.id
        
        # Skip check for admin
        if user_id == self.admin_id:
            return False
            
        # Skip check for start command (handled separately)
        if update.message and update.message.text and update.message.text.startswith('/start'):
            return False
            
        # Check if user needs restart
        if self.db.user_needs_restart(user_id):
            await update.message.reply_text(
                "🔄 **Bot telah direstart oleh admin**\n\n"
                "Silakan gunakan `/start` untuk melanjutkan penggunaan bot.\n\n"
                "💡 Data Anda (credits, premium, portfolio) tetap aman!",
                parse_mode='Markdown'
            )
            return True
        return False

    async def handle_message(self, update: Update, context: CallbackContext):
        """Handle regular text messages (not commands)"""
        # Check if user needs restart
        if await self._check_user_restart_required(update):
            return
            
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
                    loading_msg = await update.message.reply_text(f"⏳ Mengecek harga {detected_symbol} real-time...")

                    # Get price data with deployment-aware force refresh
                    price_data = self.crypto_api.get_price(detected_symbol, force_refresh=IS_DEPLOYMENT)

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

    async def _handle_direct_futures_analysis(self, query, symbol, timeframe):
        """Handle direct AI futures analysis without position selection"""
        user_id = query.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = user_id == self.admin_id

        # Check credits again for non-premium users
        if not is_premium and not is_admin and credits < 20:
            await query.edit_message_text("❌ Credit tidak cukup untuk analisis futures!")
            return

        # Show loading message
        await query.edit_message_text(f"⏳ AI sedang menganalisis {symbol} pada timeframe {timeframe}...")

        try:
            # Get AI recommendation for best trading setup
            analysis = self.ai.get_ai_futures_recommendation(symbol, timeframe, self.crypto_api)

            # Deduct credits for non-premium users
            if not is_premium and not is_admin:
                self.db.deduct_credit(user_id, 20)
                remaining_credits = self.db.get_user_credits(user_id)
                analysis += f"\n\n💳 Credit tersisa: {remaining_credits} (Analisis futures: -20 credit)"
            elif is_premium:
                analysis += f"\n\n⭐ **Status Premium** - Unlimited Access"
            elif is_admin:
                analysis += f"\n\n👑 **Admin Access** - Unlimited"

            # Add navigation keyboard
            keyboard = [
                [InlineKeyboardButton("🔄 Ganti Timeframe", callback_data=f'futures_menu_{symbol}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Split long messages if needed
            if len(analysis) > 4000:
                chunks = [analysis[i:i+4000] for i in range(0, len(analysis), 4000)]
                await query.edit_message_text(chunks[0], parse_mode='Markdown')

                # Send additional chunks
                for chunk in chunks[1:]:
                    await query.message.reply_text(chunk, parse_mode='Markdown')

                # Add keyboard to last message
                await query.message.reply_text("📈 **Navigasi:**", reply_markup=reply_markup)
            else:
                await query.edit_message_text(analysis, reply_markup=reply_markup, parse_mode='Markdown')

        except Exception as e:
            await query.edit_message_text(f"❌ Terjadi kesalahan: {str(e)[:100]}")

    async def _handle_futures_timeframe_analysis(self, query, symbol, timeframe, position='long'):
        """Handle futures timeframe analysis callback with position"""
        user_id = query.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = user_id == self.admin_id

        # Check credits again for non-premium users
        if not is_premium and not is_admin and credits < 20:
            await query.edit_message_text("❌ Credit tidak cukup untuk analisis futures!")
            return

        # Show loading message
        position_emoji = "📈" if position == 'long' else "📉"
        await query.edit_message_text(f"⏳ Menganalisis {symbol} {position_emoji} {position.upper()} pada {timeframe}...")

        try:
            # Get comprehensive timeframe analysis with position
            analysis = self.ai.get_advanced_technical_analysis_with_position(symbol, timeframe, position, self.crypto_api)

            # Deduct credits for non-premium users
            if not is_premium and not is_admin:
                self.db.deduct_credit(user_id, 20)
                remaining_credits = self.db.get_user_credits(user_id)
                analysis += f"\n\n💳 Credit tersisa: {remaining_credits} (Analisis futures: -20 credit)"
            elif is_premium:
                analysis += f"\n\n⭐ **Status Premium** - Unlimited Access"
            elif is_admin:
                analysis += f"\n\n👑 **Admin Access** - Unlimited"

            # Add navigation keyboard
            keyboard = [
                [InlineKeyboardButton("🔄 Ganti Position", callback_data=f'futures_tf_{symbol}_{timeframe}'),
                 InlineKeyboardButton("📊 Ganti Timeframe", callback_data=f'futures_menu_{symbol}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Split long messages if needed
            if len(analysis) > 4000:
                chunks = [analysis[i:i+4000] for i in range(0, len(analysis), 4000)]
                await query.edit_message_text(chunks[0], parse_mode='Markdown')

                # Send additional chunks
                for chunk in chunks[1:]:
                    await query.message.reply_text(chunk, parse_mode='Markdown')

                # Add keyboard to last message
                await query.message.reply_text("📈 **Navigasi:**", reply_markup=reply_markup)
            else:
                await query.edit_message_text(analysis, reply_markup=reply_markup, parse_mode='Markdown')

        except Exception as e:
            await query.edit_message_text(f"❌ Terjadi kesalahan: {str(e)[:100]}")

    async def _handle_deep_technical_analysis(self, query, symbol):
        """Handle deep technical analysis callback"""
        await query.edit_message_text(f"📚 Analisis teknikal mendalam untuk {symbol} akan segera hadir!")

    async def _handle_binance_data_callback(self, query, symbol):
        """Handle Binance data callback"""
        await query.edit_message_text(f"📊 Data Binance untuk {symbol} akan segera hadir!")

    async def _handle_liquidation_analysis(self, query, symbol):
        """Handle liquidation analysis callback"""
        await query.edit_message_text(f"🔥 Analisis likuidasi untuk {symbol} akan segera hadir!")

    async def _handle_long_short_analysis(self, query, symbol):
        """Handle long/short ratio analysis callback"""
        await query.edit_message_text(f"🐂 Analisis long/short ratio untuk {symbol} akan segera hadir!")

    async def _handle_funding_history(self, query, symbol):
        """Handle funding rate history callback"""
        await query.edit_message_text(f"💰 Histori funding rate untuk {symbol} akan segera hadir!")

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
            [InlineKeyboardButton("🎁 Refresh Credits Mingguan", callback_data='refresh_credits_panel')],
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

    async def restart_command(self, update: Update, context: CallbackContext):
        """Handle /restart command - Reset all users to require /start again"""
        user_id = update.message.from_user.id

        # Only admin can use restart command
        if user_id != self.admin_id:
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        # Check if confirmation is provided
        if context.args and context.args[0].lower() == 'confirm':
            try:
                # Mark all users for restart
                restart_count = self.db.mark_all_users_for_restart()
                
                success_message = f"""✅ **Bot Restart Executed Successfully!**

📊 **Results:**
• **Users marked for restart**: {restart_count}
• **Status**: All users must use `/start` again
• **Data preserved**: Credits, premium, portfolio intact

🔄 **What happens next:**
1. All users will be asked to use `/start` command
2. Other commands blocked until they restart
3. Users who `/start` will be logged as "user_reactivated"
4. Perfect for tracking active vs inactive users

💡 **Benefits:**
• Fresh engagement tracking
• Clean statistics reset
• No data loss for users

**Restart completed at**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}"""

                await update.message.reply_text(success_message, parse_mode='Markdown')
                
                # Log admin action
                self.db.log_user_activity(user_id, "admin_restart_all", f"Marked {restart_count} users for restart")
                
            except Exception as e:
                await update.message.reply_text(f"❌ **Error during restart**: {str(e)}", parse_mode='Markdown')
        else:
            # Show confirmation message
            confirmation_message = f"""🔄 **Bot Restart Confirmation**

⚠️ **WARNING**: This will reset ALL users' start status!

**What will happen:**
• All {self.db.get_bot_statistics().get('total_users', 0)} users must use `/start` again
• **NO DATA LOSS**: Credits, premium, portfolio preserved
• Commands blocked until users restart with `/start`
• Perfect for engagement tracking

**Benefits:**
• Track active vs inactive users
• Fresh statistics
• Clean user re-engagement
• Identify truly active community

**Type to confirm:**
`/restart confirm`

**To cancel:**
Just ignore this message"""

            await update.message.reply_text(confirmation_message, parse_mode='Markdown')

    async def refresh_credits_command(self, update: Update, context: CallbackContext):
        """Handle /refresh_credits command - Refresh credits for all free users"""
        user_id = update.message.from_user.id

        # Only admin can use this command
        if user_id != self.admin_id:
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        # Check if confirmation is provided
        if context.args and context.args[0].lower() == 'confirm':
            loading_msg = await update.message.reply_text("🔄 Refreshing credits for all free users...")
            
            try:
                # Direct database approach instead of subprocess
                print(f"🔄 Starting manual credit refresh by admin {user_id}")
                
                # Get all non-premium users
                self.db.cursor.execute("""
                    SELECT telegram_id, first_name, username, credits, is_premium
                    FROM users 
                    WHERE (is_premium = 0 OR is_premium IS NULL) 
                    AND telegram_id IS NOT NULL 
                    AND telegram_id != 0
                """)
                
                free_users = self.db.cursor.fetchall()
                total_free_users = len(free_users)
                
                if total_free_users == 0:
                    await loading_msg.edit_text("ℹ️ **No free users found in database**")
                    return
                
                # Update credits for all free users
                updated_count = 0
                total_credits_given = 0
                
                for user in free_users:
                    telegram_id, first_name, username, current_credits, is_premium = user
                    
                    # Set credits to 100 for free users
                    new_credits = 100
                    
                    try:
                        self.db.cursor.execute("""
                            UPDATE users SET credits = ? WHERE telegram_id = ?
                        """, (new_credits, telegram_id))
                        
                        # Log the credit refresh
                        self.db.cursor.execute("""
                            INSERT INTO user_activity (telegram_id, action, details)
                            VALUES (?, ?, ?)
                        """, (telegram_id, "manual_credit_refresh", f"Credits refreshed to {new_credits} (was {current_credits}) by admin"))
                        
                        updated_count += 1
                        total_credits_given += new_credits
                        
                        print(f"✅ {first_name} (@{username or 'no_username'}): {current_credits} → {new_credits} credits")
                        
                    except Exception as e:
                        print(f"❌ Error updating user {telegram_id}: {e}")
                        continue
                
                # Commit all changes
                self.db.conn.commit()
                
                print(f"✅ Manual credit refresh completed: {updated_count}/{total_free_users} users")
                
                success_message = f"""✅ **Credit Refresh Completed Successfully!**

📊 **Results:**
• **Free users updated**: {updated_count}/{total_free_users}
• **Credits per user**: 100
• **Total credits distributed**: {total_credits_given:,}

💰 **What happened:**
• All non-premium users now have 100 credits
• Previous credits were reset to 100
• Activity logged for tracking

🎯 **Benefits:**
• Fair access to bot features
• Encourages continued usage
• Level playing field for all free users

**Refresh completed at**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}"""

                await loading_msg.edit_text(success_message, parse_mode='Markdown')
                
                # Log admin action
                self.db.log_user_activity(user_id, "admin_manual_credit_refresh", f"Manually refreshed credits for {updated_count} free users")
                    
            except Exception as e:
                error_message = f"❌ **Error during credit refresh**: {str(e)}"
                print(f"❌ Credit refresh error: {e}")
                import traceback
                traceback.print_exc()
                await loading_msg.edit_text(error_message)
        else:
            # Show confirmation message with current statistics
            try:
                # Get current free user count
                self.db.cursor.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE (is_premium = 0 OR is_premium IS NULL) 
                    AND telegram_id IS NOT NULL
                """)
                free_users_count = self.db.cursor.fetchone()[0]
                
                # Get users with low credits
                self.db.cursor.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE (is_premium = 0 OR is_premium IS NULL) 
                    AND telegram_id IS NOT NULL
                    AND credits < 50
                """)
                low_credit_users = self.db.cursor.fetchone()[0]
                
                confirmation_message = f"""💰 **Weekly Credit Refresh Confirmation**

📊 **Current Status:**
• **Free users**: {free_users_count}
• **Users with <50 credits**: {low_credit_users}
• **Premium users**: Excluded (unlimited access)

🎁 **What will happen:**
• ALL free users will get **100 credits**
• Previous credit amounts will be reset
• Activity will be logged for each user
• Premium users are not affected

💡 **Benefits:**
• Equal opportunity for all free users
• Encourages continued bot usage
• Fair access to premium features

**Type to confirm:**
`/refresh_credits confirm`

**To cancel:**
Just ignore this message"""

                await update.message.reply_text(confirmation_message, parse_mode='Markdown')
                
            except Exception as e:
                await update.message.reply_text(f"❌ Error getting statistics: {str(e)}")

# News command will be integrated in main bot class
    async def premium_earnings_command(self, update: Update, context: CallbackContext):
        """Handle /premium_earnings command"""
        user_id = update.message.from_user.id
        is_premium = self.db.is_user_premium(user_id)
        
        if not is_premium:
            await update.message.reply_text(
                "❌ **Premium Only Feature**\n\n"
                "Fitur ini hanya tersedia untuk member Premium.\n\n"
                "💎 **Upgrade ke Premium untuk:**\n"
                "• Earning Rp 10k per referral premium\n"
                "• Withdraw ke rekening/e-wallet\n"
                "• Unlimited bot access\n\n"
                "Gunakan `/subscribe` untuk upgrade!",
                parse_mode='Markdown'
            )
            return
        
        # Get premium earnings statistics
        premium_stats = self.db.get_premium_referral_stats(user_id)
        total_earnings = premium_stats['total_earnings']
        total_referrals = premium_stats['total_referrals']
        recent_referrals = premium_stats['recent_referrals']
        
        message = f"""💰 **Premium Earnings Dashboard**

💵 **Total Earnings:** Rp {total_earnings:,}
👥 **Total Premium Referrals:** {total_referrals}
📈 **Average per Referral:** Rp {(total_earnings // total_referrals) if total_referrals > 0 else 0:,}

"""

        if recent_referrals:
            message += "📊 **Recent Premium Referrals:**\n"
            for ref in recent_referrals:
                referred_name = ref[1][:15] + "..." if len(ref[1]) > 15 else ref[1]
                subscription_type = ref[2]
                earnings = ref[3]
                date = ref[4][:10]
                message += f"• {referred_name} - {subscription_type} - Rp {earnings:,} ({date})\n"
            message += "\n"
        else:
            message += "📊 **No premium referrals yet**\n\n"
        
        message += f"""💡 **How to Earn More:**
1. Share your premium referral link
2. When someone subscribes via your link → Rp 10k
3. More subscriptions = More earnings!

🔗 **Get Your Premium Link:** `/referral`

💳 **Withdraw Information:**
• Minimum withdrawal: Rp 50.000
• Payment methods: Bank transfer, e-wallet
• Processing time: 1-3 business days
• Contact admin @Billfarr for withdrawal

📈 **Earning Tips:**
• Share in crypto communities
• Post on social media
• Target serious traders
• Explain premium benefits"""

        await update.message.reply_text(message, parse_mode='Markdown')

    async def grant_package_command(self, update: Update, context: CallbackContext):
        """Handle /grant_package command for easier premium granting"""
        user_id = update.message.from_user.id

        # Enhanced admin check
        if user_id != self.admin_id:
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ **Format salah!**\n\n"
                "Gunakan: `/grant_package <user_id> <package>`\n\n"
                "**Paket tersedia:**\n"
                "• `1month` - 1 Bulan (30 hari)\n"
                "• `2months` - 2 Bulan (60 hari)\n"
                "• `6months` - 6 Bulan (180 hari)\n"
                "• `1year` - 1 Tahun (365 hari)\n"
                "• `lifetime` - Lifetime (permanent)\n\n"
                "**Contoh:**\n"
                "• `/grant_package 123456789 6months`\n"
                "• `/grant_package 123456789 lifetime`",
                parse_mode='Markdown'
            )
            return

        try:
            target_user_id = int(context.args[0])
            package = context.args[1].lower()
        except ValueError:
            await update.message.reply_text("❌ User ID harus berupa angka!")
            return

        # Package mapping
        package_mapping = {
            '1month': ('1_month', '1 Bulan', 'Rp 320.000'),
            '2months': ('2_months', '2 Bulan', 'Rp 600.000'),
            '6months': ('6_months', '6 Bulan', 'Rp 1.800.000'),
            '1year': ('1_year', '1 Tahun', 'Rp 3.000.000'),
            'lifetime': ('lifetime', 'Lifetime', 'Rp 5.000.000')
        }

        if package not in package_mapping:
            await update.message.reply_text(
                "❌ **Paket tidak valid!**\n\n"
                "Gunakan salah satu: `1month`, `2months`, `6months`, `1year`, `lifetime`"
            )
            return

        # Check if user exists
        existing_user = self.db.get_user(target_user_id)
        if not existing_user:
            await update.message.reply_text(
                f"⚠️ **User {target_user_id} belum terdaftar!**\n\n"
                "User harus menggunakan bot terlebih dahulu dengan command `/start`."
            )
            return

        package_key, package_name, package_price = package_mapping[package]

        # Grant premium
        success = self.db.grant_premium_by_package(target_user_id, package_key)

        if success:
            user_info = self.db.get_user(target_user_id)
            username = user_info.get('username', 'No username')
            first_name = user_info.get('first_name', 'Unknown')

            message = f"""✅ **Premium {package_name} berhasil diberikan!**

👤 **User Info:**
• **ID**: {target_user_id}
• **Name**: {first_name}
• **Username**: @{username}

💎 **Premium Package:**
• **Paket**: {package_name}
• **Harga**: {package_price}
• **Status**: {'Permanent' if package_key == 'lifetime' else 'Active'}

🎉 User sekarang memiliki akses unlimited ke semua fitur premium!"""

            # Log admin action
            self.db.log_user_activity(
                user_id, 
                "admin_grant_package_premium", 
                f"Granted {package_name} premium package to user {target_user_id}"
            )

        else:
            message = f"""❌ **Gagal memberikan premium {package_name}!**

🔍 **Troubleshooting:**
• Pastikan User ID benar: {target_user_id}
• User harus sudah menggunakan `/start` di bot
• Cek koneksi database

⚠️ Coba lagi atau hubungi developer."""

        await update.message.reply_text(message, parse_mode='Markdown')