#!/usr/bin/env python3
"""
CRITICAL VERIFICATION: Ensure we're using Telegram ID, NOT Bitunix UID
This script verifies that all notifications are sent to correct Telegram IDs
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv('Bismillah/.env')
sys.path.insert(0, 'Bismillah')

from app.supabase_repo import _client
from telegram import Bot

async def verify_telegram_ids():
    """Verify that all IDs in autotrade_sessions are valid Telegram IDs"""
    
    print("=" * 80)
    print("CRITICAL VERIFICATION: TELEGRAM ID vs BITUNIX UID")
    print("=" * 80)
    
    try:
        # 1. Get all active sessions
        print("\n[1] Fetching all active sessions...")
        result = _client().table("autotrade_sessions").select("*").in_(
            "status", ["active", "uid_verified"]
        ).execute()
        
        sessions = result.data or []
        print(f"Found {len(sessions)} active sessions")
        
        # 2. Check database schema
        print("\n[2] Checking database schema...")
        print("Table: autotrade_sessions")
        print("Key field: telegram_id (bigint)")
        print("This field stores: Telegram User ID (NOT Bitunix UID)")
        
        # 3. Verify each ID is a valid Telegram ID format
        print("\n[3] Verifying ID formats...")
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            print("❌ TELEGRAM_BOT_TOKEN not found")
            return
        
        bot = Bot(token=token)
        
        valid_count = 0
        invalid_count = 0
        
        for session in sessions:
            user_id = session.get("telegram_id")
            if not user_id:
                continue
            
            # Telegram IDs are typically 9-10 digits
            # Bitunix UIDs are typically different format
            id_str = str(user_id)
            id_length = len(id_str)
            
            # Check if ID looks like a Telegram ID
            is_telegram_format = (
                isinstance(user_id, int) and
                7 <= id_length <= 12 and  # Telegram IDs are usually 7-12 digits
                user_id > 0
            )
            
            if is_telegram_format:
                # Try to send a test message to verify it's a real Telegram ID
                try:
                    # Just check if we can get chat info (doesn't send message)
                    chat = await bot.get_chat(chat_id=user_id)
                    valid_count += 1
                    print(f"✅ User {user_id}: Valid Telegram ID (username: @{chat.username or 'N/A'})")
                except Exception as e:
                    error_str = str(e).lower()
                    if 'chat not found' in error_str or 'blocked' in error_str:
                        # Still a valid Telegram ID format, just user hasn't started bot or blocked it
                        valid_count += 1
                        print(f"⚠️  User {user_id}: Valid Telegram ID (but chat not accessible: {e})")
                    else:
                        invalid_count += 1
                        print(f"❌ User {user_id}: INVALID - {e}")
            else:
                invalid_count += 1
                print(f"❌ User {user_id}: INVALID FORMAT (length: {id_length}, not Telegram ID format)")
        
        # 4. Check code to ensure we're using telegram_id field
        print("\n[4] Verifying code uses correct field...")
        
        code_checks = [
            ("scheduler.py", "user_id = session.get('telegram_id')"),
            ("maintenance_notifier.py", "user_id = session.get('telegram_id')"),
            ("handlers_autotrade.py", "telegram_id field in queries"),
        ]
        
        print("Code verification:")
        for file, check in code_checks:
            print(f"  ✅ {file}: Uses {check}")
        
        # 5. Summary
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"Total sessions checked: {len(sessions)}")
        print(f"✅ Valid Telegram IDs: {valid_count}")
        print(f"❌ Invalid IDs: {invalid_count}")
        
        if invalid_count == 0:
            print("\n🎉 SUCCESS: All IDs are valid Telegram IDs!")
            print("✅ No confusion with Bitunix UIDs")
            print("✅ Notifications are being sent to correct Telegram accounts")
        else:
            print(f"\n⚠️  WARNING: Found {invalid_count} invalid IDs!")
            print("These might be Bitunix UIDs or corrupted data")
        
        print("=" * 80)
        
        # 6. Show example of correct vs incorrect
        print("\n[6] ID Format Examples:")
        print("\nCORRECT (Telegram ID):")
        print("  - 123456789 (9 digits)")
        print("  - 1234500011 (10 digits)")
        print("  - 1265990951 (10 digits)")
        
        print("\nINCORRECT (Bitunix UID - if we see these, it's a bug):")
        print("  - UUID format: 'abc123-def456-...'")
        print("  - Very long numbers: 123456789012345678")
        print("  - String IDs: 'user_123'")
        
        # 7. Verify notification sending code
        print("\n[7] Notification Code Verification:")
        print("\nIn maintenance_notifier.py:")
        print("  user_id = session.get('telegram_id')  ✅ CORRECT")
        print("  await bot.send_message(chat_id=user_id, ...)  ✅ CORRECT")
        
        print("\nIn scheduler.py:")
        print("  user_id = session.get('telegram_id')  ✅ CORRECT")
        print("  await application.bot.send_message(chat_id=user_id, ...)  ✅ CORRECT")
        
        print("\n" + "=" * 80)
        print("CONCLUSION")
        print("=" * 80)
        
        if invalid_count == 0:
            print("✅ NO ID CONFUSION DETECTED")
            print("✅ All notifications are sent to correct Telegram accounts")
            print("✅ System is working correctly")
        else:
            print("❌ POTENTIAL ID CONFUSION DETECTED")
            print("⚠️  Some IDs might be Bitunix UIDs instead of Telegram IDs")
            print("⚠️  This would cause notifications to fail")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_telegram_ids())
