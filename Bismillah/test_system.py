
#!/usr/bin/env python3
"""
Comprehensive System Test for CryptoMentor AI
Combines all testing functionality into one file
"""

import os
import sys
import asyncio
import requests
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from crypto_api import CryptoAPI
from ai_assistant import AIAssistant

load_dotenv()

class SystemTester:
    def __init__(self):
        self.db = Database()
        self.crypto_api = CryptoAPI()
        self.ai = AIAssistant()

    def test_database(self):
        """Test database functionality"""
        print("🗄️ Testing Database...")
        try:
            stats = self.db.get_bot_statistics()
            print(f"✅ Database: {stats['total_users']} users, {stats['premium_users']} premium")
            return True
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False

    def test_apis(self):
        """Test all API connections"""
        print("🌐 Testing APIs...")
        
        # Test Binance
        try:
            response = requests.get("https://api.binance.com/api/v3/ping", timeout=10)
            binance_ok = response.status_code == 200
            print(f"⚡ Binance: {'✅' if binance_ok else '❌'}")
        except:
            binance_ok = False
            print("⚡ Binance: ❌")

        # Test CoinGecko
        try:
            response = requests.get("https://api.coingecko.com/api/v3/ping", timeout=10)
            coingecko_ok = response.status_code == 200
            print(f"🦎 CoinGecko: {'✅' if coingecko_ok else '❌'}")
        except:
            coingecko_ok = False
            print("🦎 CoinGecko: ❌")

        return binance_ok and coingecko_ok

    def test_premium_functions(self):
        """Test premium functionality"""
        print("⭐ Testing Premium Functions...")
        test_user_id = 123456789
        
        try:
            # Create test user if not exists
            if not self.db.get_user(test_user_id):
                self.db.create_user(test_user_id, "testuser", "Test User", language_code='id')
            
            # Test premium grant
            success = self.db.grant_premium(test_user_id, 30)
            is_premium = self.db.is_user_premium(test_user_id)
            
            # Test revoke
            self.db.revoke_premium(test_user_id)
            
            print(f"✅ Premium functions: Grant={success}, Check={is_premium}")
            return success and is_premium
        except Exception as e:
            print(f"❌ Premium error: {e}")
            return False

    async def test_bot_connection(self):
        """Test bot connection"""
        print("🤖 Testing Bot Connection...")
        from telegram import Bot
        
        token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
        if not token:
            print("❌ No bot token found")
            return False
        
        try:
            bot = Bot(token=token)
            bot_info = await bot.get_me()
            print(f"✅ Bot connected: @{bot_info.username}")
            return True
        except Exception as e:
            print(f"❌ Bot error: {e}")
            return False

    def test_real_time_data(self):
        """Test real-time data fetching"""
        print("📊 Testing Real-time Data...")
        
        test_symbols = ['BTC', 'ETH', 'BNB']
        success_count = 0
        
        for symbol in test_symbols:
            try:
                price_data = self.crypto_api.get_multi_api_price(symbol, force_refresh=True)
                if 'error' not in price_data and price_data.get('price', 0) > 0:
                    price = price_data.get('price', 0)
                    print(f"✅ {symbol}: ${price:,.2f}")
                    success_count += 1
                else:
                    print(f"❌ {symbol}: Failed")
            except Exception as e:
                print(f"❌ {symbol}: {str(e)[:30]}...")
        
        return success_count >= len(test_symbols) * 0.5

    async def run_all_tests(self):
        """Run comprehensive system test"""
        print("🧪 CryptoMentor AI - Comprehensive System Test")
        print("=" * 60)
        
        results = {
            'database': self.test_database(),
            'apis': self.test_apis(),
            'premium': self.test_premium_functions(),
            'bot': await self.test_bot_connection(),
            'realtime': self.test_real_time_data()
        }
        
        print("\n📊 Test Results:")
        print("=" * 30)
        
        passed = sum(results.values())
        total = len(results)
        
        for test, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test.upper()}: {status}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
        
        if passed == total:
            print("🟢 All systems operational!")
        elif passed >= total * 0.8:
            print("🟡 Most systems working")
        else:
            print("🔴 Critical issues detected")
        
        return passed >= total * 0.8

async def main():
    """Main test function"""
    tester = SystemTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
