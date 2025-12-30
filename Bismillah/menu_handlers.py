# -*- coding: utf-8 -*-
"""
CryptoMentor AI 2.0 - Menu Callback Handlers
Handles all InlineKeyboard interactions and maps to existing commands
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from menu_system import (
    MenuBuilder, get_menu_text, MAIN_MENU, PRICE_MARKET, TRADING_ANALYSIS,
    FUTURES_SIGNALS, PORTFOLIO_CREDITS, PREMIUM_REFERRAL, ASK_AI_MENU,
    SETTINGS_MENU, CHECK_PRICE, MARKET_OVERVIEW, SPOT_ANALYSIS,
    FUTURES_ANALYSIS, MULTI_COIN_SIGNALS, AUTO_SIGNAL_INFO, MY_PORTFOLIO,
    ADD_COIN, CHECK_CREDITS, UPGRADE_PREMIUM, REFERRAL_PROGRAM,
    PREMIUM_EARNINGS, ASK_AI, CHANGE_LANGUAGE, POPULAR_SYMBOLS
)
import asyncio

class MenuCallbackHandler:
    """Handles all menu callback queries"""

    def __init__(self, bot_instance):
        self.bot = bot_instance

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main callback query handler"""
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        user_id = query.from_user.id

        try:
            # Main menu navigation
            if callback_data == MAIN_MENU:
                await self.show_main_menu(query, context)
            elif callback_data == PRICE_MARKET:
                await self.show_price_market_menu(query, context)
            elif callback_data == TRADING_ANALYSIS:
                await self.show_trading_analysis_menu(query, context)
            elif callback_data == FUTURES_SIGNALS:
                await self.show_futures_signals_menu(query, context)
            elif callback_data == PORTFOLIO_CREDITS:
                await self.show_portfolio_credits_menu(query, context)
            elif callback_data == PREMIUM_REFERRAL:
                await self.show_premium_referral_menu(query, context)
            elif callback_data == ASK_AI_MENU:
                await self.show_ask_ai_menu(query, context)
            elif callback_data == SETTINGS_MENU:
                await self.show_settings_menu(query, context)

            # Action handlers
            elif callback_data == CHECK_PRICE:
                await self.handle_check_price(query, context)
            elif callback_data == MARKET_OVERVIEW:
                await self.handle_market_overview(query, context)
            elif callback_data == SPOT_ANALYSIS:
                await self.handle_spot_analysis(query, context)
            elif callback_data == FUTURES_ANALYSIS:
                await self.handle_futures_analysis(query, context)
            elif callback_data == MULTI_COIN_SIGNALS:
                await self.handle_multi_coin_signals(query, context)
            elif callback_data == AUTO_SIGNAL_INFO:
                await self.handle_auto_signal_info(query, context)
            elif callback_data == MY_PORTFOLIO:
                await self.handle_my_portfolio(query, context)
            elif callback_data == ADD_COIN:
                await self.handle_add_coin(query, context)
            elif callback_data == CHECK_CREDITS:
                await self.handle_check_credits(query, context)
            elif callback_data == UPGRADE_PREMIUM:
                await self.handle_upgrade_premium(query, context)
            elif callback_data == REFERRAL_PROGRAM:
                await self.handle_referral_program(query, context)
            elif callback_data == PREMIUM_EARNINGS:
                await self.handle_premium_earnings(query, context)
            elif callback_data == ASK_AI:
                await self.handle_ask_ai(query, context)
            elif callback_data == CHANGE_LANGUAGE:
                await self.handle_change_language(query, context)
            elif callback_data == "copy_referral_link":
                await self.handle_copy_referral_link(query, context)
            elif callback_data == "referral_stats":
                await self.handle_referral_stats(query, context)
            elif callback_data == "referral_withdrawal":
                await self.handle_referral_withdrawal(query, context)
            elif callback_data == "referral_guide":
                await self.handle_referral_guide(query, context)
            elif callback_data == "tier_system_guide":
                await self.handle_tier_system_guide(query, context)
            elif callback_data == "advanced_referral_guide":
                await self.handle_advanced_referral_guide(query, context)
            elif callback_data.startswith("set_lang_"):
                await self.handle_set_language(query, context)


            # Symbol selection handlers
            elif callback_data.startswith('symbol_'):
                await self.handle_symbol_selection(query, context)
            elif callback_data == 'manual_symbol':
                await self.handle_manual_symbol(query, context)
            elif callback_data.startswith('futures_'):
                await self.handle_futures_timeframe_selection(query, context)
            elif callback_data.startswith('price_'):
                await self.handle_price_symbol_selection(query, context)
            elif callback_data.startswith('analyze_'):
                await self.handle_analyze_symbol_selection(query, context)

        except Exception as e:
            print(f"Error in callback handler: {e}")
            await query.edit_message_text(
                "❌ Terjadi kesalahan. Silakan coba lagi atau gunakan command manual.",
                reply_markup=MenuBuilder.build_main_menu()
            )

    async def show_main_menu(self, query, context):
        """Show main menu"""
        user_id = query.from_user.id
        from database import Database
        db = Database()
        user_lang = db.get_user_language(user_id)
        
        await query.edit_message_text(
            get_menu_text(MAIN_MENU, user_lang),
            reply_markup=MenuBuilder.build_main_menu(),
            parse_mode='MARKDOWN'
        )

    async def show_price_market_menu(self, query, context):
        """Show price & market submenu"""
        user_id = query.from_user.id
        from database import Database
        db = Database()
        user_lang = db.get_user_language(user_id)
        
        await query.edit_message_text(
            get_menu_text(PRICE_MARKET, user_lang),
            reply_markup=MenuBuilder.build_price_market_menu(),
            parse_mode='MARKDOWN'
        )

    async def show_trading_analysis_menu(self, query, context):
        """Show trading analysis submenu"""
        user_id = query.from_user.id
        from database import Database
        db = Database()
        user_lang = db.get_user_language(user_id)
        
        await query.edit_message_text(
            get_menu_text(TRADING_ANALYSIS, user_lang),
            reply_markup=MenuBuilder.build_trading_analysis_menu(),
            parse_mode='MARKDOWN'
        )

    async def show_futures_signals_menu(self, query, context):
        """Show futures signals submenu"""
        await query.edit_message_text(
            get_menu_text(FUTURES_SIGNALS),
            reply_markup=MenuBuilder.build_futures_signals_menu(),
            parse_mode='MARKDOWN'
        )

    async def show_portfolio_credits_menu(self, query, context):
        """Show portfolio & credits submenu"""
        await query.edit_message_text(
            get_menu_text(PORTFOLIO_CREDITS),
            reply_markup=MenuBuilder.build_portfolio_credits_menu(),
            parse_mode='MARKDOWN'
        )

    async def show_premium_referral_menu(self, query, context):
        """Show premium & referral submenu"""
        await query.edit_message_text(
            get_menu_text(PREMIUM_REFERRAL),
            reply_markup=MenuBuilder.build_premium_referral_menu(),
            parse_mode='MARKDOWN'
        )

    async def show_ask_ai_menu(self, query, context):
        """Show ask AI submenu"""
        await query.edit_message_text(
            get_menu_text(ASK_AI_MENU),
            reply_markup=MenuBuilder.build_ask_ai_menu(),
            parse_mode='MARKDOWN'
        )

    async def show_settings_menu(self, query, context):
        """Show settings submenu"""
        await query.edit_message_text(
            get_menu_text(SETTINGS_MENU),
            reply_markup=MenuBuilder.build_settings_menu(),
            parse_mode='MARKDOWN'
        )

    async def handle_check_price(self, query, context):
        """Handle check price action - show symbol selection"""
        context.user_data['current_action'] = 'price'
        context.user_data['awaiting_symbol'] = True

        await query.edit_message_text(
            "🔹 **Check Price** - Select a cryptocurrency:\n\n"
            "Choose from popular options below or type manually:",
            reply_markup=MenuBuilder.build_symbol_selection(),
            parse_mode='MARKDOWN'
        )

    async def handle_market_overview(self, query, context):
        """Handle market overview - trigger /market command"""
        await query.edit_message_text("⏳ Loading market overview...")

        # Create fake update to trigger market command
        from telegram import User, Chat
        fake_update = Update(
            update_id=999999,
            message=query.message,
            callback_query=query
        )

        # Call market command directly
        await self.bot.market_command(fake_update, context)

    async def handle_spot_analysis(self, query, context):
        """Handle spot analysis - show symbol selection"""
        context.user_data['current_action'] = 'analyze'
        context.user_data['awaiting_symbol'] = True

        await query.edit_message_text(
            "📊 **Spot Analysis (SnD)** - 20 Credits\n\n"
            "Select a cryptocurrency for comprehensive analysis:",
            reply_markup=MenuBuilder.build_symbol_selection(),
            parse_mode='MARKDOWN'
        )

    async def handle_futures_analysis(self, query, context):
        """Handle futures analysis - show symbol selection"""
        context.user_data['current_action'] = 'futures'
        context.user_data['awaiting_symbol'] = True

        await query.edit_message_text(
            "📉 **Futures Analysis (SnD)** - 20 Credits\n\n"
            "Select a cryptocurrency for futures trading analysis:",
            reply_markup=MenuBuilder.build_symbol_selection(),
            parse_mode='MARKDOWN'
        )

    async def handle_multi_coin_signals(self, query, context):
        """Handle multi-coin signals with enhanced SnD analysis"""
        await query.edit_message_text("⏳ Generating futures signals with Supply & Demand analysis...")

        try:
            from ai_assistant import AIAssistant
            from crypto_api import crypto_api
            
            ai = AIAssistant()
            
            # Generate enhanced futures signals with SnD integration
            signals_text = await ai.generate_futures_signals(
                language='id',
                crypto_api=crypto_api,
                query_args=['4h']  # Default to 4h timeframe
            )
            
            # Send the signals
            await query.edit_message_text(
                signals_text,
                parse_mode='MARKDOWN'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error generating signals: {str(e)[:100]}...\n\n"
                "Please try again in a few seconds.",
                parse_mode='MARKDOWN'
            )

    async def handle_auto_signal_info(self, query, context):
        """Handle auto signal info"""
        info_text = """👑 **Auto Signal Information**

🤖 **What is Auto Signal?**
Automated trading signals delivered directly to your chat every 5 minutes when high-confidence opportunities are detected.

🎯 **Features:**
• Real-time signal delivery
• Supply & Demand analysis
• Multiple timeframes
• Professional entry/exit points
• Risk management included

🔒 **Availability:**
Currently available for **Lifetime Premium users only**

💎 **How to Access:**
Upgrade to Lifetime Premium via `/subscribe` to unlock this exclusive feature.

📊 **Signal Quality:**
• Minimum 75% confidence
• Advanced SnD algorithms
• Anti-spam protection
• Quality over quantity approach"""

        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Futures Menu", callback_data=FUTURES_SIGNALS)]
        ])

        await query.edit_message_text(
            info_text,
            reply_markup=back_button,
            parse_mode='MARKDOWN'
        )

    async def handle_my_portfolio(self, query, context):
        """Handle my portfolio - trigger /portfolio"""
        await query.edit_message_text("⏳ Loading your portfolio...")

        fake_update = Update(
            update_id=999999,
            message=query.message,
            callback_query=query
        )

        await self.bot.portfolio_command(fake_update, context)

    async def handle_add_coin(self, query, context):
        """Handle add coin - start step-by-step process"""
        context.user_data['current_action'] = 'add_coin'
        context.user_data['awaiting_symbol'] = True
        context.user_data['step'] = 'symbol'

        await query.edit_message_text(
            "➕ **Add Coin to Portfolio**\n\n"
            "Step 1/2: Select the cryptocurrency to add:",
            reply_markup=MenuBuilder.build_symbol_selection(),
            parse_mode='MARKDOWN'
        )

    async def handle_check_credits(self, query, context):
        """Handle check credits - trigger /credits"""
        await query.edit_message_text("⏳ Checking your credits...")

        fake_update = Update(
            update_id=999999,
            message=query.message,
            callback_query=query
        )

        await self.bot.credits_command(fake_update, context)

    async def handle_upgrade_premium(self, query, context):
        """Handle upgrade premium - trigger /subscribe"""
        await query.edit_message_text("⏳ Loading premium options...")

        fake_update = Update(
            update_id=999999,
            message=query.message,
            callback_query=query
        )

        await self.bot.subscribe_command(fake_update, context)

    async def handle_referral_program(self, query, context):
        """Handle referral program - show comprehensive referral info"""
        user_id = query.from_user.id
        user_name = query.from_user.first_name or "User"
        
        # Get bot username for referral link
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username or "CryptoMentorAI_bot"
        
        try:
            from database import Database
            db = Database()
            
            # Ensure user exists
            existing_user = db.get_user(user_id)
            if not existing_user:
                db.create_user(user_id, query.from_user.username, 
                             query.from_user.first_name, 
                             query.from_user.last_name)
            
            # Get user referral codes
            referral_codes = db.get_user_referral_codes(user_id)
            if not referral_codes:
                await query.edit_message_text("❌ Error loading referral data. Please try /start first.")
                return
                
            free_referral_code = referral_codes.get('free_referral_code', 'INVALID')
            premium_referral_code = referral_codes.get('premium_referral_code', 'INVALID')
            
            # Get stats
            earnings_summary = db.get_referral_earnings_summary(user_id)
            tier_info = db.get_user_tier(user_id)
            
            # Build links
            free_link = f"https://t.me/{bot_username}?start=ref_{free_referral_code}"
            premium_link = f"https://t.me/{bot_username}?start=prem_{premium_referral_code}"
            
            # Calculate next tier requirement
            next_requirement = 10 if tier_info['level']==1 else 25 if tier_info['level']==2 else 50 if tier_info['level']==3 else 100 if tier_info['level']==4 else 100
            progress = min(100, (earnings_summary['total_referrals'] / next_requirement * 100))
            
            referral_text = f"""🎁 **REFERRAL PROGRAM - {tier_info['tier']} TIER**

👤 **{user_name}** | Level {tier_info['level']}/5

🔗 **YOUR REFERRAL LINKS:**

🆓 **FREE REFERRAL:**
`{free_link}`
💰 Reward: {5 + int(5 * tier_info['bonus']/100)} credits per referral

💎 **PREMIUM REFERRAL:**
`{premium_link}`  
💰 Reward: Rp {int(10000 * tier_info['money_multiplier']):,} per premium subscriber

📊 **PERFORMANCE DASHBOARD:**
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Total Referrals: {earnings_summary['total_referrals']:>15} ┃
┃ Free Referrals: {earnings_summary['free_referrals']:>16} ┃
┃ Premium Referrals: {earnings_summary['premium_referrals']:>13} ┃
┃ Credits Earned: {earnings_summary['credit_earnings']:>16} ┃
┃ Money Earned: Rp {earnings_summary['money_earnings']:>13,} ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

🏆 **{tier_info['tier']} TIER STATUS:**
• Credit Bonus: +{tier_info['bonus']}%
• Money Multiplier: {tier_info['money_multiplier']}x
• Progress to next tier: {progress:.1f}%
{'▓' * int(progress/10)}{'░' * (10-int(progress/10))} {earnings_summary['total_referrals']}/{next_requirement}

💡 **EARNING STRATEGIES:**
1. Share free link in crypto groups
2. Premium link for serious traders
3. Build long-term referral network
4. Higher tiers unlock bigger rewards"""
            
            # Create buttons
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [
                    InlineKeyboardButton("📊 Detailed Stats", callback_data="referral_stats"),
                    InlineKeyboardButton("💡 Strategy Guide", callback_data="referral_guide")
                ],
                [
                    InlineKeyboardButton("🎯 Tier System", callback_data="tier_system_guide"),
                    InlineKeyboardButton("💰 Withdrawal", callback_data="referral_withdrawal")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Menu", callback_data=PREMIUM_REFERRAL)
                ]
            ]
            
            await query.edit_message_text(
                referral_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='MARKDOWN'
            )
            
        except Exception as e:
            print(f"Error in referral program handler: {e}")
            await query.edit_message_text(
                f"❌ Error loading referral data: {str(e)[:100]}\n\n"
                f"Please try /referral command directly.",
                parse_mode='MARKDOWN'
            )

    async def handle_premium_earnings(self, query, context):
        """Handle premium earnings"""
        # For now, show a message since this command might not exist
        earnings_text = """💰 **Premium Earnings Dashboard**

🎯 **Referral Earnings:**
• Total Referrals: 0
• Credits Earned: 0
• Money Earned: Rp 0

💡 **How to Earn:**
1. Share your referral link from `/referral`
2. When referred users subscribe premium, you earn money
3. All users give you credits immediately

📊 **Current Status:**
Premium users earn Rp 10,000 per premium referral

🔧 **Note:** Full earnings dashboard coming in future updates!"""

        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Premium Menu", callback_data=PREMIUM_REFERRAL)]
        ])

        await query.edit_message_text(
            earnings_text,
            reply_markup=back_button,
            parse_mode='MARKDOWN'
        )

    async def handle_ask_ai(self, query, context):
        """Handle ask AI - prompt for question"""
        context.user_data['current_action'] = 'ask_ai'
        context.user_data['awaiting_question'] = True

        prompt_text = """💬 **Ask CryptoMentor AI**

Type your question about cryptocurrency, trading, or blockchain technology.

📚 **Examples:**
• "What is DeFi?"
• "Explain Bitcoin halving"
• "How to read candlestick charts?"
• "What is supply and demand in trading?"

💡 Just type your question in the next message!"""

        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data=ASK_AI_MENU)]
        ])

        await query.edit_message_text(
            prompt_text,
            reply_markup=back_button,
            parse_mode='MARKDOWN'
        )

    async def handle_change_language(self, query, context):
        """Handle language change with interactive buttons"""
        user_id = query.from_user.id
        
        try:
            from database import Database
            db = Database()
            current_lang = db.get_user_language(user_id) or 'id'
            current_name = {'en': 'English', 'id': 'Bahasa Indonesia'}.get(current_lang, 'Bahasa Indonesia')
        except:
            current_lang = 'id'
            current_name = 'Bahasa Indonesia'

        if current_lang == 'id':
            language_text = f"""🌐 **Pengaturan Bahasa**

📍 **Bahasa Saat Ini:** {current_name} (`{current_lang}`)

🗣️ **Bahasa Tersedia:**
• 🇺🇸 English - Fitur lengkap
• 🇮🇩 Bahasa Indonesia - Fitur lengkap

💡 **Pilih bahasa yang Anda inginkan:**"""
        else:
            language_text = f"""🌐 **Language Settings**

📍 **Current Language:** {current_name} (`{current_lang}`)

🗣️ **Available Languages:**
• 🇺🇸 English - Full features
• 🇮🇩 Bahasa Indonesia - Fitur lengkap

💡 **Select your preferred language:**"""

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en"),
                InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="set_lang_id")
            ],
            [InlineKeyboardButton("🔙 Back to Settings", callback_data=SETTINGS_MENU)]
        ]

        await query.edit_message_text(
            language_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='MARKDOWN'
        )

    async def handle_symbol_selection(self, query, context):
        """Handle symbol selection from popular symbols"""
        symbol = query.data.replace('symbol_', '')
        current_action = context.user_data.get('current_action', '')

        if current_action == 'price':
            await self.execute_price_command(query, context, symbol)
        elif current_action == 'analyze':
            await self.execute_analyze_command(query, context, symbol)
        elif current_action == 'futures':
            await self.show_futures_timeframe_selection(query, context, symbol)
        elif current_action == 'add_coin':
            await self.handle_add_coin_amount(query, context, symbol)

    async def handle_manual_symbol(self, query, context):
        """Handle manual symbol input"""
        current_action = context.user_data.get('current_action', '')
        context.user_data['awaiting_manual_symbol'] = True

        action_text = {
            'price': 'check price for',
            'analyze': 'analyze',
            'futures': 'futures analysis for',
            'add_coin': 'add to portfolio'
        }.get(current_action, 'process')

        prompt_text = f"""⌨️ **Manual Symbol Input**

Type the cryptocurrency symbol you want to {action_text}.

💡 **Examples:** BTC, ETH, DOGE, SHIB, etc.

Just type the symbol in your next message!"""

        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data=MAIN_MENU)]
        ])

        await query.edit_message_text(
            prompt_text,
            reply_markup=back_button,
            parse_mode='MARKDOWN'
        )

    async def show_futures_timeframe_selection(self, query, context, symbol):
        """Show timeframe selection for futures analysis"""
        await query.edit_message_text(
            f"📉 **Futures Analysis for {symbol}**\n\n"
            f"Select your preferred timeframe:",
            reply_markup=MenuBuilder.build_timeframe_selection(symbol),
            parse_mode='MARKDOWN'
        )

    async def handle_futures_timeframe_selection(self, query, context):
        """Handle futures timeframe selection"""
        # Parse callback data: futures_SYMBOL_TIMEFRAME
        parts = query.data.split('_')
        if len(parts) >= 3:
            symbol = parts[1]
            timeframe = parts[2]

            await query.edit_message_text("⏳ Analyzing futures data...")

            # Use existing futures callback from bot.py
            await self.bot.handle_callback_query(
                Update(update_id=999999, callback_query=query),
                context
            )

    async def handle_add_coin_amount(self, query, context, symbol):
        """Handle amount input for add coin"""
        context.user_data['symbol'] = symbol
        context.user_data['step'] = 'amount'
        context.user_data['awaiting_amount'] = True

        prompt_text = f"""➕ **Add {symbol} to Portfolio**

Step 2/2: Enter the amount of {symbol} you own.

💡 **Examples:**
• 0.5 (for 0.5 {symbol})
• 100 (for 100 {symbol})
• 0.001234 (for small amounts)

Just type the number in your next message!"""

        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data=PORTFOLIO_CREDITS)]
        ])

        await query.edit_message_text(
            prompt_text,
            reply_markup=back_button,
            parse_mode='MARKDOWN'
        )

    async def execute_price_command(self, query, context, symbol):
        """Execute price command for selected symbol"""
        await query.edit_message_text(f"⏳ Fetching {symbol} price...")

        # Create fake context with args
        context.args = [symbol]
        fake_update = Update(
            update_id=999999,
            message=query.message,
            callback_query=query
        )

        await self.bot.price_command(fake_update, context)

    async def execute_analyze_command(self, query, context, symbol):
        """Execute analyze command for selected symbol"""
        await query.edit_message_text(f"⏳ Analyzing {symbol}...")

        # Create fake context with args
        context.args = [symbol]
        fake_update = Update(
            update_id=999999,
            message=query.message,
            callback_query=query
        )

        await self.bot.analyze_command(fake_update, context)

    async def handle_copy_referral_link(self, query, context):
        """Handle copy referral link"""
        user_id = query.from_user.id
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username or "CryptoMentorAI_bot"
        referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

        await query.answer(
            f"✅ Link copied!\n{referral_link}",
            show_alert=True
        )

    async def handle_referral_stats(self, query, context):
        """Handle detailed referral statistics with advanced tier system"""
        user_id = query.from_user.id
        user_name = query.from_user.first_name or "User"

        # Get detailed stats from database
        total_referrals = 0
        active_referrals = 0
        total_earnings = 0
        this_month_earnings = 0
        premium_referrals = 0

        try:
            from database import Database
            db = Database()
            stats = db.get_detailed_referral_stats(user_id)
            total_referrals = stats.get('total_referrals', 0)
            active_referrals = stats.get('active_referrals', 0)
            total_earnings = stats.get('total_earnings', 0)
            this_month_earnings = stats.get('this_month_earnings', 0)
            
            # Get premium referral count
            earnings_summary = db.get_referral_earnings_summary(user_id)
            premium_referrals = earnings_summary.get('premium_referrals', 0)
        except:
            pass

        # Get current tier and progress
        current_tier = self.get_referral_tier_info(total_referrals)
        next_tier = self.get_next_tier_info(total_referrals)
        
        # Calculate earnings potential
        credit_value = (total_referrals - premium_referrals) * 5  # 5 credits per free referral
        money_value = total_earnings
        estimated_monthly = self.calculate_monthly_potential(total_referrals, active_referrals)

        stats_text = f"""🏆 **REFERRAL DASHBOARD - {current_tier['name']} TIER**

👤 **{user_name}** | Level {current_tier['level']}/5

📊 **PERFORMANCE METRICS:**
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Total Referrals: {total_referrals:>15} ┃
┃ Free Referrals: {total_referrals - premium_referrals:>16} ┃
┃ Premium Referrals: {premium_referrals:>13} ┃
┃ Success Rate: {(active_referrals/max(total_referrals,1)*100):>17.1f}% ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

💎 **CURRENT TIER: {current_tier['name']}**
{current_tier['icon']} **Benefits:**
• Credit Bonus: +{current_tier['bonus']}% pada setiap referral
• Money Multiplier: {current_tier['money_multiplier']}x cash rewards
• Badge: {current_tier['badge']}
• Special Access: {current_tier['access']}

🎯 **PROGRESSION TO {next_tier['name']}:**
Progress: {total_referrals}/{next_tier['requirement']} ({(total_referrals/next_tier['requirement']*100):.1f}%)
{'▓' * int(total_referrals/next_tier['requirement']*10)}{'░' * (10-int(total_referrals/next_tier['requirement']*10))}
Needed: {max(0, next_tier['requirement'] - total_referrals)} more referrals

💰 **EARNINGS OVERVIEW:**
• Credits Earned: {credit_value:,} credits (≈ Rp {credit_value * 500:,})
• Cash Earned: Rp {money_value:,}
• Bulan Ini: Rp {this_month_earnings:,}
• Estimated Monthly: Rp {estimated_monthly:,}

📈 **GROWTH STRATEGY:**
{self.get_tier_specific_tips(current_tier['level'])}

🎁 **REWARDS UNLOCKED:**
{self.get_rewards_display(current_tier['level'], total_referrals)}

⚡ **TIER BONUSES AKTIF:**
• Credit boost: {current_tier['bonus']}% extra
• Withdrawal priority: {current_tier['withdrawal_priority']}
• Customer support: {current_tier['support_level']}"""

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("📋 Copy Link", callback_data="copy_referral_link"),
             InlineKeyboardButton("💡 Tips & Guide", callback_data="referral_guide")],
            [InlineKeyboardButton("🎯 Tier Guide", callback_data="tier_system_guide"),
             InlineKeyboardButton("💰 Withdrawal", callback_data="referral_withdrawal")],
            [InlineKeyboardButton("🔙 Back", callback_data="referral_program")],
        ]

        await query.edit_message_text(
            text=stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='MARKDOWN'
        )

    async def handle_referral_withdrawal(self, query, context):
        """Handle referral withdrawal request"""
        user_id = query.from_user.id

        try:
            from database import Database
            db = Database()
            stats = db.get_referral_stats(user_id)
            total_earnings = stats.get('total_earnings', 0)
        except:
            total_earnings = 0

        if total_earnings < 50000:
            await query.answer(
                f"⚠️ Minimum withdrawal Rp 50,000\nSaldo Anda: Rp {total_earnings:,}",
                show_alert=True
            )
            return

        withdrawal_text = f"""💰 **WITHDRAWAL REFERRAL EARNINGS**

💳 **Saldo Tersedia:** Rp {total_earnings:,}

📝 **Metode Withdrawal:**
• Bank Transfer (BCA, BNI, BRI, Mandiri)
• E-Wallet (OVO, DANA, GoPay)
• Crypto (USDT TRC20)

⏱️ **Processing Time:**
• Bank Transfer: 1-3 hari kerja
• E-Wallet: Instant - 24 jam  
• Crypto: 2-6 jam

💼 **Syarat Withdrawal:**
• Minimum: Rp 50,000
• Fee admin: Rp 2,500 (bank) / Rp 1,000 (e-wallet) / 1 USDT (crypto)
• KYC: Wajib untuk withdrawal pertama

📋 **Cara Request Withdrawal:**
1. Hubungi admin: @cryptomentor_admin
2. Kirim: "WITHDRAWAL + JUMLAH + METODE"
3. Upload bukti identitas (KTP/SIM)
4. Tunggu konfirmasi dan transfer

⚠️ **Penting:**
• Pastikan data bank/e-wallet benar
• Screenshot chat ini sebagai bukti
• Withdrawal processed maksimal 7 hari kerja"""

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("💬 Contact Admin", url="https://t.me/cryptomentor_admin")],
            [InlineKeyboardButton("📊 Check Balance", callback_data="referral_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="referral_program")],
        ]

        await query.edit_message_text(
            text=withdrawal_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='MARKDOWN'
        )

    def get_referral_tier_info(self, total_referrals):
        """Get comprehensive referral tier information"""
        if total_referrals >= 100:
            return {
                'name': 'DIAMOND', 'level': 5, 'bonus': 30, 'money_multiplier': 3.0,
                'icon': '💎', 'badge': '👑 Diamond Elite',
                'access': 'VIP Community + Direct Admin Access',
                'withdrawal_priority': 'Instant (0-2 hours)',
                'support_level': 'White-glove Priority Support'
            }
        elif total_referrals >= 50:
            return {
                'name': 'GOLD', 'level': 4, 'bonus': 20, 'money_multiplier': 2.5,
                'icon': '🥇', 'badge': '🏆 Gold Champion',
                'access': 'Premium Community + Beta Features',
                'withdrawal_priority': 'Fast Track (2-6 hours)',
                'support_level': 'Priority Support'
            }
        elif total_referrals >= 25:
            return {
                'name': 'SILVER', 'level': 3, 'bonus': 15, 'money_multiplier': 2.0,
                'icon': '🥈', 'badge': '⚡ Silver Elite',
                'access': 'Silver Community + Early Access',
                'withdrawal_priority': 'Accelerated (6-12 hours)',
                'support_level': 'Enhanced Support'
            }
        elif total_referrals >= 10:
            return {
                'name': 'BRONZE', 'level': 2, 'bonus': 10, 'money_multiplier': 1.5,
                'icon': '🥉', 'badge': '🔥 Bronze Achiever',
                'access': 'Member Community',
                'withdrawal_priority': 'Standard (12-24 hours)',
                'support_level': 'Standard Support'
            }
        else:
            return {
                'name': 'STARTER', 'level': 1, 'bonus': 5, 'money_multiplier': 1.0,
                'icon': '⭐', 'badge': '🌟 Rising Star',
                'access': 'Basic Community',
                'withdrawal_priority': 'Normal (24-48 hours)',
                'support_level': 'Community Support'
            }

    def get_next_tier_info(self, total_referrals):
        """Get information about next tier"""
        if total_referrals >= 100:
            return {'name': 'DIAMOND ELITE', 'requirement': 200}
        elif total_referrals >= 50:
            return {'name': 'DIAMOND', 'requirement': 100}
        elif total_referrals >= 25:
            return {'name': 'GOLD', 'requirement': 50}
        elif total_referrals >= 10:
            return {'name': 'SILVER', 'requirement': 25}
        else:
            return {'name': 'BRONZE', 'requirement': 10}

    def calculate_monthly_potential(self, total_referrals, active_referrals):
        """Calculate estimated monthly earning potential"""
        if total_referrals == 0:
            return 0
        
        # Base calculation: assume 10% of referrals become premium monthly
        conversion_rate = 0.10
        avg_premium_value = 15000  # Average premium subscription value
        
        # Tier multiplier
        tier = self.get_referral_tier_info(total_referrals)
        multiplier = tier['money_multiplier']
        
        estimated = total_referrals * conversion_rate * avg_premium_value * 0.1 * multiplier
        return int(estimated)

    def get_tier_specific_tips(self, tier_level):
        """Get tier-specific growth tips"""
        tips = {
            1: "🚀 **STARTER STRATEGY:**\n• Share di 2-3 grup crypto\n• Ajak 5 teman trading pertama\n• Focus quality over quantity",
            2: "📈 **BRONZE GROWTH:**\n• Expand ke 5+ crypto communities\n• Create tutorial content\n• Build personal crypto network",
            3: "⚡ **SILVER SCALING:**\n• Launch referral campaign\n• Partner dengan crypto influencers\n• Host crypto learning sessions",
            4: "🏆 **GOLD MASTERY:**\n• Build referral sub-network\n• Mentor bronze/silver members\n• Create premium content strategy",
            5: "💎 **DIAMOND EXCELLENCE:**\n• Lead community initiatives\n• Develop scalable systems\n• Mentor entire referral network"
        }
        return tips.get(tier_level, tips[1])

    def get_rewards_display(self, tier_level, total_referrals):
        """Display unlocked rewards"""
        rewards = []
        
        if tier_level >= 1:
            rewards.append("✅ 5 credits per free referral")
        if tier_level >= 2:
            rewards.append("✅ 10% bonus credits")
            rewards.append("✅ Bronze badge & community access")
        if tier_level >= 3:
            rewards.append("✅ 15% bonus credits")
            rewards.append("✅ Early access to features")
        if tier_level >= 4:
            rewards.append("✅ 20% bonus credits")
            rewards.append("✅ VIP support channel")
        if tier_level >= 5:
            rewards.append("✅ 30% bonus credits")
            rewards.append("✅ Direct admin access")
            
        # Milestone rewards
        milestones = [
            (5, "🎁 50 bonus credits"),
            (15, "🎁 100 bonus credits + 1 day premium"),
            (30, "🎁 1 week premium trial"),
            (75, "🎁 1 month premium"),
        ]
        
        for milestone, reward in milestones:
            if total_referrals >= milestone:
                rewards.append(f"✅ {reward}")
        
        return "\n".join(rewards) if rewards else "🔒 Complete first referral to unlock rewards"

    async def handle_referral_guide(self, query, context):
        """Show comprehensive referral guide"""
        guide_text = """📚 **PANDUAN REFERRAL MASTER**

🎯 **STRATEGI DASAR:**

**1. TARGET AUDIENCE YANG TEPAT** 🎪
• Trader crypto pemula (butuh guidance)
• Member grup crypto aktif
• Followers crypto influencers
• Teman yang tertarik investasi

**2. PLATFORM SHARING OPTIMAL** 📱
• WhatsApp: Personal approach, trust tinggi
• Telegram Groups: Crypto communities
• Discord: Gaming + crypto communities  
• Twitter/X: Crypto Twitter audience
• Instagram Stories: Visual appeal

**3. CONTENT STRATEGY** ✍️
• Screenshot profit dari bot signals
• Tutorial cara pakai bot (video)
• Testimonial hasil trading
• Before/After portfolio growth
• Educational crypto content

**4. TIMING YANG TEPAT** ⏰
• Bull market: Share profit screenshots
• Bear market: Share risk management tips
• News events: Share quick analysis
• Weekend: Educational content
• Asian hours: Indonesian audience

**5. CONVERSION TACTICS** 💡
• Offer free 1-on-1 crypto guidance
• Share exclusive trading tips
• Create beginner-friendly tutorials
• Build trust through consistency
• Follow up dengan referrals

🏆 **PRO TIPS:**
• Authenticity > Hard selling
• Educational content builds trust  
• Personal success story works best
• Community building = long-term success
• Quality referrals > Quantity spam"""

        keyboard = [
            [InlineKeyboardButton("🎯 Advanced Strategies", callback_data="advanced_referral_guide")],
            [InlineKeyboardButton("📊 Back to Stats", callback_data="referral_stats")],
        ]

        await query.edit_message_text(
            text=guide_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='MARKDOWN'
        )

    async def handle_tier_system_guide(self, query, context):
        """Show comprehensive tier system guide"""
        tier_guide = """🏆 **TIER SYSTEM GUIDE - PATH TO DIAMOND**

🌟 **TIER OVERVIEW:**

**⭐ STARTER (0 referrals)**
• Bonus: 5% extra credits
• Rewards: Learning phase
• Goal: First 10 referrals

**🥉 BRONZE (10-24 referrals)** 
• Bonus: 10% extra credits + 1.5x money
• Rewards: Community access
• Goal: Build foundation network

**🥈 SILVER (25-49 referrals)**
• Bonus: 15% extra credits + 2x money  
• Rewards: Early feature access
• Goal: Scale & systematize

**🥇 GOLD (50-99 referrals)**
• Bonus: 20% extra credits + 2.5x money
• Rewards: VIP community + priority support
• Goal: Leadership & mentoring

**💎 DIAMOND (100+ referrals)**
• Bonus: 30% extra credits + 3x money
• Rewards: Elite access + admin connection
• Goal: Master referral ecosystem

📈 **PROGRESSION STRATEGY:**

**Phase 1: Foundation (0→10)**
• Duration: 2-4 weeks
• Focus: Friends & family
• Method: Personal recommendation

**Phase 2: Growth (10→25)**  
• Duration: 1-2 months
• Focus: Community expansion
• Method: Content + networking

**Phase 3: Scale (25→50)**
• Duration: 2-3 months  
• Focus: System building
• Method: Partnerships + automation

**Phase 4: Mastery (50→100)**
• Duration: 3-6 months
• Focus: Leadership
• Method: Team building + mentoring

💰 **EARNING POTENTIAL:**
• STARTER: ~Rp 50K/month
• BRONZE: ~Rp 200K/month
• SILVER: ~Rp 500K/month  
• GOLD: ~Rp 1.5M/month
• DIAMOND: ~Rp 5M+/month

*Estimasi berdasarkan 10% conversion rate ke premium*"""

        keyboard = [
            [InlineKeyboardButton("📊 My Progress", callback_data="referral_stats")],
            [InlineKeyboardButton("💡 Strategy Guide", callback_data="referral_guide")],
        ]

        await query.edit_message_text(
            text=tier_guide,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='MARKDOWN'
        )

    async def handle_advanced_referral_guide(self, query, context):
        """Show advanced referral strategies"""
        advanced_guide = """🚀 **ADVANCED REFERRAL MASTERY**

💡 **PSYCHOLOGICAL TRIGGERS:**

**1. SCARCITY & URGENCY** ⏰
• "Limited 100 credits bonus berakhir minggu ini"
• "Premium trial hanya untuk 50 orang pertama"
• "Exclusive early access buat referral hari ini"

**2. SOCIAL PROOF** 👥
• Screenshot testimonial success stories
• "Join 10,000+ active traders di Indonesia"
• Share leaderboard achievements

**3. RECIPROCITY PRINCIPLE** 🎁
• Berikan free value dulu (tips, analysis)
• Free crypto education sebelum referral
• Help solve their trading problems first

**4. AUTHORITY POSITIONING** 👔
• Share your trading wins/credentials
• Educational content yang valuable
• Position as crypto mentor/guide

🔥 **CONVERSION OPTIMIZATION:**

**A. LANDING EXPERIENCE**
• Personal onboarding untuk setiap referral
• Custom welcome message
• Free consultation offer

**B. RETENTION STRATEGY**  
• Weekly check-in dengan referrals
• Share exclusive trading insights
• Build long-term relationships

**C. UPSELLING FUNNEL**
• Free user → Credits exhausted → Premium push
• Social proof dari existing premium users
• Limited-time upgrade discounts

📊 **TRACKING & ANALYTICS:**

**Conversion Metrics:**
• Click-through rate dari link
• Free registration rate
• Premium conversion rate
• Monthly retention rate

**Optimization Points:**
• A/B test different messaging
• Track which platforms perform best  
• Identify highest-value referral sources
• Optimize timing untuk maximum impact

🎯 **AUTOMATION TOOLS:**

• Auto-follow up messages
• Scheduled content sharing
• Referral performance tracking
• Reward notifications

💎 **DIAMOND-TIER SECRETS:**
• Build referral teams (MLM-style)
• Create crypto trading courses
• Host exclusive webinars
• Partner dengan crypto projects
• Develop personal brand as crypto expert"""

        keyboard = [
            [InlineKeyboardButton("📚 Basic Guide", callback_data="referral_guide")],
            [InlineKeyboardButton("🏆 Tier System", callback_data="tier_system_guide")],
            [InlineKeyboardButton("📊 Back to Stats", callback_data="referral_stats")],
        ]

        await query.edit_message_text(
            text=advanced_guide,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='MARKDOWN'
        )

    async def handle_set_language(self, query, context):
        """Handle language selection from buttons"""
        user_id = query.from_user.id
        lang_code = query.data.split('_')[-1]  # Extract 'en' or 'id' from 'set_lang_en'
        
        if lang_code not in ['en', 'id']:
            await query.answer("❌ Invalid language selection", show_alert=True)
            return
            
        try:
            from database import Database
            db = Database()
            
            # Update user language
            success = db.update_user_language(user_id, lang_code)
            
            if success:
                lang_names = {'en': 'English', 'id': 'Bahasa Indonesia'}
                
                if lang_code == 'id':
                    success_msg = f"""✅ **Bahasa berhasil diubah ke {lang_names[lang_code]}!**

🎯 **Perubahan yang aktif:**
• Menu dan pesan dalam Bahasa Indonesia  
• Analisis trading dalam bahasa Indonesia
• Support customer dalam bahasa Indonesia

💡 **Catatan:** Bot sekarang akan merespons dalam Bahasa Indonesia."""
                    await query.answer("✅ Bahasa berhasil diubah ke Bahasa Indonesia!")
                else:
                    success_msg = f"""✅ **Language changed to {lang_names[lang_code]}!**

🎯 **Active Changes:**
• Menus and messages in English
• Trading analysis in English  
• Customer support in English

💡 **Note:** Bot will now respond in English."""
                    await query.answer("✅ Language changed to English!")
                
                # Show success message with proper language
                await query.edit_message_text(
                    success_msg,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali ke Pengaturan" if lang_code == 'id' else "🔙 Back to Settings", callback_data=SETTINGS_MENU)]]),
                    parse_mode='MARKDOWN'
                )
                
            else:
                await query.answer("❌ Gagal mengubah bahasa. Silakan coba lagi." if lang_code == 'id' else "❌ Failed to update language. Please try again.", show_alert=True)
                
        except Exception as e:
            print(f"Error setting language: {e}")
            await query.answer("❌ Error mengubah bahasa. Silakan coba lagi." if lang_code == 'id' else "❌ Error updating language. Please try again.", show_alert=True)


def register_menu_handlers(application, bot_instance):
    """Register all menu callback handlers"""
    menu_handler = MenuCallbackHandler(bot_instance)

    # Register the main callback handler
    application.add_handler(
        CallbackQueryHandler(menu_handler.handle_callback_query)
    )

    print("✅ Menu system handlers registered successfully")