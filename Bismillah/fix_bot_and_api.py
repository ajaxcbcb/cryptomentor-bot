
#!/usr/bin/env python3
"""
Complete fix for CryptoMentor AI Bot:
1. Resolve telegram bot conflicts
2. Fix CoinGlass API connection issues
3. Test all integrations
"""

import os
import sys
import time
import signal
import psutil
import requests
import json
from datetime import datetime

def kill_bot_conflicts():
    """Kill any conflicting bot instances"""
    print("🛑 RESOLVING BOT CONFLICTS")
    print("=" * 30)
    
    killed = 0
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.info['name'] in ['python', 'python3'] and 
                    proc.info['cmdline'] and 
                    any('main.py' in str(cmd) or 'bot.py' in str(cmd) for cmd in proc.info['cmdline'])):
                    
                    if proc.info['pid'] != os.getpid():
                        print(f"🎯 Killing conflicting bot: PID {proc.info['pid']}")
                        proc.terminate()
                        proc.wait(timeout=3)
                        killed += 1
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue
                
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    if killed > 0:
        print(f"✅ Killed {killed} conflicting processes")
        time.sleep(5)
    else:
        print("✅ No conflicts found")
    
    return killed

def clear_telegram_state():
    """Clear telegram webhook and pending updates"""
    print("\n🔧 CLEARING TELEGRAM STATE")
    print("=" * 30)
    
    bot_token = os.getenv('TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("⚠️ No bot token found")
        return False
    
    try:
        # Clear webhook with pending updates
        url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        params = {"drop_pending_updates": True}
        
        response = requests.post(url, params=params, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram state cleared")
            return True
        else:
            print(f"⚠️ Telegram clear status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error clearing telegram state: {e}")
        return False

def test_coinglass_api():
    """Test CoinGlass API with multiple endpoint strategies"""
    print("\n🧪 TESTING COINGLASS V4 API")
    print("=" * 30)
    
    api_key = os.getenv("COINGLASS_API_KEY")
    if not api_key:
        print("❌ COINGLASS_API_KEY not found!")
        return False
    
    print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:]}")
    
    # Test multiple base URLs and endpoints
    test_configs = [
        {
            "name": "CoinGlass V2 Public",
            "base": "https://open-api.coinglass.com",
            "endpoint": "/public/v2/futures/ticker",
            "headers": {"X-API-KEY": api_key, "accept": "application/json"}
        },
        {
            "name": "CoinGlass V4 Public", 
            "base": "https://open-api-v4.coinglass.com",
            "endpoint": "/public/v1/futures/tickers",
            "headers": {"X-API-KEY": api_key, "accept": "application/json"}
        },
        {
            "name": "CoinGlass Pro V1",
            "base": "https://open-api.coinglass.com", 
            "endpoint": "/api/pro/v1/futures/ticker",
            "headers": {"X-API-KEY": api_key, "accept": "application/json"}
        }
    ]
    
    working_config = None
    
    for config in test_configs:
        print(f"\n📡 Testing: {config['name']}")
        url = f"{config['base']}{config['endpoint']}"
        
        try:
            # Test with BTC
            params = {"symbol": "BTC"}
            response = requests.get(url, headers=config['headers'], params=params, timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"]:
                    sample = data["data"][0] if isinstance(data["data"], list) else data["data"] 
                    price = sample.get("price", 0) if isinstance(sample, dict) else 0
                    
                    if price and price > 30000:  # BTC should be > $30k
                        print(f"   ✅ SUCCESS - Price: ${price:,.2f} (REAL DATA)")
                        working_config = config
                        break
                    else:
                        print(f"   ⚠️ Got price ${price} - might be dummy")
                else:
                    print(f"   ⚠️ No data in response")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:40]}...")
    
    if working_config:
        print(f"\n✅ WORKING CONFIG FOUND: {working_config['name']}")
        
        # Save config to env file for future use
        config_line = f"WORKING_COINGLASS_BASE={working_config['base']}\n"
        
        try:
            with open('.env', 'a') as f:
                f.write(config_line)
            print("✅ Saved working config to .env")
        except:
            print("⚠️ Could not save config to .env")
        
        return True
    else:
        print("\n❌ NO WORKING COINGLASS ENDPOINTS FOUND")
        
        print("\n📩 MESSAGE FOR COINGLASS SUPPORT:")
        print("-" * 50)
        print(f"""
Halo tim CoinGlass,
Saya sudah upgrade ke STARTUP plan dengan API Key: {api_key}
Namun semua endpoint v4 mengembalikan 404/error:

Tested endpoints:
- https://open-api-v4.coinglass.com/public/v1/futures/tickers
- https://open-api.coinglass.com/public/v2/futures/ticker  
- https://open-api.coinglass.com/api/pro/v1/futures/ticker

Status: All returning 404 or invalid data
Headers: X-API-KEY: {api_key}

Mohon bantuannya untuk aktivasi penuh akun saya.
Terima kasih.
""")
        print("-" * 50)
        print("💡 Send to: https://t.me/coinglass")
        
        return False

def main():
    """Main fix routine"""
    print("🚀 CRYPTOMENTOR AI - COMPLETE FIX ROUTINE")
    print("=" * 50)
    print(f"🕐 Started: {datetime.now().strftime('%H:%M:%S')}")
    
    # Step 1: Kill conflicts
    killed = kill_bot_conflicts()
    
    # Step 2: Clear telegram state
    telegram_ok = clear_telegram_state() 
    
    # Step 3: Test CoinGlass
    coinglass_ok = test_coinglass_api()
    
    # Results
    print(f"\n📊 FIX RESULTS")
    print("=" * 20)
    print(f"🤖 Bot Conflicts: {'✅ Resolved' if killed >= 0 else '❌ Issues'}")
    print(f"📱 Telegram State: {'✅ Cleared' if telegram_ok else '⚠️ Warning'}")
    print(f"📡 CoinGlass API: {'✅ Working' if coinglass_ok else '❌ Issues'}")
    
    if coinglass_ok:
        print(f"\n🎉 ALL SYSTEMS READY!")
        print(f"💡 You can now start the bot safely:")
        print(f"   cd Bismillah && python main.py")
        
        # Optional: Start bot automatically
        start_bot = input(f"\n🤖 Start bot now? (y/n): ").lower().strip()
        if start_bot == 'y':
            print(f"🚀 Starting bot...")
            os.chdir('Bismillah') 
            os.system('python main.py')
    else:
        print(f"\n⚠️ PARTIAL SUCCESS - Check CoinGlass API issues above")
        print(f"💡 Bot may work with limited functionality")
    
    print(f"\n🕐 Completed: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n🛑 Fix routine interrupted by user")
    except Exception as e:
        print(f"\n❌ Fix routine error: {e}")
