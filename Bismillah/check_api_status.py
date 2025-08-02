
#!/usr/bin/env python3
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_cryptonews_api():
    """Check CryptoNews API status and functionality"""
    print("📰 Checking CryptoNews API...")
    
    api_key = os.getenv("CRYPTONEWS_API_KEY")
    if not api_key:
        print("❌ CryptoNews API Key tidak ditemukan di environment variables")
        return False
    
    # Mask API key for security
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "SET"
    print(f"🔑 API Key: {masked_key}")
    
    # Test API endpoint
    url = "https://cryptonews-api.com/api/v1/category"
    params = {
        "section": "general",
        "items": 3,
        "token": api_key
    }
    
    try:
        print("🌐 Testing CryptoNews API connection...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get("data", [])
            
            if articles:
                print(f"✅ CryptoNews API AKTIF - {len(articles)} artikel ditemukan")
                print("📄 Sample artikel:")
                for i, article in enumerate(articles[:2], 1):
                    title = article.get('title', 'No title')[:60] + '...' if len(article.get('title', '')) > 60 else article.get('title', 'No title')
                    source = article.get('source_name', 'Unknown')
                    print(f"   {i}. {title} ({source})")
                return True
            else:
                print("⚠️ CryptoNews API merespons tapi tidak ada data artikel")
                return False
        else:
            print(f"❌ CryptoNews API Error - HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ CryptoNews API Timeout - Server tidak merespons")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ CryptoNews API Connection Error - Tidak dapat terhubung")
        return False
    except Exception as e:
        print(f"❌ CryptoNews API Error: {str(e)}")
        return False

def check_coingecko_api():
    """Check CoinGecko API status and functionality"""
    print("\n🦎 Checking CoinGecko API...")
    
    # Check if Pro API key exists
    pro_api_key = os.getenv("COINGECKO_API_KEY")
    if pro_api_key:
        masked_key = f"{pro_api_key[:8]}...{pro_api_key[-4:]}" if len(pro_api_key) > 12 else "SET"
        print(f"🔑 Pro API Key: {masked_key}")
    else:
        print("🔑 Pro API Key: Not set (menggunakan Free API)")
    
    # Test Free API first
    print("🌐 Testing CoinGecko Free API...")
    try:
        free_response = requests.get("https://api.coingecko.com/api/v3/ping", timeout=10)
        if free_response.status_code == 200:
            print("✅ CoinGecko Free API AKTIF")
            
            # Test getting Bitcoin price
            btc_response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "bitcoin", "vs_currencies": "usd"},
                timeout=10
            )
            if btc_response.status_code == 200:
                btc_data = btc_response.json()
                btc_price = btc_data.get('bitcoin', {}).get('usd', 0)
                print(f"💰 Bitcoin Price: ${btc_price:,.2f} (via Free API)")
            
        else:
            print(f"❌ CoinGecko Free API Error - HTTP {free_response.status_code}")
    except Exception as e:
        print(f"❌ CoinGecko Free API Error: {str(e)}")
    
    # Test Pro API if key exists
    if pro_api_key:
        print("🌐 Testing CoinGecko Pro API...")
        try:
            pro_response = requests.get(
                "https://pro-api.coingecko.com/api/v3/ping",
                headers={"x-cg-pro-api-key": pro_api_key},
                timeout=10
            )
            if pro_response.status_code == 200:
                print("✅ CoinGecko Pro API AKTIF")
                
                # Test getting market data
                market_response = requests.get(
                    "https://pro-api.coingecko.com/api/v3/global",
                    headers={"x-cg-pro-api-key": pro_api_key},
                    timeout=10
                )
                if market_response.status_code == 200:
                    market_data = market_response.json()
                    total_cap = market_data.get('data', {}).get('total_market_cap', {}).get('usd', 0)
                    btc_dominance = market_data.get('data', {}).get('market_cap_percentage', {}).get('btc', 0)
                    print(f"📊 Total Market Cap: ${total_cap:,.0f}")
                    print(f"₿ BTC Dominance: {btc_dominance:.1f}%")
                    return True
                else:
                    print(f"⚠️ CoinGecko Pro API ping OK tapi market data error - HTTP {market_response.status_code}")
            else:
                print(f"❌ CoinGecko Pro API Error - HTTP {pro_response.status_code}")
                print("💡 Kemungkinan API key tidak valid atau quota habis")
                return False
        except Exception as e:
            print(f"❌ CoinGecko Pro API Error: {str(e)}")
            return False
    
    return True

def check_binance_api():
    """Check Binance API status"""
    print("\n⚡ Checking Binance API...")
    
    try:
        # Test Binance Spot
        spot_response = requests.get("https://api.binance.com/api/v3/ping", timeout=10)
        if spot_response.status_code == 200:
            print("✅ Binance Spot API AKTIF")
            
            # Test getting BTC price
            btc_response = requests.get(
                "https://api.binance.com/api/v3/ticker/24hr",
                params={"symbol": "BTCUSDT"},
                timeout=10
            )
            if btc_response.status_code == 200:
                btc_data = btc_response.json()
                btc_price = float(btc_data['lastPrice'])
                change_24h = float(btc_data['priceChangePercent'])
                print(f"💰 BTC Price: ${btc_price:,.2f} ({change_24h:+.2f}%)")
        
        # Test Binance Futures
        futures_response = requests.get("https://fapi.binance.com/fapi/v1/ping", timeout=10)
        if futures_response.status_code == 200:
            print("✅ Binance Futures API AKTIF")
            return True
        else:
            print(f"❌ Binance Futures API Error - HTTP {futures_response.status_code}")
            
    except Exception as e:
        print(f"❌ Binance API Error: {str(e)}")
        return False

def test_ai_analysis_data():
    """Test if we can get comprehensive data for AI analysis"""
    print("\n🤖 Testing AI Analysis Data Sources...")
    
    from crypto_api import CryptoAPI
    crypto_api = CryptoAPI()
    
    # Test comprehensive futures data
    print("📊 Testing comprehensive futures data for BTC...")
    try:
        futures_data = crypto_api.get_comprehensive_futures_data('BTC')
        if 'error' not in futures_data:
            successful_calls = futures_data.get('successful_api_calls', 0)
            total_calls = futures_data.get('total_api_calls', 0)
            data_quality = futures_data.get('data_quality', 'unknown')
            
            print(f"✅ Futures Data: {successful_calls}/{total_calls} API calls successful")
            print(f"📈 Data Quality: {data_quality.upper()}")
            
            # Check individual components
            components = [
                ('Price Data', futures_data.get('price_data', {})),
                ('Mark Price', futures_data.get('mark_price_data', {})),
                ('Funding Rate', futures_data.get('funding_rate_data', {})),
                ('Open Interest', futures_data.get('open_interest_data', {})),
                ('Long/Short Ratio', futures_data.get('long_short_ratio_data', {})),
                ('Liquidations', futures_data.get('liquidation_data', {}))
            ]
            
            for name, data in components:
                status = "✅" if 'error' not in data else "❌"
                print(f"   {status} {name}")
        else:
            print(f"❌ Futures Data Error: {futures_data.get('error')}")
    except Exception as e:
        print(f"❌ Futures Data Test Error: {str(e)}")
    
    # Test news integration
    print("\n📰 Testing news integration...")
    try:
        news = crypto_api.get_crypto_news(limit=3)
        if news and len(news) > 0 and 'error' not in news[0]:
            news_source = news[0].get('source', 'unknown')
            print(f"✅ News Data: {len(news)} articles from {news_source}")
            if news_source == 'cryptonews_api':
                print("🔥 LIVE CryptoNews API integration aktif!")
            else:
                print("🔄 Fallback news system (mock data)")
        else:
            print("❌ News Data Error")
    except Exception as e:
        print(f"❌ News Test Error: {str(e)}")

def main():
    """Main function to run all API checks"""
    print("🔍 CryptoMentor AI - Advanced API Status Check")
    print("=" * 60)
    print(f"⏰ Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")
    
    # Check environment
    is_deployment = (
        os.getenv('REPLIT_DEPLOYMENT') == '1' or 
        os.getenv('REPL_DEPLOYMENT') == '1'
    )
    print(f"🌍 Environment: {'🌐 DEPLOYMENT' if is_deployment else '🔧 DEVELOPMENT'}")
    
    results = {
        'cryptonews': False,
        'coingecko': False,
        'binance': False
    }
    
    # Run all checks
    results['cryptonews'] = check_cryptonews_api()
    results['coingecko'] = check_coingecko_api()
    results['binance'] = check_binance_api()
    
    # Test AI analysis capabilities
    test_ai_analysis_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 RINGKASAN STATUS API")
    print("=" * 60)
    
    working_apis = sum(results.values())
    total_apis = len(results)
    
    for api_name, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {api_name.upper()}: {'AKTIF' if status else 'TIDAK AKTIF'}")
    
    health_percentage = (working_apis / total_apis) * 100
    print(f"\n🎯 Overall API Health: {health_percentage:.0f}% ({working_apis}/{total_apis})")
    
    if health_percentage >= 100:
        print("🟢 STATUS: EXCELLENT - Semua API aktif!")
        print("🚀 AI Analysis: Full advanced features tersedia")
    elif health_percentage >= 67:
        print("🟡 STATUS: GOOD - Mayoritas API aktif")
        print("📊 AI Analysis: Advanced features tersedia dengan beberapa keterbatasan")
    elif health_percentage >= 33:
        print("🟠 STATUS: PARTIAL - Beberapa API aktif")
        print("🔄 AI Analysis: Basic features dengan fallback data")
    else:
        print("🔴 STATUS: LIMITED - API bermasalah")
        print("⚠️ AI Analysis: Berjalan dengan simulation mode")
    
    print("\n💡 Rekomendasi untuk AI Analysis:")
    if not results['cryptonews']:
        print("   • Tambahkan CryptoNews API key untuk news integration")
    if not results['coingecko']:
        print("   • Verify CoinGecko Pro API key untuk market data")
    if not results['binance']:
        print("   • Check internet connection untuk Binance API")
    if working_apis == total_apis:
        print("   • 🎉 Semua system optimal! AI analysis siap dengan full features")

if __name__ == "__main__":
    main()
