
import os
from crypto_api import CryptoAPI

def verify_coinglass_setup():
    """Verify Coinglass API setup and configuration"""
    print("🔧 Verifying Coinglass API setup...")
    
    # Check if COINGLASS_API_KEY is in environment
    api_key = os.getenv("COINGLASS_API_KEY")
    if not api_key:
        print("❌ COINGLASS_API_KEY not found in environment variables")
        print("💡 Please add COINGLASS_API_KEY to Replit Secrets:")
        print("   1. Go to Tools > Secrets")
        print("   2. Add key: COINGLASS_API_KEY")
        print("   3. Add your Coinglass API key as value")
        return False
    
    print("✅ COINGLASS_API_KEY found in environment")
    
    # Test Coinglass API connection
    crypto_api = CryptoAPI()
    test_result = crypto_api.test_coinglass_connectivity('BTC')
    
    if test_result.get('overall_health'):
        print("✅ Coinglass API connection successful")
        print(f"🔍 Working endpoints: {test_result.get('working_endpoints', '0/4')}")
        return True
    else:
        print("❌ Coinglass API connection failed")
        print(f"🔍 Working endpoints: {test_result.get('working_endpoints', '0/4')}")
        return False

if __name__ == "__main__":
    success = verify_coinglass_setup()
    if success:
        print("🎉 Coinglass setup verification completed successfully!")
    else:
        print("❌ Coinglass setup verification failed. Please check your configuration.")
        print("\n🔧 Troubleshooting steps:")
        print("1. Verify COINGLASS_SECRET is set in Replit Secrets")
        print("2. Check if your Coinglass API key is valid")
        print("3. Ensure you have proper API rate limits")
        print("4. Try restarting the Repl")fy_coinglass_setup()
