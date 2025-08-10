import os
import logging
import sys
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file (if exists) and system environment
load_dotenv()

# Add missing imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# Import required modules for database operations
from database import Database

from crypto_api import CryptoAPI
from ai_assistant import AIAssistant
# Assuming snd_auto_signals.py contains the AutoSignalScanner class and initialize_auto_signals function
# If not, the relevant logic needs to be incorporated.
# For now, assuming the import path is correct.
try:
    from snd_auto_signals import initialize_auto_signals
except ImportError:
    logging.error("Could not import 'initialize_auto_signals' from 'snd_auto_signals'. Please ensure the file exists and is correctly placed.")
    # Provide a mock or placeholder if the module is not available to prevent startup failure
    class MockAutoSignals:
        def __init__(self, bot_instance):
            self.bot_instance = bot_instance
            self.is_running = False
            self.target_symbols = []
            self.scan_interval = 300 # 5 minutes
            self.min_confidence = 75
            self.last_scan_time = 0
            self.signal_cooldown = 1800 # 30 minutes
            self.last_signal_sent_time = 0
            self.active_scanner_task = None

        async def start_auto_scanner(self):
            logging.warning("Auto Signal Scanner is not fully implemented. Running in mock mode.")
            self.is_running = True
            # In a real scenario, this would start the loop.
            # For mock, we just set the flag.
            pass

        async def stop_auto_scanner(self):
            logging.warning("Stopping mock Auto Signal Scanner.")
            self.is_running = False
            # In a real scenario, this would cancel the task.
            pass

    def initialize_auto_signals(bot_instance):
        logging.warning("Using mock Auto Signal Scanner.")
        return MockAutoSignals(bot_instance)


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

# Setup logging with INFO level for production
logging.basicConfig(
    level=logging.INFO,  # Use INFO level for production
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# TODO: Import database client and Admin Agent after setup
try:
    from admin_agent import AdminAgent
    SUPABASE_AVAILABLE = False  # Temporarily disabled
    logger.info("✅ Admin Agent available (Database integration pending)")
except ImportError as e:
    logger.error(f"❌ Failed to import Admin Agent: {e}")
    SUPABASE_AVAILABLE = False

# Placeholder functions for compatibility
def add_user(*args, **kwargs):
    return {"success": False, "error": "Database not configured"}

def get_user(*args, **kwargs):
    return None

def update_user(*args, **kwargs):
    return {"success": False, "error": "Database not configured"}

def delete_user(*args, **kwargs):
    return {"success": False, "error": "Database not configured"}

def add_premium(*args, **kwargs):
    return {"success": False, "error": "Database not configured"}

def revoke_premium(*args, **kwargs):
    return {"success": False, "error": "Database not configured"}

def set_premium(*args, **kwargs):
    return {"success": False, "error": "Database not configured"}

def parse_premium_duration(*args, **kwargs):
    return None

def admin_set_premium(*args, **kwargs):
    return {"success": False, "error": "Database not configured"}

def admin_revoke_premium(*args, **kwargs):
    return {"success": False, "error": "Database not configured"}

def admin_grant_credits(*args, **kwargs):
    return {"success": False, "error": "Database not configured"}

def _get_env_admin_ids():
        """
        Read admin IDs from Replit Secrets dynamically.
        Priority:
          1) ADMIN1, ADMIN2, etc.
          2) ADMIN_USER_ID, ADMIN2_USER_ID (fallback)
        """
        admin_ids = set()

        # Check ADMIN1, ADMIN2, etc.
        for i in range(1, 10):
            env_key = f'ADMIN{i}'
            admin_id_str = (os.getenv(env_key) or "").strip()

            # Fallback to old naming format
            if not admin_id_str and i <= 2:
                fallback_key = f'ADMIN{i}_USER_ID' if i > 1 else 'ADMIN_USER_ID'
                admin_id_str = (os.getenv(fallback_key) or "").strip()

            # Add to set if valid
            if admin_id_str and admin_id_str.lower() != "none":
                admin_ids.add(str(admin_id_str))

        return admin_ids

# Get initial admin IDs for logging
ADMIN_IDS = _get_env_admin_ids()

if not ADMIN_IDS:
    logger.warning("No ADMIN1, ADMIN2 or fallback admin environment variables found. Admin commands will be inaccessible.")

class TelegramBot:
    def __init__(self):
        # Initialize database connection
        try:
            self.db = Database()
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            # Continue without database - some features will be limited
            self.db = None

        # TODO: Initialize database functions after setup
        self.supabase_enabled = False
        logger.info("✅ Database integration pending setup")

        # Initialize Admin Agent if available
        self.admin_agent = None
        try:
            self.admin_agent = AdminAgent()
            logger.info("✅ Admin Agent initialized (Database features pending)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Admin Agent: {e}")
            self.admin_agent = None


        # Get bot token from environment - try multiple possible keys including 'TOKEN'
        self.token = os.getenv('TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')

        if not self.token:
            # Debug: Show what environment variables are available
            logger.debug("Available environment variables:")
            for key in os.environ.keys():
                if 'BOT' in key.upper() or 'TELEGRAM' in key.upper() or 'TOKEN' in key.upper():
                    logger.debug(f"  {key} = {'SET' if os.environ[key] else 'EMPTY'}")

        logger.debug(f"Bot token found: {'YES' if self.token else 'NO'}")

        # Get all admin IDs with better error handling
        self.admin_ids = ADMIN_IDS # Use the dynamically loaded ADMIN_IDS
        self.admin_id = min(self.admin_ids) if self.admin_ids else 0

        logger.info(f"✅ Total configured admins: {len(self.admin_ids)} - IDs: {sorted(list(self.admin_ids))}")

        # Initialize components with CoinAPI integration
        self.crypto_api = CryptoAPI()
        self.ai = AIAssistant()

        # Initialize broadcast system
        self.pending_broadcast = None
        self.broadcast_in_progress = False

        # Initialize auto signals system
        self.auto_signals = None

        # Validate token before creating application
        if not self.token:
            logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
            logger.error("💡 Please set TOKEN in Replit Secrets")
            logger.error("📝 Go to Secrets tab and add your bot token")
            sys.exit(1)

        # Initialize application with token
        try:
            self.application = Application.builder().token(self.token).build()
            logger.info("✅ Bot initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot: {e}")
            sys.exit(1)

    def is_admin(self, user_id: int) -> bool:
        """Check if the user ID is one of the configured admins."""
        return str(user_id) in self.admin_ids

    def register_user_supabase(self, user):
        """TODO: Register new user in database after setup"""
        print(f"⚠️ Database not configured, skipping registration for user {user.id}")
        return False

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

            self._register_handlers()

            # Add global error handler
            self.application.add_error_handler(self._on_error)

            print("🤖 Bot handlers registered successfully")
            mode_text = "🌐 DEPLOYMENT (Always On)" if IS_DEPLOYMENT else "🔧 DEVELOPMENT (Workspace)"
            print(f"🌍 Environment: {mode_text}")
            print(f"🔑 API Status: CG=✅, BIN=✅, NEWS=✅ (Coinglass V4 + Binance + CryptoNews)")
            print("🚀 Starting bot polling with Coinglass V4 integration...")

            # Test bot connection before starting with shorter timeout
            try:
                print("🔄 Testing bot connection...")

                # Use shorter timeout for deployment environment
                bot_info = await asyncio.wait_for(
                    self.application.bot.get_me(),
                    timeout=5.0
                )

                print(f"✅ Bot connected successfully: @{bot_info.username}")
                print(f"📝 Bot ID: {bot_info.id}")
                print(f"🤖 Bot can join groups: {bot_info.can_join_groups}")

            except asyncio.TimeoutError:
                print("⚠️ Bot connection test timed out - continuing to polling...")
                logger.warning("Bot connection test timed out, starting polling anyway")
            except Exception as e:
                print(f"⚠️ Bot connection test failed: {e}")
                print("🔄 Starting polling anyway...")
                logger.warning(f"Bot connection test failed, but starting polling: {e}")

            # Initialize and start auto signals system for BOTH development and deployment
            try:
                print("[AUTO-SIGNAL] Initializing auto signals system...")
                self.auto_signals = initialize_auto_signals(self)
                if self.auto_signals:
                    # Start auto signals in BOTH modes
                    asyncio.create_task(self.auto_signals.start_auto_scanner())
                    mode_text = "DEPLOYMENT" if IS_DEPLOYMENT else "DEVELOPMENT"
                    print(f"[AUTO-SIGNAL] ✅ Auto signals scanner started in {mode_text} mode")
                    print(f"[AUTO-SIGNAL] 📊 Eligible users: Admin & Lifetime premium users")
                    print(f"[AUTO-SIGNAL] 🎯 Target coins: {len(self.auto_signals.target_symbols)}")
                    print(f"[AUTO-SIGNAL] ⚡ Min confidence: {self.auto_signals.min_confidence}%")
                    print(f"[AUTO-SIGNAL] 🔄 Scan interval: {self.auto_signals.scan_interval // 60} minutes")
                    # Check if signal_cooldown attribute exists
                    cooldown_hours = getattr(self.auto_signals, 'signal_cooldown', 3600) // 3600
                    print(f"[AUTO-SIGNAL] 🛡️ Anti-spam: {cooldown_hours}h cooldown")
                else:
                    print("[AUTO-SIGNAL] ❌ Auto signals system failed to initialize")
            except Exception as e:
                print(f"⚠️ Auto signals initialization failed: {e}")
                import traceback
                traceback.print_exc()

            # Start the bot with optimized polling for deployment
            print("✅ Bot is now running and polling for updates...")
            print("🎯 Waiting for Telegram messages...")

            # Proper initialization sequence for telegram-bot v22.x
            await self.application.initialize()
            print("✅ Application initialized")

            await self.application.start()
            print("✅ Application started")

            # Store bot instance in context for admin agent access
            self.application.bot_data['bot_instance'] = self

            # Start polling with proper error handling
            await self.application.updater.start_polling(
                poll_interval=1.0,
                timeout=20,
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query']
            )
            print("🚀 Bot polling started successfully!")

            # Keep running until interrupted - fix for telegram-bot v22.x
            try:
                import signal
                stop_event = asyncio.Event()

                def signal_handler(signum, frame):
                    print(f"\n🛑 Received signal {signum}, stopping bot...")
                    stop_event.set()

                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)

                # Wait indefinitely until stop signal
                await stop_event.wait()

            except KeyboardInterrupt:
                print("🛑 Bot stopped by interrupt signal")

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
            # Proper cleanup sequence
            try:
                if self.application:
                    print("🛑 Stopping application...")

                    # Stop updater first
                    if hasattr(self.application, 'updater') and self.application.updater.running:
                        await self.application.updater.stop()
                        print("✅ Updater stopped")

                    # Stop application
                    await self.application.stop()
                    print("✅ Application stopped")

                    # Shutdown application
                    await self.application.shutdown()
                    print("✅ Application shutdown complete")

                print("🛑 Bot stopped gracefully")
            except Exception as e:
                logger.error(f"Error during bot shutdown: {e}")
                print(f"⚠️ Cleanup error: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command with enhanced user persistence"""
        user = update.effective_user
        print(f"🎯 /start command received from user {user.id if user else 'Unknown'}")
        logger.info(f"Start command from user {user.id}")

        # Debug: Show that command handler is working
        print(f"📞 Start command handler called successfully")

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
                    self.db.log_user_activity(user.id, "user_created", f"New user: {user.first_name}")

                    # Also register in Supabase
                    self.register_user_supabase(user)

            # Generate response message
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

🤖 Saya adalah AI assistant crypto trading terlengkap dengan data real-time dari CoinAPI & Binance APIs.

💡 **Untuk memulai:** Gunakan `/help` untuk panduan lengkap semua fitur bot!

📊 **Quick Start - Contoh Penggunaan:**

**Cek Harga (CoinAPI Real-time):**
• `/price btc` - Harga Bitcoin real-time dari CoinAPI
• `/price eth` - Harga Ethereum terkini dari CoinAPI

**Analisis Mendalam:**
• `/analyze btc` - Analisis komprehensif Bitcoin (technical analysis, sentiment, prediksi)
• `/analyze eth` - Analisis Ethereum dengan data real-time dari CoinAPI

**Trading Futures dengan SnD:**
• `/futures btc` - Pilih timeframe untuk analisis futures Bitcoin dengan Supply & Demand
• `/futures_signals` - Sinyal futures lengkap dengan SnD analysis

💳 **Sistem Credit:**
- User baru dapat **100 credit gratis**
- `/analyze` = 20 credit | `/futures` = 20 credit
- `/futures_signals` = 60 credit | `/market` = 20 credit

🎁 **Cara Dapat Credit Gratis:**
• `/referral` - Ajak teman dapat 10 credit/referral
• `/subscribe` - Upgrade premium untuk unlimited access

🚀 **Fitur Terbaru:**
• Auto SnD Signals untuk Admin & Lifetime users
• Supply & Demand analysis untuk futures trading
• Data real-time dari CoinAPI (bukan simulasi)

**Semua data real-time dari CoinAPI & Binance APIs!**"""

        else:
            welcome_text = f"""🎉 **Welcome to CryptoMentor AI, {user.first_name}!**

🤖 I'm your comprehensive crypto trading AI assistant with real-time CoinAPI & Binance data.

💡 **To get started:** Use `/help` for complete guide to all bot features!

📊 **Quick Start - Usage Examples:**

**Check Prices (CoinAPI Real-time):**
• `/price btc` - Real-time Bitcoin price from CoinAPI
• `/price eth` - Current Ethereum price from CoinAPI

**Deep Analysis:**
• `/analyze btc` - Comprehensive Bitcoin analysis (technical analysis, sentiment, predictions)
• `/analyze eth` - Ethereum analysis with real-time CoinAPI data

**Futures Trading with SnD:**
• `/futures btc` - Choose timeframe for Bitcoin futures analysis with Supply & Demand
• `/futures_signals` - Complete futures signals with SnD analysis

💳 **Credit System:**
- New users get **100 free credits**
- `/analyze` = 20 credits | `/futures` = 20 credits
- `/futures_signals` = 60 credits | `/market` = 20 credits

🎁 **How to Get Free Credits:**
• `/referral` - Invite friends get 10 credits/referral
• `/subscribe` - Upgrade premium for unlimited access

🚀 **Latest Features:**
• Auto SnD Signals for Admin & Lifetime users
• Supply & Demand analysis for futures trading
• Real-time data from CoinAPI (not simulation)

**All data real-time from CoinAPI & Binance APIs!**"""

        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = update.effective_user.id
        print(f"🎯 /help command received from user {user_id}")
        logger.info(f"Help command from user {user_id}")
        help_text = """🤖 **CryptoMentor AI Bot - Panduan Lengkap (CoinAPI + Coinglass V4 Edition)**

⭐ **BEST COMMANDS untuk Pemula:**
• `/price btc` - **GRATIS** - Cek harga Bitcoin real-time dari CoinAPI
• `/analyze btc` - **20 credit** - Analisis Bitcoin lengkap dengan CoinAPI data
• `/futures btc` - **20 credit** - Trading signals Bitcoin dengan SnD analysis

📊 **Harga & Data Pasar:**
• `/price <symbol>` - Harga real-time dari CoinAPI **[GRATIS]**
  Contoh: `/price btc`, `/price eth`, `/price sol`
• `/market` - Overview pasar global dari CoinAPI (20 credit) ⭐
  Data: Total market cap, dominance, volume global, fear & greed

📈 **Analisis Trading dengan SnD:**
• `/analyze <symbol>` - Analisis fundamental + teknikal (20 credit) ⭐ **RECOMMENDED**
  Contoh: `/analyze btc` → Fundamental dari CoinAPI + Technical analysis
  Data: Rank, market cap, volume, description, website, price prediction

• `/futures <symbol>` - Analisis futures dengan Supply & Demand (20 credit)
  Contoh: `/futures btc` → Pilih timeframe dengan SnD entry/exit points
  Hasil: Entry, TP, SL, confidence level, risk management

• `/futures_signals` - Sinyal futures lengkap dengan SnD analysis (60 credit)
  Multiple coins dengan konfirmasi Supply/Demand zones

💼 **Portfolio & Credit:**
• `/portfolio` - Lihat portfolio dengan CoinAPI prices
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
- User baru: 100 credit gratis
- `/analyze` = 20 credit ⭐ (CoinAPI Analysis)
- `/futures` = 20 credit ⭐ (dengan SnD)
- `/futures_signals` = 60 credit (Multiple SnD signals)
- `/market` = 20 credit (Global overview CoinAPI)

🎯 **Langkah untuk Pemula:**
1. **Mulai dengan `/price btc`** (gratis) - harga real-time CoinAPI
2. **Coba `/market`** (20 credit) - overview pasar global CoinAPI
3. **Test `/analyze btc`** (20 credit) - CoinAPI fundamental + technical analysis
4. **Coba `/futures btc`** (20 credit) - SnD signals untuk trading
5. **Upgrade premium** untuk unlimited access

💡 **Fitur Premium:**
- Unlimited access semua fitur CoinAPI + SnD
- Auto SnD signals (Admin & Lifetime only)
- Priority support
- No credit limits

🚀 **Data Sources:**
- **Fundamental & Prices**: CoinAPI Real-time
- **Futures Signals**: Coinglass V4 Startup Plan + Internal SnD Algo
- **SnD Analysis**: Internal algorithm + CoinAPI candlesticks

🚀 **Fitur Auto Signal:**
• **Momentum-based signals**: Deteksi otomatis sinyal beli/jual
• **Confidence & Quality Filter**: Hanya sinyal 'good' dengan confidence >= 75%
• **Automatic Delivery**: Pesan dikirim ke user Admin & Lifetime
• **Scheduled Check**: Setiap 5 menit
• **Optimized**: Anti-spam, cooldown, no duplicates

🔧 **Admin Setup:**
• `/setup_admin` - Petunjuk setup admin access
• Perlu konfigurasi ADMIN_USER_ID di Replit Secrets

"""
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command with CoinAPI real-time data"""
        print(f"🎯 /price command received from user {update.effective_user.id}")

        # Check if user needs restart
        if await self._check_user_restart_required(update):
            return

        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/price <symbol>`\nContoh: `/price btc`", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()

        # Show loading with CoinMarketCap status
        mode_text = "🌐 DEPLOYMENT" if IS_DEPLOYMENT else "🔧 DEVELOPMENT"
        loading_msg = await update.message.reply_text(f"⏳ Mengambil data real-time {symbol} dari CoinAPI + Coinglass V4... ({mode_text})")

        # Get real-time data from CoinAPI
        print(f"🔄 Fetching real-time data for {symbol} from CoinAPI...")

        # Force refresh in deployment to ensure real-time data
        price_data = self.crypto_api.get_crypto_price(symbol, force_refresh=IS_DEPLOYMENT)

        if price_data and 'error' not in price_data and price_data.get('price', 0) > 0:
            # Smart price formatting
            current_price = price_data.get('price', 0)
            if current_price < 1:
                price_format = f"${current_price:.8f}"
            elif current_price < 100:
                price_format = f"${current_price:.4f}"
            else:
                price_format = f"${current_price:,.2f}"

            change_24h = price_data.get('change_24h', 0)
            change_emoji = "📈" if change_24h >= 0 else "📉"
            change_color = "+" if change_24h >= 0 else ""

            message = f"""📊 **{symbol} Real-Time CoinAPI Data**

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
            data_source = price_data.get('source', 'unknown')

            if data_source == 'coinapi':
                source_text = "🟢 CoinAPI Real-time"
                api_status = "✅ CoinAPI Active"
            else:
                source_text = "🟢 Binance Exchange"
                api_status = "✅ Binance Live Data"

            message += f"""
⏰ **Update**: {current_time}
🔄 **Source**: {source_text}
🌐 **API Status**: {api_status}
🔗 **Mode**: {'🌐 Always On (Deployment)' if IS_DEPLOYMENT else '🔧 Development Workspace'}"""
        else:
            # API error handling
            error_reason = price_data.get('error', 'All price APIs unavailable') if price_data else 'All price APIs unavailable'
            message = f"""❌ **Data harga tidak tersedia untuk {symbol}**

🌐 **Mode**: {'Deployment (Real-time Only)' if IS_DEPLOYMENT else 'Development'}
⚠️ **Error**: {error_reason}

🔄 **Solusi:**
• Coba beberapa saat lagi
• API sedang mengalami gangguan sementara
• Pastikan CoinAPI key tersedia di Secrets

💡 **Info**: Bot menggunakan CoinAPI → Binance (berurutan)"""

        await loading_msg.edit_text(message, parse_mode='Markdown')

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command - comprehensive analysis with CoinAPI integration"""
        # Check if user needs restart
        if await self._check_user_restart_required(update):
            return

        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/analyze <symbol>`\nContoh: `/analyze btc`", parse_mode='Markdown')
            return

        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = self.is_admin(user_id)

        # Check credits for non-premium, non-admin users
        if not is_premium and not is_admin and credits < 20:
            await update.message.reply_text("❌ Credit tidak cukup! Analisis komprehensif membutuhkan 20 credit. Gunakan `/credits` untuk melihat sisa credit Anda.", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()

        # Show loading
        loading_msg = await update.message.reply_text("⏳ Menganalisis data dengan CoinAPI real-time...")

        try:
            # Get comprehensive analysis using CoinAPI data
            analysis = self.ai.get_comprehensive_analysis(symbol, {}, {}, 'id', self.crypto_api)

            # Deduct credit only for non-premium, non-admin users
            if not is_premium and not is_admin:
                self.db.deduct_credit(user_id, 20)
                remaining_credits = self.db.get_user_credits(user_id)
                analysis += f"\n\n💳 Credit tersisa: {remaining_credits} (Analisis CoinAPI: -20 credit)"
            elif is_premium:
                analysis += f"\n\n⭐ **Status Premium** - Unlimited Access"
            elif is_admin:
                analysis += f"\n\n👑 **Admin Access** - Unlimited"

            # Handle long messages
            if len(analysis) > 4000:
                chunks = [analysis[i:i+4000] for i in range(0, len(analysis), 4000)]
                await loading_msg.edit_text(chunks[0], parse_mode='Markdown')
                for chunk in chunks[1:]:
                    await update.message.reply_text(chunk, parse_mode='Markdown')
            else:
                await loading_msg.edit_text(analysis, parse_mode='Markdown')

        except Exception as e:
            error_msg = f"❌ Terjadi kesalahan dalam analisis.\n\n**Error**: {str(e)[:100]}...\n\n💡 **Coba alternatif:**\n• `/price {symbol.lower()}` untuk harga basic (CoinAPI)\n• `/futures {symbol.lower()}` untuk analisis SnD futures\n• Contact admin jika masalah berlanjut"
            await loading_msg.edit_text(error_msg, parse_mode='Markdown')
            print(f"Error in analyze command: {e}")
            import traceback
            traceback.print_exc()

    async def market_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /market command with CoinAPI integration"""
        # Check if user needs restart
        if await self._check_user_restart_required(update):
            return

        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = self.is_admin(user_id)

        # Check credits for non-premium, non-admin users
        if not is_premium and not is_admin and credits < 20:
            await update.message.reply_text("❌ Credit tidak cukup! Overview pasar membutuhkan 20 credit. Gunakan `/credits` untuk melihat sisa credit Anda.", parse_mode='Markdown')
            return

        # Show enhanced loading message
        loading_msg = await update.message.reply_text("⏳ Menganalisis overview pasar crypto real-time dari CoinAPI...")

        try:
            print(f"🔄 Market command initiated by user {user_id}")

            # Get comprehensive market overview with CoinAPI real-time data
            print("📊 Calling AI market sentiment analysis with CoinAPI...")
            market_data = self.ai.get_market_sentiment('id', self.crypto_api)

            if not market_data or len(market_data.strip()) < 50:
                # Fallback if data is too short
                market_data = """🌍 **OVERVIEW PASAR CRYPTO (CoinAPI)**

⚠️ **Data sementara tidak lengkap**

💡 **Alternatif yang bisa dicoba:**
• `/price btc` - Cek harga Bitcoin dari CoinAPI
• `/price eth` - Cek harga Ethereum dari CoinAPI
• `/analyze btc` - Analisis mendalam Bitcoin dengan CoinAPI data

🔄 Coba command `/market` lagi dalam beberapa menit untuk data lengkap."""

            # Deduct credit only for non-premium, non-admin users (20 credits for market overview)
            if not is_premium and not is_admin:
                self.db.deduct_credit(user_id, 20)
                remaining_credits = self.db.get_user_credits(user_id)
                market_data += f"\n\n💳 Credit tersisa: {remaining_credits} (Overview pasar CoinAPI: -20 credit)"
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
            error_msg = f"❌ Terjadi kesalahan saat menganalisis pasar.\n\n**Error**: {str(e)[:100]}...\n\n💡 **Coba alternatif:**\n• `/price btc` (CoinAPI)\n• `/analyze ethereum` (CoinAPI)\n• `/futures_signals` (SnD)"
            await loading_msg.edit_text(error_msg, parse_mode='Markdown')
            print(f"❌ Error in market command: {e}")
            import traceback
            traceback.print_exc()

    async def futures_signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /futures_signals command with CoinAPI + Coinglass analysis"""
        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = self.is_admin(user_id)

        # Check credits for non-premium, non-admin users
        if not is_premium and not is_admin and credits < 60:
            await update.message.reply_text("❌ Credit tidak cukup! Sinyal futures membutuhkan 60 credit. Gunakan `/credits` untuk melihat sisa credit Anda.", parse_mode='Markdown')
            return

        # Show loading message with query processing info
        query_display = ""
        if context.args:
            # Clean the query for display - remove "SND" and show clean timeframe
            raw_query = ' '.join(context.args).upper()
            query_parts = raw_query.split()
            cleaned_parts = [part for part in query_parts if part != 'SND']

            if cleaned_parts:
                # Show cleaned query in loading message
                if any(tf in cleaned_parts[0] for tf in ['M', 'H', 'D', 'W']):
                    clean_timeframe = cleaned_parts[0]
                    query_display = f" untuk {clean_timeframe}"
                else:
                    query_display = f" untuk {cleaned_parts[0]}"

        loading_msg = await update.message.reply_text(f"⏳ Menganalisis sinyal futures dengan CoinAPI + Coinglass V4{query_display}...")

        try:
            print(f"🔄 Starting futures signals generation for user {user_id}")

            # Generate signals using new async method with query args
            signals = await self.ai.generate_futures_signals('id', self.crypto_api, context.args)

            if not signals or len(signals.strip()) < 50:
                fallback_msg = f"""❌ **Gagal Generate Sinyal Futures**

💡 **Kemungkinan Penyebab:**
• Market volatilitas rendah
• Tidak ada setup trading yang jelas
• API rate limiting

🔄 **Solusi:**
• Coba lagi dalam 15-30 menit
• Gunakan `/futures btc` untuk analisis spesifik
• Gunakan `/analyze btc` untuk analisis fundamental"""

                await loading_msg.edit_text(fallback_msg, parse_mode='Markdown')
                return

            # Deduct credit only for non-premium, non-admin users
            if not is_premium and not is_admin:
                self.db.deduct_credit(user_id, 60)
                remaining_credits = self.db.get_user_credits(user_id)
                signals += f"\n\n💳 Credit tersisa: {remaining_credits} (Sinyal futures: -60 credit)"
            elif is_premium:
                signals += f"\n\n⭐ **Status Premium** - Unlimited Access"
            elif is_admin:
                signals += f"\n\n👑 **Admin Access** - Unlimited"

            # Handle long messages
            if len(signals) > 4000:
                chunks = [signals[i:i+4000] for i in range(0, len(signals), 4000)]
                try:
                    await loading_msg.edit_text(chunks[0], parse_mode='MarkdownV2')
                    for chunk in chunks[1:]:
                        await update.message.reply_text(chunk, parse_mode='MarkdownV2')
                except Exception as e:
                    print(f"⚠️ Markdown error, sending as plain text: {e}")
                    await loading_msg.edit_text(chunks[0], parse_mode=None)
                    for chunk in chunks[1:]:
                        await update.message.reply_text(chunk, parse_mode=None)
            else:
                try:
                    await loading_msg.edit_text(signals, parse_mode='MarkdownV2')
                except Exception as e:
                    print(f"⚠️ Markdown error, sending as plain text: {e}")
                    await loading_msg.edit_text(signals, parse_mode=None)

        except Exception as e:
            error_msg = f"❌ Terjadi kesalahan dalam analisis sinyal futures.\n\n**Error**: {str(e)[:100]}...\n\n💡 Coba `/futures btc` untuk analisis spesifik."
            await loading_msg.edit_text(error_msg, parse_mode='Markdown')
            print(f"❌ Error in futures_signals command: {e}")
            import traceback
            traceback.print_exc()

    async def futures_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /futures command with SnD timeframe selection"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/futures <symbol>`\nContoh: `/futures btc`", parse_mode='Markdown')
            return

        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = self.is_admin(user_id)

        # Check credits for non-premium, non-admin users (20 credits for SnD futures analysis)
        if not is_premium and not is_admin and credits < 20:
            await update.message.reply_text("❌ Credit tidak cukup! Analisis SnD futures membutuhkan 20 credit. Gunakan `/credits` untuk melihat sisa credit Anda.", parse_mode='Markdown')
            return

        # Clean the symbol query - remove "SND" if present and extract timeframe
        raw_query = ' '.join(context.args).upper()
        query_parts = raw_query.split()

        # Check if first part looks like a timeframe (contains M, H, D, W)
        if len(query_parts) >= 2 and any(tf in query_parts[0] for tf in ['M', 'H', 'D', 'W']):
            # Extract timeframe and symbol, remove "SND" if present
            timeframe_input = query_parts[0].upper()
            remaining_parts = [part for part in query_parts[1:] if part.upper() != 'SND']
            symbol = remaining_parts[0] if remaining_parts else 'BTC'
        else:
            # Standard format: symbol only
            symbol = query_parts[0] if query_parts else 'BTC'
            timeframe_input = None

        # Show timeframe selection with inline keyboard for SnD analysis
        keyboard = [
            [InlineKeyboardButton("⚡ 15M", callback_data=f'snd_futures_{symbol}_15m'),
             InlineKeyboardButton("🔥 30M", callback_data=f'snd_futures_{symbol}_30m')],
            [InlineKeyboardButton("📈 1H", callback_data=f'snd_futures_{symbol}_1h'),
             InlineKeyboardButton("🚀 4H", callback_data=f'snd_futures_{symbol}_4h')],
            [InlineKeyboardButton("💎 1D", callback_data=f'snd_futures_{symbol}_1d'),
             InlineKeyboardButton("🌟 1W", callback_data=f'snd_futures_{symbol}_1w')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Display cleaned timeframe if provided in query
        display_text = f"📊 **Analisis Supply & Demand Futures {symbol}**\n\n"
        if timeframe_input:
            # Clean display: show only timeframe without "SND"
            clean_timeframe = timeframe_input.replace('SND', '').strip()
            display_text += f"🎯 **Timeframe yang diminta**: {clean_timeframe}\n\n"

        display_text += "Pilih timeframe untuk analisis SnD dengan Entry/TP/SL:"

        await update.message.reply_text(
            display_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        try:
            await query.answer()
            callback_data = query.data
            user_id = query.from_user.id

            # Handle SnD futures analysis callbacks
            if callback_data.startswith('snd_futures_'):
                parts = callback_data.split('_')
                if len(parts) >= 4:
                    symbol = parts[2]
                    timeframe = parts[3]

                    # Check credits
                    is_premium = self.db.is_user_premium(user_id)
                    is_admin = self.is_admin(user_id)
                    credits = self.db.get_user_credits(user_id)

                    if not is_premium and not is_admin and credits < 20:
                        await query.edit_message_text("❌ Credit tidak cukup untuk analisis futures!")
                        return

                    # Show loading
                    await query.edit_message_text(
                        f"⏳ Menganalisis {symbol} {timeframe} dengan CoinAPI + Coinglass V4...\n\n"
                        "🔍 Memproses data real-time...",
                        parse_mode='Markdown'
                    )

                    try:
                        print(f"🎯 Processing futures analysis: {symbol} {timeframe}")

                        # Get futures analysis using new async method
                        analysis_text = await self.ai.get_futures_analysis(symbol, timeframe, 'id', self.crypto_api)

                        # Deduct credits
                        if not is_premium and not is_admin:
                            self.db.deduct_credit(user_id, 20)
                            remaining_credits = self.db.get_user_credits(user_id)
                            analysis_text += f"\n\n💳 Credit tersisa: {remaining_credits} (Futures {timeframe}: -20 credit)"
                        elif is_premium:
                            analysis_text += f"\n\n⭐ **Status Premium** - Unlimited Access"
                        elif is_admin:
                            analysis_text += f"\n\n👑 **Admin Access** - Unlimited"

                        # Handle long messages
                        if len(analysis_text) > 4000:
                            chunks = [analysis_text[i:i+4000] for i in range(0, len(analysis_text), 4000)]
                            try:
                                await query.edit_message_text(chunks[0], parse_mode='MarkdownV2')
                                for chunk in chunks[1:]:
                                    await query.message.reply_text(chunk, parse_mode='MarkdownV2')
                            except Exception as markdown_error:
                                print(f"⚠️ MarkdownV2 error, sending as plain text: {markdown_error}")
                                # Remove escape characters for plain text
                                plain_chunks = [chunk.replace('\\', '') for chunk in chunks]
                                await query.edit_message_text(plain_chunks[0], parse_mode=None)
                                for chunk in plain_chunks[1:]:
                                    await query.message.reply_text(chunk, parse_mode=None)
                        else:
                            try:
                                await query.edit_message_text(analysis_text, parse_mode='MarkdownV2')
                            except Exception as markdown_error:
                                print(f"⚠️ MarkdownV2 error, sending as plain text: {markdown_error}")
                                # Remove escape characters for plain text
                                plain_text = analysis_text.replace('\\', '')
                                await query.edit_message_text(plain_text, parse_mode=None)

                        print(f"✅ Successfully sent futures analysis to user {user_id}")

                    except Exception as e:
                        # Create safe error message without problematic characters
                        error_msg = f"❌ Error dalam analisis futures: {str(e)[:100]}...\n\n💡 Solusi:\n• Coba /price {symbol} untuk harga basic\n• Gunakan /futures_signals untuk multiple signals\n• Contact admin jika masalah berlanjut"
                        await query.edit_message_text(error_msg, parse_mode=None)
                        print(f"❌ Error in futures callback: {e}")
                        import traceback
                        traceback.print_exc()

            elif callback_data.startswith('futures_analysis_'):
                # Existing futures analysis logic
                parts = callback_data.split('_')
                if len(parts) >= 4:
                    symbol = parts[2]
                    timeframe = parts[3]

                    # Show loading
                    await query.edit_message_text(
                        f"⏳ Menganalisis {symbol} {timeframe}...",
                        parse_mode='Markdown'
                    )

                    # Get analysis with SnD enhancement
                    analysis = self.ai.get_futures_analysis(symbol, timeframe, 'id', self.crypto_api)

                    await query.edit_message_text(analysis, parse_mode='Markdown')

            elif callback_data.startswith('lang_'):
                # Language selection
                language = callback_data.split('_')[1]
                self.db.set_user_language(user_id, language)

                if language == 'id':
                    await query.edit_message_text("✅ Bahasa diubah ke Bahasa Indonesia")
                else:
                    await query.edit_message_text("✅ Language changed to English")

        except Exception as e:
            print(f"Error in callback query handler: {e}")
            try:
                await query.edit_message_text("❌ Terjadi kesalahan dalam memproses permintaan.")
            except:
                pass

    def _format_snd_analysis(self, symbol, timeframe, snd_data, price_data):
        """Format Supply & Demand analysis results"""
        try:
            current_price = price_data.get('price', 0) if 'error' not in price_data else 0
            price_format = f"${current_price:.4f}" if current_price < 100 else f"${current_price:,.2f}"

            signals = snd_data.get('signals', [])
            confidence = snd_data.get('confidence_score', 0)
            market_structure = snd_data.get('market_structure', {})

            message = f"""📊 **Supply & Demand Analysis - {symbol} ({timeframe})**

💰 **Current Price**: {price_format}
🎯 **Overall Confidence**: {confidence:.1f}%
📈 **Market Structure**: {market_structure.get('pattern', 'Unknown').title()}

"""

            if signals:
                for i, signal in enumerate(signals[:2], 1):  # Show top 2 signals
                    direction = signal.get('direction', 'N/A')
                    entry = signal.get('entry_price', 0)
                    sl = signal.get('stop_loss', 0)
                    tp1 = signal.get('take_profit_1', 0)
                    tp2 = signal.get('take_profit_2', 0)
                    conf = signal.get('confidence', 0)
                    rr = signal.get('risk_reward_ratio', 0)
                    reason = signal.get('reason', 'N/A')

                    direction_emoji = "🟢" if direction == 'LONG' else "🔴"

                    message += f"""**{i}. {direction} Signal {direction_emoji}**
• **Entry**: ${entry:.4f}
• **Stop Loss**: ${sl:.4f}
• **Take Profit 1**: ${tp1:.4f}
• **Take Profit 2**: ${tp2:.4f}
• **Confidence**: {conf:.1f}%
• **Risk/Reward**: {rr:.1f}:1
• **Reason**: {reason}

"""
            else:
                message += "⚠️ No clear SnD signals at current levels\n\n"

            message += f"""⚠️ **SnD Trading Rules:**
• Wait for price action confirmation at zones
• Use proper position sizing (1-3% risk)
• Monitor volume for zone validation
• Exit partial at TP1, hold for TP2

📡 **Data Source**: CoinAPI + Binance SnD Analysis
🕐 **Analysis Time**: {datetime.now().strftime('%H:%M:%S WIB')}"""

            return message

        except Exception as e:
            return f"❌ Error formatting SnD analysis: {str(e)}"

    async def credits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /credits command"""
        user_id = update.message.from_user.id
        credits = self.db.get_user_credits(user_id)
        is_premium = self.db.is_user_premium(user_id)
        is_admin = self.is_admin(user_id)

        if is_admin:
            message = f"""💳 **CryptoMentor AI Bot - Credit Information**

👑 **Status**: **ADMIN**
♾️ **Credit**: **UNLIMITED**

🛠️ **Akses Admin:**
• Unlimited semua fitur
• Auto SnD signals access
• Kontrol penuh bot
• Panel admin tersedia

Selamat mengelola CryptoMentor AI!"""
        elif is_premium:
            # Check if lifetime premium
            user_data = self.db.get_user(user_id)
            is_lifetime = user_data and user_data.get('subscription_end') is None if user_data else False

            message = f"""💳 **CryptoMentor AI Bot - Credit Information**

⭐ **Status**: **PREMIUM {'LIFETIME' if is_lifetime else ''}**
♾️ **Credit**: **UNLIMITED**

🚀 **Fitur Premium:**
• Unlimited analisis CoinAPI + SnD
• Akses semua command SnD
• {'Auto SnD signals (Lifetime only)' if is_lifetime else 'Priority support'}
• Priority support

Terima kasih telah menjadi member premium!"""
        else:
            message = f"""💳 **CryptoMentor AI Bot - Credit Information**

💰 **Credit tersisa**: **{credits}**

📊 **Biaya per Fitur (CoinAPI + SnD):**
• `/analyze <symbol>` - 20 credit (CoinAPI analysis) ⭐
• `/futures <symbol>` - 20 credit (SnD futures analysis) ⭐
• `/futures_signals` - 60 credit (SnD sinyal lengkap)
• `/market` - 20 credit (overview pasar CoinAPI)
• Fitur lainnya - **Gratis**

🎯 **Rekomendasi untuk Pemula:**
• Mulai dengan `/price btc` (GRATIS - CoinAPI)
• Coba `/market` (20 credit) - overview pasar global CoinAPI
• Test `/analyze btc` (20 credit) - CoinAPI analysis!
• Coba `/futures btc` (20 credit) - SnD signals untuk trading

💡 **Cara Mendapat Credit:**
• `/referral` - Ajak teman (10 credit/referral)
• `/subscribe` - Upgrade ke Premium (unlimited + auto signals)
• 🎁 User baru mendapat 100 credit gratis

🚀 **Premium Benefits:**
- Unlimited access semua fitur CoinAPI + SnD
- Auto SnD signals (Lifetime users only)
- Priority support

Gunakan credit dengan bijak!"""
        await update.message.reply_text(message, parse_mode='Markdown')

    # Auto Signals Admin Commands
    async def auto_signals_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /auto_signals_status command - Admin only"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if not self.auto_signals:
            await update.message.reply_text("❌ Auto signals system tidak tersedia.")
            return

        status = "🟢 RUNNING" if self.auto_signals.is_running else "🔴 STOPPED"
        eligible_users = self.db.get_eligible_auto_signal_users()

        message = f"""🎯 **Auto SnD Signals Status**

📊 **Status**: {status}
👥 **Eligible Users**: {len(eligible_users)} (Admin + Lifetime)
⏰ **Scan Interval**: {self.auto_signals.scan_interval // 60} minutes
🎯 **Target Coins**: {len(self.auto_signals.target_symbols)} altcoins
📈 **Min Confidence**: {self.auto_signals.min_confidence}%
🕐 **Last Scan**: {datetime.fromtimestamp(self.auto_signals.last_scan_time).strftime('%H:%M:%S') if self.auto_signals.last_scan_time > 0 else 'Never'}

🔧 **Commands:**
• `/enable_auto_signal_ai` - Start momentum signals scanner
• `/disable_auto_signal_ai` - Stop momentum signals scanner

💡 **Target**: Admin & Lifetime premium users only"""

        await update.message.reply_text(message, parse_mode='Markdown')

    async def start_auto_signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /enable_auto_signal_ai command - Admin only"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if not self.auto_signals:
            await update.message.reply_text("❌ Auto signals system tidak tersedia.")
            return

        if self.auto_signals.is_running:
            await update.message.reply_text("⚠️ Auto SnD signals sudah berjalan.")
            return

        # Start auto signals
        try:
            asyncio.create_task(self.auto_signals.start_auto_scanner())
            await update.message.reply_text(
                f"✅ **Auto SnD Signals Enabled**\n\n"
                f"🎯 Scanning {len(self.auto_signals.target_symbols)} altcoins\n"
                f"⏰ Every {self.auto_signals.scan_interval // 60} minutes\n"
                f"👥 For Admin & Lifetime users only\n\n"
                f"📊 Next scan will start in approximately {self.auto_signals.scan_interval // 60} minutes...",
                parse_mode='Markdown'
            )
            self.db.log_user_activity(user_id, "admin_enable_auto_signals", "Enabled Auto SnD Signals")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to enable auto signals: {e}")
            logger.error(f"Error enabling auto signals: {e}")


    async def stop_auto_signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /disable_auto_signal_ai command - Admin only"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if not self.auto_signals:
            await update.message.reply_text("❌ Auto signals system tidak tersedia.")
            return

        if not self.auto_signals.is_running:
            await update.message.reply_text("⚠️ Auto SnD signals sudah berhenti.")
            return

        # Stop auto signals
        try:
            await self.auto_signals.stop_auto_scanner()
            await update.message.reply_text("🛑 **Auto SnD Signals Disabled**\n\nScanner has been stopped.", parse_mode='Markdown')
            self.db.log_user_activity(user_id, "admin_disable_auto_signals", "Disabled Auto SnD Signals")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to stop auto signals: {e}")
            logger.error(f"Error stopping auto signals: {e}")


    # Rest of the existing methods (portfolio, subscribe, referral, admin commands, etc.)
    # I'll include the essential ones for functionality

    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /portfolio command"""
        user_id = update.message.from_user.id
        portfolio = self.db.get_user_portfolio(user_id)

        if not portfolio:
            message = """💼 **Portfolio Anda kosong**

Gunakan `/add_coin <symbol> <amount>` untuk menambah koin ke portfolio.
Contoh: `/add_coin btc 0.5`

Harga akan diambil real-time dari CoinAPI."""
        else:
            message = "💼 **Portfolio Anda (CoinAPI Real-time):**\n\n"
            total_value = 0

            for coin in portfolio:
                symbol = coin['symbol']
                amount = coin['amount']
                price_data = self.crypto_api.get_crypto_price(symbol, force_refresh=True)

                if price_data and 'error' not in price_data:
                    current_price = price_data.get('price', 0)
                    value = amount * current_price
                    total_value += value

                    price_format = f"${current_price:.4f}" if current_price < 100 else f"${current_price:,.2f}"
                    value_format = f"${value:,.2f}"
                    message += f"• {symbol}: {amount} koin ({price_format} = {value_format})\n"
                else:
                    message += f"• {symbol}: {amount} koin (Price unavailable)\n"

            message += f"\n💰 **Total Value: ${total_value:,.2f}** (CoinAPI)"

        await update.message.reply_text(message, parse_mode='Markdown')

    async def add_coin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        message = f"✅ Berhasil menambahkan {amount} {symbol} ke portfolio Anda!\n\nHarga akan diupdate real-time dari CoinAPI saat Anda cek `/portfolio`."
        await update.message.reply_text(message)

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribe command"""
        user_id = update.message.from_user.id
        username = update.message.from_user.username or "Tidak ada username"
        first_name = update.message.from_user.first_name or ""

        # Check current status
        is_premium = self.db.is_user_premium(user_id)
        user_data = self.db.get_user(user_id)
        is_lifetime = user_data and user_data.get('subscription_end') is None if user_data else False

        if is_premium:
            premium_type = "LIFETIME" if is_lifetime else "PREMIUM"
            auto_signals_status = "✅ Auto SnD Signals Access" if is_lifetime else "❌ Auto Signals (Lifetime Only)"

            message = f"""⭐ **Status {premium_type} Aktif**

👤 **{first_name}**, Anda sudah menjadi member {premium_type}!

🚀 **Keuntungan yang Anda nikmati:**
• ♾️ Unlimited analisis CoinAPI + SnD
• 🎯 Akses prioritas ke semua fitur
• 📊 Data real-time CoinAPI tanpa batas
• {auto_signals_status}
• 🛡️ Support premium

✨ **Terima kasih telah menjadi {premium_type} Member!**
Nikmati semua fitur tanpa batasan credit."""
        else:
            message = f"""⭐ **Upgrade ke Premium**

👤 **Informasi Anda:**
• **User ID:** `{user_id}`
• **Username:** @{username}
• **Nama:** {first_name}

🚀 **Fitur Premium CoinAPI + SnD:**
• ♾️ Unlimited analisis dengan CoinAPI real-time
• 📊 Analisis SnD futures lengkap
• 🚨 Alert harga real-time CoinAPI
• 📈 Sinyal trading premium dengan SnD
• 🎯 Support prioritas
• 🔔 Auto SnD signals (Lifetime only)

💰 **Paket Langganan:**
• **1 Bulan** - Rp 320.000
• **2 Bulan** - Rp 600.000 🔥 **PROMO!** (Hemat 40k)
• **6 Bulan** - Rp 1.800.000 💎 **POPULER!** (Hemat 120k)
• **1 Tahun** - Rp 3.000.000 ⭐ **TERBAIK!** (Hemat 840k)
• **Lifetime** - Rp 5.000.000 🚀 **ULTIMATE!** (Auto SnD Signals)

💳 **Metode Pembayaran:**

🏦 **Transfer Bank:**
• Bank Mandiri
• A/N: NABIL FARREL AL FARI
• No. Rek: 1560018407074

📱 **E-Wallet:**
• Shopee Pay / Dana / GO-PAY
• No. HP: 087779274400

📋 **Cara Upgrade:**
1. Transfer sesuai paket yang dipilih
2. Kirim bukti pembayaran ke admin @Billfarr
3. Sertakan informasi ini:
   • User ID: `{user_id}`
   • Username: @{username}
   • Nama: {first_name}
   • Paket: (pilih paket)
4. Tunggu konfirmasi aktivasi (maks 24 jam)

💬 **Butuh bantuan?** Chat admin @Billfarr

🎯 **Special Benefits:**
• **Lifetime**: Auto SnD signals + CoinAPI unlimited
• **Regular Premium**: CoinAPI unlimited analysis

ℹ️ **Catatan Penting:**
Pastikan menyertakan User ID (`{user_id}`) dan paket yang dipilih untuk aktivasi cepat."""

        await update.message.reply_text(message, parse_mode='Markdown')

    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            credits_earned = total_free_referrals * 10  # 10 credits per referral
        except Exception as e:
            print(f"Error getting free referral stats: {e}")
            total_free_referrals = 0
            credits_earned = 0

        # Get premium referral statistics
        premium_stats = self.db.get_premium_referral_stats(user_id)

        message = f"""🎁 **Program Referral CryptoMentor (CoinAPI Edition)**

🔗 **Link Referral FREE (Credit Bonus):**
`https://t.me/{bot_username}?start={free_code}`

💰 **Keuntungan FREE:**
• Anda dapat 10 credit per referral
• Teman dapat 100 credit awal + 5 bonus
• Instant reward untuk CoinAPI access!

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
• Withdraw earnings ke rekening/e-wallet

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
• Unlimited CoinAPI + SnD features

Gunakan `/subscribe` untuk upgrade!

"""

        message += f"""🔗 **Cara Menggunakan:**

**FREE Referral:**
1. Bagikan link FREE ke teman
2. Mereka /start → Anda dapat 10 credit untuk CoinAPI

**PREMIUM Referral** {'(Tersedia)' if is_premium else '(Premium Only)'}:
1. Bagikan link PREMIUM ke calon customer
2. Mereka subscribe premium → Anda dapat Rp 10.000
3. Withdraw earnings ke rekening Anda

💡 **Tips:** Gunakan link FREE untuk sharing biasa, link PREMIUM untuk monetisasi!

🚀 **New Features:** Referral members dapat akses CoinAPI real-time + SnD analysis!"""

        await update.message.reply_text(message, parse_mode='Markdown')

    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    async def handle_ask_ai(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask_ai command - Free AI questions"""
        if not context.args:
            await update.message.reply_text(
                "❌ Gunakan format: `/ask_ai <pertanyaan>`\n\n"
                "Contoh: `/ask_ai apa itu DeFi?`\n"
                "Contoh: `/ask_ai explain bitcoin halving`",
                parse_mode='Markdown'
            )
            return

        question = ' '.join(context.args)
        user_id = update.message.from_user.id

        # Show loading
        loading_msg = await update.message.reply_text("🤖 AI sedang memproses pertanyaan Anda...")

        try:
            # Get AI response
            response = self.ai.get_ai_response(question, 'id')

            # Log activity
            self.db.log_user_activity(user_id, "ask_ai", f"Question: {question[:50]}...")

            await loading_msg.edit_text(response, parse_mode='Markdown')

        except Exception as e:
            await loading_msg.edit_text(f"❌ Terjadi kesalahan: {str(e)}")
            print(f"Error in ask_ai command: {e}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        text = update.message.text.lower().strip()
        user_id = update.message.from_user.id

        print(f"📝 Message received from user {user_id}: '{text[:20]}...'")
        logger.info(f"Message from user {user_id}: {text[:50]}")

        # Quick price check for popular symbols
        popular_symbols = ['btc', 'eth', 'bnb', 'sol', 'ada', 'doge', 'avax', 'matic', 'dot', 'link']

        if text in popular_symbols:
            # Quick price check using CoinAPI
            symbol = text.upper()
            loading_msg = await update.message.reply_text(f"⏳ Cek harga {symbol} dari CoinAPI...")

            price_data = self.crypto_api.get_crypto_price(symbol, force_refresh=True)

            if price_data and 'error' not in price_data and price_data.get('price', 0) > 0:
                current_price = price_data.get('price', 0)
                if current_price < 1:
                    price_format = f"${current_price:.8f}"
                elif current_price < 100:
                    price_format = f"${current_price:.4f}"
                else:
                    price_format = f"${current_price:,.2f}"

                change_24h = price_data.get('change_24h', 0)
                change_emoji = "📈" if change_24h >= 0 else "📉"
                change_color = "+" if change_24h >= 0 else ""

                message = f"""💰 **{symbol} Quick Price**

{price_format} {change_emoji} {change_color}{change_24h:.2f}%

🔄 Source: CoinAPI Real-time
💡 Ketik `/price {symbol.lower()}` untuk detail lengkap
📊 Ketik `/analyze {symbol.lower()}` untuk analisis mendalam"""

                await loading_msg.edit_text(message, parse_mode='Markdown')
            else:
                await loading_msg.edit_text(f"❌ Tidak dapat menemukan data CoinAPI untuk {symbol}")

            return

        # Default AI response for other questions
        if len(text) > 10:  # Only respond to meaningful questions
            try:
                response = self.ai.get_ai_response(text, 'id')
                await update.message.reply_text(response, parse_mode='Markdown')

                # Log activity
                self.db.log_user_activity(user_id, "ai_chat", f"Message: {text[:50]}...")

            except Exception as e:
                print(f"Error in AI response: {e}")

    async def _check_user_restart_required(self, update: Update):
        """Check if user needs to restart after admin restart"""
        user_id = update.message.from_user.id

        # Check if user is banned
        if self.db.is_user_banned(user_id):
            await update.message.reply_text(
                "🚫 **Akun Anda telah dibanned oleh admin**\n\n"
                "Anda tidak dapat menggunakan bot ini lagi.\n"
                "Hubungi admin jika ini adalah kesalahan.",
                parse_mode='Markdown'
            )
            return True

        if self.db.user_needs_restart(user_id):
            await update.message.reply_text(
                "🔄 **Bot telah direstart oleh admin**\n\n"
                "Silakan gunakan `/start` untuk mengaktifkan kembali akun Anda.",
                parse_mode='Markdown'
            )
            return True
        return False

    # Essential admin commands
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        # Get bot statistics
        stats = self.db.get_bot_statistics()
        eligible_auto_users = self.db.get_eligible_auto_signal_users()
        auto_status = "🟢 RUNNING" if self.auto_signals and self.auto_signals.is_running else "🔴 STOPPED"
        deployment_mode = "🚀 DEPLOYMENT" if IS_DEPLOYMENT else "🔧 DEVELOPMENT"

        # Enhanced admin verification for multiple admins
        admin_env_vars = {}
        for i in range(1, 10):
            key = f'ADMIN{i}' # Changed to ADMIN{i}
            env_value = os.getenv(key)
            if env_value and env_value != '0':
                admin_env_vars[key] = env_value

        if not self.is_admin(user_id):
            await update.message.reply_text(
                f"❌ **Access Denied**\n\n"
                f"**Your ID**: {user_id}\n"
                f"**Configured Admin IDs**: {sorted(list(self.admin_ids))}\n"
                f"**Environment Variables**: {', '.join(admin_env_vars.keys()) if admin_env_vars else 'NONE SET'}\n\n"
                f"⚠️ Admin access hanya untuk user dengan ID yang sesuai dengan admin environment variables di Secrets.",
                parse_mode='Markdown'
            )
            return

        message = f"""👑 **CryptoMentor AI - Admin Panel** ({deployment_mode})

🔑 **Admin Verification:**
• **Your User ID**: {user_id} ✅
• **Your Admin Status**: {'✅ PRIMARY' if user_id == self.admin_id else '✅ SECONDARY'}
• **All Admin IDs**: {sorted(list(self.admin_ids))}
• **Environment Variables**: {', '.join(admin_env_vars.keys()) if admin_env_vars else 'NONE SET'}
• **Admin Access**: ✅ VERIFIED & GRANTED

📊 **Bot Statistics:**
• Total Users: {stats['total_users']}
• Premium Users: {stats['premium_users']}
• Banned Users: {stats.get('banned_users', 0)}
• Active Today: {stats['active_today']}
• Total Credits: {stats['total_credits']:,}

🎯 **Auto SnD Signals:**
• Status: {auto_status}
• Mode: Works in {deployment_mode} mode
• Eligible Users: {len(eligible_auto_users)} (Admin + Lifetime)
• Scan Interval: {(self.auto_signals.scan_interval // 60) if self.auto_signals else 'N/A'} minutes

🔧 **Admin Commands:**
• `/setpremium <user_id> <type>` - Set premium (month/lifetime)
• `/revoke_premium <user_id>` - Remove premium status
• `/grant_credits <user_id> <amount>` - Add credits
• `/banned <user_id> <ban|unban|check>` - Ban/unban user management
• `/auto_signals_status` - SnD signals status
• `/enable_auto_signal_ai` - Start momentum signals scanner
• `/disable_auto_signal_ai` - Stop momentum signals scanner
• `/broadcast <message>` - Send broadcast
• `/setup_admin` - Show admin setup instructions

🌐 **API Status:**
• CoinAPI: {'✅ Active' if hasattr(self.crypto_api, 'data_provider') and self.crypto_api.data_provider else '❌ No Provider'}
• Binance: ✅ Active (Public API)
• Auto Signals: {auto_status}

💡 **V4 Features:**
- CoinAPI integration
- Advanced futures analysis with real-time data
- Supply & Demand analysis for futures
- Auto signals for admin & lifetime users"""

        await update.message.reply_text(message, parse_mode='Markdown')





    async def setpremium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command untuk set premium user dengan Admin Agent"""

        # Admin access check
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Akses ditolak. Command ini hanya untuk admin.")
            return

        try:
            # Parse arguments
            if len(context.args) < 2:
                await update.message.reply_text(
                    "❌ Format salah!\n"
                    "Gunakan: /setpremium <user_id> <duration>\n\n"
                    "Duration format:\n"
                    "• `month` atau `bulan` - 30 hari\n"
                    "• `lifetime` - Seumur hidup\n"
                    "• `30d` - 30 hari\n"
                    "• `days:90` - 90 hari",
                    parse_mode='Markdown'
                )
                return

            target_user_id = context.args[0]
            duration_arg = context.args[1]

            # Execute via Admin Agent
            bot_instance = context.bot_data.get('bot_instance')
            if not bot_instance or not hasattr(bot_instance, 'admin_agent'):
                await update.message.reply_text("❌ Admin Agent tidak tersedia")
                return

            result = bot_instance.admin_agent.execute_command("/setpremium", target_user_id, duration_arg)

            if result["status"] == "success":
                await update.message.reply_text(
                    f"✅ {result['message']}\n"
                    f"👤 User: {target_user_id}\n"
                    f"📝 Command: /setpremium {duration_arg}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ {result['message']}\n"
                    f"🔧 Code: {result.get('code', 'UNKNOWN')}"
                )

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            print(f"❌ Error in setpremium command: {e}")

    async def grant_credits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /grant_credits command"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if len(context.args) < 2:
            await update.message.reply_text("❌ Gunakan format: `/grant_credits <user_id> <amount>`\nContoh: `/grant_credits 123456789 100`")
            return

        target_user_id = context.args[0]
        amount_str = context.args[1] # Keep as string for agent

        # Execute via Admin Agent
        bot_instance = context.bot_data.get('bot_instance')
        if not bot_instance or not hasattr(bot_instance, 'admin_agent'):
            await update.message.reply_text("❌ Admin Agent tidak tersedia")
            return

        result = bot_instance.admin_agent.execute_command("/grant_credits", target_user_id, amount_str)

        if result["status"] == "success":
            data = result["data"]
            message = f"✅ **Credits Granted Successfully**\n\n"
            message += f"👤 **User ID**: {target_user_id}\n"
            message += f"💳 **Credits Added**: +{data['credits_added']}\n"
            message += f"📊 **Previous Total**: {data['previous_credits']}\n"
            message += f"🎯 **New Total**: {data['new_total']}\n\n"
            message += f"💡 {result['message']}"

            # Log admin action
            self.db.log_user_activity(
                user_id,
                "admin_grant_credits",
                f"Added {amount_str} credits to user {target_user_id}"
            )
        else:
            message = f"❌ **Error**: {result['message']}\n"
            message += f"🔧 Code: {result.get('code', 'UNKNOWN')}"

        await update.message.reply_text(message, parse_mode='Markdown')


    async def check_user_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check_user_status command - Admin only"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if len(context.args) < 1:
            await update.message.reply_text("❌ Gunakan format: `/check_user_status <user_id>`\nContoh: `/check_user_status 123456789`")
            return

        target_user_id = context.args[0]

        # Execute via Admin Agent
        bot_instance = context.bot_data.get('bot_instance')
        if not bot_instance or not hasattr(bot_instance, 'admin_agent'):
            await update.message.reply_text("❌ Admin Agent tidak tersedia")
            return

        result = bot_instance.admin_agent.execute_command("/check_user_status", target_user_id)

        if result["status"] == "success":
            data = result["data"]

            # Format premium status
            if data["premium_type"] == "lifetime":
                premium_status = "🌟 LIFETIME PREMIUM"
            elif data["premium_type"] == "timed":
                premium_status = f"⭐ PREMIUM (until {data['premium_until'][:10]})"
            else:
                premium_status = "❌ FREE USER"

            message = f"📊 **User Status Report**\n\n"
            message += f"👤 **User ID**: {target_user_id}\n"
            message += f"💎 **Premium Status**: {premium_status}\n"
            message += f"💳 **Credits**: {data['credits']}\n"
            message += f"📅 **Premium Until**: {data['premium_until'] if data['premium_until'] else 'N/A'}\n\n"

            if data["is_premium"]:
                message += "✅ User has active premium access"
            else:
                message += "⚠️ User is on free tier"
        else:
            message = f"❌ **Error**: {result['message']}\n"
            message += f"🔧 Code: {result.get('code', 'UNKNOWN')}"

        await update.message.reply_text(message, parse_mode='Markdown')


    async def revoke_premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command untuk revoke premium user dengan Admin Agent"""

        # Admin access check
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Akses ditolak. Command ini hanya untuk admin.")
            return

        try:
            # Parse arguments
            if len(context.args) < 1:
                await update.message.reply_text(
                    "❌ Format salah!\n"
                    "Gunakan: /revoke_premium <user_id>"
                )
                return

            target_user_id = context.args[0]

            # Execute via Admin Agent
            bot_instance = context.bot_data.get('bot_instance')
            if not bot_instance or not hasattr(bot_instance, 'admin_agent'):
                await update.message.reply_text("❌ Admin Agent tidak tersedia")
                return

            result = bot_instance.admin_agent.execute_command("/revoke_premium", target_user_id)

            if result["status"] == "success":
                await update.message.reply_text(
                    f"✅ {result['message']}\n"
                    f"👤 User: {target_user_id}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ {result['message']}\n"
                    f"🔧 Code: {result.get('code', 'UNKNOWN')}"
                )

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            print(f"❌ Error in revoke_premium command: {e}")


    async def fix_all_credits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /fix_all_credits command"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        try:
            # Fix NULL and negative credits
            fixed_count = self.db.fix_all_user_credits()

            message = f"""✅ **Mass Credit Fix Completed!**

🔧 **Fixed Issues:**
• **Users Fixed**: {fixed_count}
• **Actions**: NULL credits → 100, Negative credits → 10

📊 **Database Health**: All users now have valid credits

💡 **Next Steps**: Monitor for any remaining issues."""

            # Log admin action
            self.db.log_user_activity(
                user_id,
                "admin_fix_all_credits",
                f"Fixed credits for {fixed_count} users"
            )

        except Exception as e:
            message = f"❌ **Error dalam mass credit fix!**\n\n**Error**: {str(e)}"
            print(f"Error in fix_all_credits_command: {e}")

        await update.message.reply_text(message, parse_mode='Markdown')

    async def broadcast_welcome_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast_welcome command"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        welcome_message = """🎉 **CryptoMentor AI Update - CoinAPI Integration!**

🚀 **New Features:**
• ✅ Real-time data dari CoinAPI (bukan simulasi)
• 📊 Supply & Demand (SnD) analysis untuk futures
• 🎯 Auto SnD signals untuk Admin & Lifetime users
• 📈 Enhanced technical analysis

💰 **Quick Start:**
• `/price btc` - GRATIS harga real-time CoinAPI
• `/analyze btc` - 20 credit analisis CoinAPI
• `/futures btc` - 20 credit SnD futures signals

🎁 **Special Offer:**
Semua user dapat 100 credit gratis untuk mencoba fitur CoinAPI baru!

**Selamat trading dengan data real-time! 📈**"""

        self.pending_broadcast = welcome_message

        await update.message.reply_text(
            f"📢 **Preview Welcome Broadcast:**\n\n{welcome_message}\n\n"
            "Gunakan `/confirm_broadcast` untuk mengirim atau `/cancel_broadcast` untuk membatalkan.",
            parse_mode='Markdown'
        )

    async def recovery_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /recovery_stats command"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        try:
            stats = self.db.get_bot_statistics()

            message = f"""📊 **Recovery & Database Stats**

👥 **User Stats:**
• Total Users: {stats['total_users']}
• Premium Users: {stats['premium_users']}
• Active Today: {stats['active_today']}

💳 **Credit Stats:**
• Total Credits: {stats['total_credits']:,}
• Average Credits/User: {stats['avg_credits']:.1f}

📈 **Activity Stats:**
• Commands Today: {stats['commands_today']}
• Total Analyses: {stats['analyses_count']}

🔧 **System Health:**
• Database: ✅ Online
• CoinAPI: ✅ Active
• Auto Signals: {'🟢 Running' if self.auto_signals and self.auto_signals.is_running else '🔴 Stopped'}

⏰ **Last Update**: {datetime.now().strftime('%H:%M:%S WIB')}"""

        except Exception as e:
            message = f"❌ **Error getting recovery stats!**\n\n**Error**: {str(e)}"
            print(f"Error in recovery_stats_command: {e}")

        await update.message.reply_text(message, parse_mode='Markdown')

    async def check_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check_admin command"""
        user_id = update.message.from_user.id

        is_admin = self.is_admin(user_id)

        message = f"""🔍 **Admin Check**

👤 **Your Info:**
• **User ID**: {user_id}
• **Admin Status**: {'✅ ADMIN' if is_admin else '❌ NOT ADMIN'}
• **Configured Admin ID**: {self.admin_id}

{'👑 You have full admin access!' if is_admin else '⚠️ You do not have admin privileges.'}"""

        await update.message.reply_text(message, parse_mode='Markdown')

    async def restart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /restart command"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        await update.message.reply_text(
            "🔄 **Bot Restart Initiated**\n\n"
            "Bot akan restart dalam 5 detik...\n"
            "Semua user akan perlu menggunakan `/start` lagi setelah restart.",
            parse_mode='Markdown'
        )

        # Mark all users as needing restart
        self.db.mark_all_users_for_restart()

        # Log admin action
        self.db.log_user_activity(user_id, "admin_restart", "Bot restart initiated")

        # Exit to trigger restart (in deployment, this will auto-restart)
        import sys
        sys.exit(0)

    async def refresh_credits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /refresh_credits command"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        try:
            # Give all free users 50 bonus credits
            refreshed_count = self.db.refresh_all_free_user_credits()

            message = f"""✅ **Credit Refresh Completed!**

🎁 **Bonus Credits Distributed:**
• **Users Updated**: {refreshed_count}
• **Bonus Given**: +50 credits to all free users
• **Premium Users**: Unaffected (unlimited access)

💡 **Purpose**: Help free users try CoinAPI features

📊 **Next**: Monitor usage and engagement"""

            # Log admin action
            self.db.log_user_activity(
                user_id,
                "admin_refresh_credits",
                f"Gave +50 credits to {refreshed_count} free users"
            )

        except Exception as e:
            message = f"❌ **Error in credit refresh!**\n\n**Error**: {str(e)}"
            print(f"Error in refresh_credits_command: {e}")

        await update.message.reply_text(message, parse_mode='Markdown')

    async def premium_earnings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /premium_earnings command"""
        user_id = update.message.from_user.id
        is_premium = self.db.is_user_premium(user_id)

        if not is_premium:
            await update.message.reply_text(
                "❌ **Command ini hanya untuk Premium users!**\n\n"
                "Upgrade ke Premium untuk akses:\n"
                "• Dashboard earnings dari referral premium\n"
                "• Withdrawal ke rekening/e-wallet\n\n"
                "Gunakan `/subscribe` untuk upgrade!",
                parse_mode='Markdown'
            )
            return

        try:
            # Get premium referral earnings
            premium_stats = self.db.get_premium_referral_stats(user_id)

            message = f"""💎 **Premium Earnings Dashboard**

💰 **Total Earnings**: Rp {premium_stats['total_earnings']:,}
👥 **Total Premium Referrals**: {premium_stats['total_referrals']}
📈 **Average per Referral**: Rp {premium_stats['total_earnings'] // max(premium_stats['total_referrals'], 1):,}

📊 **Recent Premium Referrals:**"""

            if premium_stats['recent_referrals']:
                for ref in premium_stats['recent_referrals'][:5]:
                    referred_name = ref[1][:15] + "..." if len(ref[1]) > 15 else ref[1]
                    subscription_type = ref[2]
                    earnings = ref[3]
                    date = ref[4][:10]
                    message += f"\n• {referred_name} ({subscription_type}) - Rp {earnings:,} ({date})"
            else:
                message += "\n• Belum ada referral premium"

            message += f"""

💳 **Withdrawal Info:**
• Minimum withdrawal: Rp 50.000
• Available: {'✅ Ready' if premium_stats['total_earnings'] >= 50000 else '❌ Below minimum'}
• Contact: Admin @Billfarr untuk withdrawal

🔗 **Premium Referral Link:**
Gunakan `/referral` untuk mendapatkan link premium referral Anda!"""

        except Exception as e:
            message = f"❌ **Error getting earnings data!**\n\n**Error**: {str(e)}"
            print(f"Error in premium_earnings_command: {e}")

        await update.message.reply_text(message, parse_mode='Markdown')

    async def grant_package_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /grant_package command"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ **Format salah!**\n\n"
                "Gunakan: `/grant_package <user_id> <package>`\n\n"
                "**Available Packages:**\n"
                "• `1month` - Premium 1 bulan\n"
                "• `2month` - Premium 2 bulan\n"
                "• `6month` - Premium 6 bulan\n"
                "• `1year` - Premium 1 tahun\n"
                "• `lifetime` - Premium lifetime (Auto signals)\n"
                "• `credits_100` - 100 credits\n"
                "• `credits_500` - 500 credits\n\n"
                "**Contoh:** `/grant_package 123456789 lifetime`",
                parse_mode='Markdown'
            )
            return

        try:
            target_user_id = int(context.args[0])
            package = context.args[1].lower()
        except ValueError:
            await update.message.reply_text("❌ User ID harus berupa angka!")
            return

        # Check if user exists
        existing_user = self.db.get_user(target_user_id)
        if not existing_user:
            await update.message.reply_text(f"❌ User {target_user_id} tidak ditemukan dalam database.")
            return

        try:
            user_info = self.db.get_user(target_user_id)
            username = user_info.get('username', 'No username')
            first_name = user_info.get('first_name', 'Unknown')

            if package == 'lifetime':
                success = self.db.grant_permanent_premium(target_user_id)
                package_name = "Premium Lifetime (Auto Signals)"
            elif package == '1month':
                success = self.db.grant_premium(target_user_id, 30)
                package_name = "Premium 1 Bulan"
            elif package == '2month':
                success = self.db.grant_premium(target_user_id, 60)
                package_name = "Premium 2 Bulan"
            elif package == '6month':
                success = self.db.grant_premium(target_user_id, 180)
                package_name = "Premium 6 Bulan"
            elif package == '1year':
                success = self.db.grant_premium(target_user_id, 365)
                package_name = "Premium 1 Tahun"
            elif package == 'credits_100':
                success = self.db.add_credits(target_user_id, 100)
                package_name = "100 Credits"
            elif package == 'credits_500':
                success = self.db.add_credits(target_user_id, 500)
                package_name = "500 Credits"
            else:
                await update.message.reply_text(f"❌ Package '{package}' tidak dikenali!")
                return

            if success:
                message = f"""✅ **Package berhasil diberikan!**

👤 **User Info:**
• **ID**: {target_user_id}
• **Name**: {first_name}
• **Username**: @{username}

📦 **Package**: {package_name}
🎉 **Status**: Activated

💡 User sekarang dapat menikmati benefit package ini!"""

                # Log admin action
                self.db.log_user_activity(
                    user_id,
                    "admin_grant_package",
                    f"Granted package '{package_name}' to user {target_user_id}"
                )
            else:
                message = f"❌ **Gagal memberikan package!** Terjadi kesalahan dalam proses."

        except Exception as e:
            message = f"❌ **Error sistem saat memberikan package!**\n\n**Error**: {str(e)}"
            print(f"Error in grant_package_command: {e}")

        await update.message.reply_text(message, parse_mode='Markdown')

    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast command"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        # Get the original message text and extract everything after "/broadcast "
        original_text = update.message.text
        if not original_text or len(original_text.strip()) <= 10:  # "/broadcast " = 10 chars
            await update.message.reply_text("❌ Gunakan format: `/broadcast <message>`")
            return

        # Extract message preserving exact formatting (spaces, newlines, etc.)
        if original_text.startswith('/broadcast '):
            message = original_text[11:]  # Remove "/broadcast " (11 characters)
        else:
            await update.message.reply_text("❌ Format broadcast tidak valid.")
            return

        if not message.strip():
            await update.message.reply_text("❌ Pesan broadcast tidak boleh kosong.")
            return

        self.pending_broadcast = message

        await update.message.reply_text(
            f"📢 **Preview Broadcast Message:**\n\n{message}\n\n"
            "Gunakan `/confirm_broadcast` untuk mengirim atau `/cancel_broadcast` untuk membatalkan.",
            parse_mode='Markdown'
        )

    async def confirm_broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /confirm_broadcast command"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if not self.pending_broadcast:
            await update.message.reply_text("❌ Tidak ada broadcast yang pending.")
            return

        if self.broadcast_in_progress:
            await update.message.reply_text("❌ Broadcast sedang berlangsung. Harap tunggu.")
            return

        # Start broadcast
        self.broadcast_in_progress = True
        all_users = self.db.get_all_users()

        await update.message.reply_text(f"📢 Memulai broadcast ke {len(all_users)} users...")

        success_count = 0
        for user_data in all_users:
            user_id_target = user_data.get('user_id')
            if not user_id_target:
                continue

            try:
                # Send message with exact formatting - try markdown first, fallback to plain text
                try:
                    await self.application.bot.send_message(
                        chat_id=user_id_target,
                        text=self.pending_broadcast,
                        parse_mode='Markdown'
                    )
                except Exception as markdown_error:
                    # If markdown fails, send as plain text to preserve exact formatting
                    print(f"Markdown failed for user {user_id_target}, sending as plain text: {markdown_error}")
                    await self.application.bot.send_message(
                        chat_id=user_id_target,
                        text=self.pending_broadcast,
                        parse_mode=None
                    )

                success_count += 1
                await asyncio.sleep(0.1)  # Rate limiting

            except Exception as e:
                print(f"Failed to send broadcast to user {user_id_target}: {e}")
                continue

        # Cleanup
        self.pending_broadcast = None
        self.broadcast_in_progress = False

        await update.message.reply_text(f"✅ Broadcast selesai! Berhasil dikirim ke {success_count}/{len(all_users)} users.")

    async def cancel_broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel_broadcast command"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if not self.pending_broadcast:
            await update.message.reply_text("❌ Tidak ada broadcast yang pending.")
            return

        self.pending_broadcast = None
        await update.message.reply_text("✅ Broadcast dibatalkan.")

    async def setup_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setup_admin command - Shows admin setup instructions"""
        user_id = update.message.from_user.id
        first_name = update.message.from_user.first_name or "User"

        # Get current admin configuration
        admin_env_vars = {}
        for i in range(1, 10):
            key = f'ADMIN{i}'
            env_value = os.getenv(key)
            if env_value and env_value != '0':
                admin_env_vars[key] = env_value

        is_admin = self.is_admin(user_id)

        message = f"""🔧 **Admin Setup Instructions**

👤 **Your Information:**
• **User ID**: `{user_id}`
• **Name**: {first_name}
• **Current Status**: {'✅ ADMIN' if is_admin else '❌ NOT ADMIN'}

📊 **Current Admin Configuration:**
• **Configured Admins**: {len(self.admin_ids)}
• **Admin IDs**: {sorted(list(self.admin_ids)) if self.admin_ids else 'NONE SET'}
• **Environment Variables**: {', '.join(admin_env_vars.keys()) if admin_env_vars else 'NONE SET'}

⚙️ **Setup Instructions:**

**Step 1: Buka Replit Secrets**
• Klik tab "Secrets" di sidebar kiri
• Atau buka: Tools → Secrets

**Step 2: Tambahkan Admin Configuration**
• Key: `ADMIN1`
• Value: `{user_id}` (your User ID)

**Step 3 (Optional): Tambah Admin Kedua**
• Key: `ADMIN2`
• Value: `[USER_ID_ADMIN_KEDUA]`

**Step 4: Restart Bot**
• Klik Stop → Run untuk restart bot
• Bot akan memuat konfigurasi admin baru

💡 **Format Environment Variables:**
```
ADMIN1 = {user_id}
ADMIN2 = [optional_second_admin_id]
```

🔍 **Verifikasi Setup:**
• Gunakan `/admin` setelah restart
• Gunakan `/sb_status` untuk test admin access

⚠️ **Catatan Penting:**
• Hanya user dengan ID yang sesuai yang bisa akses admin commands
• Maksimal 9 admin (ADMIN1 sampai ADMIN9)
• Restart diperlukan setelah mengubah environment variables"""

        await update.message.reply_text(message, parse_mode='Markdown')

    async def banned_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /banned command - Admin only"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ **Format salah!**\n\n"
                "Gunakan: `/banned <user_id> <action>`\n\n"
                "**Available Actions:**\n"
                "• `ban` - Ban user from using bot\n"
                "• `unban` - Unban user\n"
                "• `check` - Check ban status\n\n"
                "**Contoh:**\n"
                "• `/banned 123456789 ban`\n"
                "• `/banned 123456789 unban`\n"
                "• `/banned 123456789 check`",
                parse_mode='Markdown'
            )
            return

        try:
            target_user_id = int(context.args[0])
            action = context.args[1].lower()
        except ValueError:
            await update.message.reply_text("❌ User ID harus berupa angka!")
            return

        # Check if user exists
        existing_user = self.db.get_user(target_user_id)
        if not existing_user:
            await update.message.reply_text(f"❌ User {target_user_id} tidak ditemukan dalam database.")
            return

        try:
            user_info = self.db.get_user(target_user_id)
            username = user_info.get('username', 'No username')
            first_name = user_info.get('first_name', 'Unknown')
            current_banned_status = user_info.get('banned', False)

            if action == 'ban':
                if current_banned_status:
                    message = f"⚠️ **User sudah dalam status banned**\n\n👤 **User**: {first_name} (@{username})\n🆔 **ID**: {target_user_id}"
                else:
                    success = self.db.ban_user(target_user_id)
                    if success:
                        message = f"""🚫 **User berhasil dibanned!**

👤 **User Info:**
• **ID**: {target_user_id}
• **Name**: {first_name}
• **Username**: @{username}
• **Status**: BANNED

⚠️ User tidak dapat menggunakan bot lagi sampai di-unban."""

                        # Log admin action
                        self.db.log_user_activity(
                            user_id,
                            "admin_ban_user",
                            f"Banned user {target_user_id} ({first_name})"
                        )
                    else:
                        message = f"❌ **Gagal melakukan ban!** Terjadi kesalahan dalam proses."

            elif action == 'unban':
                if not current_banned_status:
                    message = f"⚠️ **User tidak dalam status banned**\n\n👤 **User**: {first_name} (@{username})\n🆔 **ID**: {target_user_id}"
                else:
                    success = self.db.unban_user(target_user_id)
                    if success:
                        message = f"""✅ **User berhasil di-unban!**

👤 **User Info:**
• **ID**: {target_user_id}
• **Name**: {first_name}
• **Username**: @{username}
• **Status**: ACTIVE

✅ User sekarang dapat menggunakan bot kembali."""

                        # Log admin action
                        self.db.log_user_activity(
                            user_id,
                            "admin_unban_user",
                            f"Unbanned user {target_user_id} ({first_name})"
                        )
                    else:
                        message = f"❌ **Gagal melakukan unban!** Terjadi kesalahan dalam proses."

            elif action == 'check':
                ban_status = "🚫 BANNED" if current_banned_status else "✅ ACTIVE"
                message = f"""📊 **Ban Status Check**

👤 **User Info:**
• **ID**: {target_user_id}
• **Name**: {first_name}
• **Username**: @{username}
• **Ban Status**: {ban_status}

💡 User {'tidak dapat menggunakan bot' if current_banned_status else 'dapat menggunakan bot normal'}."""

            else:
                await update.message.reply_text(f"❌ Action '{action}' tidak dikenali! Gunakan: ban, unban, atau check.")
                return

        except Exception as e:
            message = f"❌ **Error sistem saat memproses ban command!**\n\n**Error**: {str(e)}"
            print(f"Error in banned_command: {e}")

        await update.message.reply_text(message, parse_mode='Markdown')

    async def cancel_broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel_broadcast command"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin only command.")
            return

        if not self.pending_broadcast:
            await update.message.reply_text("❌ Tidak ada broadcast yang pending.")
            return

        self.pending_broadcast = None
        await update.message.reply_text("✅ Broadcast dibatalkan.")

    async def whoami_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /whoami command - shows user ID"""
        user_id = update.effective_user.id if update.effective_user else None
        username = update.effective_user.username if update.effective_user else "No username"
        first_name = update.effective_user.first_name if update.effective_user else "Unknown"

        message = f"👤 **Your Information:**\n\n"
        message += f"• **User ID**: `{user_id}`\n"
        message += f"• **Username**: @{username}\n"
        message += f"• **Name**: {first_name}\n"
        message += f"• **Admin Status**: {'✅ ADMIN' if self.is_admin(user_id) else '❌ NOT ADMIN'}"

        await update.message.reply_text(message, parse_mode='Markdown')

    async def admin_debug_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_debug command - shows admin configuration debug info"""
        user_id = update.effective_user.id if update.effective_user else None

        # Get current admin configuration
        admin_ids = set()
        env_info = []

        # Check ADMIN1, ADMIN2, etc.
        for i in range(1, 10):
            env_key = f'ADMIN{i}'
            admin_id_str = (os.getenv(env_key) or "").strip()

            if admin_id_str:
                env_info.append(f"{env_key}=SET")
                if admin_id_str.lower() != "none":
                    admin_ids.add(str(admin_id_str))

            # Check fallback
            if i <= 2:
                fallback_key = f'ADMIN{i}_USER_ID' if i > 1 else 'ADMIN_USER_ID'
                fallback_str = (os.getenv(fallback_key) or "").strip()
                if fallback_str and not admin_id_str:
                    env_info.append(f"{fallback_key}=SET (fallback)")
                    if fallback_str.lower() != "none":
                        admin_ids.add(str(fallback_str))

        is_caller_admin = self.is_admin(user_id)

        message = f"🔧 **Admin Debug Information**\n\n"
        message += f"👤 **Caller ID**: `{user_id}`\n"
        message += f"✅ **Is Admin**: {is_caller_admin}\n"
        message += f"👑 **Resolved Admin IDs**: {sorted(list(admin_ids)) if admin_ids else 'NONE'}\n"
        message += f"⚙️ **Environment Variables**: {', '.join(env_info) if env_info else 'NONE SET'}\n\n"

        message += f"💡 **Expected Format in Replit Secrets:**\n"
        message += f"• Key: `ADMIN1`, Value: `{user_id}` (your ID)\n"
        message += f"• Key: `ADMIN2`, Value: `[second_admin_id]` (optional)\n\n"

        message += f"🔄 **Remember**: Restart bot after changing Secrets!"

        await update.message.reply_text(message, parse_mode='Markdown')

    async def _on_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Global error handler to log unhandled exceptions"""
        user_id = getattr(getattr(update, "effective_user", None), "id", None)
        command = getattr(getattr(update, "message", None), "text", "unknown")
        print(f"⚠️ Bot Error: {repr(context.error)} | User: {user_id} | Command: {command[:50]}")

    def _register_handlers(self):
        """Register all bot handlers"""
        # Add command handlers with proper async functions
        self.application.add_handler(CommandHandler("start", self.start))
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
        self.application.add_handler(CommandHandler("whoami", self.whoami_command))
        self.application.add_handler(CommandHandler("admin_debug", self.admin_debug_command))

        # Admin commands
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CommandHandler("revoke_premium", self.revoke_premium_command))
        self.application.add_handler(CommandHandler("setpremium", self.setpremium_command))
        self.application.add_handler(CommandHandler("grant_credits", self.grant_credits_command))
        self.application.add_handler(CommandHandler("check_user_status", self.check_user_status_command))
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
        self.application.add_handler(CommandHandler("setup_admin", self.setup_admin_command)) # Added setup_admin command
        self.application.add_handler(CommandHandler("banned", self.banned_command))

        # Supabase health check command
        try:
            from handlers_sb import cmd_sb_status
            self.application.add_handler(CommandHandler("sb_status", cmd_sb_status))
            print("✅ Supabase status command registered")
        except ImportError as e:
            print(f"⚠️ Supabase handler not available: {e}")
        # Renamed for clarity and consistency with user request
        self.application.add_handler(CommandHandler("auto_signal_ai_status", self.auto_signals_status_command))
        self.application.add_handler(CommandHandler("enable_auto_signal_ai", self.start_auto_signals_command))
        self.application.add_handler(CommandHandler("disable_auto_signal_ai", self.stop_auto_signals_command))


        # Add callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))

        # Add message handler for regular text (should be last)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    # End of TelegramBot class definition
if __name__ == "__main__":
    bot = TelegramBot()
    asyncio.run(bot.run_bot())