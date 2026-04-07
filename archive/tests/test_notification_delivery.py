#!/usr/bin/env python3
"""
Test notification delivery to verify if users are actually receiving messages.
This will send a test message to all active users and log the results.
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv('Bismillah/.env')
sys.path.insert(0, 'Bismillah')

from telegram import Bot
from app.supabase_repo import _client

async def test_notification_delivery():
    """Test if notifications are actually being delivered to users"""
    
    print("=" * 80)
    print("NOTIFICATION DELIVERY TEST")
    print("=" * 80)
    
    # Initialize bot
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found")
        return
    
    bot = Bot(token=token)
    
    # Get all active sessions
    try:
        result = _client().table("autotrade_sessions").select("*").in_(
            "status", ["active", "uid_verified"]
        ).execute()
        
        sessions = result.data or []
        print(f"\n📊 Found {len(sessions)} active sessions")
        
        if not sessions:
            print("❌ No active sessions found")
            return
        
        # Test sending to each user
        success_count = 0
        failed_count = 0
        blocked_count = 0
        
        test_message = (
            "🔔 <b>Test Notification</b>\n\n"
            "Ini adalah test notification untuk memastikan bot dapat mengirim pesan ke Anda.\n\n"
            "Jika Anda menerima pesan ini, berarti sistem notifikasi berfungsi dengan baik.\n\n"
            "Abaikan pesan ini."
        )
        
        for session in sessions:
            user_id = session.get("telegram_id")
            if not user_id:
                continue
            
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=test_message,
                    parse_mode='HTML'
                )
                success_count += 1
                print(f"✅ User {user_id}: Message sent successfully")
                await asyncio.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                error_str = str(e).lower()
                if 'blocked' in error_str or 'bot was blocked' in error_str:
                    blocked_count += 1
                    print(f"🚫 User {user_id}: Bot blocked by user")
                elif 'chat not found' in error_str:
                    blocked_count += 1
                    print(f"🚫 User {user_id}: Chat not found (user never started bot)")
                else:
                    failed_count += 1
                    print(f"❌ User {user_id}: Failed - {e}")
        
        print("\n" + "=" * 80)
        print("DELIVERY TEST RESULTS")
        print("=" * 80)
        print(f"✅ Successfully delivered: {success_count}")
        print(f"🚫 Blocked/Not started: {blocked_count}")
        print(f"❌ Failed (other errors): {failed_count}")
        print(f"📊 Total users: {len(sessions)}")
        print(f"📈 Delivery rate: {(success_count / len(sessions) * 100):.1f}%")
        print("=" * 80)
        
        if blocked_count > 0:
            print(f"\n⚠️ WARNING: {blocked_count} users have blocked the bot or never started it!")
            print("These users will NOT receive any notifications.")
            print("This is the most likely reason why users report not receiving notifications.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_notification_delivery())
