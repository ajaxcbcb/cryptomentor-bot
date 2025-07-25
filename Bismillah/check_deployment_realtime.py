
#!/usr/bin/env python3
"""
Real-time Data Verification for Deployment
Memverifikasi bahwa bot menggunakan data real-time di deployment mode
"""

import os
import sys
import time
import requests
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto_api import CryptoAPI

def check_deployment_realtime():
    """Check if deployment mode is working with real-time data"""
    print("🚀 TESTING DEPLOYMENT REAL-TIME DATA")
    print("=" * 50)
    
    # Force deployment environment variables for testing
    os.environ['REPLIT_DEPLOYMENT'] = '1'
    os.environ['REPL_SLUG'] = 'cryptomentor-test'
    
    # Create deployment flag
    with open('/tmp/repl_deployment_flag', 'w') as f:
        f.write(f"deployment_test_{datetime.now().isoformat()}")
    
    print("✅ Deployment environment forced")
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize CryptoAPI
    crypto_api = CryptoAPI()
    
    # Test symbols
    test_symbols = ['BTC', 'ETH', 'BNB', 'SOL']
    
    print("📊 Testing Real-time Price Data in Deployment Mode:")
    print("-" * 55)
    
    success_count = 0
    total_tests = len(test_symbols)
    
    for symbol in test_symbols:
        try:
            print(f"\n🔄 Testing {symbol}...")
            start_time = time.time()
            
            # Test with force refresh (deployment mode)
            price_data = crypto_api.get_multi_api_price(symbol, force_refresh=True)
            
            response_time = (time.time() - start_time) * 1000
            
            if 'error' in price_data:
                print(f"❌ {symbol}: {price_data.get('error', 'Unknown error')}")
                print(f"   Response time: {response_time:.0f}ms")
            elif price_data.get('price', 0) > 0:
                price = price_data.get('price', 0)
                change_24h = price_data.get('change_24h', 0)
                source = price_data.get('primary_source', price_data.get('source', 'unknown'))
                
                # Check if this is real data (not mock)
                is_real_data = source not in ['fallback_simulation', 'mock']
                
                if is_real_data:
                    print(f"✅ {symbol}: ${price:,.4f} ({change_24h:+.2f}%)")
                    print(f"   Source: {source}")
                    print(f"   Response time: {response_time:.0f}ms")
                    print(f"   Status: 🚀 REAL-TIME DATA")
                    success_count += 1
                else:
                    print(f"❌ {symbol}: ${price:,.4f} (MOCK DATA)")
                    print(f"   Source: {source}")
                    print(f"   Status: ⚠️ NOT REAL-TIME")
            else:
                print(f"❌ {symbol}: Invalid price data")
                
        except Exception as e:
            print(f"❌ {symbol}: Exception - {str(e)[:50]}...")
    
    print("\n" + "=" * 50)
    print("📊 DEPLOYMENT REAL-TIME TEST RESULTS:")
    print("=" * 50)
    
    success_rate = (success_count / total_tests) * 100
    
    print(f"✅ Successful real-time data: {success_count}/{total_tests}")
    print(f"📈 Success rate: {success_rate:.1f}%")
    
    if success_rate >= 75:
        status = "🟢 EXCELLENT - Deployment ready for real-time data"
    elif success_rate >= 50:
        status = "🟡 GOOD - Most APIs working"
    elif success_rate >= 25:
        status = "🟠 PARTIAL - Some APIs working"
    else:
        status = "🔴 POOR - Real-time data not working"
    
    print(f"🎯 Overall Status: {status}")
    
    # Cleanup
    try:
        os.remove('/tmp/repl_deployment_flag')
        print("\n🧹 Cleanup completed")
    except:
        pass
    
    return success_rate >= 50

if __name__ == "__main__":
    success = check_deployment_realtime()
    sys.exit(0 if success else 1)
