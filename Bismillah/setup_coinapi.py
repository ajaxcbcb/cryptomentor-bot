
import os
from crypto_api import CryptoAPI

def verify_api_setup():
    """Verify Coinglass V4 and CoinMarketCap API setup and configuration"""
    print("🔧 Verifying Coinglass V4 and CoinMarketCap API setup...")
    
    # Check if COINGLASS_SECRET is in environment
    coinglass_key = os.getenv("COINGLASS_SECRET")
    if not coinglass_key:
        print("❌ COINGLASS_SECRET not found in environment variables")
        print("💡 Please add COINGLASS_SECRET to Replit Secrets:")
        print("   1. Go to Tools > Secrets")
        print("   2. Add key: COINGLASS_SECRET")
        print("   3. Add your Coinglass API key as value")
        coinglass_ok = False
    else:
        print("✅ COINGLASS_SECRET found in environment")
        coinglass_ok = True
    
    # Check if CMC_API_KEY is in environment
    cmc_key = os.getenv("CMC_API_KEY")
    if not cmc_key:
        print("❌ CMC_API_KEY not found in environment variables")
        print("💡 Please add CMC_API_KEY to Replit Secrets:")
        print("   1. Go to Tools > Secrets")
        print("   2. Add key: CMC_API_KEY")
        print("   3. Add your CoinMarketCap API key as value")
        cmc_ok = False
    else:
        print("✅ CMC_API_KEY found in environment")
        cmc_ok = True
    
    # Test API connections
    crypto_api = CryptoAPI()
    
    # Test Coinglass
    if coinglass_ok:
        test_result = crypto_api.get_coinglass_futures_data('BTC')
        if 'error' not in test_result:
            print("✅ Coinglass API connection successful")
            coinglass_working = True
        else:
            print("❌ Coinglass API connection failed")
            print(f"   Error: {test_result.get('error', 'Unknown error')}")
            coinglass_working = False
    else:
        coinglass_working = False
    
    # Test CoinMarketCap
    if cmc_ok:
        test_result = crypto_api.get_coinmarketcap_summary('BTC')
        if 'error' not in test_result:
            print("✅ CoinMarketCap API connection successful")
            cmc_working = True
        else:
            print("❌ CoinMarketCap API connection failed")
            print(f"   Error: {test_result.get('error', 'Unknown error')}")
            cmc_working = False
    else:
        cmc_working = False
    
    overall_health = coinglass_working and cmc_working
    
    return {
        'coinglass_key_present': coinglass_ok,
        'cmc_key_present': cmc_ok,
        'coinglass_working': coinglass_working,
        'cmc_working': cmc_working,
        'overall_health': overall_health
    }

if __name__ == "__main__":
    result = verify_api_setup()
    if result['overall_health']:
        print("🎉 API setup verification completed successfully!")
        print("✅ Both Coinglass and CoinMarketCap APIs are working")
    else:
        print("❌ API setup verification failed. Please check your configuration.")
        print("\n🔧 Troubleshooting steps:")
        if not result['coinglass_working']:
            print("1. Verify COINGLASS_SECRET is set in Replit Secrets")
            print("2. Check if your Coinglass API key is valid")
        if not result['cmc_working']:
            print("3. Verify CMC_API_KEY is set in Replit Secrets")
            print("4. Check if your CoinMarketCap API key is valid")
        print("5. Try restarting the Repl")
