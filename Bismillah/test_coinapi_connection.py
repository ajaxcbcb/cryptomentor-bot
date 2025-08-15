
#!/usr/bin/env python3
"""
Test COINAPI connection specifically
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_coinapi_connection():
    """Test COINAPI connection and display detailed status"""
    print("🔍 COINAPI Connection Test")
    print("=" * 50)
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")
    
    # Check if API key exists
    coinapi_key = os.getenv('COINAPI_API_KEY')
    
    if not coinapi_key:
        print("❌ COINAPI_API_KEY not found in environment variables")
        print("💡 Please add COINAPI_API_KEY to Replit Secrets:")
        print("   1. Go to Tools > Secrets")
        print("   2. Add key: COINAPI_API_KEY")
        print("   3. Add your CoinAPI key as value")
        return False
    
    # Mask the key for security
    masked_key = coinapi_key[:8] + "..." + coinapi_key[-4:] if len(coinapi_key) > 12 else "KEY_SET"
    print(f"✅ COINAPI_API_KEY found: {masked_key}")
    
    # Test API connection
    print("\n🔄 Testing COINAPI connection...")
    
    try:
        # Test with BTC/USD exchange rate
        headers = {
            'X-CoinAPI-Key': coinapi_key,
            'User-Agent': 'CryptoMentor-Bot/2.0'
        }
        
        response = requests.get(
            'https://rest.coinapi.io/v1/exchangerate/BTC/USD',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            rate = data.get('rate', 0)
            
            print(f"✅ COINAPI connected successfully!")
            print(f"📊 BTC/USD Rate: ${rate:,.2f}")
            print(f"🕐 Last Update: {data.get('time', 'Unknown')}")
            
            # Test rate limits
            remaining = response.headers.get('X-RateLimit-Remaining', 'Unknown')
            limit = response.headers.get('X-RateLimit-Limit', 'Unknown')
            
            print(f"📈 Rate Limit: {remaining}/{limit} requests remaining")
            
            return True
            
        elif response.status_code == 401:
            print("❌ COINAPI authentication failed!")
            print("🔑 API key is invalid or expired")
            print("💡 Check your API key in Replit Secrets")
            return False
            
        elif response.status_code == 429:
            print("⚠️ COINAPI rate limit exceeded!")
            print("📊 Too many requests - wait before testing again")
            return False
            
        else:
            print(f"❌ COINAPI error: HTTP {response.status_code}")
            print(f"📝 Response: {response.text[:100]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ COINAPI connection timeout")
        print("🌐 Network or API server issues")
        return False
        
    except Exception as e:
        print(f"❌ COINAPI connection error: {e}")
        return False

def main():
    """Main function"""
    success = test_coinapi_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 COINAPI Connection: SUCCESS")
        print("✅ Your bot can access real-time crypto data!")
    else:
        print("❌ COINAPI Connection: FAILED")
        print("🔧 Please fix the issues above")
    
    return success

if __name__ == "__main__":
    main()
