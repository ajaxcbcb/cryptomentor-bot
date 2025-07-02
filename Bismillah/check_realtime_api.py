
#!/usr/bin/env python3
"""
Real-time API Status Checker untuk Deployment Mode
Memverifikasi bahwa semua API berjalan dengan baik dalam mode deployment
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from crypto_api import CryptoAPI

# Load environment variables
load_dotenv()

def check_deployment_mode():
    """Check if running in deployment mode"""
    is_deployment = os.getenv('REPLIT_DEPLOYMENT') == '1' or os.getenv('REPL_DEPLOYMENT') == '1'
    return is_deployment

def test_realtime_api():
    """Test real-time API performance"""
    print("🚀 TESTING REAL-TIME API PERFORMANCE")
    print("=" * 50)
    
    # Initialize API
    crypto_api = CryptoAPI()
    is_deployment = check_deployment_mode()
    
    print(f"🌍 Environment: {'DEPLOYMENT' if is_deployment else 'DEVELOPMENT'}")
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test major cryptocurrencies
    test_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA']
    
    print("📊 Testing Real-time Price Data:")
    print("-" * 30)
    
    successful_tests = 0
    total_tests = len(test_symbols)
    
    for symbol in test_symbols:
        try:
            start_time = time.time()
            
            # Test with force refresh if in deployment
            price_data = crypto_api.get_multi_api_price(symbol, force_refresh=is_deployment)
            
            response_time = (time.time() - start_time) * 1000
            
            if 'error' not in price_data and price_data.get('price', 0) > 0:
                price = price_data.get('price', 0)
                change_24h = price_data.get('change_24h', 0)
                source = price_data.get('primary_source', 'unknown')
                
                print(f"✅ {symbol}: ${price:,.2f} ({change_24h:+.2f}%) - {source} ({response_time:.0f}ms)")
                successful_tests += 1
            else:
                print(f"❌ {symbol}: API Error - {price_data.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"❌ {symbol}: Exception - {str(e)}")
    
    print()
    print("📈 Testing Advanced Features:")
    print("-" * 30)
    
    # Test futures data
    try:
        futures_data = crypto_api.get_comprehensive_futures_data('BTC')
        if 'error' not in futures_data:
            success_count = futures_data.get('successful_api_calls', 0)
            total_count = futures_data.get('total_api_calls', 6)
            print(f"✅ Futures Data: {success_count}/{total_count} endpoints working")
        else:
            print(f"❌ Futures Data: {futures_data.get('error')}")
    except Exception as e:
        print(f"❌ Futures Data: Exception - {str(e)}")
    
    # Test global market data
    try:
        global_data = crypto_api.get_coingecko_global_data()
        if 'error' not in global_data:
            total_mcap = global_data.get('total_market_cap', 0)
            print(f"✅ Global Data: Market Cap ${total_mcap:,.0f}")
        else:
            print(f"❌ Global Data: {global_data.get('error')}")
    except Exception as e:
        print(f"❌ Global Data: Exception - {str(e)}")
    
    # Test news integration
    try:
        news_data = crypto_api.get_crypto_news(3)
        if news_data and len(news_data) > 0:
            news_source = news_data[0].get('source', 'unknown')
            print(f"✅ News Data: {len(news_data)} articles from {news_source}")
        else:
            print("❌ News Data: No articles retrieved")
    except Exception as e:
        print(f"❌ News Data: Exception - {str(e)}")
    
    print()
    print("📊 SUMMARY:")
    print("=" * 50)
    print(f"Environment: {'🚀 DEPLOYMENT (Real-time)' if is_deployment else '🔧 DEVELOPMENT (Standard)'}")
    print(f"Price API Success Rate: {successful_tests}/{total_tests} ({(successful_tests/total_tests)*100:.1f}%)")
    
    if successful_tests == total_tests:
        print("🟢 Status: ALL SYSTEMS OPERATIONAL")
        print("✅ Real-time API working perfectly!")
    elif successful_tests >= total_tests * 0.8:
        print("🟡 Status: MOSTLY OPERATIONAL")
        print("⚠️ Some API endpoints may have issues")
    else:
        print("🔴 Status: DEGRADED PERFORMANCE")
        print("❌ Multiple API failures detected")
    
    # API Health Check
    try:
        api_status = crypto_api.check_api_status()
        print(f"\n🏥 API Health:")
        print(f"• Binance Spot: {'✅' if api_status.get('binance_spot') else '❌'}")
        print(f"• Binance Futures: {'✅' if api_status.get('binance_futures') else '❌'}")
        print(f"• Advanced Features: {'✅' if api_status.get('binance_advanced') else '❌'}")
        print(f"• Overall Health: {'✅' if api_status.get('overall_health') else '❌'}")
    except Exception as e:
        print(f"\n❌ API Health Check Failed: {str(e)}")

if __name__ == "__main__":
    test_realtime_api()
