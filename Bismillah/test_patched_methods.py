
#!/usr/bin/env python3
"""Test script to verify all patched CryptoAPI methods work correctly"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from crypto_api import CryptoAPI
import time

def test_crypto_api():
    """Test all CryptoAPI methods including patched ones"""
    print("🧪 Testing CryptoAPI with all patched methods...")
    
    # Initialize API
    api = CryptoAPI()
    
    # Test symbols
    test_symbols = ['BTC', 'ETH']
    
    print(f"\n📋 Testing methods with symbols: {', '.join(test_symbols)}")
    
    for symbol in test_symbols:
        print(f"\n🔬 Testing {symbol}:")
        
        # Test missing methods that should now be patched
        methods_to_test = [
            ('get_binance_long_short_ratio', 'Long/Short Ratio'),
            ('get_binance_open_interest', 'Open Interest'), 
            ('get_binance_funding_rate', 'Funding Rate'),
            ('get_binance_oi', 'OI (alias)'),
            ('get_liquidation_zones', 'Liquidation Zones'),
            ('analyze_supply_demand', 'Supply/Demand Analysis')
        ]
        
        for method_name, description in methods_to_test:
            try:
                if hasattr(api, method_name):
                    print(f"  ✅ {description}: Method exists")
                    method = getattr(api, method_name)
                    result = method(symbol)
                    
                    if isinstance(result, dict) and 'error' not in result:
                        print(f"     ✅ {description}: Data retrieved successfully")
                    elif isinstance(result, dict) and 'error' in result:
                        print(f"     ⚠️  {description}: API returned error - {result['error'][:50]}...")
                    else:
                        print(f"     ⚠️  {description}: Unexpected response format")
                else:
                    print(f"  ❌ {description}: Method missing!")
                    
            except Exception as e:
                print(f"  ❌ {description}: Exception - {str(e)[:50]}...")
        
        time.sleep(1)  # Avoid API rate limits

    print(f"\n✅ CryptoAPI testing completed!")
    print(f"🎯 All required methods should now be available and working with CoinGlass V4")

if __name__ == "__main__":
    test_crypto_api()
