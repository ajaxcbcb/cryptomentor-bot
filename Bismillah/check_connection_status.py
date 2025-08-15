
#!/usr/bin/env python3
"""
Comprehensive Connection Status Checker
Memeriksa semua API key dan bot token
"""

import os
import sys
import requests
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_telegram_bot_token():
    """Check Telegram Bot Token"""
    print("🤖 CHECKING TELEGRAM BOT TOKEN")
    print("=" * 40)
    
    # Try both possible token environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    
    if not bot_token:
        print("❌ Bot token tidak ditemukan di environment variables")
        print("🔍 Mencari di: TELEGRAM_BOT_TOKEN, BOT_TOKEN")
        
        # Show available bot-related env vars
        found_vars = []
        for key in os.environ.keys():
            if 'BOT' in key.upper() or 'TELEGRAM' in key.upper():
                found_vars.append(f"{key} = {'SET' if os.environ[key] else 'EMPTY'}")
        
        if found_vars:
            print("📋 Environment variables yang ditemukan:")
            for var in found_vars:
                print(f"  {var}")
        else:
            print("📋 Tidak ada environment variables bot yang ditemukan")
        
        return False
    
    # Mask token for security
    masked_token = f"{bot_token[:10]}...{bot_token[-10:]}" if len(bot_token) > 20 else "SET"
    print(f"🔑 Bot Token: {masked_token}")
    
    try:
        # Test bot connection
        response = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getMe",
            timeout=10
        )
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info.get('result', {})
                username = bot_data.get('username', 'Unknown')
                first_name = bot_data.get('first_name', 'Unknown')
                print(f"✅ Bot Token VALID")
                print(f"👤 Bot Username: @{username}")
                print(f"📝 Bot Name: {first_name}")
                return True
            else:
                print(f"❌ Bot Token Invalid: {bot_info.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ Bot Token Error - HTTP {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Telegram API Timeout - Network issue")
        return False
    except Exception as e:
        print(f"❌ Bot Token Check Error: {str(e)}")
        return False

❌ CoinAPI Check Error: {str(e)}")
        return False

def check_coingecko_key():
    """Check CoinGecko API Key"""
    print("\n🦎 CHECKING COINGECKO API KEY")
    print("=" * 40)
    
    coingecko_key = os.getenv("COINGECKO_API_KEY")
    if not coingecko_key:
        print("❌ COINGECKO_API_KEY tidak ditemukan di environment variables")
        print("💡 Bot akan menggunakan CoinGecko Free API (dengan rate limit)")
        return False
    
    # Mask API key for security
    masked_key = f"{coingecko_key[:8]}...{coingecko_key[-4:]}" if len(coingecko_key) > 12 else "SET"
    print(f"🔑 CoinGecko Pro Key: {masked_key}")
    
    try:
        # Test CoinGecko Pro API
        headers = {'x-cg-pro-api-key': coingecko_key}
        response = requests.get(
            "https://pro-api.coingecko.com/api/v3/ping",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ CoinGecko Pro Key VALID")
            
            # Test market data
            market_response = requests.get(
                "https://pro-api.coingecko.com/api/v3/global",
                headers=headers,
                timeout=10
            )
            if market_response.status_code == 200:
                market_data = market_response.json()
                total_cap = market_data.get('data', {}).get('total_market_cap', {}).get('usd', 0)
                print(f"📊 Market Cap Test: ${total_cap:,.0f}")
            return True
        else:
            print(f"❌ CoinGecko Pro Key Invalid - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CoinGecko Check Error: {str(e)}")
        return False

def check_cryptonews_key():
    """Check CryptoNews API Key"""
    print("\n📰 CHECKING CRYPTONEWS API KEY")
    print("=" * 40)
    
    cryptonews_key = os.getenv("CRYPTONEWS_API_KEY")
    if not cryptonews_key:
        print("❌ CRYPTONEWS_API_KEY tidak ditemukan di environment variables")
        print("💡 Bot akan menggunakan mock news data")
        return False
    
    # Mask API key for security
    masked_key = f"{cryptonews_key[:8]}...{cryptonews_key[-4:]}" if len(cryptonews_key) > 12 else "SET"
    print(f"🔑 CryptoNews Key: {masked_key}")
    
    try:
        # Test CryptoNews API
        response = requests.get(
            "https://cryptonews-api.com/api/v1/category",
            params={
                "section": "general",
                "items": 1,
                "token": cryptonews_key
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get("data", [])
            if articles:
                print("✅ CryptoNews Key VALID")
                print(f"📄 Article Test: {len(articles)} articles available")
                return True
            else:
                print("⚠️ CryptoNews Key Valid but no articles returned")
                return True
        else:
            print(f"❌ CryptoNews Key Invalid - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CryptoNews Check Error: {str(e)}")
        return False

def check_binance_api():
    """Check Binance Public API"""
    print("\n⚡ CHECKING BINANCE PUBLIC API")
    print("=" * 40)
    
    try:
        # Test Binance Spot API
        response = requests.get("https://api.binance.com/api/v3/ping", timeout=10)
        if response.status_code == 200:
            print("✅ Binance Spot API Working")
            
            # Test price data
            btc_response = requests.get(
                "https://api.binance.com/api/v3/ticker/24hr",
                params={"symbol": "BTCUSDT"},
                timeout=10
            )
            if btc_response.status_code == 200:
                btc_data = btc_response.json()
                btc_price = float(btc_data['lastPrice'])
                change_24h = float(btc_data['priceChangePercent'])
                print(f"💰 BTC Price Test: ${btc_price:,.2f} ({change_24h:+.2f}%)")
        
        # Test Binance Futures API
        futures_response = requests.get("https://fapi.binance.com/fapi/v1/ping", timeout=10)
        if futures_response.status_code == 200:
            print("✅ Binance Futures API Working")
            return True
        else:
            print(f"❌ Binance Futures API Error - HTTP {futures_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Binance API Check Error: {str(e)}")
        return False

def main():
    """Main function to check all connections"""
    print("🔍 CRYPTOMENTOR AI - CONNECTION STATUS CHECK")
    print("=" * 60)
    print(f"⏰ Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")
    
    # Check deployment mode
    deployment_checks = {
        'REPLIT_DEPLOYMENT': os.getenv('REPLIT_DEPLOYMENT') == '1',
        'REPL_DEPLOYMENT': os.getenv('REPL_DEPLOYMENT') == '1',
        'REPL_SLUG': bool(os.getenv('REPL_SLUG')),
        'deployment_flag': os.path.exists('/tmp/repl_deployment_flag')
    }
    
    is_deployment = any(deployment_checks.values())
    print(f"🌍 Environment: {'🌐 DEPLOYMENT MODE' if is_deployment else '🔧 DEVELOPMENT MODE'}")
    
    # Check all connections
    results = {}
    results['telegram'] = check_telegram_bot_token()
    results['coinapi'] = check_coinapi_key()
    results['coingecko'] = check_coingecko_key()
    results['cryptonews'] = check_cryptonews_key()
    results['binance'] = check_binance_api()
    
    # Summary Report
    print("\n" + "=" * 60)
    print("📊 CONNECTION SUMMARY REPORT")
    print("=" * 60)
    
    working_connections = sum(results.values())
    total_connections = len(results)
    
    # Essential vs Optional
    essential_apis = ['telegram', 'coinapi', 'binance']
    optional_apis = ['coingecko', 'cryptonews']
    
    essential_working = sum(results[api] for api in essential_apis if api in results)
    optional_working = sum(results[api] for api in optional_apis if api in results)
    
    print("🔑 ESSENTIAL CONNECTIONS:")
    for api in essential_apis:
        status = "✅ CONNECTED" if results.get(api) else "❌ FAILED"
        print(f"   • {api.upper()}: {status}")
    
    print("\n🎛️ OPTIONAL CONNECTIONS:")
    for api in optional_apis:
        status = "✅ CONNECTED" if results.get(api) else "❌ NOT SET"
        print(f"   • {api.upper()}: {status}")
    
    # Overall Status
    essential_health = (essential_working / len(essential_apis)) * 100
    overall_health = (working_connections / total_connections) * 100
    
    print(f"\n🎯 OVERALL STATUS:")
    print(f"   • Essential APIs: {essential_working}/{len(essential_apis)} ({essential_health:.0f}%)")
    print(f"   • Total APIs: {working_connections}/{total_connections} ({overall_health:.0f}%)")
    
    if essential_health >= 100:
        print("🟢 STATUS: EXCELLENT - All essential APIs working!")
        print("🚀 Bot ready for full operation")
    elif essential_health >= 67:
        print("🟡 STATUS: GOOD - Most essential APIs working")
        print("📊 Bot can operate with minor limitations")
    else:
        print("🔴 STATUS: CRITICAL - Essential APIs failed")
        print("⚠️ Bot may not function properly")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if not results.get('telegram'):
        print("   🔥 URGENT: Fix Telegram Bot Token - Bot cannot start without this!")
    if not results.get('coinapi'):
        print("   🔥 URGENT: Fix CoinAPI Key - Required for real-time prices!")
    if not results.get('binance'):
        print("   ⚠️ Check internet connection - Binance API not accessible")
    if not results.get('coingecko'):
        print("   💡 Add CoinGecko Pro Key for enhanced market data")
    if not results.get('cryptonews'):
        print("   💡 Add CryptoNews Key for live news integration")
    
    if essential_health >= 100 and overall_health >= 100:
        print("   🎉 All systems optimal! Bot ready for deployment!")

if __name__ == "__main__":
    main()
