
<line_number>1</line_number>
#!/usr/bin/env python3
import requests
import json
from datetime import datetime

def test_binance_spot_api():
    """Test Binance Spot API connection"""
    print("🔍 Testing Binance Spot API...")
    
    try:
        # Test ping
        ping_response = requests.get("https://api.binance.com/api/v3/ping", timeout=10)
        if ping_response.status_code == 200:
            print("✅ Binance Spot API Ping: OK")
        else:
            print(f"❌ Binance Spot API Ping: HTTP {ping_response.status_code}")
            return False
        
        # Test BTC price
        price_response = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": "BTCUSDT"},
            timeout=10
        )
        
        if price_response.status_code == 200:
            data = price_response.json()
            price = float(data['price'])
            print(f"✅ BTC Price: ${price:,.2f}")
        else:
            print(f"❌ Price Request: HTTP {price_response.status_code}")
            return False
        
        # Test 24h ticker
        ticker_response = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={"symbol": "BTCUSDT"},
            timeout=10
        )
        
        if ticker_response.status_code == 200:
            ticker_data = ticker_response.json()
            change_24h = float(ticker_data['priceChangePercent'])
            volume = float(ticker_data['volume'])
            print(f"✅ BTC 24h Change: {change_24h:+.2f}%")
            print(f"✅ BTC 24h Volume: {volume:,.0f}")
        else:
            print(f"❌ 24h Ticker: HTTP {ticker_response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Binance Spot API Error: {e}")
        return False

def test_binance_futures_api():
    """Test Binance Futures API connection"""
    print("\n⚡ Testing Binance Futures API...")
    
    try:
        # Test futures ping
        ping_response = requests.get("https://fapi.binance.com/fapi/v1/ping", timeout=10)
        if ping_response.status_code == 200:
            print("✅ Binance Futures API Ping: OK")
        else:
            print(f"❌ Binance Futures API Ping: HTTP {ping_response.status_code}")
            return False
        
        # Test futures price
        price_response = requests.get(
            "https://fapi.binance.com/fapi/v1/ticker/price",
            params={"symbol": "BTCUSDT"},
            timeout=10
        )
        
        if price_response.status_code == 200:
            data = price_response.json()
            price = float(data['price'])
            print(f"✅ BTC Futures Price: ${price:,.2f}")
        else:
            print(f"❌ Futures Price Request: HTTP {price_response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Binance Futures API Error: {e}")
        return False

def test_crypto_api_integration():
    """Test CryptoAPI class integration"""
    print("\n🔧 Testing CryptoAPI Integration...")
    
    try:
        from crypto_api import crypto_api
        
        # Test BTC price through CryptoAPI
        btc_data = crypto_api.get_crypto_price("BTC", force_refresh=True)
        
        if 'error' not in btc_data:
            price = btc_data.get('price', 0)
            change_24h = btc_data.get('change_24h', 0)
            volume_24h = btc_data.get('volume_24h', 0)
            
            print(f"✅ CryptoAPI BTC Price: ${price:,.2f}")
            print(f"✅ CryptoAPI BTC Change: {change_24h:+.2f}%")
            print(f"✅ CryptoAPI BTC Volume: ${volume_24h:,.0f}")
            
            return True
        else:
            print(f"❌ CryptoAPI Error: {btc_data.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ CryptoAPI Integration Error: {e}")
        return False

def main():
    print("🚀 Binance API Connection Test")
    print("=" * 50)
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    spot_ok = test_binance_spot_api()
    futures_ok = test_binance_futures_api()
    crypto_api_ok = test_crypto_api_integration()
    
    print("\n📊 RESULTS SUMMARY:")
    print(f"{'✅' if spot_ok else '❌'} Binance Spot API: {'OK' if spot_ok else 'FAILED'}")
    print(f"{'✅' if futures_ok else '❌'} Binance Futures API: {'OK' if futures_ok else 'FAILED'}")
    print(f"{'✅' if crypto_api_ok else '❌'} CryptoAPI Integration: {'OK' if crypto_api_ok else 'FAILED'}")
    
    if spot_ok and futures_ok and crypto_api_ok:
        print("\n🎉 All APIs working correctly!")
    else:
        print("\n⚠️ Some APIs have issues - check logs above")

if __name__ == "__main__":
    main()
