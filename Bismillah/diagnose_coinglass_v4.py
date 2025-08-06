
import os
import requests
import json
from datetime import datetime

def diagnose_coinglass_v4():
    """Diagnose CoinGlass V4 API connection issues"""
    
    print("🔍 DIAGNOSING COINGLASS V4 API CONNECTION")
    print("=" * 50)
    
    # Get API key
    api_key = os.getenv("COINGLASS_API_KEY")
    if not api_key:
        print("❌ COINGLASS_API_KEY not found in environment!")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Test different endpoint variations
    test_endpoints = [
        "https://open-api-v4.coinglass.com/public/v1/futures/tickers",
        "https://open-api-v4.coinglass.com/api/futures/price-change-list",
        "https://open-api-v4.coinglass.com/api/pro/v1/futures/ticker",
        "https://open-api.coinglass.com/public/v2/futures/ticker",
        "https://open-api.coinglass.com/api/pro/v1/futures/ticker"
    ]
    
    headers = {
        "X-API-KEY": api_key,
        "accept": "application/json"
    }
    
    print(f"\n🚀 Testing {len(test_endpoints)} endpoints...")
    
    working_endpoints = []
    
    for i, url in enumerate(test_endpoints, 1):
        print(f"\n{i}. Testing: {url}")
        
        try:
            # Test with BTC first
            params = {"symbol": "BTC"}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ SUCCESS - Got JSON response")
                    
                    # Check if data looks real
                    if "data" in data and data["data"]:
                        sample = data["data"][0] if isinstance(data["data"], list) else data["data"]
                        price = sample.get("price", 0) if isinstance(sample, dict) else 0
                        
                        if price and price > 10000:  # BTC should be > $10k
                            print(f"   📊 Price: ${price:,.2f} - Looks REAL!")
                            working_endpoints.append({
                                "url": url,
                                "sample_data": sample,
                                "price": price
                            })
                        else:
                            print(f"   ⚠️ Price: ${price} - Might be DUMMY data")
                    else:
                        print(f"   ⚠️ No data field in response")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response")
                    
            elif response.status_code == 404:
                print(f"   ❌ 404 - Endpoint not found")
            elif response.status_code == 401:
                print(f"   ❌ 401 - Unauthorized (API key issue)")
            elif response.status_code == 429:
                print(f"   ❌ 429 - Rate limited")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except requests.RequestException as e:
            print(f"   ❌ Network error: {str(e)[:50]}...")
    
    print(f"\n📊 DIAGNOSIS RESULTS")
    print("=" * 30)
    
    if working_endpoints:
        print(f"✅ Found {len(working_endpoints)} working endpoint(s):")
        for endpoint in working_endpoints:
            print(f"   • {endpoint['url']}")
            print(f"     Price: ${endpoint['price']:,.2f}")
        
        print(f"\n✅ CoinGlass V4 API is WORKING with real data!")
        return True
        
    else:
        print("❌ NO working endpoints found!")
        print("\n📩 SUPPORT MESSAGE FOR COINGLASS:")
        print("-" * 40)
        print(f"""
Halo tim CoinGlass,
Saya sudah upgrade ke STARTUP plan dan mendapatkan API Key: {api_key}
Namun saat saya mengakses endpoint API v4, hasilnya error 404/401.
Saya sudah pakai header X-API-Key, dan mencoba berbagai endpoint v4.
Mohon bantuannya untuk aktivasi penuh akun saya. Terima kasih.

Tested endpoints:
{chr(10).join(['- ' + url for url in test_endpoints])}

Current status: All endpoints returning 404 or errors.
""")
        print("-" * 40)
        print("\n💡 Send this message to: https://t.me/coinglass")
        return False

def test_specific_symbols():
    """Test specific symbols that are failing"""
    api_key = os.getenv("COINGLASS_API_KEY")
    if not api_key:
        return
    
    print(f"\n🎯 TESTING SPECIFIC SYMBOLS FROM LOGS")
    print("=" * 40)
    
    failing_symbols = ["SANDUSDT", "VETUSDT", "MANAUSDT"]
    working_url = "https://open-api-v4.coinglass.com/api/futures/price-change-list"
    
    headers = {
        "X-API-KEY": api_key,
        "accept": "application/json"
    }
    
    for symbol in failing_symbols:
        print(f"\n🔍 Testing {symbol}:")
        
        try:
            params = {"symbol": symbol}
            response = requests.get(working_url, headers=headers, params=params, timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    print(f"   ✅ {symbol} is available!")
                else:
                    print(f"   ❌ {symbol} returned empty data")
            else:
                print(f"   ❌ {symbol} not available (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:30]}...")

if __name__ == "__main__":
    print(f"🕐 Diagnosis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run main diagnosis
    api_working = diagnose_coinglass_v4()
    
    # Test specific symbols
    test_specific_symbols()
    
    print(f"\n{'✅ DIAGNOSIS COMPLETE - API WORKING' if api_working else '❌ DIAGNOSIS COMPLETE - API ISSUES FOUND'}")
    print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
