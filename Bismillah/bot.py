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
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN not found in environment variables")

        self.application = None
        self.admin_ids = self._load_admin_ids()
        
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
        self.application.add_handler(CommandHandler("portfolio", self.portfolio_command))
        self.application.add_handler(CommandHandler("credits", self.credits_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("referral", self.referral_command))
        self.application.add_handler(CommandHandler("language", self.language_command))
        self.application.add_handler(CommandHandler("id", self.id_command))
        
        # Admin command handler
        self.application.add_handler(CommandHandler("admin", self.admin_command))

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
        """Handle /start command with menu integration"""
        user = update.effective_user

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

        try:
            from crypto_api import crypto_api

            # Get real price data
            price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)

            if 'error' in price_data:
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
            await update.effective_message.reply_text(
                f"❌ **Price Error**: {str(e)[:100]}\n\n"
                f"💡 Try: `/price btc` or `/price eth`",
                parse_mode='MARKDOWN'
            )

    async def market_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle market overview command with real Binance data"""
        try:
            from crypto_api import crypto_api
            from datetime import datetime
            from pytz import timezone as tz_module
            
            # Fetch market data in parallel (5 pairs)
            market_data = crypto_api.get_market_overview_fast()
            
            if not market_data.get('success', False):
                await update.effective_message.reply_text(
                    f"❌ **Market Data Error**\n\nFailed to fetch market data",
                    parse_mode='MARKDOWN'
                )
                return
            
            # Format market overview
            pairs = market_data.get('pairs', [])
            sentiment = market_data.get('sentiment', 'UNKNOWN')
            
            # Sentiment emoji
            sentiment_emoji = '🟢' if sentiment == 'BULLISH' else ('🟡' if sentiment == 'NEUTRAL' else '🔴')
            
            # Build pairs summary
            pairs_lines = []
            for pair in pairs:
                emoji = pair.get('emoji', '○')
                symbol = pair.get('symbol', 'N/A')
                price = pair.get('price', 0)
                change = pair.get('change_24h', 0)
                volume = pair.get('volume_24h', 0)
                
                # Format price
                if price >= 1:
                    price_str = f"${price:,.0f}" if price > 1000 else f"${price:.2f}"
                else:
                    price_str = f"${price:.6f}"
                
                # Format change
                change_str = f"{'+' if change > 0 else ''}{change:.2f}%"
                change_emoji = '📈' if change > 0 else ('📉' if change < 0 else '➡️')
                
                # Format volume
                if volume > 1_000_000_000:
                    volume_str = f"${volume/1_000_000_000:.1f}B"
                elif volume > 1_000_000:
                    volume_str = f"${volume/1_000_000:.1f}M"
                else:
                    volume_str = f"${volume/1_000:,.0f}K"
                
                pair_line = f"{emoji} **{symbol}**: {price_str} | {change_emoji} {change_str} | 📊 {volume_str}"
                pairs_lines.append(pair_line)
            
            pairs_text = "\n".join(pairs_lines)
            current_time = datetime.now(tz_module('Asia/Jakarta')).strftime('%H:%M:%S')
            
            message_text = f"""🌍 **GLOBAL MARKET OVERVIEW**

⏰ {current_time} WIB

📊 **Market Sentiment:** {sentiment_emoji} **{sentiment}**

--------------------

{pairs_text}

--------------------

💡 *Data from Binance Spot Market*"""
            
            await update.effective_message.reply_text(
                message_text,
                parse_mode='MARKDOWN'
            )
            
        except Exception as e:
            logger.error(f"Market command error: {e}", exc_info=True)
            await update.effective_message.reply_text(
                f"❌ **Error**: {str(e)[:100]}",
                parse_mode='MARKDOWN'
            )

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
                "❌ **Usage:** `/futures <symbol> <timeframe>`\n\n"
                "**Example:** `/futures BTC 1h`\n"
                "**Timeframes:** 15m, 30m, 1h, 4h, 1d, 1w",
                parse_mode='MARKDOWN'
            )
            return

        symbol = context.args[0].upper()
        timeframe = context.args[1].lower()

        # Placeholder for AI Assistant and Crypto API
        # In a real scenario, these would be initialized or passed in
        self.ai_assistant = AIAssistant() # Assuming AIAssistant is available and can be instantiated like this
        from crypto_api import crypto_api # Assuming crypto_api is available
        self.crypto_api = crypto_api

        # Assuming ProgressTracker and safe_send_message are available
        # For demonstration, defining dummy versions if not imported
        class ProgressTracker:
            async def update_progress(self, message):
                pass

        async def safe_send_message(bot, chat_id, text):
            try:
                await bot.send_message(chat_id=chat_id, text=text, parse_mode='MARKDOWN')
            except Exception as e:
                print(f"Error sending message: {e}")

        # Handle /futures command
        try:
            user_id = update.effective_user.id
            args = context.args

            print(f"🔍 Futures command called by user {user_id} with args: {args}")

            symbol = args[0].upper() if args else 'BTC'
            timeframe = args[1] if len(args) > 1 else '4h'

            print(f"📊 Processing futures analysis for {symbol} on {timeframe}")

            # Create progress tracker
            message = await update.message.reply_text("⏳ Analyzing futures signals...")
            progress_tracker = ProgressTracker()

            # Get analysis with error handling
            try:
                analysis = await self.ai_assistant.get_futures_analysis(
                    symbol, timeframe, 'id', self.crypto_api, progress_tracker, user_id
                )
                print(f"✅ Analysis generated successfully for {symbol}")
            except Exception as analysis_error:
                print(f"❌ Analysis generation failed: {analysis_error}")
                analysis = f"❌ Analysis failed for {symbol}: {str(analysis_error)[:100]}..."

            # Send result
            await safe_send_message(context.bot, update.effective_chat.id, analysis)
            print(f"📤 Message sent to user {user_id}")

        except Exception as e:
            error_msg = f"❌ Error in futures analysis: {str(e)[:100]}..."
            await update.message.reply_text(error_msg)
            print(f"❌ Futures command error: {e}")
            import traceback
            traceback.print_exc()


    async def futures_signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle futures signals command"""
        # Placeholder for AI Assistant and Crypto API
        # In a real scenario, these would be initialized or passed in
        try:
            from ai_assistant import AIAssistant
            from crypto_api import crypto_api
            self.ai_assistant = AIAssistant()
            self.crypto_api = crypto_api

            # Assuming ProgressTracker and safe_send_message are available
            class ProgressTracker:
                async def update_progress(self, message):
                    pass

            async def safe_send_message(bot, chat_id, text):
                try:
                    await bot.send_message(chat_id=chat_id, text=text, parse_mode='MARKDOWN')
                except Exception as e:
                    print(f"Error sending message: {e}")

            user_id = update.effective_user.id
            print(f"🔍 Futures signals command called by user {user_id}")

            # Create progress tracker
            message = await update.message.reply_text("⏳ Generating multi-coin futures signals...")
            progress_tracker = ProgressTracker()

            # Get signals with error handling
            try:
                signals = await self.ai_assistant.generate_futures_signals(
                    'id', self.crypto_api, context.args, progress_tracker
                )
                print("✅ Multi-coin futures signals generated successfully")
            except Exception as signal_error:
                print(f"❌ Signal generation failed: {signal_error}")
                signals = f"❌ Signal generation failed: {str(signal_error)[:100]}..."

            # Send result
            await safe_send_message(context.bot, update.effective_chat.id, signals)
            print(f"📤 Message sent to user {user_id}")

        except Exception as e:
            error_msg = f"❌ Error in futures signals: {str(e)[:100]}..."
            await update.message.reply_text(error_msg)
            print(f"❌ Futures signals command error: {e}")
            import traceback
            traceback.print_exc()


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
        credits = 100  # Placeholder

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
        """Handle referral command"""
        user_id = update.effective_user.id
        referral_link = f"https://t.me/your_bot?start={user_id}"

        await update.effective_message.reply_text(
            f"🎁 **Referral Program**\n\n"
            f"👥 **Your Referral Link:**\n"
            f"`{referral_link}`\n\n"
            f"💰 **Rewards:**\n"
            f"• 50 credits per referral\n"
            f"• Premium users earn money\n\n"
            f"📊 **Your Stats:**\n"
            f"• Referrals: 0\n"
            f"• Credits Earned: 0",
            parse_mode='MARKDOWN'
        )

    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language command"""
        lang = context.args[0].lower() if context.args else None

        if not lang or lang not in ['en', 'id']:
            await update.effective_message.reply_text(
                "🌐 **Language Selection**\n\n"
                "**Usage:** `/language <code>`\n\n"
                "**Available:**\n"
                "• `en` - English\n"
                "• `id` - Bahasa Indonesia",
                parse_mode='MARKDOWN'
            )
            return

        lang_names = {'en': 'English', 'id': 'Bahasa Indonesia'}
        await update.effective_message.reply_text(
            f"✅ Language changed to {lang_names[lang]}!",
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
        """Handle /admin command - show admin panel"""
        user_id = update.effective_user.id
        is_admin = user_id in self.admin_ids
        
        if not is_admin:
            await update.effective_message.reply_text(
                f"❌ **Access Denied**\n\nYou are not authorized to use admin commands.",
                parse_mode='MARKDOWN'
            )
            return
        
        admin_menu = f"""👑 **ADMIN PANEL**

👤 Admin ID: `{user_id}`

📊 **Commands:**
• `/signal_on` - Enable auto signals
• `/signal_off` - Disable auto signals  
• `/signal_status` - Check status

🔧 **Bot Status:**
• HTTP/2: ✅
• Rate limit: ✅ (9 RPS)
• Market overview: ✅"""
        
        await update.effective_message.reply_text(admin_menu, parse_mode='MARKDOWN')

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