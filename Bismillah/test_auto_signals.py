
#!/usr/bin/env python3
"""
Test script untuk auto signals functionality
"""
import asyncio
import os
import sys
sys.path.append('.')

from database import Database
from snd_auto_signals import initialize_auto_signals

class MockBot:
    def __init__(self):
        self.sent_messages = []
        
    class MockApplication:
        class MockBot:
            async def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None):
                print(f"📤 MOCK SEND: chat_id={chat_id}, text_length={len(text)}")
                print(f"📝 Message preview: {text[:200]}...")
                return {"message_id": 123}
                
        def __init__(self):
            self.bot = self.MockBot()
    
    def __init__(self):
        self.application = self.MockApplication()

async def test_auto_signals():
    """Test auto signals system"""
    print("🧪 Testing Auto Signals System")
    print("=" * 50)
    
    # Test 1: Database connection
    print("1️⃣ Testing database connection...")
    db = Database()
    
    # Test 2: Check eligible users
    print("2️⃣ Testing eligible users query...")
    eligible_users = db.get_eligible_auto_signal_users()
    print(f"✅ Found {len(eligible_users)} eligible users")
    
    # Test 3: Initialize auto signals
    print("3️⃣ Testing auto signals initialization...")
    mock_bot = MockBot()
    auto_signals = initialize_auto_signals(mock_bot)
    
    if auto_signals:
        print("✅ Auto signals initialized successfully")
        
        # Test 4: Manual signal generation
        print("4️⃣ Testing manual signal generation...")
        try:
            # Generate one test signal manually
            test_signal = {
                'symbol': 'BTC',
                'direction': 'LONG',
                'entry_price': 50000,
                'tp1': 51500,
                'tp2': 53000,
                'sl': 48500,
                'confidence': 85,
                'risk_reward': 2.5,
                'current_price': 50000,
                'trend': 'bullish',
                'market_structure': 'long_bias',
                'risk_level': 'medium',
                'timeframe': '1h',
                'scan_time': '10:00:00',
                'reason': 'Test signal',
                'zone_strength': 80,
                'long_ratio': 45,
                'change_24h': 2.3
            }
            
            # Test signal formatting
            message = auto_signals._format_auto_signals_message([test_signal])
            print(f"✅ Signal formatted successfully ({len(message)} chars)")
            
            # Test signal sending
            print("5️⃣ Testing signal broadcast...")
            await auto_signals._send_signals_to_users([test_signal], eligible_users)
            
        except Exception as e:
            print(f"❌ Error in manual test: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Auto signals initialization failed")

if __name__ == "__main__":
    asyncio.run(test_auto_signals())
