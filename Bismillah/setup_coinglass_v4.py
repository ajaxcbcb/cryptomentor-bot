
#!/usr/bin/env python3
"""
Coinglass V4 API Setup Script
This script helps configure and test the new Coinglass V4 API integration.
"""

import os
import requests
from datetime import datetime

def check_environment():
    """Check if the required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    coinglass_key = os.getenv("COINGLASS_API_KEY")
    
    if coinglass_key:
        print("✅ COINGLASS_API_KEY is set")
        # Hide the key for security, only show first 8 characters
        masked_key = coinglass_key[:8] + "..." if len(coinglass_key) > 8 else "***"
        print(f"   Key: {masked_key}")
        return True
    else:
        print("❌ COINGLASS_API_KEY not found")
        print("💡 Please set COINGLASS_API_KEY in Replit Secrets")
        return False

def test_coinglass_v4_connection():
    """Test connection to Coinglass V4 API"""
    print("\n🧪 Testing Coinglass V4 API connection...")
    
    coinglass_key = os.getenv("COINGLASS_API_KEY")
    if not coinglass_key:
        print("❌ Cannot test - API key not found")
        return False
    
    # Test endpoints
    base_url = "https://open-api.coinglass.com/public/v4"
    headers = {
        "accept": "application/json",
        "X-API-KEY": coinglass_key
    }
    
    test_endpoints = [
        ("Futures Ticker", f"{base_url}/futures/ticker", {"symbol": "BTC"}),
        ("Open Interest", f"{base_url}/open_interest", {"symbol": "BTC"}),
        ("Funding Rate", f"{base_url}/funding_rate", {"symbol": "BTC"}),
        ("Long/Short Ratio", f"{base_url}/long_short_ratio", {"symbol": "BTC"}),
        ("Liquidation Map", f"{base_url}/liquidation_map", {"symbol": "BTC"})
    ]
    
    successful_tests = 0
    total_tests = len(test_endpoints)
    
    for name, url, params in test_endpoints:
        try:
            print(f"  Testing {name}...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"    ✅ {name} - OK")
                    successful_tests += 1
                else:
                    print(f"    ⚠️ {name} - API returned success=false")
                    print(f"       Message: {data.get('msg', 'No message')}")
            else:
                print(f"    ❌ {name} - HTTP {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ {name} - Error: {str(e)}")
    
    print(f"\n📊 Test Results: {successful_tests}/{total_tests} endpoints working")
    
    if successful_tests >= 3:
        print("🎉 Coinglass V4 API is working well!")
        return True
    elif successful_tests >= 1:
        print("⚠️ Coinglass V4 API partially working - some endpoints may have issues")
        return True
    else:
        print("❌ Coinglass V4 API not responding properly")
        return False

def show_migration_guide():
    """Show migration guide from old Coinglass to V4"""
    print("\n📋 Coinglass V4 Migration Summary:")
    print("=" * 50)
    
    print("\n🔧 Environment Variable Changes:")
    print("  OLD: COINGLASS_SECRET")
    print("  NEW: COINGLASS_API_KEY")
    
    print("\n🌐 API URL Changes:")
    print("  OLD: https://open-api.coinglass.com/api/pro/v1/")
    print("  OLD: https://open-api.coinglass.com/public/v2/")  
    print("  NEW: https://open-api.coinglass.com/public/v4/")
    
    print("\n🔑 Header Changes:")
    print("  OLD: {'coinglassSecret': api_key}")
    print("  NEW: {'X-API-KEY': api_key}")
    
    print("\n✨ New V4 Features:")
    print("  • Simplified endpoint structure")
    print("  • Improved response format")
    print("  • Better error handling")
    print("  • Enhanced data accuracy")
    print("  • Startup Plan features fully supported")

def main():
    """Main setup function"""
    print("🚀 Coinglass V4 API Setup & Test")
    print("=" * 40)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment
    if not check_environment():
        print("\n❌ Setup incomplete - please configure COINGLASS_API_KEY first")
        return
    
    # Test API connection
    if test_coinglass_v4_connection():
        print("\n✅ Coinglass V4 setup completed successfully!")
        print("🤖 Your bot is ready to use Coinglass V4 Startup Plan features")
    else:
        print("\n⚠️ Setup completed with warnings")
        print("💡 Some features may not work properly")
    
    # Show migration info
    show_migration_guide()
    
    print("\n🎯 Next Steps:")
    print("1. Run your bot with: python main.py")
    print("2. Test futures commands: /futures btc")
    print("3. Check futures signals: /futures_signals")
    print("4. Monitor the bot logs for any API errors")

if __name__ == "__main__":
    main()
