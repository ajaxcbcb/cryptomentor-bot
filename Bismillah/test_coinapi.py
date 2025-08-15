
#!/usr/bin/env python3
"""
Test CoinAPI Integration
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crypto_api import CryptoAPI

def test_coinapi():
    """Test CoinAPI functionality"""
    print("🔍 Testing CoinAPI Integration...")
    
    # Check API key
    coinapi_key = os.getenv('COINAPI_KEY') or os.getenv('COINAPI_IO_KEY')
    if not coinapi_key:
        print("❌ COINAPI_KEY not found in environment")
        print("💡 Please add COINAPI_KEY to Replit Secrets")
        return False
    
    print(f"✅ CoinAPI Key found: {coinapi_key[-4:]}")
    
    # Test API
    crypto_api = CryptoAPI()
    
    # Test popular coins
    test_symbols = ['BTC', 'ETH', 'BNB']
    
    for symbol in test_symbols:
        print(f"\n🔄 Testing {symbol}...")
        
        # Test CoinAPI directly
        coinapi_result = crypto_api.get_coinapi_price(symbol)
        if 'error' not in coinapi_result:
            price = coinapi_result['price']
            print(f"✅ CoinAPI: ${price:,.4f}")
        else:
            print(f"❌ CoinAPI: {coinapi_result['error']}")
        
        # Test unified method
        unified_result = crypto_api.get_crypto_price(symbol, force_refresh=True)
        if 'error' not in unified_result:
            price = unified_result['price']
            source = unified_result.get('source', 'unknown')
            print(f"✅ Unified: ${price:,.4f} from {source}")
        else:
            print(f"❌ Unified: {unified_result.get('error', 'Unknown error')}")
    
    return True

if __name__ == "__main__":
    test_coinapi()
