#!/usr/bin/env python3
"""
Restart all active autotrade engines
"""

import os
import sys
import asyncio
sys.path.insert(0, 'Bismillah')

from dotenv import load_dotenv
load_dotenv('Bismillah/.env')

from app.supabase_repo import _client
from app.autotrade_engine import start_engine, is_running, stop_engine
from app.handlers_autotrade import get_user_api_keys
from telegram import Bot

async def main():
    s = _client()
    
    # Get bot token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env")
        return
    
    bot = Bot(token=bot_token)
    
    # Get all active sessions
    result = s.table("autotrade_sessions").select("*").eq("status", "active").execute()
    sessions = result.data or []
    
    print(f"\n{'='*80}")
    print(f"RESTARTING ALL ENGINES")
    print(f"{'='*80}\n")
    print(f"Found {len(sessions)} active sessions\n")
    
    restarted = 0
    failed = 0
    
    for session in sessions:
        user_id = session['telegram_id']
        capital = session.get('initial_deposit', 0)
        leverage = session.get('leverage', 10)
        trading_mode = session.get('trading_mode', 'swing')
        
        print(f"User {user_id} ({trading_mode}, {capital} USDT, {leverage}x)...")
        
        # Stop if running
        if is_running(user_id):
            print(f"  Stopping existing engine...")
            stop_engine(user_id)
            await asyncio.sleep(1)
        
        # Get API keys
        keys = get_user_api_keys(user_id)
        if not keys:
            print(f"  ❌ No API keys found")
            failed += 1
            continue
        
        try:
            # Check if user has premium skill
            from app.skills_repo import has_skill
            is_premium = has_skill(user_id, "dual_tp_rr3")
            
            # Start engine
            start_engine(
                bot=bot,
                user_id=user_id,
                api_key=keys['api_key'],
                api_secret=keys['api_secret'],
                amount=capital,
                leverage=leverage,
                notify_chat_id=user_id,
                is_premium=is_premium,
                silent=False,  # Send notification
                exchange_id=keys.get('exchange', 'bitunix'),
            )
            
            print(f"  ✅ Engine started")
            restarted += 1
            
            # Send notification
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        "🔄 <b>AutoTrade Engine Restarted</b>\n\n"
                        "✅ Your engine has been restarted with improved stability\n\n"
                        "📊 <b>Settings:</b>\n"
                        f"• Mode: <b>{trading_mode.title()}</b>\n"
                        f"• Capital: <b>{capital} USDT</b>\n"
                        f"• Leverage: <b>{leverage}x</b>\n\n"
                        "🔧 <b>What's New:</b>\n"
                        "• Fixed connection issues\n"
                        "• Improved signal generation\n"
                        "• Better error handling\n\n"
                        "Use /autotrade to check status."
                    ),
                    parse_mode='HTML'
                )
                print(f"  📨 Notification sent")
            except Exception as notify_err:
                print(f"  ⚠️  Notification failed: {notify_err}")
            
            await asyncio.sleep(0.5)  # Rate limit
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"RESTART COMPLETE")
    print(f"{'='*80}")
    print(f"✅ Restarted: {restarted}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {len(sessions)}")
    print()

if __name__ == "__main__":
    asyncio.run(main())
