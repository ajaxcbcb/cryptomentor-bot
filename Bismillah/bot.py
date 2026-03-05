#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CryptoMentor AI Bot - Main Bot Class
Enhanced with button-based menu system and async support
OPTIMIZED: Lazy imports, shared services, caching for performance
"""

import os
import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

logger = logging.getLogger(__name__)

# Lazy-loaded modules (imported when needed)
_menu_handlers_loaded = False
_supabase_available = None
_sb_handlers = None


def _lazy_load_menu():
    """Lazy load menu system only when needed"""
    global _menu_handlers_loaded
    if not _menu_handlers_loaded:
        from menu_handlers import register_menu_handlers
        _menu_handlers_loaded = True
        return register_menu_handlers
    from menu_handlers import register_menu_handlers
    return register_menu_handlers


def _check_supabase():
    """Lazy check for Supabase availability"""
    global _supabase_available, _sb_handlers
    if _supabase_available is None:
        try:
            from app.supabase_conn import get_supabase_client, health
            from app.sb_repo import ensure_user_registered, get_user_by_telegram_id
            from app.routers.sb_quickcheck import handlers as sb_handlers
            _supabase_available = True
            _sb_handlers = sb_handlers
        except ImportError:
            _supabase_available = False
            _sb_handlers = None
            print("⚠️ Supabase integration not available, using local fallback")
    return _supabase_available, _sb_handlers

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
        
        # Use lazy-loaded services (initialized on first access)
        self._ai_assistant = None
        self._crypto_api = None
        print(f"✅ Bot initialized with {len(self.admin_ids)} admin(s)")

    @property
    def ai_assistant(self):
        """Lazy-load AI assistant on first access"""
        if self._ai_assistant is None:
            from services import get_ai_assistant
            self._ai_assistant = get_ai_assistant()
        return self._ai_assistant

    @property
    def crypto_api(self):
        """Lazy-load crypto API on first access"""
        if self._crypto_api is None:
            from services import get_crypto_api
            self._crypto_api = get_crypto_api()
        return self._crypto_api

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
    
    async def clear_all_user_states(self):
        """
        Clear all pending user states on bot restart
        This prevents users from continuing old commands after bot restart
        """
        try:
            from services import get_database
            db = get_database()
            
            # Clear any pending states in database if stored there
            # For now, we'll just log that we're starting fresh
            print("🔄 Bot restarted - All user command states will be reset")
            print("   Users will need to start new commands")
            
            # Note: user_data in context is automatically cleared on bot restart
            # This is just for logging and any database cleanup if needed
            
        except Exception as e:
            print(f"⚠️ Error clearing user states: {e}")

    async def setup_application(self):
        """Setup telegram application with handlers"""
        self.application = Application.builder().token(self.token).build()
        
        # Clear all pending user states on bot restart
        await self.clear_all_user_states()
        
        # Auto-migrate OpenClaw tables if needed
        try:
            from services import get_database
            from app.openclaw_auto_migrate import auto_migrate_openclaw
            
            print("🔍 Checking OpenClaw database...")
            db = get_database()
            migrated = auto_migrate_openclaw(db)
            
            if migrated:
                print("✅ OpenClaw tables created successfully!")
            else:
                print("✅ OpenClaw tables already exist")
        except Exception as e:
            print(f"⚠️ OpenClaw auto-migration skipped: {e}")
            print("   OpenClaw features may not work until migration is run")

        # Register core command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # Basic command handlers
        self.application.add_handler(CommandHandler("price", self.price_command))
        self.application.add_handler(CommandHandler("market", self.market_command))
        self.application.add_handler(CommandHandler("portfolio", self.portfolio_command))
        self.application.add_handler(CommandHandler("credits", self.credits_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("referral", self.referral_command))
        self.application.add_handler(CommandHandler("language", self.language_command))
        self.application.add_handler(CommandHandler("id", self.id_command))

        # Register manual signal handlers (Task 3: Manual Signal Generation Fix)
        try:
            from app.handlers_manual_signals import (
                cmd_analyze, cmd_futures, cmd_futures_signals,
                cmd_signal, cmd_signals
            )
            self.application.add_handler(CommandHandler("analyze", cmd_analyze))
            self.application.add_handler(CommandHandler("futures", cmd_futures))
            self.application.add_handler(CommandHandler("futures_signals", cmd_futures_signals))
            self.application.add_handler(CommandHandler("signal", cmd_signal))
            self.application.add_handler(CommandHandler("signals", cmd_signals))
            print("✅ Manual signal handlers registered (with premium check & rate limiting)")
        except Exception as e:
            print(f"⚠️ Manual signal handlers failed to register: {e}")
            # Fallback to old handlers if new ones fail
            self.application.add_handler(CommandHandler("analyze", self.analyze_command))
            self.application.add_handler(CommandHandler("futures", self.futures_command))
            self.application.add_handler(CommandHandler("futures_signals", self.futures_signals_command))
            self.application.add_handler(CommandHandler("signal", self.signal_command))
            self.application.add_handler(CommandHandler("signals", self.signals_command))
            print("⚠️ Using fallback signal handlers")

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

        # Register menu system handlers (lazy load)
        register_menu_handlers = _lazy_load_menu()
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

        # AI HANDLERS RE-ENABLED with Cerebras (ultra-fast)
        # Commands /ai, /chat, /aimarket now use Cerebras AI (0.4s response time)
        try:
            from app.handlers_deepseek import handle_ai_analyze, handle_ai_chat, handle_ai_market_summary
            self.application.add_handler(CommandHandler("ai", handle_ai_analyze))
            self.application.add_handler(CommandHandler("chat", handle_ai_chat))
            self.application.add_handler(CommandHandler("aimarket", handle_ai_market_summary))
            print("✅ AI handlers registered (Cerebras - ultra fast)")
        except Exception as e:
            print(f"⚠️ AI handlers failed to register: {e}")

        # Register Supabase handlers if available (lazy check)
        supabase_available, sb_handlers = _check_supabase()
        if supabase_available and sb_handlers:
            for handler in sb_handlers:
                self.application.add_handler(handler)

        # Register signal tracking admin handlers
        try:
            from app.handlers_signal_tracking import (
                cmd_winrate, cmd_weekly_report, cmd_upload_logs, cmd_signal_stats
            )
            self.application.add_handler(CommandHandler("winrate", cmd_winrate))
            self.application.add_handler(CommandHandler("weekly_report", cmd_weekly_report))
            self.application.add_handler(CommandHandler("upload_logs", cmd_upload_logs))
            self.application.add_handler(CommandHandler("signal_stats", cmd_signal_stats))
            print("✅ Signal tracking admin commands registered")
        except Exception as e:
            print(f"⚠️ Signal tracking admin commands failed to register: {e}")

        # Register Automaton handlers
        try:
            from app.handlers_automaton import (
                automaton_command, spawn_agent_command, agent_status_command, deposit_command,
                balance_command, agent_logs_command, withdraw_command,
                agent_lineage_command, handle_spawn_parent_callback
            )
            # Main automaton command with subcommands
            self.application.add_handler(CommandHandler("automaton", automaton_command))
            
            # Individual commands (backward compatibility)
            self.application.add_handler(CommandHandler("spawn_agent", spawn_agent_command))
            self.application.add_handler(CommandHandler("agent_status", agent_status_command))
            self.application.add_handler(CommandHandler("agent_lineage", agent_lineage_command))
            self.application.add_handler(CommandHandler("deposit", deposit_command))
            self.application.add_handler(CommandHandler("balance", balance_command))
            self.application.add_handler(CommandHandler("agent_logs", agent_logs_command))
            self.application.add_handler(CommandHandler("withdraw", withdraw_command))
            
            # Register callback handlers for spawn parent selection
            self.application.add_handler(CallbackQueryHandler(
                handle_spawn_parent_callback,
                pattern="^spawn_(noparent|parent)_"
            ))
            
            print("✅ Automaton handlers registered")
        except Exception as e:
            print(f"⚠️ Automaton handlers failed to register: {e}")
        
        # Register admin automaton handlers
        try:
            from app.handlers_admin_automaton import (
                admin_wallets_command, admin_wallet_details_command,
                admin_revenue_command, admin_agents_command,
                admin_process_withdrawal_command
            )
            self.application.add_handler(CommandHandler("admin_wallets", admin_wallets_command))
            self.application.add_handler(CommandHandler("admin_wallet_details", admin_wallet_details_command))
            self.application.add_handler(CommandHandler("admin_revenue", admin_revenue_command))
            self.application.add_handler(CommandHandler("admin_agents", admin_agents_command))
            self.application.add_handler(CommandHandler("admin_process_withdrawal", admin_process_withdrawal_command))
            print("✅ Admin automaton handlers registered")
        except Exception as e:
            print(f"⚠️ Admin automaton handlers failed to register: {e}")
        
        # Register admin credits handlers (manual deposit verification for AUTOMATON)
        try:
            from app.handlers_admin_credits import (
                admin_add_automaton_credits_command,
                admin_check_automaton_credits_command
            )
            self.application.add_handler(CommandHandler("admin_add_automaton_credits", admin_add_automaton_credits_command))
            self.application.add_handler(CommandHandler("admin_check_automaton_credits", admin_check_automaton_credits_command))
            print("✅ Admin AUTOMATON credits handlers registered")
        except Exception as e:
            print(f"⚠️ Admin AUTOMATON credits handlers failed to register: {e}")
        
        # Register OpenClaw AI Assistant handlers (seamless chat mode)
        try:
            from app.openclaw_message_handler import (
                openclaw_start_command, openclaw_exit_command,
                openclaw_create_command, openclaw_buy_command,
                openclaw_help_command
            )
            from app.openclaw_callbacks import register_openclaw_callbacks
            from app.handlers_openclaw_skills import register_openclaw_skill_handlers
            
            self.application.add_handler(CommandHandler("openclaw_start", openclaw_start_command))
            self.application.add_handler(CommandHandler("openclaw", openclaw_start_command))  # Alias
            self.application.add_handler(CommandHandler("openclaw_exit", openclaw_exit_command))
            self.application.add_handler(CommandHandler("openclaw_create", openclaw_create_command))
            self.application.add_handler(CommandHandler("openclaw_buy", openclaw_buy_command))
            self.application.add_handler(CommandHandler("openclaw_help", openclaw_help_command))
            self.application.add_handler(CommandHandler("openclaw_balance", self.openclaw_balance_command))
            self.application.add_handler(CommandHandler("openclaw_history", self.openclaw_history_command))
            
            # Register callback handlers
            register_openclaw_callbacks(self.application)
            
            # Register skill handlers
            register_openclaw_skill_handlers(self.application)
            
            print("✅ OpenClaw AI Assistant handlers registered (seamless chat mode + skills)")
        except Exception as e:
            print(f"⚠️ OpenClaw handlers failed to register: {e}")
        
        # Register OpenClaw Simple CLI handlers (lightweight alternative)
        try:
            from app.handlers_openclaw_simple import register_openclaw_handlers
            register_openclaw_handlers(self.application)
            print("✅ OpenClaw CLI handlers registered (status, help, ask)")
        except Exception as e:
            print(f"⚠️ OpenClaw CLI handlers failed to register: {e}")
        
        # Register OpenClaw Deposit handlers (payment system)
        try:
            from app.handlers_openclaw_deposit import register_openclaw_deposit_handlers
            register_openclaw_deposit_handlers(self.application)
            print("✅ OpenClaw deposit handlers registered (payment & credits)")
        except Exception as e:
            print(f"⚠️ OpenClaw deposit handlers failed to register: {e}")
        
        # Register OpenClaw Admin handlers (credit management & monitoring)
        try:
            from app.handlers_openclaw_admin import register_openclaw_admin_handlers
            register_openclaw_admin_handlers(self.application)
            print("✅ OpenClaw admin handlers registered (monitoring & management)")
        except Exception as e:
            print(f"⚠️ OpenClaw admin handlers failed to register: {e}")
        
        # Register OpenClaw Admin Credit handlers (balance check & notifications)
        try:
            from app.handlers_openclaw_admin_credits import register_openclaw_admin_credit_handlers
            register_openclaw_admin_credit_handlers(self.application)
            print("✅ OpenClaw admin credit handlers registered (balance & notifications)")
        except Exception as e:
            print(f"⚠️ OpenClaw admin credit handlers failed to register: {e}")
        
        # Register OpenClaw LangChain handlers (NEW - Production-grade architecture)
        try:
            from app.handlers_openclaw_langchain import register_openclaw_langchain_handlers
            register_openclaw_langchain_handlers(self.application)
            print("✅ OpenClaw LangChain handlers registered (production-grade)")
        except Exception as e:
            print(f"⚠️ OpenClaw LangChain handlers failed to register: {e}")
        
        # Note: Automaton is for AUTONOMOUS TRADING only (Lifetime Premium)
        # Signal generation uses bot's own system (/analyze, /futures, /ai)
        # OpenClaw is for PERSONAL AI ASSISTANT (Claude Sonnet 4.5) with seamless chat


        # Message handler for menu interactions
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        print("✅ Application handlers registered successfully")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with menu integration and referral processing"""
        user = update.effective_user
        
        # CRITICAL: Store user's chat_id for autosignal delivery
        from app.chat_store import remember_chat
        remember_chat(user.id, update.effective_chat.id)
        print(f"✅ Stored chat_id for user {user.id}")

        # Use shared database instance
        from services import get_database
        db = get_database()

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

        # Register user - Supabase FIRST (primary), Local DB second (backup)
        try:
            # PRIMARY: Register to Supabase using RPC
            try:
                from app.sb_repo import upsert_user_strict
                supabase_result = upsert_user_strict(
                    user.id,
                    user.username,
                    user.first_name,
                    user.last_name,
                    referrer_id
                )
                print(f"✅ User {user.id} registered to Supabase (primary)")
            except Exception as sb_error:
                print(f"⚠️ Supabase registration failed: {sb_error}")
            
            # SECONDARY: Register to Local DB (backup + compatibility)
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

        # Lazy load menu system
        from menu_system import MenuBuilder, get_menu_text, MAIN_MENU

        welcome_text = f"""🤖 **Welcome to CryptoMentor AI 3.0**

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
        # Store user's chat_id for autosignal delivery
        if update.effective_user and update.effective_chat:
            from app.chat_store import remember_chat
            remember_chat(update.effective_user.id, update.effective_chat.id)
        
        from menu_system import MenuBuilder, get_menu_text, MAIN_MENU
        await update.message.reply_text(
            get_menu_text(MAIN_MENU),
            reply_markup=MenuBuilder.build_main_menu(),
            parse_mode='MARKDOWN'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
        user_id = update.effective_user.id

        # Get user language
        from services import get_database
        db = get_database()
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

🧠 **Perintah Generate Sinyal Manual:**
• `/analyze <symbol>` - Analisis single coin (20 kredit)
  Contoh: `/analyze BTCUSDT`
• `/futures <symbol> <timeframe>` - Sinyal futures (20 kredit)
  Contoh: `/futures ETHUSDT 4h`
• `/futures_signals` - Sinyal multi-coin (60 kredit)
  Contoh: `/futures_signals`

👑 **Lifetime Premium:** Semua command GRATIS (tanpa biaya kredit)

🤖 **Cerebras AI Assistant (ULTRA FAST!):**
• `/ai <symbol>` - Analisis market dengan AI (0.4s response!)
• `/chat <pesan>` - Chat santai tentang market & trading
• `/aimarket` - Summary kondisi market global dengan AI

👑 **Premium & Akun:**
• `/subscribe` - Upgrade ke premium
• `/referral` - Program referral
• `/language <en|id>` - Ubah bahasa

💡 **Tips:** Gunakan menu tombol untuk pengalaman terbaik!
🔥 **Fitur Baru:** Cerebras AI - 70x lebih cepat dari sebelumnya!"""
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

🧠 **Manual Signal Generation:**
• `/analyze <symbol>` - Single coin analysis (20 credits)
  Example: `/analyze BTCUSDT`
• `/futures <symbol> <timeframe>` - Futures signal (20 credits)
  Example: `/futures ETHUSDT 4h`
• `/futures_signals` - Multi-coin signals (60 credits)
  Example: `/futures_signals`

👑 **Lifetime Premium:** All commands FREE (no credit charge)

🤖 **Cerebras AI Assistant (ULTRA FAST!):**
• `/ai <symbol>` - Market analysis with AI (0.4s response!)
• `/chat <message>` - Casual chat about market & trading
• `/aimarket` - Global market summary with AI insights

👑 **Premium & Account:**
• `/subscribe` - Upgrade to premium
• `/referral` - Referral program
• `/language <en|id>` - Change language

💡 **Tip:** Use the button menu for the best experience!
🔥 **New Feature:** Cerebras AI - 70x faster than before!"""

        await update.message.reply_text(help_text, parse_mode='MARKDOWN')

    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle price command with real Binance integration"""
        symbol = context.args[0].upper() if context.args else "BTC"
        user_id = update.effective_user.id

        # Get user language
        from services import get_database
        db = get_database()
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
            from menu_handler import get_estimated_time_message, get_user_timezone_from_context

            # Get user timezone for estimated time
            user_id = update.effective_user.id
            user_tz = get_user_timezone_from_context(context, user_id)
            est_time = get_estimated_time_message(5, user_tz)
            
            # Show loading message with estimated time
            loading_msg = await update.message.reply_text(
                f"⏳ **Fetching market overview from Binance...**\n\n"
                f"📊 Loading prices...\n{est_time}",
                parse_mode='MARKDOWN'
            )

            # Wait briefly while fetching
            await asyncio.sleep(1)

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
                
                # Get SMC trend indicator
                smc_indicator = ""
                try:
                    from smc_analyzer import smc_analyzer
                    coin_symbol = coin + 'USDT'
                    smc_result = smc_analyzer.analyze(coin_symbol, '1h', limit=100)
                    if 'error' not in smc_result:
                        structure = smc_result.get('structure', {})
                        trend = structure.trend if hasattr(structure, 'trend') else 'ranging'
                        ema_21 = smc_result.get('ema_21', 0)
                        current_price = smc_result.get('current_price', 0)
                        
                        if trend == 'uptrend':
                            smc_indicator = " [HH/HL]"
                        elif trend == 'downtrend':
                            smc_indicator = " [LH/LL]"
                        
                        if ema_21 > 0 and current_price > 0:
                            ema_pos = "↑" if current_price > ema_21 else "↓"
                            smc_indicator += f" EMA21:{ema_pos}"
                except Exception as e:
                    print(f"SMC error for {coin}: {e}")
                
                market_text += f"• {idx}. {coin}: ${price:,.2f} ({change:+.2f}%) {emoji}{smc_indicator}\n"

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
            from services import get_database
            db = get_database()
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
        """Handle analyze command with tiered DCA zones for Spot trading"""
        import html as html_escape
        
        symbol = context.args[0].upper() if context.args else "BTC"
        timeframe = "1h"

        # Add USDT if not present
        if not any(symbol.endswith(pair) for pair in ['USDT', 'BUSD', 'USDC']):
            symbol += 'USDT'

        try:
            from snd_zone_detector import detect_snd_zones
            from menu_handler import get_estimated_time_message, get_user_timezone_from_context

            # Get user timezone for estimated time
            user_id = update.effective_user.id
            user_tz = get_user_timezone_from_context(context, user_id)
            est_time = get_estimated_time_message(5, user_tz)
            
            # Check and deduct credits (20 for Spot Analysis)
            try:
                from app.credits_guard import require_credits
                ok, remain, msg = require_credits(user_id, 20)
                if not ok:
                    await update.effective_message.reply_text(
                        f"❌ {html_escape.escape(str(msg))}\n\n⭐ Upgrade ke Premium untuk akses unlimited!"
                    )
                    return
            except Exception as e:
                print(f"Credit check error: {e}")
                remain = "N/A"

            # Show loading message
            loading_msg = await update.effective_message.reply_text(
                f"🔄 Analyzing {symbol} 1h with Supply & Demand zones...\n"
                f"⏱️ {est_time}"
            )

            # Get SnD analysis
            snd_result = detect_snd_zones(symbol, timeframe, limit=100)

            if 'error' in snd_result:
                await loading_msg.edit_text(
                    f"❌ Error: {snd_result['error']}\n\n"
                    f"💡 Try: /analyze btc or /analyze eth"
                )
                return

            current_price = snd_result.get('current_price', 0)
            demand_zones = snd_result.get('demand_zones', [])
            supply_zones = snd_result.get('supply_zones', [])

            def fmt_price(p):
                if p >= 1000:
                    return f"${p:,.2f}"
                elif p >= 1:
                    return f"${p:,.4f}"
                elif p >= 0.0001:
                    return f"${p:.6f}"
                else:
                    return f"${p:.8f}"

            avg_demand = sum(z.midpoint for z in demand_zones) / len(demand_zones) if demand_zones else 0
            avg_supply = sum(z.midpoint for z in supply_zones) / len(supply_zones) if supply_zones else 0

            if avg_demand and avg_supply:
                mid_range = (avg_demand + avg_supply) / 2
                if current_price > mid_range * 1.02:
                    trend = "Bullish"
                elif current_price < mid_range * 0.98:
                    trend = "Bearish"
                else:
                    trend = "Sideways"
            else:
                trend = "Neutral"

            avg_strength = 0
            if demand_zones:
                avg_strength = sum(z.strength for z in demand_zones) / len(demand_zones)
            if avg_strength >= 60:
                volume_status = "Accumulation"
            elif avg_strength >= 40:
                volume_status = "Neutral"
            else:
                volume_status = "Distribution"

            zone_count = len(demand_zones) + len(supply_zones)
            base_confidence = min(85, 50 + (zone_count * 5))
            if demand_zones:
                base_confidence += min(15, demand_zones[0].strength / 5)
            confidence = min(95, base_confidence)

            display_symbol = symbol.replace('USDT', '')

            response = f"""📊 Spot Signal – {display_symbol} ({timeframe.upper()})

💰 Price: {fmt_price(current_price)}

🟢 BUY ZONES
"""

            zone_labels = [
                ("A", "Strong", "40%"),
                ("B", "Discount", "35%"),
                ("C", "Deep", "25%")
            ]

            sorted_demands = sorted(demand_zones, key=lambda z: abs(current_price - z.midpoint))

            if sorted_demands:
                for i, (label, desc, alloc) in enumerate(zone_labels):
                    if i < len(sorted_demands):
                        zone = sorted_demands[i]
                        zone_width = zone.high - zone.low
                        tp1 = zone.high + (zone_width * 1.5)
                        tp2 = zone.high + (zone_width * 3.0)
                        strength = zone.strength if hasattr(zone, 'strength') else 50

                        response += f"""
Zone {label} – {desc}
  📍 Entry: {fmt_price(zone.low)} - {fmt_price(zone.high)}
  💰 Allocation: {alloc}
  🎯 TP1: {fmt_price(tp1)} | TP2: {fmt_price(tp2)}
  📊 Strength: {strength:.0f}%
"""
            else:
                response += "\n⏳ No active demand zones detected\n"

            response += "\n🔴 SELL ZONE (Take Profit)\n"
            if supply_zones:
                best_supply = supply_zones[0]
                response += f"  🎯 {fmt_price(best_supply.low)} - {fmt_price(best_supply.high)}\n"
            else:
                response += "  No active supply zone\n"

            # Add SMC Analysis
            try:
                from smc_analyzer import smc_analyzer
                from smc_formatter import format_smc_analysis
                
                smc_result = smc_analyzer.analyze(symbol, timeframe, limit=200)
                smc_text = format_smc_analysis(smc_result, compact=False)
                response += smc_text
            except Exception as e:
                print(f"SMC analysis error: {e}")
                # Continue without SMC if it fails

            response += f"""
📈 Context:
  • Trend: {trend}
  • Volume: {volume_status}
  • Confidence: {confidence:.0f}%

💳 Credit terpakai: 20 | Sisa: {remain}

⚠️ Spot only • LIMIT order at zone"""

            await loading_msg.edit_text(response)

        except Exception as e:
            import traceback
            traceback.print_exc()
            await update.effective_message.reply_text(
                f"❌ Analysis error: {str(e)[:100]}\n\n"
                f"💡 Try: /analyze btc or check symbol format"
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
            from menu_handler import get_estimated_time_message, get_user_timezone_from_context
            
            user_id = update.effective_user.id
            user_tz = get_user_timezone_from_context(context, user_id)
            est_time = get_estimated_time_message(5, user_tz)
            
            # Check and deduct credits (20 for Futures Analysis)
            try:
                from app.credits_guard import require_credits
                ok, remain, msg = require_credits(user_id, 20)
                if not ok:
                    await update.effective_message.reply_text(
                        f"❌ {msg}\n\n⭐ Upgrade ke Premium untuk akses unlimited!",
                        parse_mode='HTML'
                    )
                    return
            except Exception as e:
                print(f"Credit check error: {e}")
                # Continue if credit system fails (fallback)
            
            await update.message.reply_text(f"⏳ Analyzing {symbol} {timeframe} with Supply & Demand zones...\n{est_time}")

            try:
                from snd_zone_detector import detect_snd_zones
                
                # Get SnD zones
                snd_result = detect_snd_zones(symbol, timeframe, limit=100)
                
                if 'error' in snd_result:
                    await update.message.reply_text(f"❌ Analysis error: {snd_result['error']}")
                    return

                current_price = snd_result.get('current_price', 0)
                demand_zones = snd_result.get('demand_zones', [])
                supply_zones = snd_result.get('supply_zones', [])
                signal_type = snd_result.get('entry_signal')
                signal_strength = snd_result.get('signal_strength', 0)

                # Helper function for price formatting
                def fmt_price(p):
                    if p >= 1000: return f"${p:,.2f}"
                    elif p >= 1: return f"${p:.4f}"
                    elif p >= 0.0001: return f"${p:.6f}"
                    else: return f"${p:.8f}"
                
                # Build SnD analysis response with HTML formatting
                response = f"📊 <b>Futures: {symbol} ({timeframe})</b>\n\n"
                response += f"💰 <b>Current Price:</b> {fmt_price(current_price)}\n\n"

                # Add demand zones (BUY ENTRIES)
                if demand_zones:
                    response += f"🟢 <b>DEMAND ZONES (BUY SETUP):</b> {len(demand_zones)} zone(s)\n"
                    for i, zone in enumerate(demand_zones[:3], 1):
                        entry = zone.entry_price if hasattr(zone, 'entry_price') else zone.midpoint
                        strength = zone.strength if hasattr(zone, 'strength') else 0
                        response += f"\n<b>Zone {i}:</b> 💵 Entry {fmt_price(entry)}\n"
                        response += f"  • Range: {fmt_price(zone.low)} - {fmt_price(zone.high)}\n"
                        response += f"  • Strength: {strength:.0f}%\n"
                        
                        # Calculate SL and TP
                        zone_width = zone.high - zone.low
                        sl = zone.low - (zone_width * 0.5)
                        tp1 = current_price + (zone_width * 1.5)
                        tp2 = current_price + (zone_width * 2.5)
                        
                        response += f"  • 🛑 SL: {fmt_price(sl)}\n"
                        response += f"  • 🎯 TP1: {fmt_price(tp1)}\n"
                        response += f"  • 🎯 TP2: {fmt_price(tp2)}\n"
                else:
                    response += "🟢 <b>DEMAND ZONES:</b> No active demand zones\n"

                # Add supply zones (SHORT ENTRIES)
                if supply_zones:
                    response += f"\n🔴 <b>SUPPLY ZONES (SHORT SETUP):</b> {len(supply_zones)} zone(s)\n"
                    for i, zone in enumerate(supply_zones[:3], 1):
                        entry = zone.entry_price if hasattr(zone, 'entry_price') else zone.midpoint
                        strength = zone.strength if hasattr(zone, 'strength') else 0
                        response += f"\n<b>Zone {i}:</b> 📍 Entry {fmt_price(entry)}\n"
                        response += f"  • Range: {fmt_price(zone.low)} - {fmt_price(zone.high)}\n"
                        response += f"  • Strength: {strength:.0f}%\n"
                        
                        # Calculate SL and TP for shorts
                        zone_width = zone.high - zone.low
                        sl = zone.high + (zone_width * 0.5)
                        tp1 = current_price - (zone_width * 1.5)
                        tp2 = current_price - (zone_width * 2.5)
                        
                        response += f"  • 🛑 SL: {fmt_price(sl)}\n"
                        response += f"  • 🎯 TP1: {fmt_price(tp1)}\n"
                        response += f"  • 🎯 TP2: {fmt_price(tp2)}\n"
                else:
                    response += "\n🔴 <b>SUPPLY ZONES:</b> No active supply zones\n"

                # Add SMC Analysis
                try:
                    from smc_analyzer import smc_analyzer
                    from smc_formatter import format_smc_analysis
                    
                    smc_result = smc_analyzer.analyze(symbol, timeframe, limit=200)
                    smc_text = format_smc_analysis(smc_result, compact=False)
                    # Convert to HTML format (replace markdown with HTML tags)
                    smc_text = smc_text.replace('**', '<b>').replace('**', '</b>')
                    response += smc_text
                except Exception as e:
                    print(f"SMC analysis error: {e}")
                    # Continue without SMC if it fails

                # Add signal status
                response += f"\n⚡ <b>SIGNAL:</b>"
                if signal_type:
                    response += f" ✅ {signal_type}\n📊 Strength: {signal_strength:.0f}%\n"
                else:
                    response += f" ⏳ Awaiting confirmation\n"
                
                response += "\n<i>⚠️ Futures • LIMIT order at zone</i>"

                await update.message.reply_text(response, parse_mode='HTML')
                
            except ImportError:
                await update.message.reply_text(f"❌ SnD detector not available, please try again")
            except Exception as e:
                await update.message.reply_text(f"❌ Analysis error: {str(e)[:100]}")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:80]}")


    async def futures_signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle futures signals command"""
        try:
            from futures_signal_generator import FuturesSignalGenerator
            from menu_handler import get_estimated_time_message, get_user_timezone_from_context
            
            user_id = update.effective_user.id
            user_tz = get_user_timezone_from_context(context, user_id)
            est_time = get_estimated_time_message(10, user_tz)
            await update.message.reply_text(f"⏳ Generating multi-coin futures signals...\n{est_time}")

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
            from menu_handler import get_estimated_time_message, get_user_timezone_from_context
            
            user_id = update.effective_user.id
            user_tz = get_user_timezone_from_context(context, user_id)
            est_time = get_estimated_time_message(10, user_tz)
            await update.message.reply_text(f"⏳ Generating multi-coin futures signals...\n{est_time}")

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
            from menu_handler import get_estimated_time_message, get_user_timezone_from_context
            
            user_id = update.effective_user.id
            user_tz = get_user_timezone_from_context(context, user_id)
            est_time = get_estimated_time_message(5, user_tz)
            
            await query.answer("⏳ Generating signal...")
            await query.edit_message_text(f"⏳ Generating professional signal...\n{est_time}")

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
        """Handle credits command - fetch from Supabase with different response for premium users"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "User"

        # Get user language and credits from Supabase
        from services import get_database
        db = get_database()
        user_lang = db.get_user_language(user_id)
        
        # Check premium status
        from app.users_repo import is_premium_active
        is_premium = is_premium_active(user_id)
        
        # Fetch credits and user data from Supabase
        credits = 0
        is_lifetime = False
        premium_until = None
        has_autosignal = False
        autosignal_until = None
        automaton_credits = 0  # AUTOMATON credits
        
        try:
            from supabase_client import get_user as supabase_get_user
            user_data = supabase_get_user(user_id)
            if user_data:
                credits = user_data.get('credits', 0) or 0
                is_lifetime = user_data.get('is_lifetime', False)
                premium_until = user_data.get('premium_until')
                if user_data.get('first_name'):
                    user_name = user_data.get('first_name')
            else:
                credits = db.get_user_credits(user_id)
        except Exception as e:
            print(f"Error fetching credits from Supabase: {e}")
            credits = db.get_user_credits(user_id)
        
        # Fetch AUTOMATON credits from user_credits_balance table
        try:
            if db.supabase_enabled:
                from supabase_client import supabase
                if supabase:
                    credits_result = supabase.table('user_credits_balance')\
                        .select('available_credits')\
                        .eq('user_id', user_id)\
                        .execute()
                    
                    if credits_result.data:
                        automaton_credits = float(credits_result.data[0].get('available_credits', 0))
        except Exception as e:
            print(f"Error fetching AUTOMATON credits: {e}")
        
        # Check Auto Signal status from local JSON file
        try:
            import json
            import os
            from datetime import datetime
            autosignal_file = os.path.join(os.path.dirname(__file__), 'autosignal_users.json')
            if os.path.exists(autosignal_file):
                with open(autosignal_file, 'r') as f:
                    autosignal_data = json.load(f)
                user_autosignal = autosignal_data.get(str(user_id))
                if user_autosignal:
                    has_autosignal = user_autosignal.get('has_autosignal', False)
                    autosignal_until = user_autosignal.get('autosignal_until')
                    if autosignal_until:
                        expiry = datetime.fromisoformat(autosignal_until.replace('Z', '+00:00').replace('+00:00', ''))
                        if expiry < datetime.utcnow():
                            has_autosignal = False
        except Exception as e:
            print(f"Error reading autosignal data: {e}")

        if is_premium:
            # Premium user response
            if is_lifetime:
                premium_status = "♾️ LIFETIME"
                autosignal_text = "✔ Auto Signal: ♾️ SELAMANYA"
            elif premium_until:
                premium_status = f"⏳ Until: {str(premium_until)[:10]}"
                if has_autosignal and autosignal_until:
                    autosignal_text = f"✔ Auto Signal: ✅ Aktif (s/d {str(autosignal_until)[:10]})"
                else:
                    autosignal_text = "✔ Auto Signal: ❌ Tidak aktif"
            else:
                premium_status = "✅ Active"
                if has_autosignal and autosignal_until:
                    autosignal_text = f"✔ Auto Signal: ✅ Aktif (s/d {str(autosignal_until)[:10]})"
                else:
                    autosignal_text = "✔ Auto Signal: ❌ Tidak aktif"
            
            if user_lang == 'id':
                await update.effective_message.reply_text(
                    f"👑 <b>Status Premium Aktif</b>\n\n"
                    f"👤 Pengguna: {user_name}\n"
                    f"🆔 UID Telegram: <code>{user_id}</code>\n"
                    f"🏆 Status: {premium_status}\n\n"
                    f"💰 <b>Credits:</b>\n"
                    f"• Bot Credits: {credits:,}\n"
                    f"• AUTOMATON Credits: {automaton_credits:,.0f}\n\n"
                    f"✨ <b>Keuntungan Premium:</b>\n"
                    f"✔ Akses UNLIMITED ke semua fitur\n"
                    f"✔ Tidak membutuhkan kredit\n"
                    f"✔ Spot & Futures Analysis tanpa batas\n"
                    f"✔ Multi-Coin Signals tanpa batas\n"
                    f"{autosignal_text}\n\n"
                    f"🤖 <b>AUTOMATON Credits:</b>\n"
                    f"• Untuk AI Agent (autonomous trading)\n"
                    f"• Minimum spawn: 3.000 credits ($30)\n\n"
                    f"🎉 Nikmati semua fitur tanpa batasan!",
                    parse_mode='HTML'
                )
            else:
                autosignal_text_en = autosignal_text.replace("Aktif", "Active").replace("Tidak aktif", "Not active").replace("SELAMANYA", "FOREVER").replace("s/d", "until")
                await update.effective_message.reply_text(
                    f"👑 <b>Premium Status Active</b>\n\n"
                    f"👤 User: {user_name}\n"
                    f"🆔 Telegram UID: <code>{user_id}</code>\n"
                    f"🏆 Status: {premium_status}\n\n"
                    f"💰 <b>Credits:</b>\n"
                    f"• Bot Credits: {credits:,}\n"
                    f"• AUTOMATON Credits: {automaton_credits:,.0f}\n\n"
                    f"✨ <b>Premium Benefits:</b>\n"
                    f"✔ UNLIMITED access to all features\n"
                    f"✔ No credits required\n"
                    f"✔ Unlimited Spot & Futures Analysis\n"
                    f"✔ Unlimited Multi-Coin Signals\n"
                    f"{autosignal_text_en}\n\n"
                    f"🤖 <b>AUTOMATON Credits:</b>\n"
                    f"• For AI Agent (autonomous trading)\n"
                    f"• Minimum spawn: 3,000 credits ($30)\n\n"
                    f"🎉 Enjoy all features without limits!",
                    parse_mode='HTML'
                )
        else:
            # Free user response - also show Auto Signal status if they have it
            if has_autosignal and autosignal_until:
                autosignal_status_id = f"\n📡 <b>Auto Signal:</b> ✅ Aktif (s/d {str(autosignal_until)[:10]})"
                autosignal_status_en = f"\n📡 <b>Auto Signal:</b> ✅ Active (until {str(autosignal_until)[:10]})"
            else:
                autosignal_status_id = ""
                autosignal_status_en = ""
            
            if user_lang == 'id':
                await update.effective_message.reply_text(
                    f"💳 <b>Saldo Kredit</b>\n\n"
                    f"👤 Pengguna: {user_name}\n"
                    f"🆔 UID Telegram: <code>{user_id}</code>\n"
                    f"💰 Bot Credits: {credits}{autosignal_status_id}\n"
                    f"🤖 AUTOMATON Credits: {automaton_credits:,.0f}\n\n"
                    f"📊 <b>Biaya Bot Credits:</b>\n"
                    f"• Analisis Spot: 20 kredit\n"
                    f"• Analisis Futures: 20 kredit\n"
                    f"• Sinyal Multi-Coin: 60 kredit\n\n"
                    f"🤖 <b>AUTOMATON Credits:</b>\n"
                    f"• Untuk AI Agent (autonomous trading)\n"
                    f"• Minimum spawn: 3.000 credits ($30)\n"
                    f"• 1 USDC = 100 credits\n\n"
                    f"⭐ Upgrade ke Premium untuk akses unlimited!",
                    parse_mode='HTML'
                )
            else:
                await update.effective_message.reply_text(
                    f"💳 <b>Credit Balance</b>\n\n"
                    f"👤 User: {user_name}\n"
                    f"🆔 Telegram UID: <code>{user_id}</code>\n"
                    f"💰 Bot Credits: {credits}{autosignal_status_en}\n"
                    f"🤖 AUTOMATON Credits: {automaton_credits:,.0f}\n\n"
                    f"📊 <b>Bot Credit Costs:</b>\n"
                    f"• Spot Analysis: 20 credits\n"
                    f"• Futures Analysis: 20 credits\n"
                    f"• Multi-Coin Signals: 60 credits\n\n"
                    f"🤖 <b>AUTOMATON Credits:</b>\n"
                    f"• For AI Agent (autonomous trading)\n"
                    f"• Minimum spawn: 3,000 credits ($30)\n"
                    f"• 1 USDC = 100 credits\n\n"
                    f"⭐ Upgrade to Premium for unlimited access!",
                    parse_mode='HTML'
                )

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle subscribe command - NOW REDIRECTS TO OPENCLAW CREDITS"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        user_id = update.effective_user.id
        
        # Check if user already has premium/lifetime (legacy users)
        from services import get_database
        db = get_database()
        
        try:
            result = db.execute_query(
                "SELECT subscription_end, is_premium FROM users WHERE telegram_id = %s",
                (user_id,)
            )
            
            if result and len(result) > 0:
                subscription_end = result[0][0]
                is_premium = result[0][1]
                
                # Check if legacy premium/lifetime user
                if subscription_end and is_premium:
                    from datetime import datetime
                    if subscription_end > datetime.now():
                        legacy_message = (
                            "👑 <b>Legacy Premium User</b>\n\n"
                            "You still have active premium subscription.\n"
                            "Your premium features remain active.\n\n"
                            "For new AI features, check out OpenClaw Credits below!"
                        )
                        await update.message.reply_text(legacy_message, parse_mode='HTML')
        except:
            pass
        
        subscription_text = f"""🤖 <b>CryptoMentor AI 3.0 – OpenClaw Credits</b>

<b>🎯 NEW: OpenClaw AI Assistant</b>
Powered by Claude Sonnet 4.5 - Your Personal AI Trading Assistant

<b>💡 What is OpenClaw?</b>
• 🧠 Advanced AI conversations
• 📊 Real-time crypto market analysis
• 🔍 Smart trading insights
• 💬 Natural language interface
• 🚀 Autonomous agent capabilities

<b>💰 PRICING (Pay-as-you-go)</b>

Credits = OpenRouter API Balance (Real-time)
Minimum Top-Up: <b>Rp 100.000</b> (~$7 USD)

<b>Recommended Amounts:</b>
• Rp 100.000 → ~$7 credits
• Rp 200.000 → ~$14 credits
• Rp 500.000 → ~$35 credits
• Rp 1.000.000 → ~$70 credits

<b>💳 PAYMENT METHODS</b>

🏦 <b>Transfer Bank (IDR)</b>
Nama: NABIL FARREL AL FARI
Bank: Mandiri
No Rek: 1560018407074

📱 <b>E-Money (IDR)</b>
ShopeePay / GoPay / DANA
📞 0877-7927-4400

⛓️ <b>Crypto (USD)</b>
Network: BEP20 (Binance Smart Chain)
Address:
<code>0xed7342ac9c22b1495af4d63f15a7c9768a028ea8</code>

Supported: USDT, USDC, BNB (BEP20 only!)

<b>✅ HOW TO TOP-UP</b>

1️⃣ Choose amount (min. Rp 100.000)
2️⃣ Send payment via Bank/E-Money/Crypto
3️⃣ Send proof to admin: 👉 @BillFarr
4️⃣ Include this info:

✅ Amount: Rp XXX.XXX
✅ Your UID: <code>{user_id}</code>
✅ Purpose: OpenClaw Credits

5️⃣ Credits added after verification!

<b>📊 CHECK BALANCE</b>
Use: /openclaw_balance

<b>🚀 START USING</b>
Just chat normally - OpenClaw is now default!
No commands needed, just type your question.

<b>📌 NOTES</b>
• Credits shared across all users
• Real-time sync with OpenRouter
• Admin manually adds credits
• No subscription needed
• Pay only for what you use

<b>🎁 LEGACY USERS</b>
Existing Premium/Lifetime users:
Your subscription remains active for old features.
OpenClaw is separate pay-as-you-go system.

---

<b>💡 Quick Start:</b>
1. Top-up credits (min. Rp 100k)
2. Start chatting with AI
3. Get trading insights instantly!"""
        
        keyboard = [
            [InlineKeyboardButton("💰 Top-Up Credits", callback_data="deposit_start")],
            [InlineKeyboardButton("💳 Check Balance", callback_data="balance_check")],
            [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/BillFarr")],
        ]
        
        await update.effective_message.reply_text(
            subscription_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

    async def openclaw_balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show OpenClaw credit balance"""
        user_id = update.effective_user.id
        
        try:
            from services import get_database
            from app.openclaw_manager import get_openclaw_manager
            
            db = get_database()
            manager = get_openclaw_manager(db)
            
            # Get credits
            credits = manager.get_user_credits(user_id)
            
            # Get assistants
            assistants = manager.get_user_assistants(user_id)
            
            # Get total usage stats
            total_tokens = 0
            total_spent = 0
            for assistant in assistants:
                total_tokens += assistant.get('total_tokens_used', 0)
                total_spent += float(assistant.get('total_credits_spent', 0))
            
            await update.message.reply_text(
                f"💰 **OpenClaw Credit Balance**\n\n"
                f"👤 User: {update.effective_user.first_name}\n"
                f"🆔 ID: `{user_id}`\n\n"
                f"💳 **Credits:** {credits:,}\n"
                f"🤖 **Assistants:** {len(assistants)}\n"
                f"📊 **Total Tokens Used:** {total_tokens:,}\n"
                f"💸 **Total Spent:** {total_spent:,.0f} credits\n\n"
                f"💰 **Purchase:** /openclaw_buy\n"
                f"📚 **Help:** /openclaw_help",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Error:** {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    async def openclaw_history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show conversation history"""
        user_id = update.effective_user.id
        
        try:
            from services import get_database
            from app.openclaw_manager import get_openclaw_manager
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            db = get_database()
            manager = get_openclaw_manager(db)
            
            # Get conversations
            conversations = manager.get_user_conversations(user_id, limit=10)
            
            if not conversations:
                await update.message.reply_text(
                    "📚 **No Conversations Yet**\n\n"
                    "Start chatting with your AI Assistant:\n"
                    "/openclaw_start",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Build conversation list
            text = "📚 **Recent Conversations**\n\n"
            
            for i, conv in enumerate(conversations, 1):
                assistant_name = conv.get('assistant_name', 'Unknown')
                message_count = conv.get('message_count', 0)
                total_credits = float(conv.get('total_credits_spent', 0))
                updated_at = str(conv.get('updated_at', ''))[:16]
                
                text += f"{i}. 🤖 {assistant_name}\n"
                text += f"   💬 {message_count} messages • 💰 {total_credits:.0f} credits\n"
                text += f"   🕐 {updated_at}\n\n"
            
            text += "\n💡 Start new chat: /openclaw_start"
            
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Error:** {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle referral command with enhanced tier system"""
        from services import get_database
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "User"

        # Get bot username for referral link
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username or "CryptoMentorAI_bot"

        try:
            db = get_database()

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
                from services import get_database
                db = get_database()
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
            from services import get_database
            db = get_database()

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
        from services import get_database
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

        db = get_database()
        user_tz = db.get_user_timezone(user_id)
        tz_offsets = {'WIB': 7, 'WITA': 8, 'WIT': 9, 'SGT': 8, 'MYT': 8, 'GST': 4, 'GMT': 0, 'EST': -5, 'PST': -8}
        offset = tz_offsets.get(user_tz, 7)
        local_time = (datetime.utcnow() + timedelta(hours=offset)).strftime('%H:%M:%S')

        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        admin_panel_text = f"""**CryptoMentorAI V3.0** | Admin Panel

• 📊 **STATUS**
⏰ {local_time} {user_tz}
🟢 ONLINE • Uptime: {uptime_str}
{level_emoji} {level_name}
🆔 `{user_id}`
"""

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("🗄 Database Status", callback_data="admin_db_status")],
            [InlineKeyboardButton("👥 User Management", callback_data="admin_user_mgmt")],
            [InlineKeyboardButton("⚙️ Admin Settings", callback_data="admin_settings")],
            [InlineKeyboardButton("💎 Premium Control", callback_data="admin_premium")],
            [InlineKeyboardButton("📊 Signal Tracking", callback_data="admin_signal_tracking")],
            [InlineKeyboardButton("💰 Reset All Credits", callback_data="admin_reset_credits")]
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
                lifetime_users = 0
                active_today = 0
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

                    try:
                        lifetime_result = sb_client.table('users').select('id', count='exact').eq('is_lifetime', True).execute()
                        lifetime_users = lifetime_result.count if lifetime_result.count else 0
                    except Exception as le:
                        print(f"[DB STATUS] Lifetime query error: {le}")
                        lifetime_users = 0

                    from datetime import datetime
                    try:
                        today = datetime.utcnow().date().isoformat()
                        active_result = sb_client.table('users').select('id', count='exact').gte('last_active', today).execute()
                        active_today = active_result.count if active_result.count else 0
                    except:
                        active_today = 0
                else:
                    print(f"[DB STATUS] Health check failed: {status_msg}")

                import sqlite3
                import os
                local_users = 0
                try:
                    sqlite_path = os.path.join(os.path.dirname(__file__), 'cryptomentor.db')
                    if os.path.exists(sqlite_path):
                        conn = sqlite3.connect(sqlite_path)
                        cursor = conn.cursor()
                        cursor.execute('SELECT COUNT(*) FROM users')
                        local_users = cursor.fetchone()[0]
                        conn.close()
                except Exception as le:
                    print(f"[DB STATUS] Local SQLite error: {le}")
                    local_users = 0

                combined_users = total_users + local_users

                db_text = f"""🗄 **Database Status**

**Connection**
{connection_status} Supabase
 📡 Region: Southeast Asia

**Users**
 👥 Total Users: {combined_users}
   ☁️ Supabase (New): {total_users}
   💾 Local DB (Old): {local_users}
 👑 Premium Users: {premium_users}
 ♾️ Lifetime Users: {lifetime_users}
 🟢 Active Today: {active_today}

**Storage**
 ☁️ Supabase: users, portfolios, referrals
 💾 SQLite: cryptomentor.db
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

        elif query.data == "admin_user_mgmt":
            user_mgmt_text = """**👥 User Management**

• **Available Actions:**
 🔍 Search User - Find user by ID/username
 📋 List Users - View recent users
 🚫 Ban/Unban - Manage user access
 📊 User Stats - View detailed statistics

_Select an action below:_
"""
            keyboard = [
                [InlineKeyboardButton("🔍 Search User", callback_data="admin_search_user")],
                [InlineKeyboardButton("📋 List Users", callback_data="admin_list_users")],
                [InlineKeyboardButton("🚫 Ban/Unban User", callback_data="admin_ban_user")],
                [InlineKeyboardButton("◀️ Back", callback_data="admin_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(user_mgmt_text, reply_markup=reply_markup, parse_mode='MARKDOWN')

        elif query.data == "admin_settings":
            settings_text = """**⚙️ Admin Settings**

• **Configuration Options:**
 🔔 Notifications - Toggle admin alerts
 🌐 Bot Settings - Configure bot behavior
 📢 Broadcast - Send message to all users
 📊 Database Stats - View broadcast statistics
 🔄 Restart Bot - Restart bot service

_Select an option below:_
"""
            keyboard = [
                [InlineKeyboardButton("🔔 Notifications", callback_data="admin_notif")],
                [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
                [InlineKeyboardButton("📊 Database Stats", callback_data="admin_db_stats")],
                [InlineKeyboardButton("🔄 Restart Bot", callback_data="admin_restart")],
                [InlineKeyboardButton("◀️ Back", callback_data="admin_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(settings_text, reply_markup=reply_markup, parse_mode='MARKDOWN')

        elif query.data == "admin_premium":
            premium_text = """**💎 Premium Control**

• **Premium Management:**
 ➕ Add Premium - Grant premium access
 ➖ Remove Premium - Revoke premium
 ♾️ Set Lifetime - Grant lifetime access
 🎁 Manage Credits - Add or reset credits (bot features)
 🤖 Manage AUTOMATON Credits - For AI Agent deposits

_Select an action below:_
"""
            keyboard = [
                [InlineKeyboardButton("➕ Add Premium", callback_data="admin_add_premium")],
                [InlineKeyboardButton("➖ Remove Premium", callback_data="admin_remove_premium")],
                [InlineKeyboardButton("♾️ Set Lifetime", callback_data="admin_set_lifetime")],
                [InlineKeyboardButton("📡 Grant Auto Signal", callback_data="admin_grant_autosignal")],
                [InlineKeyboardButton("🎁 Manage Credits", callback_data="admin_add_credits")],
                [InlineKeyboardButton("🤖 Manage AUTOMATON Credits", callback_data="admin_automaton_credits")],
                [InlineKeyboardButton("◀️ Back", callback_data="admin_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(premium_text, reply_markup=reply_markup, parse_mode='MARKDOWN')

        elif query.data == "admin_add_premium":
            msg = await query.edit_message_text(
                "📝 **Add Premium Access**\n\n"
                "🆔 Reply with user ID and days (e.g., `123456789 30`)\n"
                "Or just user ID for 30 days default",
                parse_mode='MARKDOWN',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_premium")]])
            )
            context.user_data['awaiting_input'] = 'admin_add_premium'
            context.user_data['message_id'] = msg.message_id
            context.user_data['state_timestamp'] = time.time()

        elif query.data == "admin_remove_premium":
            msg = await query.edit_message_text(
                "📝 **Remove Premium Access**\n\n"
                "🆔 Reply with user ID",
                parse_mode='MARKDOWN',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_premium")]])
            )
            context.user_data['awaiting_input'] = 'admin_remove_premium'
            context.user_data['message_id'] = msg.message_id
            context.user_data['state_timestamp'] = time.time()

        elif query.data == "admin_set_lifetime":
            msg = await query.edit_message_text(
                "📝 **Set Lifetime Access**\n\n"
                "🆔 Reply with user ID to grant lifetime premium",
                parse_mode='MARKDOWN',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_premium")]])
            )
            context.user_data['awaiting_input'] = 'admin_set_lifetime'
            context.user_data['message_id'] = msg.message_id
            context.user_data['state_timestamp'] = time.time()

        elif query.data == "admin_grant_autosignal":
            msg = await query.edit_message_text(
                "📡 **Grant Auto Signal Access**\n\n"
                "🆔 Reply with: `user_id days`\n\n"
                "Example: `123456789 30` → 30 days\n"
                "Example: `123456789` → default 30 days\n\n"
                "⚠️ Akses akan berakhir sesuai waktu yang ditentukan\n"
                "💡 Works even for non-premium users!",
                parse_mode='MARKDOWN',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_premium")]])
            )
            context.user_data['awaiting_input'] = 'admin_grant_autosignal'
            context.user_data['message_id'] = msg.message_id
            context.user_data['state_timestamp'] = time.time()

        elif query.data == "admin_add_credits":
            credits_text = """**🎁 Manage Credits**

Choose an action:
"""
            keyboard = [
                [InlineKeyboardButton("➕ Add Credits to User", callback_data="admin_add_credits_manual")],
                [InlineKeyboardButton("🔄 Reset Users Below 100", callback_data="admin_reset_users_credits")],
                [InlineKeyboardButton("◀️ Back", callback_data="admin_premium")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(credits_text, reply_markup=reply_markup, parse_mode='MARKDOWN')

        elif query.data == "admin_automaton_credits":
            automaton_credits_text = """**🤖 Manage AUTOMATON Credits**

⚠️ **PENTING:** Ini untuk AUTOMATON credits (AI Agent), bukan credits bot biasa!

**AUTOMATON Credits:**
• Untuk AI Agent (autonomous trading)
• Deposit USDC → Manual verification
• 1 USDC = 100 AUTOMATON credits
• Minimum: $30 USDC (3,000 credits)

**Regular Bot Credits:**
• Untuk /analyze, /futures, /ai
• Gunakan menu "🎁 Manage Credits"

Choose an action:
"""
            keyboard = [
                [InlineKeyboardButton("➕ Add AUTOMATON Credits", callback_data="admin_add_automaton_credits_manual")],
                [InlineKeyboardButton("🔍 Check AUTOMATON Credits", callback_data="admin_check_automaton_credits_manual")],
                [InlineKeyboardButton("📖 View Guide", callback_data="admin_automaton_guide")],
                [InlineKeyboardButton("◀️ Back", callback_data="admin_premium")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(automaton_credits_text, reply_markup=reply_markup, parse_mode='MARKDOWN')

        elif query.data == "admin_add_automaton_credits_manual":
            msg = await query.edit_message_text(
                "📝 **Add AUTOMATON Credits to User**\n\n"
                "🆔 Reply with: `user_id amount note`\n\n"
                "**Example:**\n"
                "`123456789 3000 Deposit $30 USDC verified`\n\n"
                "**Conversion:**\n"
                "• 1 USDC = 100 credits\n"
                "• $30 = 3,000 credits\n"
                "• $50 = 5,000 credits\n\n"
                "⚠️ **PENTING:** Ini untuk AUTOMATON credits (AI Agent)!",
                parse_mode='MARKDOWN',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_automaton_credits")]])
            )
            context.user_data['awaiting_input'] = 'admin_add_automaton_credits_manual'
            context.user_data['message_id'] = msg.message_id
            context.user_data['state_timestamp'] = time.time()

        elif query.data == "admin_check_automaton_credits_manual":
            msg = await query.edit_message_text(
                "🔍 **Check AUTOMATON Credits**\n\n"
                "🆔 Reply with user ID to check their AUTOMATON credits\n\n"
                "**Example:** `123456789`\n\n"
                "⚠️ **PENTING:** Ini cek AUTOMATON credits (AI Agent)!",
                parse_mode='MARKDOWN',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_automaton_credits")]])
            )
            context.user_data['awaiting_input'] = 'admin_check_automaton_credits_manual'
            context.user_data['message_id'] = msg.message_id
            context.user_data['state_timestamp'] = time.time()

        elif query.data == "admin_automaton_guide":
            guide_text = """📖 **AUTOMATON Credits Guide**

**2 Jenis Credits:**

1️⃣ **Regular Bot Credits** (🎁 Manage Credits)
   • Untuk: /analyze, /futures, /ai
   • Command: /grant_credits

2️⃣ **AUTOMATON Credits** (🤖 Manage AUTOMATON Credits)
   • Untuk: AI Agent, spawn agent
   • Command: /admin_add_automaton_credits

**Cara Pakai:**

**User deposit USDC untuk AI Agent:**
1. User kirim bukti transfer
2. Verify di blockchain (Base Network)
3. Add AUTOMATON credits via menu ini
4. User receive notification

**User minta credits untuk /analyze:**
1. Gunakan menu "🎁 Manage Credits"
2. Add regular bot credits

**⚠️ JANGAN SAMPAI TERTUKAR!**

**Quick Commands:**
• Add AUTOMATON: `/admin_add_automaton_credits <id> <amount> <note>`
• Check AUTOMATON: `/admin_check_automaton_credits <id>`
• Add Regular: `/grant_credits <id> <amount>`
"""
            keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="admin_automaton_credits")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(guide_text, reply_markup=reply_markup, parse_mode='MARKDOWN')

        elif query.data == "admin_add_credits_manual":
            msg = await query.edit_message_text(
                "📝 **Add Credits to User**\n\n"
                "🆔 Reply with user ID and credits (e.g., `123456789 100`)",
                parse_mode='MARKDOWN',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_add_credits")]])
            )
            context.user_data['awaiting_input'] = 'admin_add_credits_manual'
            context.user_data['message_id'] = msg.message_id
            context.user_data['state_timestamp'] = time.time()

        elif query.data == "admin_reset_users_credits":
            await self.handle_admin_reset_below_100(query, context)

        elif query.data == "admin_reset_users_credits_confirm":
            await self.handle_admin_reset_below_100_confirm(query, context)

        elif query.data == "admin_reset_credits":
            await self.handle_admin_reset_credits(query, context)

        elif query.data == "admin_reset_credits_confirm":
            await self.handle_admin_reset_credits_confirm(query, context)

        elif query.data == "admin_signal_tracking":
            # Signal Tracking submenu
            from app.signal_tracker_integration import get_current_winrate
            from app.signal_logger import signal_logger
            from pathlib import Path
            import os
            
            # Get stats
            stats = get_current_winrate(7)
            
            # Count files
            log_dir = Path("signal_logs")
            total_prompts = 0
            active_signals = 0
            completed_signals = 0
            
            try:
                prompt_files = list(log_dir.glob("prompts_*.jsonl"))
                for file in prompt_files:
                    with open(file, "r") as f:
                        total_prompts += sum(1 for _ in f)
                
                active_file = log_dir / "active_signals.jsonl"
                if active_file.exists():
                    with open(active_file, "r") as f:
                        active_signals = sum(1 for _ in f)
                
                completed_file = log_dir / "completed_signals.jsonl"
                if completed_file.exists():
                    with open(completed_file, "r") as f:
                        completed_signals = sum(1 for _ in f)
            except Exception as e:
                print(f"Error counting files: {e}")
            
            # Get storage status
            use_gdrive = os.getenv('USE_GDRIVE', 'true').lower() == 'true'
            storage_type = "Unknown"
            storage_status = "❌ Disabled"
            
            if use_gdrive and os.path.exists('G:/'):
                storage_type = "G: Drive (Local)"
                storage_status = "✅ Enabled"
            else:
                try:
                    from app.supabase_storage import supabase_storage
                    if supabase_storage.enabled:
                        storage_type = "Supabase Storage (Cloud)"
                        storage_status = "✅ Enabled"
                except:
                    pass
            
            # Build stats text
            winrate_text = "No data"
            if stats:
                winrate_text = f"{stats['winrate']}% ({stats['wins']}W/{stats['losses']}L)"
            
            tracking_text = f"""📊 **Signal Tracking Dashboard**

**📈 Performance (7 Days)**
• Winrate: {winrate_text}
• Total Signals: {stats['total_signals'] if stats else 0}
• Avg PnL: {stats['avg_pnl']:+.2f}% if stats else 'N/A'

**📝 Data Stored**
• User Prompts: {total_prompts}
• Active Signals: {active_signals}
• Completed: {completed_signals}

**☁️ Storage**
• Type: {storage_type}
• Status: {storage_status}

_Select an action below:_
"""
            
            keyboard = [
                [InlineKeyboardButton("📊 View Stats", callback_data="admin_st_stats")],
                [InlineKeyboardButton("📈 Winrate 7d", callback_data="admin_st_winrate_7")],
                [InlineKeyboardButton("📈 Winrate 30d", callback_data="admin_st_winrate_30")],
                [InlineKeyboardButton("📄 Weekly Report", callback_data="admin_st_report")],
                [InlineKeyboardButton("☁️ Upload Logs", callback_data="admin_st_upload")],
                [InlineKeyboardButton("◀️ Back", callback_data="admin_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(tracking_text, reply_markup=reply_markup, parse_mode='MARKDOWN')

        elif query.data == "admin_st_stats":
            # Show detailed statistics
            from app.handlers_signal_tracking import cmd_signal_stats
            # Call the command handler directly
            await cmd_signal_stats(update, context)

        elif query.data == "admin_st_winrate_7":
            # Show 7-day winrate
            from app.signal_tracker_integration import get_current_winrate
            stats = get_current_winrate(7)
            
            if not stats:
                await query.answer("❌ No winrate data available", show_alert=True)
                return
            
            winrate_text = f"""📊 **WINRATE SIGNAL (7 HARI)**

━━━━━━━━━━━━━━━━━━━━━━

📈 **STATISTIK:**
• Total Signal: {stats['total_signals']}
• Win: {stats['wins']} ✅
• Loss: {stats['losses']} ❌
• Winrate: {stats['winrate']}% 🎯
• Avg PnL: {stats['avg_pnl']:+.2f}%

━━━━━━━━━━━━━━━━━━━━━━
"""
            
            keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="admin_signal_tracking")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(winrate_text, reply_markup=reply_markup, parse_mode='MARKDOWN')

        elif query.data == "admin_st_winrate_30":
            # Show 30-day winrate
            from app.signal_tracker_integration import get_current_winrate
            stats = get_current_winrate(30)
            
            if not stats:
                await query.answer("❌ No winrate data available", show_alert=True)
                return
            
            winrate_text = f"""📊 **WINRATE SIGNAL (30 HARI)**

━━━━━━━━━━━━━━━━━━━━━━

📈 **STATISTIK:**
• Total Signal: {stats['total_signals']}
• Win: {stats['wins']} ✅
• Loss: {stats['losses']} ❌
• Winrate: {stats['winrate']}% 🎯
• Avg PnL: {stats['avg_pnl']:+.2f}%

━━━━━━━━━━━━━━━━━━━━━━
"""
            
            keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="admin_signal_tracking")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(winrate_text, reply_markup=reply_markup, parse_mode='MARKDOWN')

        elif query.data == "admin_st_report":
            # Generate weekly report
            await query.answer("⏳ Generating report...", show_alert=False)
            
            try:
                from app.weekly_report import weekly_reporter
                report = await weekly_reporter.generate_report()
                
                keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="admin_signal_tracking")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(report, reply_markup=reply_markup, parse_mode='MARKDOWN')
            except Exception as e:
                await query.answer(f"❌ Error: {str(e)[:100]}", show_alert=True)

        elif query.data == "admin_st_upload":
            # Upload logs to storage
            await query.answer("⏳ Uploading logs...", show_alert=False)
            
            try:
                import os
                use_gdrive = os.getenv('USE_GDRIVE', 'true').lower() == 'true'
                
                if use_gdrive and os.path.exists('G:/'):
                    from app.local_gdrive_sync import local_gdrive_sync
                    synced, failed = local_gdrive_sync.sync_all_logs()
                    result_text = f"""✅ **G: Drive Sync Complete!**

📊 Synced: {synced} files
❌ Failed: {failed} files
"""
                else:
                    from app.supabase_storage import supabase_storage
                    uploaded, failed = supabase_storage.upload_all_logs()
                    result_text = f"""✅ **Supabase Upload Complete!**

📊 Uploaded: {uploaded} files
❌ Failed: {failed} files
"""
                
                keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="admin_signal_tracking")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode='MARKDOWN')
            except Exception as e:
                await query.answer(f"❌ Error: {str(e)[:100]}", show_alert=True)

        elif query.data == "admin_search_user":
            msg = await query.edit_message_text(
                "🔍 **Search User**\n\n"
                "Enter user ID or username to search:",
                parse_mode='MARKDOWN',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_user_mgmt")]])
            )
            context.user_data['awaiting_input'] = 'admin_search_user'
            context.user_data['message_id'] = msg.message_id
            context.user_data['state_timestamp'] = time.time()

        elif query.data == "admin_list_users":
            from services import get_database
            db = get_database()
            try:
                # Get last 10 users
                users = db.get_recent_users(limit=10)
                if users:
                    user_text = "📋 **Recent Users**\n\n"
                    for i, user in enumerate(users, 1):
                        user_text += f"{i}. {user.get('first_name', 'Unknown')}\n"
                        user_text += f"   🆔 {user.get('telegram_id')}\n"
                        user_text += f"   💰 Credits: {user.get('credits', 0)}\n"
                        user_text += f"   📅 Created: {user.get('created_at', 'N/A')[:10]}\n\n"
                else:
                    user_text = "📭 No users found"
                
                keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="admin_user_mgmt")]]
                await query.edit_message_text(
                    user_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='MARKDOWN'
                )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ Error loading users: {str(e)}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="admin_user_mgmt")]]),
                    parse_mode='MARKDOWN'
                )

        elif query.data == "admin_ban_user":
            msg = await query.edit_message_text(
                "🚫 **Ban/Unban User**\n\n"
                "Enter user ID to ban/unban:",
                parse_mode='MARKDOWN',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_user_mgmt")]])
            )
            context.user_data['awaiting_input'] = 'admin_ban_user'
            context.user_data['message_id'] = msg.message_id
            context.user_data['state_timestamp'] = time.time()

        elif query.data == "admin_notif":
            notif_text = """🔔 **Notifications Settings**

Current status: Admin alerts enabled

Choose action:
"""
            keyboard = [
                [InlineKeyboardButton("✅ Enable", callback_data="admin_notif_enable")],
                [InlineKeyboardButton("❌ Disable", callback_data="admin_notif_disable")],
                [InlineKeyboardButton("◀️ Back", callback_data="admin_settings")]
            ]
            await query.edit_message_text(
                notif_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='MARKDOWN'
            )

        elif query.data == "admin_notif_enable":
            context.user_data['admin_notifications'] = True
            await query.edit_message_text(
                "✅ **Notifications Enabled**\n\nAdmin alerts are now ON",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="admin_settings")]]),
                parse_mode='MARKDOWN'
            )

        elif query.data == "admin_notif_disable":
            context.user_data['admin_notifications'] = False
            await query.edit_message_text(
                "❌ **Notifications Disabled**\n\nAdmin alerts are now OFF",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="admin_settings")]]),
                parse_mode='MARKDOWN'
            )

        elif query.data == "admin_broadcast":
            # Get real-time user count
            try:
                from services import get_database
                db = get_database()
                broadcast_data = db.get_all_broadcast_users()
                user_count = broadcast_data['stats']['total_unique']
                
                # Log for debugging
                print(f"[Broadcast] User count: {user_count}")
                print(f"[Broadcast] Local: {broadcast_data['stats']['local_count']}, "
                      f"Supabase: {broadcast_data['stats']['supabase_count']}")
            except Exception as e:
                print(f"[Broadcast] Error getting user count: {e}")
                user_count = "unknown"
            
            msg = await query.edit_message_text(
                "📢 **Broadcast Message**\n\n"
                "Type your message to send to ALL users:\n\n"
                f"⚠️ This will reach {user_count} users!",
                parse_mode='MARKDOWN',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_settings")]])
            )
            context.user_data['awaiting_input'] = 'admin_broadcast'
            context.user_data['message_id'] = msg.message_id
            context.user_data['state_timestamp'] = time.time()  # Add timestamp to prevent stale state detection

        elif query.data == "admin_db_stats":
            # Show database statistics
            try:
                from app.admin_status import format_database_stats
                stats_text = format_database_stats()
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Refresh", callback_data="admin_db_stats")],
                    [InlineKeyboardButton("◀️ Back", callback_data="admin_settings")]
                ]
                
                await query.edit_message_text(
                    stats_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='MARKDOWN'
                )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ **Error loading database stats**\n\n{str(e)}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="admin_settings")]]),
                    parse_mode='MARKDOWN'
                )

        elif query.data == "admin_restart":
            restart_text = """🔄 **Restart Bot Service**

⚠️ **WARNING:**
• Bot will go OFFLINE for ~10-15 seconds
• All active connections will be terminated
• Pending operations may be lost
• Users cannot use bot during restart

❓ **Are you sure?**"""
            keyboard = [
                [InlineKeyboardButton("✅ YES - Restart Now", callback_data="admin_restart_confirm")],
                [InlineKeyboardButton("❌ Cancel", callback_data="admin_settings")]
            ]
            await query.edit_message_text(
                restart_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='MARKDOWN'
            )

        elif query.data == "admin_restart_confirm":
            await query.edit_message_text(
                "🔄 **Restarting bot...**\n\n"
                "⏳ Please wait...",
                parse_mode='MARKDOWN'
            )
            import os
            import sys
            print("[ADMIN] Bot restart initiated")
            os.execv(sys.executable, ['python'] + sys.argv)

        elif query.data == "admin_back":
            from services import get_database
            from datetime import datetime, timedelta

            level_emoji = {1: "👑", 2: "🔷", 3: "🔶"}.get(admin_level, "👤")
            level_name = {1: "ADMIN 1 (Owner)", 2: "ADMIN 2 (Manager)", 3: "ADMIN 3 (Moderator)"}.get(admin_level, "UNKNOWN")

            db = get_database()
            user_tz = db.get_user_timezone(user_id)
            tz_offsets = {'WIB': 7, 'WITA': 8, 'WIT': 9, 'SGT': 8, 'MYT': 8, 'GST': 4, 'GMT': 0, 'EST': -5, 'PST': -8}
            offset = tz_offsets.get(user_tz, 7)
            local_time = (datetime.utcnow() + timedelta(hours=offset)).strftime('%H:%M:%S')

            uptime_seconds = int(time.time() - self.start_time)
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours}h {minutes}m {seconds}s"

            admin_panel_text = f"""**CryptoMentorAI V3.0** | Admin Panel

• 📊 **STATUS**
⏰ {local_time} {user_tz}
🟢 ONLINE • Uptime: {uptime_str}
{level_emoji} {level_name}
🆔 `{user_id}`
"""

            keyboard = [
                [InlineKeyboardButton("🗄 Database Status", callback_data="admin_db_status")],
                [InlineKeyboardButton("👥 User Management", callback_data="admin_user_mgmt")],
                [InlineKeyboardButton("⚙️ Admin Settings", callback_data="admin_settings")],
                [InlineKeyboardButton("💎 Premium Control", callback_data="admin_premium")],
                [InlineKeyboardButton("💰 Reset All Credits", callback_data="admin_reset_credits")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                admin_panel_text,
                reply_markup=reply_markup,
                parse_mode='MARKDOWN'
            )

    async def handle_admin_reset_credits(self, query, context):
        """Show reset credits confirmation"""
        from services import get_database
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        try:
            # Get current user counts
            db = get_database()
            local_stats = db.get_user_stats()

            supabase_users = 0
            try:
                from supabase_client import get_live_user_count
                supabase_users = get_live_user_count()
            except:
                pass

            warning_text = f"""⚠️ **RESET ALL CREDITS - CONFIRMATION REQUIRED**

🎯 **Action:** Set 200 credits for ALL users
📊 **Scope:** Both Local SQLite & Supabase databases

📈 **Current User Count:**
• 📁 Local SQLite: {local_stats['total_users']} users
• ☁️ Supabase: {supabase_users} users
• 💎 Premium users: Will keep unlimited access

⚠️ **WARNING:**
• This will reset ALL free users to 200 credits
• Premium users are unaffected
• Action cannot be undone
• Both databases will be updated

❓ **Are you sure you want to proceed?**"""

            keyboard = [
                [InlineKeyboardButton("✅ YES - Reset All Credits to 200", callback_data="admin_reset_credits_confirm")],
                [InlineKeyboardButton("❌ Cancel", callback_data="admin_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                warning_text,
                reply_markup=reply_markup,
                parse_mode='MARKDOWN'
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error loading reset credits page: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]),
                parse_mode='MARKDOWN'
            )

    async def handle_admin_reset_credits_confirm(self, query, context):
        """Execute reset credits for all users to 200"""
        from services import get_database
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        try:
            # Show processing message
            await query.edit_message_text(
                "⏳ **Processing credit reset to 200...**\n\n"
                "📁 Updating Local SQLite database...\n"
                "☁️ Updating Supabase database...\n\n"
                "Please wait...",
                parse_mode='MARKDOWN'
            )

            db = get_database()
            local_updated = 0
            supabase_updated = 0
            errors = []

            # 1. Reset credits in Local SQLite to 200
            try:
                local_updated = db.set_all_user_credits(200)
                print(f"✅ Local SQLite: Updated {local_updated} users to 200 credits")
            except Exception as e:
                errors.append(f"Local SQLite error: {str(e)}")
                print(f"❌ Local SQLite error: {e}")

            # 2. Reset credits in Supabase to 200
            try:
                from supabase_client import supabase
                if supabase:
                    # Try RPC function first
                    try:
                        result = supabase.rpc('reset_all_user_credits', {'p_amount': 200}).execute()
                        supabase_updated = result.data if isinstance(result.data, int) else 0
                        print(f"✅ Supabase RPC: Updated {supabase_updated} users to 200 credits")
                    except Exception as rpc_error:
                        # Fallback: direct table update
                        print(f"⚠️ RPC not available, using direct update: {rpc_error}")
                        result = supabase.table('users').update({'credits': 200}).or_('is_premium.is.null,is_premium.eq.false').execute()
                        supabase_updated = len(result.data) if result.data else 0
                        print(f"✅ Supabase direct: Updated {supabase_updated} users to 200 credits")
                else:
                    errors.append("Supabase client not available")
            except Exception as e:
                errors.append(f"Supabase error: {str(e)}")
                print(f"❌ Supabase error: {e}")

            # 3. Log the admin action
            admin_id = query.from_user.id
            db.log_user_activity(
                admin_id,
                "admin_reset_all_credits",
                f"Reset credits to 200: Local:{local_updated}, Supabase:{supabase_updated}"
            )

            # 4. Show results
            if errors:
                result_text = f"""⚠️ **CREDIT RESET COMPLETED WITH WARNINGS**

✅ **Successfully Updated:**
• 📁 Local SQLite: {local_updated} users
• ☁️ Supabase: {supabase_updated} users
• 💰 New Balance: 200 credits

❌ **Errors Encountered:**
"""
                for error in errors:
                    result_text += f"• {error}\n"

                result_text += "\n💡 Check console logs for more details."
            else:
                result_text = f"""✅ **CREDIT RESET COMPLETED SUCCESSFULLY**

📊 **Updated User Counts:**
• 📁 Local SQLite: {local_updated} users
• ☁️ Supabase: {supabase_updated} users
• 💰 New Credit Balance: 200 for all free users

🎯 All users now have 200 credits
👑 Premium users maintain unlimited access"""

            keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_back")]]

            await query.edit_message_text(
                result_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='MARKDOWN'
            )

        except Exception as e:
            await query.edit_message_text(
                f"❌ **CRITICAL ERROR**\n\n"
                f"Failed to reset credits: {str(e)}\n\n"
                f"Please check console logs for details.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]),
                parse_mode='MARKDOWN'
            )

    async def handle_admin_reset_below_100(self, query, context):
        """Show confirmation for resetting credits ONLY for users below 100"""
        from services import get_database
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        try:
            db = get_database()

            # Count users below 100 credits in local DB
            try:
                db.cursor.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE credits < 100 
                    AND (is_premium = 0 OR is_premium IS NULL)
                """)
                local_below_100 = db.cursor.fetchone()[0]
            except:
                local_below_100 = 0

            # Count users below 100 in Supabase
            supabase_below_100 = 0
            try:
                from supabase_client import supabase
                if supabase:
                    # Use or_ filter to handle NULL and false values for is_premium
                    result = supabase.table('users').select('telegram_id', count='exact').lt('credits', 100).or_('is_premium.is.null,is_premium.eq.false').execute()
                    supabase_below_100 = result.count if result.count else 0
            except Exception as e:
                print(f"Supabase count error: {e}")
                pass

            warning_text = f"""⚠️ **RESET CREDITS BELOW 100 - CONFIRMATION**

🎯 **Action:** Set 100 credits for users with < 100 credits
📊 **Scope:** Both Local SQLite & Supabase databases

📈 **Users Below 100 Credits:**
• 📁 Local SQLite: {local_below_100} users
• ☁️ Supabase: {supabase_below_100} users

💡 **Note:**
• Only users with credits < 100 will be affected
• Users with 100+ credits will NOT change
• Premium users are unaffected

❓ **Are you sure you want to proceed?**"""

            keyboard = [
                [InlineKeyboardButton("✅ YES - Reset Users Below 100", callback_data="admin_reset_users_credits_confirm")],
                [InlineKeyboardButton("❌ Cancel", callback_data="admin_add_credits")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                warning_text,
                reply_markup=reply_markup,
                parse_mode='MARKDOWN'
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_add_credits")]]),
                parse_mode='MARKDOWN'
            )

    async def handle_admin_reset_below_100_confirm(self, query, context):
        """Execute reset credits for users below 100"""
        from services import get_database
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        try:
            await query.edit_message_text(
                "⏳ **Processing...**\n\n"
                "📁 Updating Local SQLite (users < 100 credits)...\n"
                "☁️ Updating Supabase (users < 100 credits)...",
                parse_mode='MARKDOWN'
            )

            db = get_database()
            local_updated = 0
            supabase_updated = 0
            errors = []

            # 1. Reset credits in Local SQLite (only users below 100)
            try:
                local_updated = db.reset_credits_below_threshold(threshold=100, new_amount=100)
                print(f"✅ Local SQLite: Reset {local_updated} users below 100")
            except Exception as e:
                errors.append(f"Local SQLite: {str(e)}")
                print(f"❌ Local SQLite error: {e}")

            # 2. Reset credits in Supabase (only users below 100)
            try:
                from supabase_client import supabase
                if supabase:
                    # Try RPC first
                    try:
                        result = supabase.rpc('reset_credits_below_threshold', {
                            'p_threshold': 100,
                            'p_new_amount': 100
                        }).execute()
                        supabase_updated = result.data if isinstance(result.data, int) else 0
                        print(f"✅ Supabase RPC: Reset {supabase_updated} users")
                    except Exception as rpc_error:
                        # Fallback: direct table update with proper NULL handling
                        print(f"⚠️ RPC not available, using direct update: {rpc_error}")
                        # Update users where credits < 100 AND (is_premium is NULL OR is_premium = false)
                        result = supabase.table('users').update({'credits': 100}).lt('credits', 100).or_('is_premium.is.null,is_premium.eq.false').execute()
                        supabase_updated = len(result.data) if result.data else 0
                        print(f"✅ Supabase direct: Updated {supabase_updated} users")
                else:
                    errors.append("Supabase client not available")
            except Exception as e:
                errors.append(f"Supabase: {str(e)}")
                print(f"❌ Supabase error: {e}")

            # 3. Log admin action
            admin_id = query.from_user.id
            db.log_user_activity(
                admin_id,
                "admin_reset_credits_below_100",
                f"Reset credits < 100: Local:{local_updated}, Supabase:{supabase_updated}"
            )

            # 4. Show results
            if errors:
                result_text = f"""⚠️ **COMPLETED WITH WARNINGS**

✅ **Updated Users (credits < 100):**
• 📁 Local SQLite: {local_updated} users
• ☁️ Supabase: {supabase_updated} users

❌ **Errors:**
"""
                for error in errors:
                    result_text += f"• {error}\n"
            else:
                result_text = f"""✅ **RESET BELOW 100 COMPLETED**

📊 **Updated Users:**
• 📁 Local SQLite: {local_updated} users
• ☁️ Supabase: {supabase_updated} users
• 💰 New Balance: 100 credits

✅ All users with < 100 credits now have 100 credits"""

            keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_add_credits")]]

            await query.edit_message_text(
                result_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='MARKDOWN'
            )

        except Exception as e:
            await query.edit_message_text(
                f"❌ **ERROR:** {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_add_credits")]]),
                parse_mode='MARKDOWN'
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages - DEFAULT: Route to OpenClaw AI Assistant"""
        # CRITICAL: Store user's chat_id for autosignal delivery (on any interaction)
        if update.effective_user and update.effective_chat:
            from app.chat_store import remember_chat
            remember_chat(update.effective_user.id, update.effective_chat.id)
        
        # PRIORITY 0: Check if user is admin - auto-activate OpenClaw
        try:
            from services import get_database
            from app.openclaw_manager import get_openclaw_manager
            from app.openclaw_admin_handler import get_openclaw_admin_handler
            
            db = get_database()
            openclaw_manager = get_openclaw_manager(db)
            admin_handler = get_openclaw_admin_handler(openclaw_manager)
            
            # Try to auto-activate for admin
            await admin_handler.handle_admin_message(update, context)
        except Exception as e:
            logger.debug(f"Admin handler skipped: {e}")
        
        # PRIORITY 1: DEFAULT MODE - Route ALL messages to OpenClaw AI Assistant
        try:
            from services import get_database
            from app.openclaw_manager import get_openclaw_manager
            from app.openclaw_message_handler import get_openclaw_message_handler
            from app.openclaw_agent_tools import get_openclaw_agent_tools
            from app.openclaw_agent_loop import get_openclaw_agentic_loop
            
            db = get_database()
            openclaw_manager = get_openclaw_manager(db)
            
            # Initialize autonomous agent components
            agent_tools = get_openclaw_agent_tools(db, self.application)
            agentic_loop = get_openclaw_agentic_loop(openclaw_manager, agent_tools)
            
            # Create message handler with agentic loop
            openclaw_handler = get_openclaw_message_handler(openclaw_manager)
            openclaw_handler.agentic_loop = agentic_loop  # Inject agentic loop
            
            # Handle with OpenClaw (will auto-create session if needed)
            handled = await openclaw_handler.handle_message(update, context)
            if handled:
                # Message was handled by OpenClaw AI Assistant (with autonomous capabilities)
                return
        except Exception as e:
            # OpenClaw error - show error to user
            logger.error(f"OpenClaw handler error: {e}")
            await update.message.reply_text(
                "❌ OpenClaw AI Assistant temporarily unavailable.\n\n"
                "Please try again or use /menu for other features.",
                parse_mode=None
            )
            return
        
        user_data = context.user_data
        text = update.message.text
        
        # Add timestamp to track when state was created
        # If no timestamp exists, this is likely a stale state from before restart
        if user_data and not user_data.get('state_timestamp'):
            # Check if user has any awaiting states
            has_awaiting_state = any(
                key.startswith('awaiting_') or key == 'action' 
                for key in user_data.keys()
            )
            
            if has_awaiting_state:
                # Clear stale state
                print(f"🔄 Clearing stale state for user {update.effective_user.id}")
                user_data.clear()
                
                # Inform user
                await update.message.reply_text(
                    "⚠️ Bot telah direstart. Command sebelumnya dibatalkan.\n\n"
                    "Silakan gunakan /menu atau /start untuk memulai kembali.",
                    parse_mode='Markdown'
                )
                return
        
        # Set timestamp for new states (will be set by command handlers)
        # This is just a safety check

        # Handle withdrawal details input
        if user_data.get('awaiting_withdrawal_details'):
            try:
                from menu_handlers import MenuCallbackHandler
                handler = MenuCallbackHandler(self)
                await handler.process_withdrawal_details(update, context)
                return
            except Exception as e:
                print(f"Error processing withdrawal details: {e}")
                user_data['awaiting_withdrawal_details'] = False
                await update.message.reply_text(
                    "Terjadi kesalahan. Silakan coba lagi dari menu Referral Program."
                )
                return

        # Handle agent name input for spawn_agent
        if user_data.get('awaiting_agent_name') and user_data.get('action') == 'spawn_agent':
            agent_name = text.strip()
            
            # Clear the awaiting state
            user_data.pop('awaiting_agent_name', None)
            user_data.pop('action', None)
            user_data.pop('state_timestamp', None)
            
            try:
                # Import spawn agent handler
                from app.handlers_automaton import spawn_agent_command
                
                # Create fake context with args (agent name)
                context.args = agent_name.split()  # Split in case of multi-word names
                
                # Call the spawn agent command
                await spawn_agent_command(update, context)
                return
                
            except Exception as e:
                print(f"❌ Error spawning agent: {e}")
                import traceback
                traceback.print_exc()
                await update.message.reply_text(
                    f"❌ Error: {str(e)[:100]}\n\n"
                    f"Silakan coba lagi dengan /spawn_agent <nama_agent>",
                    parse_mode='Markdown'
                )
                return

        # Handle admin inputs
        awaiting = user_data.get('awaiting_input')
        
        # Debug logging
        if awaiting:
            print(f"🔍 DEBUG: awaiting_input = {awaiting}")
            print(f"🔍 DEBUG: text = {text[:100]}")
        
        if awaiting == 'admin_broadcast':
            broadcast_msg = text.strip()
            from services import get_database
            db = get_database()
            try:
                # Use enhanced broadcast user fetching
                broadcast_data = db.get_all_broadcast_users()
                all_user_ids = broadcast_data['unique_ids']
                stats = broadcast_data['stats']
                
                total_unique = stats['total_unique']
                
                if total_unique == 0:
                    await update.message.reply_text(
                        "❌ No users found for broadcast!",
                        parse_mode='HTML'
                    )
                    user_data.pop('awaiting_input', None)
                    user_data.pop('message_id', None)
                    return
                
                print(f"📢 Broadcast: {stats['local_count']} local, "
                      f"{stats['supabase_count']} supabase, "
                      f"{total_unique} unique users")
                
                # Send progress message
                progress_msg = await update.message.reply_text(
                    f"📤 <b>Broadcasting...</b>\n\n"
                    f"📊 <b>Target Users:</b>\n"
                    f"• Local DB: {stats['local_count']}\n"
                    f"• Supabase: {stats['supabase_count']} ({stats['supabase_unique']} unique)\n"
                    f"• Total Unique: {total_unique}\n"
                    f"• Duplicates: {stats['duplicates']}\n\n"
                    f"⏳ Starting broadcast...",
                    parse_mode='HTML'
                )
                
                success_count = 0
                fail_count = 0
                blocked_count = 0
                
                # Broadcast with rate limiting
                import asyncio
                batch_size = 30  # Send 30 messages per second (Telegram limit)
                
                user_list = list(all_user_ids)
                for i in range(0, len(user_list), batch_size):
                    batch = user_list[i:i+batch_size]
                    
                    for user_id in batch:
                        try:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=f"📢 <b>Admin Broadcast</b>\n\n{broadcast_msg}",
                                parse_mode='HTML'
                            )
                            success_count += 1
                        except Exception as e:
                            error_msg = str(e).lower()
                            if 'blocked' in error_msg or 'forbidden' in error_msg or 'chat not found' in error_msg:
                                blocked_count += 1
                            fail_count += 1
                            # Only log first few errors to avoid spam
                            if fail_count <= 10:
                                print(f"Failed to send to {user_id}: {e}")
                    
                    # Update progress every 3 batches (90 messages)
                    if i % (batch_size * 3) == 0 and i > 0:
                        try:
                            progress_pct = (i / total_unique) * 100
                            await progress_msg.edit_text(
                                f"📤 <b>Broadcasting...</b>\n\n"
                                f"📊 <b>Progress:</b> {i}/{total_unique} ({progress_pct:.1f}%)\n"
                                f"✉️ Sent: {success_count}\n"
                                f"🚫 Blocked: {blocked_count}\n"
                                f"❌ Failed: {fail_count - blocked_count}",
                                parse_mode='HTML'
                            )
                        except:
                            pass
                    
                    # Rate limiting - wait 1 second between batches
                    if i + batch_size < len(user_list):
                        await asyncio.sleep(1)
                
                # Calculate success rate
                success_rate = (success_count / total_unique * 100) if total_unique > 0 else 0
                
                # Final report with detailed stats
                await progress_msg.edit_text(
                    f"✅ <b>Broadcast Complete!</b>\n\n"
                    f"📊 <b>Database Stats:</b>\n"
                    f"• Local DB: {stats['local_count']} users\n"
                    f"• Supabase: {stats['supabase_count']} users\n"
                    f"• Supabase Unique: {stats['supabase_unique']} users\n"
                    f"• Duplicates Removed: {stats['duplicates']}\n"
                    f"• Total Unique: {total_unique} users\n\n"
                    f"📤 <b>Delivery Results:</b>\n"
                    f"✉️ Successfully sent: {success_count}\n"
                    f"🚫 Blocked bot: {blocked_count}\n"
                    f"❌ Other failures: {fail_count - blocked_count}\n"
                    f"📊 Total attempts: {total_unique}\n\n"
                    f"📈 <b>Success Rate:</b> {success_rate:.1f}%\n\n"
                    f"💡 <b>Note:</b> Users who blocked the bot or deleted their account cannot receive messages.",
                    parse_mode='HTML'
                )
                
                # Log broadcast activity
                try:
                    db.log_admin_activity(
                        admin_id=update.effective_user.id,
                        action="broadcast",
                        details=f"Sent to {success_count}/{total_unique} users. Success rate: {success_rate:.1f}%"
                    )
                except:
                    pass
                    
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"Broadcast error: {error_trace}")
                await update.message.reply_text(
                    f"❌ <b>Broadcast failed</b>\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Please check logs for details.",
                    parse_mode='HTML'
                )
            user_data.pop('awaiting_input', None)
            user_data.pop('message_id', None)
            return

        if awaiting in ['admin_add_premium', 'admin_remove_premium', 'admin_set_lifetime', 'admin_grant_autosignal', 'admin_add_credits_manual', 'admin_search_user', 'admin_ban_user', 'admin_add_automaton_credits_manual', 'admin_check_automaton_credits_manual']:
            from services import get_database
            from datetime import datetime, timedelta
            
            parts = text.strip().split()
            try:
                if awaiting == 'admin_search_user':
                    search_query = parts[0]
                    db = get_database()
                    user = db.search_user(search_query)
                    if user:
                        user_text = f"""🔍 **User Found**

🆔 User ID: {user.get('telegram_id')}
📝 Name: {user.get('first_name')} {user.get('last_name', '')}
👤 Username: @{user.get('username', 'N/A')}
💰 Credits: {user.get('credits', 0)}
👑 Premium: {'Yes' if user.get('is_premium') else 'No'}
♾️ Lifetime: {'Yes' if user.get('is_lifetime') else 'No'}
🚫 Banned: {'Yes' if user.get('banned') else 'No'}
📅 Created: {user.get('created_at', 'N/A')[:10]}"""
                        await update.message.reply_text(user_text, parse_mode='MARKDOWN')
                    else:
                        await update.message.reply_text("❌ User not found!", parse_mode='MARKDOWN')
                
                elif awaiting == 'admin_ban_user':
                    user_id = int(parts[0])
                    db = get_database()
                    user = db.search_user(str(user_id))
                    if user:
                        if user.get('banned'):
                            db.unban_user(user_id)
                            await update.message.reply_text(
                                f"✅ User unbanned!\n\n"
                                f"🆔 User: {user_id}",
                                parse_mode='MARKDOWN'
                            )
                        else:
                            db.ban_user(user_id)
                            await update.message.reply_text(
                                f"✅ User banned!\n\n"
                                f"🆔 User: {user_id}",
                                parse_mode='MARKDOWN'
                            )
                    else:
                        await update.message.reply_text("❌ User not found!", parse_mode='MARKDOWN')
                
                else:
                    user_id = int(parts[0])
                    db = get_database()
                    
                    if awaiting == 'admin_add_premium':
                        days = int(parts[1]) if len(parts) > 1 else 30
                        premium_until = datetime.utcnow() + timedelta(days=days)
                        db.add_user_premium(user_id, premium_until)
                        
                        try:
                            from app.supabase_repo import set_premium_normalized
                            result = set_premium_normalized(user_id, f"{days}d")
                            supabase_status = f"✅ Supabase: is_premium={result.get('is_premium')}, until={str(result.get('premium_until', ''))[:10]}"
                        except Exception as e:
                            supabase_status = f"⚠️ Supabase error: {str(e)[:50]}"
                        
                        await update.message.reply_text(
                            f"✅ Premium access added!\n\n"
                            f"🆔 User: {user_id}\n"
                            f"📅 Days: {days}\n"
                            f"⏰ Until: {premium_until.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            f"📊 Database Sync:\n"
                            f"✅ Local DB: Updated\n"
                            f"{supabase_status}"
                        )
                        
                        try:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=f"🎉 <b>Selamat! Anda Mendapat Premium!</b>\n\n"
                                     f"👑 Status: <b>PREMIUM MEMBER</b>\n"
                                     f"📅 Durasi: {days} hari\n"
                                     f"⏰ Berlaku hingga: {premium_until.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                     f"✨ <b>Keuntungan Premium:</b>\n"
                                     f"✔ Akses UNLIMITED ke semua fitur\n"
                                     f"✔ Tidak membutuhkan kredit\n"
                                     f"✔ Spot & Futures Analysis tanpa batas\n"
                                     f"✔ Multi-Coin Signals tanpa batas\n\n"
                                     f"🚀 Nikmati semua fitur premium sekarang!",
                                parse_mode='HTML'
                            )
                        except Exception as e:
                            print(f"Failed to notify user {user_id}: {e}")
                    
                    elif awaiting == 'admin_remove_premium':
                        db.remove_user_premium(user_id)
                        
                        try:
                            from app.supabase_repo import revoke_premium
                            result = revoke_premium(user_id)
                            supabase_status = f"✅ Supabase: is_premium={result.get('is_premium')}, is_lifetime={result.get('is_lifetime')}"
                        except Exception as e:
                            supabase_status = f"⚠️ Supabase error: {str(e)[:50]}"
                        
                        await update.message.reply_text(
                            f"✅ Premium access removed!\n\n"
                            f"🆔 User: {user_id}\n\n"
                            f"📊 Database Sync:\n"
                            f"✅ Local DB: Updated\n"
                            f"{supabase_status}"
                        )
                    
                    elif awaiting == 'admin_set_lifetime':
                        db.set_user_lifetime(user_id, True)
                        
                        try:
                            from app.supabase_repo import set_premium_normalized
                            result = set_premium_normalized(user_id, 'lifetime')
                            supabase_status = f"✅ Supabase: is_premium={result.get('is_premium')}, is_lifetime={result.get('is_lifetime')}"
                        except Exception as e:
                            supabase_status = f"⚠️ Supabase error: {str(e)[:50]}"
                        
                        await update.message.reply_text(
                            f"✅ Lifetime access granted!\n\n"
                            f"🆔 User: {user_id}\n"
                            f"♾️ Status: Lifetime Premium\n\n"
                            f"📊 Database Sync:\n"
                            f"✅ Local DB: Updated\n"
                            f"{supabase_status}"
                        )
                        
                        try:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=f"🎉 <b>Selamat! Anda Mendapat LIFETIME Premium!</b>\n\n"
                                     f"♾️ Status: <b>LIFETIME MEMBER</b>\n"
                                     f"📅 Durasi: SELAMANYA\n\n"
                                     f"✨ <b>Keuntungan Lifetime:</b>\n"
                                     f"✔ Akses UNLIMITED ke semua fitur SELAMANYA\n"
                                     f"✔ Tidak membutuhkan kredit\n"
                                     f"✔ Spot & Futures Analysis tanpa batas\n"
                                     f"✔ Multi-Coin Signals tanpa batas\n"
                                     f"✔ Auto Signal access SELAMANYA\n\n"
                                     f"🚀 Terima kasih telah menjadi member Lifetime!",
                                parse_mode='HTML'
                            )
                        except Exception as e:
                            print(f"Failed to notify user {user_id}: {e}")
                    
                    elif awaiting == 'admin_grant_autosignal':
                        days = int(parts[1]) if len(parts) > 1 else 30
                        expiry_date = datetime.utcnow() + timedelta(days=days)
                        
                        db_status = "❌ Not saved"
                        try:
                            import json
                            import os
                            autosignal_file = os.path.join(os.path.dirname(__file__), 'autosignal_users.json')
                            
                            if os.path.exists(autosignal_file):
                                with open(autosignal_file, 'r') as f:
                                    autosignal_data = json.load(f)
                            else:
                                autosignal_data = {}
                            
                            autosignal_data[str(user_id)] = {
                                'has_autosignal': True,
                                'autosignal_until': expiry_date.isoformat(),
                                'granted_at': datetime.utcnow().isoformat()
                            }
                            
                            with open(autosignal_file, 'w') as f:
                                json.dump(autosignal_data, f, indent=2)
                            
                            db_status = f"✅ Local DB: Auto Signal granted until {expiry_date.strftime('%Y-%m-%d')}"
                        except Exception as e:
                            db_status = f"⚠️ Error: {str(e)[:50]}"
                        
                        await update.message.reply_text(
                            f"✅ Auto Signal access granted!\n\n"
                            f"🆔 User: {user_id}\n"
                            f"📡 Feature: Auto Signal\n"
                            f"📅 Days: {days}\n"
                            f"⏰ Until: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            f"📊 Status:\n"
                            f"{db_status}"
                        )
                        
                        try:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=f"🎉 <b>Selamat! Anda Mendapat Akses Auto Signal!</b>\n\n"
                                     f"📡 Feature: <b>AUTO SIGNAL</b>\n"
                                     f"📅 Durasi: {days} hari\n"
                                     f"⏰ Berlaku hingga: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                     f"✨ <b>Keuntungan Auto Signal:</b>\n"
                                     f"✔ Terima sinyal trading otomatis\n"
                                     f"✔ Notifikasi langsung ke chat Anda\n"
                                     f"✔ Supply & Demand zone alerts\n\n"
                                     f"🚀 Gunakan /credits untuk cek status!",
                                parse_mode='HTML'
                            )
                        except Exception as e:
                            print(f"Failed to notify user {user_id}: {e}")
                    
                    elif awaiting == 'admin_add_credits_manual':
                        credits = int(parts[1]) if len(parts) > 1 else 100
                        db.add_user_credits(user_id, credits)
                        await update.message.reply_text(
                            f"✅ Credits added!\n\n"
                            f"🆔 User: {user_id}\n"
                            f"💰 Added: {credits}",
                            parse_mode='MARKDOWN'
                        )
                    
                    elif awaiting == 'admin_add_automaton_credits_manual':
                        # Format: user_id amount note
                        print(f"🎯 AUTOMATON CREDITS HANDLER TRIGGERED!")
                        print(f"   Parts: {parts}")
                        print(f"   User ID from parts[0]: {parts[0] if parts else 'NO PARTS'}")
                        
                        if len(parts) < 3:
                            print(f"❌ Not enough parts: {len(parts)}")
                            await update.message.reply_text(
                                "❌ Format salah!\n\n"
                                "Format: `user_id amount note`\n"
                                "Contoh: `123456789 3000 Deposit $30 USDC verified`",
                                parse_mode='MARKDOWN'
                            )
                            return
                        
                        try:
                            amount = float(parts[1])
                            note = ' '.join(parts[2:])
                            
                            print(f"🔧 Admin adding AUTOMATON credits: user_id={user_id}, amount={amount}, note={note}")
                            
                            # Call the admin command function
                            from app.handlers_admin_credits import admin_add_automaton_credits_command
                            
                            # Create fake context with args
                            context.args = [str(user_id), str(amount), note]
                            await admin_add_automaton_credits_command(update, context)
                        except Exception as e:
                            print(f"❌ Error adding AUTOMATON credits: {e}")
                            await update.message.reply_text(
                                f"❌ Error: {str(e)[:200]}\n\n"
                                f"Silakan coba lagi atau gunakan command:\n"
                                f"`/admin_add_automaton_credits {user_id} {parts[1] if len(parts) > 1 else '3000'} {' '.join(parts[2:]) if len(parts) > 2 else 'Manual'}`",
                                parse_mode='MARKDOWN'
                            )
                    
                    elif awaiting == 'admin_check_automaton_credits_manual':
                        # Call the admin command function
                        try:
                            print(f"🔧 Admin checking AUTOMATON credits: user_id={user_id}")
                            
                            from app.handlers_admin_credits import admin_check_automaton_credits_command
                            
                            # Create fake context with args
                            context.args = [str(user_id)]
                            await admin_check_automaton_credits_command(update, context)
                        except Exception as e:
                            print(f"❌ Error checking AUTOMATON credits: {e}")
                            await update.message.reply_text(
                                f"❌ Error: {str(e)[:200]}\n\n"
                                f"Silakan coba lagi atau gunakan command:\n"
                                f"`/admin_check_automaton_credits {user_id}`",
                                parse_mode='MARKDOWN'
                            )
                
                user_data.pop('awaiting_input', None)
                user_data.pop('message_id', None)
                return  # Stop processing after handling admin input
                
            except (ValueError, IndexError):
                await update.message.reply_text(
                    "❌ Invalid format! Please check your input and try again.",
                    parse_mode='MARKDOWN'
                )
                return  # Stop processing after error
            return

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
                    f"Select timeframe: 15m, 30m, 1h, 4h, 1d",
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

        # Handle AI chat input
        elif user_data.get('action') == 'ai_chat' and user_data.get('awaiting_input'):
            question = text.strip()
            user_data.clear()
            
            try:
                # Import DeepSeek handler
                from app.handlers_deepseek import handle_ai_chat
                
                # Create fake context with args
                context.args = question.split()  # Split into words for args
                
                # Call handler
                await handle_ai_chat(update, context)
                
            except Exception as e:
                print(f"Error calling AI chat: {e}")
                import traceback
                traceback.print_exc()
                await update.message.reply_text(
                    f"❌ Error: {str(e)}\n\nSilakan coba lagi dengan `/chat <pertanyaan>`",
                    parse_mode='Markdown'
                )

        # Handle AI analyze input
        elif user_data.get('action') == 'ai_analyze' and user_data.get('awaiting_input'):
            symbol = text.strip().upper()
            user_data.clear()
            
            try:
                # Import DeepSeek handler
                from app.handlers_deepseek import handle_ai_analyze
                
                # Create fake context with args
                context.args = [symbol]
                
                # Call handler
                await handle_ai_analyze(update, context)
                
            except Exception as e:
                print(f"Error calling AI analyze: {e}")
                import traceback
                traceback.print_exc()
                await update.message.reply_text(
                    f"❌ Error: {str(e)}\n\nSilakan coba lagi dengan `/ai <symbol>`",
                    parse_mode='Markdown'
                )

        # Handle AI questions (legacy)
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

            # Add error handler to catch all exceptions
            async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
                """Log errors caused by updates"""
                logger.error(f"❌ Exception while handling update {update}:")
                logger.error(f"   Error: {context.error}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                print(f"❌ ERROR in update handler: {context.error}")
                print(f"   Update: {update}")
            
            self.application.add_error_handler(error_handler)
            print("✅ Error handler registered")

            # Initialize and start polling
            await self.application.initialize()
            await self.application.start()

            print("🚀 CryptoMentor AI Bot is running...")
            print(f"🤖 Bot username: @{(await self.application.bot.get_me()).username}")
            print("🔄 Polling for updates...")

            # Start polling - DON'T drop pending updates to see what's there
            await self.application.updater.start_polling(
                poll_interval=1.0,
                timeout=30,
                drop_pending_updates=False  # Changed to False to process pending updates
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

            # Initialize App AutoSignal scheduler (FAST version - no AI)
            try:
                from app.autosignal_fast import start_background_scheduler
                start_background_scheduler(self.application)
                print("📡 App AutoSignal scheduler started (FAST mode)")
            except Exception as e:
                print(f"⚠️ App AutoSignal scheduler failed to start: {e}")
            
            # Initialize Automaton Background Services
            try:
                from app.background_services import get_background_services
                from services import get_database
                db = get_database()
                self.background_services = get_background_services(db, self.application.bot)
                await self.background_services.start()
                print("🤖 Automaton Background Services started")
            except Exception as e:
                print(f"⚠️ Automaton Background Services failed to start: {e}")

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
            # Stop background services
            if hasattr(self, 'background_services'):
                try:
                    await self.background_services.stop()
                    print("✅ Background services stopped")
                except Exception as e:
                    print(f"⚠️ Error stopping background services: {e}")
            
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