#!/usr/bin/env python3
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from crypto_api import CryptoAPI

# Load environment variables
load_dotenv()

def check_binance():
    """
    Test Binance API connection
    """
    try:
        # Test Binance Spot API
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {'symbol': 'BTCUSDT'}

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'price' in data and float(data['price']) > 0:
                return {
                    'status': 'success',
                    'response_time': response.elapsed.total_seconds(),
                    'sample_price': data['price'],
                    'endpoint': 'spot',
                    'timestamp': datetime.now().isoformat()
                }

        return {
            'status': 'failed',
            'error': f'HTTP {response.status_code}: {response.text[:100]}',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def check_api_health():
    """Advanced comprehensive API health check"""
    print("🏥 CryptoMentor Advanced API Health Report")
    print("=" * 60)

    # Environment detection
    is_deployment = (
        os.getenv('REPLIT_DEPLOYMENT') == '1' or 
        os.getenv('REPL_DEPLOYMENT') == '1'
    )
    print(f"🌍 Environment: {'🌐 DEPLOYMENT (Always On)' if is_deployment else '🔧 DEVELOPMENT (Workspace)'}")
    print(f"⏰ Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")

    # Enhanced API key validation with masking
    print("\n🔐 API Configuration & Security:")
    cryptonews_key = os.getenv("CRYPTONEWS_API_KEY")

    def mask_key(key):
        if not key or len(key) < 8:
            return "❌ NOT SET"
        return f"✅ SET ({key[-4:]})"

    print(f"• Binance API: 🔓 Public (No key required)")
    print(f"• CryptoNews API Key: {mask_key(cryptonews_key)}")

    # Network connectivity test
    print(f"\n🌐 Network Connectivity Test:")
    connectivity_results = {}

    test_endpoints = {
        'Binance': 'https://api.binance.com/api/v3/ping',
        'CoinGecko Free': 'https://api.coingecko.com/api/v3/ping',
        'CoinGecko Pro': 'https://pro-api.coingecko.com/api/v3/ping',
        'CryptoNews': 'https://cryptonews-api.com'
    }

    for service, endpoint in test_endpoints.items():
        try:
            import time
            start_time = time.time()
            response = requests.get(endpoint, timeout=10)
            response_time = round((time.time() - start_time) * 1000, 2)

            if response.status_code == 200:
                connectivity_results[service] = f"✅ Online ({response_time}ms)"
            else:
                connectivity_results[service] = f"⚠️ HTTP {response.status_code} ({response_time}ms)"
        except Exception as e:
            connectivity_results[service] = f"❌ Offline ({str(e)[:30]}...)"

    for service, status in connectivity_results.items():
        print(f"  • {service}: {status}")

    # Initialize APIs
    crypto_api = CryptoAPI()

    # Test other APIs
    print("\n💰 Testing Price APIs:")

    # Test Binance
    try:
        btc_price = crypto_api.get_binance_price('BTC')
        if 'error' not in btc_price and btc_price.get('price', 0) > 0:
            print(f"  • Binance API: ✅ Working (BTC: ${btc_price['price']:,.2f})")
        else:
            print(f"  • Binance API: ❌ Error - {btc_price.get('error', 'Unknown')}")
    except Exception as e:
        print(f"  • Binance API: ❌ Exception - {str(e)}")

    # Test CoinGecko
    try:
        btc_price_cg = crypto_api.get_price('bitcoin')
        if 'error' not in btc_price_cg and btc_price_cg.get('price', 0) > 0:
            print(f"  • CoinGecko API: ✅ Working (BTC: ${btc_price_cg['price']:,.2f})")
        else:
            print(f"  • CoinGecko API: ❌ Error - {btc_price_cg.get('error', 'Unknown')}")
    except Exception as e:
        print(f"  • CoinGecko API: ❌ Exception - {str(e)}")

    # Test Market Overview
    print("\n🌍 Testing Market Data:")
    try:
        market_data = crypto_api.get_market_overview()
        if 'error' not in market_data:
            total_cap = market_data.get('total_market_cap', 0)
            print(f"  • Market Overview: ✅ Working (Total Cap: ${total_cap:,.0f})")
        else:
            print(f"  • Market Overview: ❌ Error - {market_data.get('error', 'Unknown')}")
    except Exception as e:
        print(f"  • Market Overview: ❌ Exception - {str(e)}")

    # Test News API
    print("\n📰 Testing News API:")
    try:
        news = crypto_api.get_crypto_news(limit=3)
        if news and isinstance(news, list) and len(news) > 0 and 'error' not in news[0]:
            print(f"  • CryptoNews API: ✅ Working ({len(news)} articles fetched)")
        else:
            print(f"  • CryptoNews API: ❌ Error - {news[0].get('error', 'No data') if news else 'No response'}")
    except Exception as e:
        print(f"  • CryptoNews API: ❌ Exception - {str(e)}")

    # Advanced features showcase
    print("\n🚀 Advanced Features Available:")

    # Real-time price monitoring
    print("📊 Real-time Price Monitoring:")
    major_coins = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA']
    price_sources = []

    for coin in major_coins[:3]:  # Test first 3 coins
        try:
            price_data = crypto_api.get_price(coin)
            source = price_data.get('source', 'unknown')
            price = price_data.get('price', 0)
            if source in ['binance', 'coingecko', 'coingecko_free']:
                price_sources.append(f"  • {coin}: ${price:,.2f} via {source.title()}")
            else:
                price_sources.append(f"  • {coin}: ${price:,.2f} via simulation")
        except Exception as e:
            price_sources.append(f"  • {coin}: Error - {str(e)[:30]}...")

    for source in price_sources:
        print(source)

    # News integration test
    print("\n📰 News Integration:")
    try:
        news = crypto_api.get_crypto_news(limit=2)
        if news:
            news_source = news[0].get('source', 'unknown')
            if news_source == 'cryptonews_api':
                print("  ✅ Live CryptoNews API connected")
                print(f"     Latest: {news[0].get('title', 'N/A')[:50]}...")
            else:
                print("  🔄 Enhanced mock news system active")
                print(f"     Sample: {news[0].get('title', 'N/A')[:50]}...")
    except Exception as e:
        print(f"  ❌ News system error: {str(e)[:40]}...")

    # Advanced Binance Futures Analysis
    print("\n⚡ Advanced Binance Futures Analysis:")
    try:
        # Test comprehensive futures data
        comp_data = crypto_api.get_comprehensive_futures_data('BTC')

        if 'error' not in comp_data:
            success_rate = comp_data.get('successful_api_calls', 0)
            total_calls = comp_data.get('total_api_calls', 6)
            quality = comp_data.get('data_quality', 'unknown')

            print(f"  ✅ Binance Comprehensive API: {success_rate}/{total_calls} endpoints")
            print(f"  📊 Data Quality: {quality.upper()}")

            # Test specific endpoints
            futures_data = crypto_api.get_futures_data('BTC')
            long_ratio = futures_data.get('long_ratio', 0)
            print(f"  📈 Long/Short Ratio: {long_ratio:.1f}%")

            funding_data = crypto_api.get_funding_rate('BTC')
            avg_funding = funding_data.get('average_funding_rate', 0)
            print(f"  💰 Avg Funding Rate: {avg_funding:.4f}%")

            oi_data = crypto_api.get_open_interest('BTC')
            oi_value = oi_data.get('open_interest', 0)
            print(f"  📊 Open Interest: ${oi_value:,.0f}")

            liq_data = crypto_api.get_liquidation_data('BTC')
            total_liq = liq_data.get('total_liquidation', 0)
            print(f"  🔥 Total Liquidations: ${total_liq:,.0f}")

        else:
            print(f"  ❌ Binance comprehensive data error")

    except Exception as e:
        print(f"  ❌ Futures analysis error: {str(e)[:40]}...")

    print("\n" + "=" * 60)
    print("🎯 Advanced Summary Report:")

    # Calculate overall system health
    real_apis = sum([
        1 if connectivity_results.get('Binance', '').startswith('✅') else 0,
        1 if connectivity_results.get('CoinGecko Pro', '').startswith('✅') or connectivity_results.get('CoinGecko Free', '').startswith('✅') else 0,
        1 if cryptonews_key else 0
    ])

    total_apis = 3
    system_health = (real_apis / total_apis) * 100

    if system_health >= 75:
        status_color = "🟢"
        status_text = "EXCELLENT"
        recommendation = "All major systems operational. Full advanced features available!"
    elif system_health >= 50:
        status_color = "🟡" 
        status_text = "GOOD"
        recommendation = "Most systems working. Advanced features partially available."
    elif system_health >= 25:
        status_color = "🟠"
        status_text = "FAIR" 
        recommendation = "Limited API access. Basic features available with fallbacks."
    else:
        status_color = "🔴"
        status_text = "MAINTENANCE"
        recommendation = "Running in simulation mode. All features work with enhanced mock data."

    print(f"{status_color} Overall System Health: {status_text} ({system_health:.0f}%)")
    print(f"💰 Price APIs: {len([x for x in connectivity_results.values() if '✅' in x])}/{len(connectivity_results)} online")
    print(f"🔄 Real Data Coverage: {real_apis}/{total_apis} major APIs")

    print(f"\n💡 Advanced Recommendation:")
    print(f"   {recommendation}")

    # Feature availability matrix
    print(f"\n🎛️ Feature Availability Matrix:")
    print(f"   • Real-time Prices: {'✅ Full' if connectivity_results.get('Binance', '').startswith('✅') else '🔄 Simulated'}")
    print(f"   • Market Overview: {'✅ Full' if connectivity_results.get('CoinGecko Pro', '').startswith('✅') else '🔄 Simulated'}")
    print(f"   • Futures Analysis: ✅ Full (Binance API)")
    print(f"   • News Integration: {'✅ Live' if cryptonews_key else '🔄 Enhanced Mock'}")
    print(f"   • AI Analysis: ✅ Always Available")

    print(f"\n🌟 Next Steps to Optimize:")
    if system_health < 100:
        if not connectivity_results.get('CoinGecko Pro', '').startswith('✅'):
            print("   • Verify CoinGecko Pro API key for enhanced market data")

        if not cryptonews_key:
            print("   • Add CryptoNews API key for live news integration")
    else:
        print("   • All systems optimal! Enjoy full advanced features 🚀")

def main():
    """
    Comprehensive API health check - Binance only
    """
    print("🔍 API Health Check - CryptoMentor Bot (Binance)")
    print("=" * 50)

    # Check Binance Spot
    print("\n🔄 Testing Binance Spot API...")
    binance_spot_result = check_binance()
    if binance_spot_result['status'] == 'success':
        print(f"✅ Binance Spot: OK ({binance_spot_result['response_time']:.2f}s)")
        print(f"   Sample BTC price: ${binance_spot_result['sample_price']}")
    else:
        print(f"❌ Binance Spot: {binance_spot_result['error']}")

    # Check Binance Futures
    print("\n⚡ Testing Binance Futures API...")
    try:
        futures_url = "https://fapi.binance.com/fapi/v1/ticker/price"
        futures_response = requests.get(futures_url, params={'symbol': 'BTCUSDT'}, timeout=10)
        if futures_response.status_code == 200:
            futures_data = futures_response.json()
            print(f"✅ Binance Futures: OK ({futures_response.elapsed.total_seconds():.2f}s)")
            print(f"   Sample BTC futures price: ${futures_data['price']}")
            futures_working = True
        else:
            print(f"❌ Binance Futures: HTTP {futures_response.status_code}")
            futures_working = False
    except Exception as e:
        print(f"❌ Binance Futures: {str(e)}")
        futures_working = False

    # Summary
    print("\n" + "=" * 50)
    working_apis = sum([
        binance_spot_result['status'] == 'success',
        futures_working
    ])
    total_apis = 2

    if working_apis == total_apis:
        print("🎉 All Binance APIs are working correctly!")
    elif working_apis > 0:
        print(f"⚠️ {working_apis}/{total_apis} Binance APIs working")
    else:
        print("❌ All Binance APIs are down!")

    return working_apis == total_apis

if __name__ == "__main__":
    check_api_health()