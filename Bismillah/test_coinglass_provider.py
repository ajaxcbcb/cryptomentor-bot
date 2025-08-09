
#!/usr/bin/env python3
"""
Test script for CoinGlass Provider V4
"""

import os
import sys
from datetime import datetime
from coinglass_provider import CoinGlassProvider

def test_coinglass_provider():
    """Test the new CoinGlass provider"""
    print("🚀 Testing CoinGlass Provider V4")
    print("=" * 50)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize provider
    provider = CoinGlassProvider()
    
    # Test API key
    print(f"\n🔑 API Key Status: {'✅ Enabled' if provider.api_key else '❌ Disabled'}")
    if provider.api_key:
        print(f"   Key: {provider.api_key[:10]}...")
    
    # Test connection
    print("\n🧪 Testing API connection...")
    connection_test = provider.test_connection()
    print(f"   Status: {connection_test['status']}")
    if connection_test['status'] == 'failed':
        print(f"   Error: {connection_test['error']}")
        return False
    
    # Test symbol mapping
    print("\n🗺️ Testing symbol mapping...")
    test_symbols = ['BTC', 'ETH', 'BNB', 'btc', 'BTCUSDT']
    for symbol in test_symbols:
        mapped = provider._map_symbol(symbol)
        print(f"   {symbol} → {mapped}")
    
    # Test individual endpoints
    print("\n📊 Testing individual endpoints...")
    test_symbol = 'BTC'
    successful_tests = 0
    
    endpoints = [
        ('Futures Ticker', provider.get_futures_ticker),
        ('Open Interest', provider.get_open_interest_chart),
        ('Funding Rate', provider.get_funding_rate_chart),
        ('Long/Short Ratio', provider.get_long_short_ratio),
        ('Liquidation Map', provider.get_liquidation_map),
        ('Volume Chart', provider.get_volume_chart)
    ]
    
    for endpoint_name, endpoint_func in endpoints:
        try:
            print(f"   Testing {endpoint_name}...", end=" ")
            result = endpoint_func(test_symbol)
            
            if isinstance(result, dict) and 'error' not in result:
                print("✅")
                successful_tests += 1
            else:
                print(f"❌ {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    # Test comprehensive data
    print(f"\n📋 Testing comprehensive data...")
    try:
        comprehensive = provider.get_comprehensive_data(test_symbol)
        if 'error' not in comprehensive:
            print(f"   ✅ Comprehensive data: {comprehensive['data_quality']}")
            successful_tests += 1
        else:
            print(f"   ❌ {comprehensive['error']}")
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
    
    # Show supported symbols
    print(f"\n📝 Supported symbols ({len(provider.get_supported_symbols())}):")
    symbols = provider.get_supported_symbols()
    for i in range(0, len(symbols), 10):
        print(f"   {', '.join(symbols[i:i+10])}")
    
    # Summary
    total_tests = len(endpoints) + 1  # +1 for comprehensive test
    print(f"\n📊 Test Results: {successful_tests}/{total_tests} endpoints working")
    
    if successful_tests >= total_tests * 0.8:
        print("✅ CoinGlass Provider V4 is working properly")
        return True
    elif successful_tests >= total_tests * 0.5:
        print("⚠️ CoinGlass Provider V4 has partial functionality")
        return True
    else:
        print("❌ CoinGlass Provider V4 is not responding properly")
        return False

if __name__ == "__main__":
    try:
        success = test_coinglass_provider()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Test error: {e}")
        sys.exit(1)
