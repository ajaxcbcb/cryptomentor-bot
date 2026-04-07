#!/bin/bash
# Broadcast engine status using bot's Python environment

cd /root/cryptomentor-bot/Bismillah

# Run Python script with proper environment
/root/cryptomentor-bot/venv/bin/python3 << 'PYTHON_SCRIPT'
import asyncio
import sys
import os

# Load .env if exists
from pathlib import Path
env_file = Path('.env')
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv()
else:
    # Try parent directory
    env_file = Path('../.env')
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

# Now import bot modules
from telegram import Bot
from app.supabase_repo import _client

async def send_status():
    # Get token
    token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN') or os.getenv('TOKEN')
    
    if not token:
        print("❌ Bot token not found")
        print(f"   Checked: TELEGRAM_BOT_TOKEN, BOT_TOKEN, TOKEN")
        print(f"   .env exists: {Path('.env').exists()}")
        return
    
    print(f"✅ Token found: {token[:20]}...")
    
    bot = Bot(token=token)
    s = _client()
    
    # Get active sessions
    result = s.table("autotrade_sessions").select(
        "telegram_id, trading_mode, initial_deposit, leverage"
    ).eq("status", "active").execute()
    
    print(f"\n📊 Sending to {len(result.data)} active users...\n")
    
    sent = 0
    failed = 0
    
    for sess in result.data:
        uid = sess.get('telegram_id')
        mode = sess.get('trading_mode', 'swing').upper()
        cap = sess.get('initial_deposit', 0)
        lev = sess.get('leverage', 10)
        
        msg = (
            f"✅ <b>AutoTrade Engine: ACTIVE</b>\n\n"
            f"🤖 Your engine is running 24/7\n\n"
            f"<b>Settings:</b>\n"
            f"• Mode: {mode}\n"
            f"• Capital: ${cap:.1f}\n"
            f"• Leverage: {lev}x\n\n"
            f"<b>Status:</b> Monitoring market & ready to trade\n\n"
            f"💡 No action needed - engine works automatically\n\n"
            f"Check status: /autotrade"
        )
        
        try:
            await bot.send_message(chat_id=uid, text=msg, parse_mode='HTML')
            print(f"✅ {uid}")
            sent += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"❌ {uid}: {e}")
            failed += 1
    
    print(f"\n✅ Sent: {sent}, Failed: {failed}\n")

asyncio.run(send_status())
PYTHON_SCRIPT
