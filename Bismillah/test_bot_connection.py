
#!/usr/bin/env python3
"""
Test bot connection and handlers
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Bot

# Load environment variables
load_dotenv()

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_bot_connection():
    """Test basic bot connection"""
    print("🔍 Testing Bot Connection")
    print("=" * 40)
    
    # Get token
    token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
    
    if not token:
        print("❌ No bot token found!")
        return False
    
    print(f"🔑 Token found: {token[:10]}...{token[-10:]}")
    
    try:
        # Create bot instance
        bot = Bot(token=token)
        
        # Test getMe
        print("📞 Testing getMe...")
        bot_info = await bot.get_me()
        
        print(f"✅ Bot connected successfully!")
        print(f"📝 Bot username: @{bot_info.username}")
        print(f"🆔 Bot ID: {bot_info.id}")
        print(f"👤 Bot name: {bot_info.first_name}")
        print(f"🔗 Can join groups: {bot_info.can_join_groups}")
        print(f"📱 Can read all group messages: {bot_info.can_read_all_group_messages}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot connection failed: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bot_connection())
    if result:
        print("\n✅ Bot connection test PASSED")
    else:
        print("\n❌ Bot connection test FAILED")
