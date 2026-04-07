#!/usr/bin/env python3
"""
Simple script to restart engines on VPS (run from VPS directly)
This script loads environment from the running bot process
"""

import asyncio
import logging
from telegram import Bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def restart_engines():
    """Send restart command to all active users via bot"""
    
    # Import after path is set
    from app.supabase_repo import _client
    from app.autotrade_engine import start_engine, is_running, stop_engine
    from app.handlers_autotrade import get_user_api_keys
    from app.skills_repo import has_skill
    import os
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    bot = Bot(token=bot_token)
    
    s = _client()
    result = s.table("autotrade_sessions").select("*").eq("status", "active").execute()
    sessions = result.data or []
    
    logger.info(f"Found {len(sessions)} active sessions")
    
    restarted = 0
    failed = 0
    
    for session in sessions:
        user_id = session['telegram_id']
        capital = session.get('initial_deposit', 0)
        leverage = session.get('leverage', 10)
        trading_mode = session.get('trading_mode', 'swing')
        
        logger.info(f"Restarting user {user_id}...")
        
        # Stop if running
        if is_running(user_id):
            stop_engine(user_id)
            await asyncio.sleep(1)
        
        # Get API keys
        keys = get_user_api_keys(user_id)
        if not keys:
            logger.error(f"No API keys for user {user_id}")
            failed += 1
            continue
        
        try:
            is_premium = has_skill(user_id, "dual_tp_rr3")
            
            start_engine(
                bot=bot,
                user_id=user_id,
                api_key=keys['api_key'],
                api_secret=keys['api_secret'],
                amount=capital,
                leverage=leverage,
                notify_chat_id=user_id,
                is_premium=is_premium,
                silent=False,
                exchange_id=keys.get('exchange', 'bitunix'),
            )
            
            logger.info(f"✅ Engine started for user {user_id}")
            restarted += 1
            
            # Send notification
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        "🔄 <b>AutoTrade Engine Restarted</b>\n\n"
                        "✅ Your engine has been restarted with fixes\n\n"
                        "📊 <b>Settings:</b>\n"
                        f"• Mode: <b>{trading_mode.title()}</b>\n"
                        f"• Capital: <b>{capital} USDT</b>\n"
                        f"• Leverage: <b>{leverage}x</b>\n\n"
                        "🔧 <b>Improvements:</b>\n"
                        "• Fixed connection stability\n"
                        "• Improved signal generation\n"
                        "• Better error handling\n\n"
                        "Use /autotrade to check status."
                    ),
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.warning(f"Notification failed for {user_id}: {e}")
            
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Failed to restart user {user_id}: {e}")
            failed += 1
    
    logger.info(f"Restart complete: {restarted} success, {failed} failed")

if __name__ == "__main__":
    asyncio.run(restart_engines())
