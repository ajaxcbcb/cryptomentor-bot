
#!/usr/bin/env python3
"""
Deployment API Verification Script
Memverifikasi semua API siap untuk mode deployment dengan data real-time
"""

import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_deployment_apis():
    """Verify all APIs are ready for deployment mode"""
    print("🚀 VERIFYING DEPLOYMENT API STATUS")
    print("=" * 50)
    
    # Check deployment environment
    is_deployment = (
        os.getenv('REPLIT_DEPLOYMENT') == '1' or 
        os.getenv('REPL_DEPLOYMENT') == '1'
    )
    
    print(f"🌍 Environment: {'🌐 DEPLOYMENT MODE' if is_deployment else '🔧 DEVELOPMENT MODE'}")
    print(f"⏰ Verification Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # API Keys Check
    print("🔐 API KEYS VERIFICATION:")
    print("-" * 30)
    
    coingecko_key = os.getenv("COINGECKO_API_KEY")
    cryptonews_key = os.getenv("CRYPTONEWS_API_KEY")
    
    def mask_key(key):
        if not key or len(key) < 8:
            return "❌ NOT SET"
        return f"✅ SET ({key[:8]}...{key[-4:]})"
    
    print(f"• CoinGecko Pro API Key: {mask_key(coingecko_key)}")
    print(f"• CryptoNews API Key: {mask_key(cryptonews_key)}")
    print()
    
    # Test API Connectivity
    print("🌐 API CONNECTIVITY TEST:")
    print("-" * 30)
    
    api_results = {}
    
    # 1. Test Binance APIs
    print("📊 Testing Binance APIs...")
    try:
        # Binance Spot
        spot_response = requests.get("https://api.binance.com/api/v3/ping", timeout=10)
        binance_spot_ok = spot_response.status_code == 200
        
        # Binance Futures  
        futures_response = requests.get("https://fapi.binance.com/fapi/v1/ping", timeout=10)
        binance_futures_ok = futures_response.status_code == 200
        
        print(f"  • Binance Spot API: {'✅ Connected' if binance_spot_ok else '❌ Failed'}")
        print(f"  • Binance Futures API: {'✅ Connected' if binance_futures_ok else '❌ Failed'}")
        
        api_results['binance'] = binance_spot_ok and binance_futures_ok
        
    except Exception as e:
        print(f"  • Binance APIs: ❌ Connection Error - {str(e)}")
        api_results['binance'] = False
    
    # 2. Test CoinGecko API
    print("\n🦎 Testing CoinGecko APIs...")
    try:
        # Test Free API
        free_response = requests.get("https://api.coingecko.com/api/v3/ping", timeout=10)
        coingecko_free_ok = free_response.status_code == 200
        print(f"  • CoinGecko Free API: {'✅ Connected' if coingecko_free_ok else '❌ Failed'}")
        
        # Test Pro API if key exists
        coingecko_pro_ok = False
        if coingecko_key:
            headers = {'x-cg-pro-api-key': coingecko_key}
            pro_response = requests.get(
                "https://pro-api.coingecko.com/api/v3/ping", 
                headers=headers, 
                timeout=10
            )
            coingecko_pro_ok = pro_response.status_code == 200
            print(f"  • CoinGecko Pro API: {'✅ Connected' if coingecko_pro_ok else '❌ Failed'}")
        else:
            print(f"  • CoinGecko Pro API: ⚠️ No API Key (using Free)")
        
        api_results['coingecko'] = coingecko_free_ok or coingecko_pro_ok
        
    except Exception as e:
        print(f"  • CoinGecko APIs: ❌ Connection Error - {str(e)}")
        api_results['coingecko'] = False
    
    # 3. Test CryptoNews API
    print("\n📰 Testing CryptoNews API...")
    try:
        if cryptonews_key:
            news_response = requests.get(
                "https://cryptonews-api.com/api/v1/category",
                params={
                    "section": "general",
                    "items": 1,
                    "token": cryptonews_key
                },
                timeout=10
            )
            cryptonews_ok = news_response.status_code == 200
            print(f"  • CryptoNews API: {'✅ Connected' if cryptonews_ok else '❌ Failed'}")
            
            if cryptonews_ok:
                data = news_response.json()
                articles = data.get("data", [])
                print(f"    Sample: {len(articles)} articles available")
                
        else:
            print(f"  • CryptoNews API: ⚠️ No API Key (using fallback)")
            cryptonews_ok = False
        
        api_results['cryptonews'] = cryptonews_ok
        
    except Exception as e:
        print(f"  • CryptoNews API: ❌ Connection Error - {str(e)}")
        api_results['cryptonews'] = False
    
    print()
    
    # Test Real-time Data Fetching
    print("📈 REAL-TIME DATA TEST:")
    print("-" * 30)
    
    test_symbols = ['BTC', 'ETH', 'BNB']
    successful_fetches = 0
    
    for symbol in test_symbols:
        try:
            # Test price fetch
            price_response = requests.get(
                f"https://api.binance.com/api/v3/ticker/24hr",
                params={'symbol': f'{symbol}USDT'},
                timeout=10
            )
            
            if price_response.status_code == 200:
                data = price_response.json()
                price = float(data['lastPrice'])
                change = float(data['priceChangePercent'])
                print(f"  • {symbol}: ${price:,.2f} ({change:+.2f}%) ✅")
                successful_fetches += 1
            else:
                print(f"  • {symbol}: ❌ Price fetch failed")
                
        except Exception as e:
            print(f"  • {symbol}: ❌ Error - {str(e)[:30]}...")
    
    print()
    
    # Overall Status Report
    print("📊 DEPLOYMENT READINESS REPORT:")
    print("=" * 50)
    
    total_apis = len(api_results)
    working_apis = sum(api_results.values())
    price_success_rate = (successful_fetches / len(test_symbols)) * 100
    
    print(f"🔗 API Connectivity: {working_apis}/{total_apis} APIs working")
    print(f"💰 Price Data: {successful_fetches}/{len(test_symbols)} symbols ({price_success_rate:.0f}%)")
    
    # Overall readiness assessment
    if working_apis >= 2 and successful_fetches >= 2:
        status = "🟢 READY FOR DEPLOYMENT"
        description = "All critical APIs working, real-time data available"
    elif working_apis >= 1 and successful_fetches >= 1:
        status = "🟡 PARTIALLY READY"
        description = "Basic functionality available, some APIs may be down"
    else:
        status = "🔴 NOT READY"
        description = "Critical API failures detected"
    
    print(f"\n🎯 Status: {status}")
    print(f"📝 Description: {description}")
    
    # API Priority for Deployment
    print(f"\n⚡ API Priority Order for Deployment:")
    print(f"  1. Binance (Price & Futures): {'✅' if api_results.get('binance') else '❌'}")
    print(f"  2. CoinGecko (Market Data): {'✅' if api_results.get('coingecko') else '❌'}")
    print(f"  3. CryptoNews (News & Sentiment): {'✅' if api_results.get('cryptonews') else '❌'}")
    
    print(f"\n💡 Deployment will work with force_refresh=True for real-time data")
    
    return {
        'ready_for_deployment': working_apis >= 2 and successful_fetches >= 2,
        'api_status': api_results,
        'price_success_rate': price_success_rate
    }

if __name__ == "__main__":
    verify_deployment_apis()
