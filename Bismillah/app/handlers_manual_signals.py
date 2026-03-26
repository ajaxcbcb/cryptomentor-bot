"""
Manual Signal Handlers
Command handlers for manual signal generation: /analyze, /futures, /futures_signals, /signal, /signals
"""

from telegram import Update
from telegram.ext import ContextTypes
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
import re

from futures_signal_generator import FuturesSignalGenerator
from app.premium_checker import check_and_deduct_credits

# Credit costs
COST_SINGLE_SIGNAL = 20
COST_MULTI_SIGNAL = 60

# Rate limiting: max 5 requests per minute per user
user_rate_limits: Dict[int, List[datetime]] = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 5


def validate_symbol(symbol: str) -> tuple[bool, str]:
    """
    Validate trading symbol format.
    
    Args:
        symbol: Trading symbol to validate
        
    Returns:
        Tuple of (is_valid, cleaned_symbol or error_message)
    """
    if not symbol:
        return (False, "Symbol cannot be empty")
    
    # Remove special characters, keep only alphanumeric
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', symbol).upper()
    
    if len(cleaned) > 20:
        return (False, "Symbol too long (max 20 characters)")
    
    if len(cleaned) < 2:
        return (False, "Symbol too short (min 2 characters)")
    
    # Ensure it ends with USDT
    if not cleaned.endswith('USDT'):
        cleaned += 'USDT'
    
    return (True, cleaned)


def validate_timeframe(timeframe: str) -> tuple[bool, str]:
    """
    Validate timeframe format.
    
    Args:
        timeframe: Timeframe to validate
        
    Returns:
        Tuple of (is_valid, cleaned_timeframe or error_message)
    """
    valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
    
    cleaned = timeframe.lower().strip()
    
    if cleaned not in valid_timeframes:
        return (False, f"Invalid timeframe. Valid options: {', '.join(valid_timeframes)}")
    
    return (True, cleaned)


def check_rate_limit(user_id: int) -> tuple[bool, int]:
    """
    Check if user exceeded rate limit.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Tuple of (is_allowed, seconds_until_reset)
    """
    now = datetime.now()
    minute_ago = now - timedelta(minutes=1)
    
    # Clean old requests (older than 1 minute)
    user_rate_limits[user_id] = [
        ts for ts in user_rate_limits[user_id]
        if ts > minute_ago
    ]
    
    # Check if user exceeded limit
    if len(user_rate_limits[user_id]) >= MAX_REQUESTS_PER_MINUTE:
        # Calculate seconds until oldest request expires
        oldest_request = min(user_rate_limits[user_id])
        seconds_until_reset = int((oldest_request + timedelta(minutes=1) - now).total_seconds())
        return (False, max(1, seconds_until_reset))
    
    # Add current request
    user_rate_limits[user_id].append(now)
    return (True, 0)


async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /analyze <symbol> command.
    Generate single signal for spot/futures trading.
    
    Usage: /analyze BTCUSDT
    Cost: 20 credits (FREE for lifetime premium)
    """
    user_id = update.effective_user.id
    
    # Check rate limit
    is_allowed, cooldown = check_rate_limit(user_id)
    if not is_allowed:
        await update.message.reply_text(
            f"❌ Too many requests. Please wait {cooldown} seconds before trying again."
        )
        return
    
    # Parse arguments
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /analyze <symbol>\n\n"
            "Example:\n"
            "• /analyze BTCUSDT\n"
            "• /analyze ETH (automatically adds USDT)\n\n"
            "💰 Cost: 20 credits\n"
            "👑 Lifetime Premium: FREE"
        )
        return
    
    # Validate symbol
    symbol_input = context.args[0]
    is_valid, result = validate_symbol(symbol_input)
    
    if not is_valid:
        await update.message.reply_text(f"❌ {result}")
        return
    
    symbol = result
    
    # Check and deduct credits (bypass for lifetime premium)
    success, msg = check_and_deduct_credits(user_id, COST_SINGLE_SIGNAL)
    if not success:
        await update.message.reply_text(
            f"❌ {msg}\n\n"
            "💡 Get more credits:\n"
            "• Use /credits to check balance\n"
            "• Use /subscribe for premium access"
        )
        return
    
    # Show loading message
    loading_msg = await update.message.reply_text(
        f"⏳ Analyzing {symbol}...\n"
        f"📊 Generating signal with Supply & Demand analysis...\n"
        f"⏱️ Estimated time: 3-5 seconds"
    )
    
    try:
        # Generate signal
        generator = FuturesSignalGenerator()
        signal_text = await generator.generate_signal(symbol, '1h')
        
        # Delete loading message
        await loading_msg.delete()
        
        # Send signal
        await update.message.reply_text(signal_text)
        
        print(f"✅ Signal generated for {symbol} by user {user_id}")
        
    except Exception as e:
        await loading_msg.delete()
        error_msg = str(e)[:100]
        await update.message.reply_text(
            f"❌ Error generating signal for {symbol}\n\n"
            f"Details: {error_msg}\n\n"
            "Please try again or contact support if the issue persists."
        )
        print(f"❌ Error in cmd_analyze for {symbol}: {e}")


async def cmd_futures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /futures <symbol> <timeframe> command.
    Generate single futures signal with custom timeframe.
    
    Usage: /futures BTCUSDT 4h
    Cost: 20 credits (FREE for lifetime premium)
    """
    user_id = update.effective_user.id
    
    # Check rate limit
    is_allowed, cooldown = check_rate_limit(user_id)
    if not is_allowed:
        await update.message.reply_text(
            f"❌ Too many requests. Please wait {cooldown} seconds before trying again."
        )
        return
    
    # Parse arguments
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /futures <symbol> [timeframe]\n\n"
            "Examples:\n"
            "• /futures BTCUSDT 1h\n"
            "• /futures ETH 4h\n"
            "• /futures SOLUSDT (default: 1h)\n\n"
            "Valid timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 1d\n\n"
            "💰 Cost: 20 credits\n"
            "👑 Lifetime Premium: FREE"
        )
        return
    
    # Validate symbol
    symbol_input = context.args[0]
    is_valid, result = validate_symbol(symbol_input)
    
    if not is_valid:
        await update.message.reply_text(f"❌ {result}")
        return
    
    symbol = result
    
    # Validate timeframe (default: 1h)
    timeframe = '1h'
    if len(context.args) > 1:
        is_valid, result = validate_timeframe(context.args[1])
        if not is_valid:
            await update.message.reply_text(f"❌ {result}")
            return
        timeframe = result
    
    # Check and deduct credits
    success, msg = check_and_deduct_credits(user_id, COST_SINGLE_SIGNAL)
    if not success:
        await update.message.reply_text(
            f"❌ {msg}\n\n"
            "💡 Get more credits:\n"
            "• Use /credits to check balance\n"
            "• Use /subscribe for premium access"
        )
        return
    
    # Show loading message
    loading_msg = await update.message.reply_text(
        f"⏳ Generating futures signal for {symbol} ({timeframe.upper()})...\n"
        f"📊 Analyzing market structure and S&D zones...\n"
        f"⏱️ Estimated time: 3-5 seconds"
    )
    
    try:
        # Generate signal
        generator = FuturesSignalGenerator()
        signal_text = await generator.generate_signal(symbol, timeframe)
        
        # Delete loading message
        await loading_msg.delete()
        
        # Send signal
        await update.message.reply_text(signal_text)
        
        print(f"✅ Futures signal generated for {symbol} {timeframe} by user {user_id}")
        
    except Exception as e:
        await loading_msg.delete()
        error_msg = str(e)[:100]
        await update.message.reply_text(
            f"❌ Error generating signal for {symbol} ({timeframe})\n\n"
            f"Details: {error_msg}\n\n"
            "Please try again or contact support if the issue persists."
        )
        print(f"❌ Error in cmd_futures for {symbol} {timeframe}: {e}")


async def cmd_futures_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /futures_signals command.
    Generate multi-coin signals (10 top coins).
    
    Usage: /futures_signals
    Cost: 60 credits (FREE for lifetime premium)
    """
    user_id = update.effective_user.id
    
    # Check rate limit
    is_allowed, cooldown = check_rate_limit(user_id)
    if not is_allowed:
        await update.message.reply_text(
            f"❌ Too many requests. Please wait {cooldown} seconds before trying again."
        )
        return
    
    # Check and deduct credits
    success, msg = check_and_deduct_credits(user_id, COST_MULTI_SIGNAL)
    if not success:
        await update.message.reply_text(
            f"❌ {msg}\n\n"
            "💡 Get more credits:\n"
            "• Use /credits to check balance\n"
            "• Use /subscribe for premium access"
        )
        return
    
    # Show loading message
    loading_msg = await update.message.reply_text(
        "⏳ Generating multi-coin signals...\n"
        "📊 Scanning 10 top coins\n"
        "🔗 Data sources: Binance + CryptoCompare + Helius\n"
        "⏱️ Estimated time: 10-15 seconds\n\n"
        "Please wait..."
    )
    
    try:
        # Generate multi signals
        generator = FuturesSignalGenerator()
        signals_text = await generator.generate_multi_signals()
        
        # Delete loading message
        await loading_msg.delete()
        
        # Send signals (may need to split if too long)
        if len(signals_text) > 4096:
            # Telegram message limit is 4096 characters
            # Split into multiple messages
            parts = []
            current_part = ""
            
            for line in signals_text.split('\n'):
                if len(current_part) + len(line) + 1 > 4000:
                    parts.append(current_part)
                    current_part = line + '\n'
                else:
                    current_part += line + '\n'
            
            if current_part:
                parts.append(current_part)
            
            # Send each part
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(signals_text)
        
        print(f"✅ Multi-coin signals generated by user {user_id}")
        
    except Exception as e:
        await loading_msg.delete()
        error_msg = str(e)[:100]
        await update.message.reply_text(
            f"❌ Error generating multi-coin signals\n\n"
            f"Details: {error_msg}\n\n"
            "Please try again or contact support if the issue persists."
        )
        print(f"❌ Error in cmd_futures_signals: {e}")


# Command aliases
cmd_signal = cmd_analyze  # /signal is alias for /analyze
cmd_signals = cmd_futures_signals  # /signals is alias for /futures_signals
