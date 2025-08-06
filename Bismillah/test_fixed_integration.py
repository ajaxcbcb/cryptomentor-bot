
#!/usr/bin/env python3
"""
Test script untuk memverifikasi perbaikan integrasi CoinGlass V4
"""

import os
import sys
from datetime import datetime

# Tambahkan path untuk import module
sys.path.append('/home/runner/CryptoMentor-AI-Bot-2025/Bismillah')

from coinglass_provider import CoinGlassProvider
from crypto_api import CryptoAPI

def test_symbol_mapping():
    """Test symbol mapping fixes"""
    print("🧪 Testing Symbol Mapping")
    print("=" * 50)
    
    provider = CoinGlassProvider()
    
    test_cases = [
        ('BTC', 'BTCUSDT'),
        ('ETH', 'ETHUSDT'),
        ('SOL', 'SOLUSDT'),
        ('SAND', 'SANDUSDT'),  # Should NOT become SANDTUSDT
        ('MATIC', 'MATICUSDT'),
        ('BTCUSDT', 'BTCUSDT'),  # Should remain unchanged
        ('SANDUSDT', 'SANDUSDT')  # Should remain unchanged
    ]
    
    all_passed = True
    for input_symbol, expected in test_cases:
        actual = provider._clean_symbol(input_symbol)
        status = "✅" if actual == expected else "❌"
        print(f"  {status} {input_symbol} -> {actual} (expected: {expected})")
        if actual != expected:
            all_passed = False
    
    return all_passed

def test_coinglass_endpoints():
    """Test CoinGlass V4 endpoints"""
    print("\n🧪 Testing CoinGlass V4 Endpoints")
    print("=" * 50)
    
    provider = CoinGlassProvider()
    crypto_api = CryptoAPI()
    
    if not provider.api_key:
        print("❌ COINGLASS_API_KEY not found")
        return False
    
    # Test with popular symbols that should work
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    endpoints = [
        ('Ticker', provider.get_futures_ticker),
        ('Open Interest', provider.get_open_interest_chart),
        ('Funding Rate', provider.get_funding_rate_chart),
        ('Long/Short Ratio', provider.get_long_short_ratio),
        ('Liquidation Map', provider.get_liquidation_map)
    ]
    
    success_count = 0
    total_tests = 0
    
    for symbol in test_symbols:
        print(f"\n📊 Testing {symbol}:")
        for endpoint_name, endpoint_func in endpoints:
            total_tests += 1
            try:
                result = endpoint_func(symbol)
                if 'error' not in result:
                    print(f"  ✅ {endpoint_name}: Success")
                    success_count += 1
                else:
                    error_msg = result['error']
                    if 'tidak tersedia' in error_msg or 'not available' in error_msg:
                        print(f"  ⚠️ {endpoint_name}: {error_msg}")
                        success_count += 0.5  # Partial credit for clean error handling
                    else:
                        print(f"  ❌ {endpoint_name}: {error_msg}")
            except Exception as e:
                print(f"  ❌ {endpoint_name}: Exception - {e}")
    
    success_rate = success_count / total_tests
    print(f"\n📊 Success Rate: {success_rate*100:.1f}% ({success_count}/{total_tests})")
    return success_rate > 0.6

def test_price_data():
    """Test price data without dummy fallbacks"""
    print("\n🧪 Testing Price Data (No Dummy Values)")
    print("=" * 50)
    
    crypto_api = CryptoAPI()
    test_symbols = ['BTC', 'ETH', 'SOL', 'SAND', 'MATIC']
    
    all_good = True
    for symbol in test_symbols:
        try:
            price_data = crypto_api.get_crypto_price(symbol)
            if 'error' not in price_data:
                price = price_data.get('price', 0)
                source = price_data.get('source', 'unknown')
                
                # Check for suspicious dummy prices
                if symbol == 'BTC' and abs(price - 70000) < 1000:
                    print(f"  ❌ {symbol}: Suspicious dummy price ${price:.2f}")
                    all_good = False
                elif price > 0:
                    print(f"  ✅ {symbol}: ${price:.4f} (Source: {source})")
                else:
                    print(f"  ❌ {symbol}: Invalid price {price}")
                    all_good = False
            else:
                print(f"  ⚠️ {symbol}: {price_data['error']}")
        except Exception as e:
            print(f"  ❌ {symbol}: Exception - {e}")
            all_good = False
    
    return all_good

def test_supply_demand_analysis():
    """Test supply/demand analysis"""
    print("\n🧪 Testing Supply/Demand Analysis")
    print("=" * 50)
    
    crypto_api = CryptoAPI()
    test_symbols = ['BTC', 'ETH']
    
    for symbol in test_symbols:
        try:
            analysis = crypto_api.analyze_supply_demand(symbol)
            if 'error' not in analysis:
                signal = analysis.get('signal', 'UNKNOWN')
                confidence = analysis.get('confidence', 0)
                source = analysis.get('source', 'unknown')
                print(f"  ✅ {symbol}: {signal} ({confidence}%) - {source}")
            else:
                print(f"  ⚠️ {symbol}: {analysis['error']}")
        except Exception as e:
            print(f"  ❌ {symbol}: Exception - {e}")

def main():
    """Run all tests"""
    print("🚀 CryptoMentor AI - Integration Test Suite")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Symbol Mapping", test_symbol_mapping),
        ("CoinGlass Endpoints", test_coinglass_endpoints),
        ("Price Data", test_price_data)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {e}")
    
    # Additional test
    test_supply_demand_analysis()
    
    print(f"\n📊 SUMMARY: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Integration is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main()
