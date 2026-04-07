#!/usr/bin/env python3
"""
Send engine status notification via bot's main.py
This runs in the bot's context so it has access to everything
"""

import sys
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

import asyncio
from telegram import Bot
from app.supabase_repo import _client
import os

# Load environment from bot's context
os.chdir('/root/cryptomentor-bot/Bismillah')

async def send_notifications():
    """Send status to all active users"""
    
    # Get token from bot.py's method
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        # Try alternative names
        token = os.getenv('BOT_TOKEN') or os.getenv('TOKEN')
    
    if not token:
        print("❌ Cannot find bot token")
        return
    
    bot = Bot(token=token)
    
    # Get active sessions
    s = _client()
    result = s.table("autotrade_sessions").select(
        "telegram_id, trading_mode, risk_mode, initial_deposit, leverage"
    ).eq("status", "active").execute()
    
    print(f"\n✅ Found {len(result.data)} active engines\n")
    
    for session in result.data:
        user_id = session.get('telegram_id')
        mode = session.get('trading_mode', 'swing').upper()
        capital = session.get('initial_deposit', 0)
        leverage = session.get('leverage', 10)
        
        msg = (
            f"✅ <b>Engine Status: ACTIVE & RUNNING</b>\n\n"
            f"🤖 Your AutoTrade engine is currently <b>ACTIVE</b> and monitoring the market 24/7.\n\n"
            f"<b>Current Settings:</b>\n"
            f"• Mode: {mode}\n"
            f"• Capital: ${capital:.2f} USDT\n"
            f"• Leverage: {leverage}x\n\n"
            f"<b>What this means:</b>\n"
            f"✓ Engine scans market automatically\n"
            f"✓ Executes trades when signals appear\n"
            f"✓ Manages positions with TP/SL\n"
            f"✓ No manual action needed from you\n\n"
            f"💡 Your engine works 24/7 even when you're offline.\n\n"
            f"📊 Check anytime: /autotrade"
        )
        
        try:
            await bot.send_message(chat_id=user_id, text=msg, parse_mode='HTML')
            print(f"✅ Sent to {user_id}")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"❌ Failed {user_id}: {e}")
    
    print(f"\n✅ Notifications sent!\n")

if __name__ == "__main__":
    asyncio.run(send_notifications())
