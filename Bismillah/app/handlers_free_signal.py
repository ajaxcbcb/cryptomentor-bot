"""
Free Signal Handlers - NO AI/LLM Required
For Premium & Lifetime users to get instant signals using only Binance API + SMC
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.helpers import escape_markdown

from app.premium_checker import is_premium_user
from app.admin_auth import is_admin
from app.autosignal_fast import compute_signal_fast, format_signal_text, cmc_top_symbols

logger = logging.getLogger(__name__)


async def free_signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /free_signal - Generate instant signal without AI/LLM
    Available for: Premium users, Lifetime users, Admins
    Uses: Binance API + SMC analysis only (NO AI cost)
    """
    user_id = update.effective_user.id
    
    try:
        # Check if user is premium, lifetime, or admin
        user_is_admin = is_admin(user_id)
        user_is_premium = is_premium_user(user_id)
        
        if not (user_is_admin or user_is_premium):
            await update.message.reply_text(
                "❌ <b>Premium Feature</b>\n\n"
                "Free Signal (tanpa AI) hanya tersedia untuk:\n"
                "• Premium users\n"
                "• Lifetime users\n"
                "• Admins\n\n"
                "Upgrade ke premium untuk akses unlimited signals tanpa biaya AI!\n\n"
                "Contact admin untuk upgrade.",
                parse_mode='HTML'
            )
            return
        
        # Show coin selection menu
        keyboard = [
            [
                InlineKeyboardButton("🔥 Top 10 Coins", callback_data="free_signal:top10"),
                InlineKeyboardButton("📊 Top 25 Coins", callback_data="free_signal:top25")
            ],
            [
                InlineKeyboardButton("₿ BTC", callback_data="free_signal:BTC"),
                InlineKeyboardButton("Ξ ETH", callback_data="free_signal:ETH"),
                InlineKeyboardButton("◎ SOL", callback_data="free_signal:SOL")
            ],
            [
                InlineKeyboardButton("🔗 BNB", callback_data="free_signal:BNB"),
                InlineKeyboardButton("💎 ADA", callback_data="free_signal:ADA"),
                InlineKeyboardButton("🌊 XRP", callback_data="free_signal:XRP")
            ],
            [
                InlineKeyboardButton("🔵 DOT", callback_data="free_signal:DOT"),
                InlineKeyboardButton("🐕 DOGE", callback_data="free_signal:DOGE"),
                InlineKeyboardButton("🔺 AVAX", callback_data="free_signal:AVAX")
            ],
            [
                InlineKeyboardButton("🟣 MATIC", callback_data="free_signal:MATIC"),
                InlineKeyboardButton("🔗 LINK", callback_data="free_signal:LINK"),
                InlineKeyboardButton("🦄 UNI", callback_data="free_signal:UNI")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        status_text = "🔑 ADMIN" if user_is_admin else "⭐ PREMIUM"
        
        await update.message.reply_text(
            f"🎯 <b>Free Signal Generator</b>\n\n"
            f"Status: {status_text}\n"
            f"Cost: <b>FREE</b> (No AI/LLM cost)\n"
            f"Speed: <b>INSTANT</b> (1-2 seconds)\n\n"
            f"📊 <b>Analysis Method:</b>\n"
            f"• Smart Money Concepts (SMC)\n"
            f"• Order Blocks\n"
            f"• Fair Value Gaps (FVG)\n"
            f"• Market Structure\n"
            f"• Supply & Demand Zones\n"
            f"• EMA 21\n"
            f"• Week High/Low\n\n"
            f"Pilih coin untuk generate signal:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    except Exception as e:
        logger.error(f"Error in free_signal_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Error generating signal menu. Please try again."
        )


async def free_signal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle free signal button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    try:
        # Check premium status
        user_is_admin = is_admin(user_id)
        user_is_premium = is_premium_user(user_id)
        
        if not (user_is_admin or user_is_premium):
            await query.edit_message_text(
                "❌ Premium feature only. Contact admin to upgrade."
            )
            return
        
        # Parse callback data
        data = query.data.replace("free_signal:", "")
        
        # Show processing message
        await query.edit_message_text(
            "⏳ <b>Generating Signal...</b>\n\n"
            "Analyzing market data...\n"
            "This will take 1-2 seconds.",
            parse_mode='HTML'
        )
        
        # Handle different options
        if data == "top10":
            await generate_multiple_signals(query, user_id, limit=10)
        elif data == "top25":
            await generate_multiple_signals(query, user_id, limit=25)
        else:
            # Single coin signal
            await generate_single_signal(query, user_id, data)
    
    except Exception as e:
        logger.error(f"Error in free_signal_callback: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error generating signal. Please try again."
        )


async def generate_single_signal(query, user_id: int, symbol: str):
    """Generate signal for a single coin"""
    try:
        # Generate signal using SMC (no AI)
        signal = compute_signal_fast(symbol)
        
        if not signal:
            await query.edit_message_text(
                f"📊 <b>{symbol}USDT Analysis</b>\n\n"
                f"❌ No clear signal at the moment.\n\n"
                f"Reasons:\n"
                f"• No strong SMC setup\n"
                f"• Market is ranging\n"
                f"• Confidence below 75%\n\n"
                f"Try another coin or wait for better setup.",
                parse_mode='HTML'
            )
            return
        
        # Format signal text
        signal_text = format_signal_text(signal)
        
        # Add footer
        footer = (
            f"\n\n💡 <b>Free Signal</b> (No AI cost)\n"
            f"Generated using SMC + Technical Analysis\n"
            f"⚡ Instant • 🎯 Accurate • 💰 Free"
        )
        
        # Send signal
        await query.edit_message_text(
            signal_text + footer,
            parse_mode='MarkdownV2'
        )
        
        logger.info(f"Free signal generated for user {user_id}: {symbol} {signal.get('side')}")
    
    except Exception as e:
        logger.error(f"Error generating single signal: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error analyzing {symbol}. Please try again."
        )


async def generate_multiple_signals(query, user_id: int, limit: int = 10):
    """Generate signals for top N coins"""
    try:
        # Get top coins from CMC
        await query.edit_message_text(
            f"⏳ <b>Scanning Top {limit} Coins...</b>\n\n"
            f"Fetching market data from CoinMarketCap...",
            parse_mode='HTML'
        )
        
        try:
            top_coins = cmc_top_symbols(limit=limit)
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error fetching top coins: {str(e)}\n\n"
                f"Please try again or select a specific coin."
            )
            return
        
        # Analyze each coin
        signals_found = []
        coins_analyzed = 0
        
        for coin in top_coins:
            coins_analyzed += 1
            
            # Update progress every 5 coins
            if coins_analyzed % 5 == 0:
                await query.edit_message_text(
                    f"⏳ <b>Scanning Top {limit} Coins...</b>\n\n"
                    f"Progress: {coins_analyzed}/{len(top_coins)}\n"
                    f"Signals found: {len(signals_found)}",
                    parse_mode='HTML'
                )
            
            try:
                signal = compute_signal_fast(coin)
                if signal and signal.get('confidence', 0) >= 75:
                    signals_found.append(signal)
            except Exception as e:
                logger.warning(f"Error analyzing {coin}: {e}")
                continue
        
        # Send results
        if not signals_found:
            await query.edit_message_text(
                f"📊 <b>Top {limit} Coins Analysis</b>\n\n"
                f"❌ No clear signals found at the moment.\n\n"
                f"Analyzed: {coins_analyzed} coins\n"
                f"Signals: 0\n\n"
                f"Market might be ranging or no strong setups available.\n"
                f"Try again later or select a specific coin.",
                parse_mode='HTML'
            )
            return
        
        # Format multiple signals
        result_text = f"🎯 <b>Top {limit} Coins - Signals Found</b>\n\n"
        result_text += f"Analyzed: {coins_analyzed} coins\n"
        result_text += f"Signals: {len(signals_found)}\n\n"
        
        for i, sig in enumerate(signals_found[:5], 1):  # Show max 5 signals
            symbol = sig.get('symbol', '?')
            side = sig.get('side', '?')
            conf = sig.get('confidence', 0)
            price = sig.get('price', 0)
            
            result_text += f"{i}. <b>{symbol}</b>\n"
            result_text += f"   Side: {side} | Conf: {conf}%\n"
            result_text += f"   Price: ${price:,.2f}\n\n"
        
        if len(signals_found) > 5:
            result_text += f"... and {len(signals_found) - 5} more signals\n\n"
        
        result_text += (
            f"💡 <b>Free Signals</b> (No AI cost)\n"
            f"Generated using SMC + Technical Analysis\n"
            f"⚡ Instant • 🎯 Accurate • 💰 Free\n\n"
            f"Use /free_signal to get detailed signal for specific coin."
        )
        
        await query.edit_message_text(
            result_text,
            parse_mode='HTML'
        )
        
        logger.info(f"Multiple free signals generated for user {user_id}: {len(signals_found)} signals")
    
    except Exception as e:
        logger.error(f"Error generating multiple signals: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Error scanning coins. Please try again."
        )


async def free_signal_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help for free signal feature"""
    help_text = (
        "🎯 <b>Free Signal - Help</b>\n\n"
        "<b>What is Free Signal?</b>\n"
        "Generate instant trading signals WITHOUT using AI/LLM.\n"
        "100% FREE - No OpenRouter/API costs!\n\n"
        "<b>Who can use it?</b>\n"
        "• Premium users ⭐\n"
        "• Lifetime users 💎\n"
        "• Admins 🔑\n\n"
        "<b>How it works:</b>\n"
        "1. Uses Binance API for real-time data\n"
        "2. Applies Smart Money Concepts (SMC)\n"
        "3. Analyzes Order Blocks, FVG, Market Structure\n"
        "4. Generates signal in 1-2 seconds\n\n"
        "<b>Analysis includes:</b>\n"
        "• Order Blocks (Bullish/Bearish)\n"
        "• Fair Value Gaps (FVG)\n"
        "• Market Structure (Trend)\n"
        "• Supply & Demand Zones\n"
        "• EMA 21 confirmation\n"
        "• Week High/Low context\n\n"
        "<b>Commands:</b>\n"
        "• /free_signal - Generate signal\n"
        "• /free_signal_help - Show this help\n\n"
        "<b>Advantages:</b>\n"
        "✅ Instant (1-2 seconds)\n"
        "✅ Free (No AI cost)\n"
        "✅ Accurate (SMC-based)\n"
        "✅ Unlimited usage\n"
        "✅ Real-time data\n\n"
        "<b>vs OpenClaw AI:</b>\n"
        "• Free Signal: Fast, free, technical only\n"
        "• OpenClaw AI: Slower, costs credits, includes reasoning\n\n"
        "Use Free Signal for quick technical analysis!\n"
        "Use OpenClaw AI for detailed market insights."
    )
    
    await update.message.reply_text(help_text, parse_mode='HTML')


def register_free_signal_handlers(application):
    """Register free signal handlers"""
    
    # Commands
    application.add_handler(CommandHandler("free_signal", free_signal_command))
    application.add_handler(CommandHandler("free_signal_help", free_signal_help))
    
    # Callbacks
    application.add_handler(
        CallbackQueryHandler(
            free_signal_callback,
            pattern="^free_signal:"
        )
    )
    
    logger.info("Free Signal handlers registered successfully")
