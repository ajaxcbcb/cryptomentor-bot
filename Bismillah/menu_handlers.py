
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
        await query.edit_message_text(
            get_menu_text(MAIN_MENU),
            reply_markup=MenuBuilder.build_main_menu(),
            parse_mode='MARKDOWN'
        )
    
    async def show_price_market_menu(self, query, context):
        """Show price & market submenu"""
        await query.edit_message_text(
            get_menu_text(PRICE_MARKET),
            reply_markup=MenuBuilder.build_price_market_menu(),
            parse_mode='MARKDOWN'
        )
    
    async def show_trading_analysis_menu(self, query, context):
        """Show trading analysis submenu"""
        await query.edit_message_text(
            get_menu_text(TRADING_ANALYSIS),
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
        """Handle multi-coin signals - trigger /futures_signals"""
        await query.edit_message_text("⏳ Generating futures signals...")
        
        # Create fake update to trigger futures_signals command
        fake_update = Update(
            update_id=999999,
            message=query.message,
            callback_query=query
        )
        
        # Call futures_signals command directly
        await self.bot.futures_signals_command(fake_update, context)
    
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
        """Handle referral program - trigger /referral"""
        await query.edit_message_text("⏳ Loading referral information...")
        
        fake_update = Update(
            update_id=999999,
            message=query.message,
            callback_query=query
        )
        
        await self.bot.referral_command(fake_update, context)
    
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
        """Handle change language - trigger /language"""
        fake_update = Update(
            update_id=999999,
            message=query.message,
            callback_query=query
        )
        
        await self.bot.language_command(fake_update, context)
    
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

def register_menu_handlers(application, bot_instance):
    """Register all menu callback handlers"""
    menu_handler = MenuCallbackHandler(bot_instance)
    
    # Register the main callback handler
    application.add_handler(
        CallbackQueryHandler(menu_handler.handle_callback_query)
    )
    
    print("✅ Menu system handlers registered successfully")
