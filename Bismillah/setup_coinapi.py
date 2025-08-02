
import os
from crypto_api import CryptoAPI

def verify_coinapi_setup():
    """Verify CoinAPI setup and configuration"""
    print("🔧 Verifying CoinAPI setup...")
    
    # Check if COINAPI_KEY is in environment
    api_key = os.getenv("COINAPI_KEY")
    if not api_key:
        print("❌ COINAPI_KEY not found in environment variables")
        print("💡 Please add COINAPI_KEY to Replit Secrets:")
        print("   1. Go to Tools > Secrets")
        print("   2. Add key: COINAPI_KEY")
        print("   3. Add your CoinAPI key as value")
        return False
    
    print("✅ COINAPI_KEY found in environment")
    
    # Test CoinAPI connection
    crypto_api = CryptoAPI()
    test_result = crypto_api.test_coinapi_connectivity('BTC')
    
    if test_result.get('overall_health'):
        print("✅ CoinAPI connection successful")
        print(f"💰 BTC price test: ${test_result.get('price_value', 0):,.2f}")
        return True
    else:
        print("❌ CoinAPI connection failed")
        print(f"🔍 Working endpoints: {test_result.get('working_endpoints', '0/2')}")
        return False

if __name__ == "__main__":
    verify_coinapi_setup()
