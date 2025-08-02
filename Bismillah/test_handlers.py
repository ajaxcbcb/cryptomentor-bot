
#!/usr/bin/env python3
"""
Test bot handlers registration
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import bot components
from bot import TelegramBot

async def test_handlers():
    """Test handlers registration"""
    print("🔍 Testing Bot Handlers")
    print("=" * 40)
    
    try:
        # Initialize bot
        bot = TelegramBot()
        print("✅ Bot initialized")
        
        # Check if application is created
        if bot.application:
            print("✅ Telegram Application created")
            
            # Check handlers
            handlers = bot.application.handlers
            print(f"📋 Total handler groups: {len(handlers)}")
            
            # Count handlers by type
            command_handlers = 0
            message_handlers = 0
            callback_handlers = 0
            
            for group_id, group_handlers in handlers.items():
                print(f"📂 Group {group_id}: {len(group_handlers)} handlers")
                for handler in group_handlers:
                    handler_type = type(handler).__name__
                    if 'Command' in handler_type:
                        command_handlers += 1
                    elif 'Message' in handler_type:
                        message_handlers += 1
                    elif 'Callback' in handler_type:
                        callback_handlers += 1
                    print(f"  ├─ {handler_type}")
            
            print(f"\n📊 Handler Summary:")
            print(f"  🎯 Command handlers: {command_handlers}")
            print(f"  💬 Message handlers: {message_handlers}")
            print(f"  🔘 Callback handlers: {callback_handlers}")
            
            # Test specific critical handlers
            print(f"\n🔍 Checking critical handlers...")
            
            # Try to find start command handler
            start_found = False
            help_found = False
            
            for group_handlers in handlers.values():
                for handler in group_handlers:
                    if hasattr(handler, 'command') and handler.command == ['start']:
                        start_found = True
                        print("✅ /start handler found")
                    elif hasattr(handler, 'command') and handler.command == ['help']:
                        help_found = True
                        print("✅ /help handler found")
            
            if not start_found:
                print("❌ /start handler NOT found")
            if not help_found:
                print("❌ /help handler NOT found")
                
            return True
        else:
            print("❌ Telegram Application not created")
            return False
            
    except Exception as e:
        print(f"❌ Handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_handlers())
    if result:
        print("\n✅ Handler test PASSED")
    else:
        print("\n❌ Handler test FAILED")
