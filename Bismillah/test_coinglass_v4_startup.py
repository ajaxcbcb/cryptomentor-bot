
#!/usr/bin/env python3
"""
Test CoinGlass V4 STARTUP Plan Integration
Verify real-time data access and endpoint functionality
"""

import os
import sys
import time
from datetime import datetime

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_coinglass_v4_startup():
    """Test CoinGlass V4 STARTUP plan integration"""
    print("🚀 Testing CoinGlass V4 STARTUP Plan Integration...\n")
    
    # Check API key
    api_key = os.getenv("COINGLASS_API_KEY")
    if not api_key:
        print("❌ COINGLASS_API_KEY not found in environment variables")
        print("💡 Please set COINGLASS_API_KEY in Replit Secrets")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    try:
        # Import and test CoinGlass provider
        from coinglass_provider import CoinGlassProvider
        
        provider = CoinGlassProvider()
        
        # Test STARTUP plan access
        test_results = provider.test_startup_plan_access()
        
        print(f"\n📊 Test Summary:")
        print(f"Success Rate: {test_results['success_rate']:.1f}%")
        print(f"Working Endpoints: {test_results['successful_endpoints']}/{test_results['total_endpoints']}")
        
        # Test specific symbols
        test_symbols = ['BTC', 'ETH', 'BNB']
        print(f"\n🎯 Testing specific symbols:")
        
        for symbol in test_symbols:
            print(f"\n--- Testing {symbol} ---")
            
            # Test ticker
            ticker_result = provider.get_futures_ticker(symbol)
            if 'error' not in ticker_result:
                price = ticker_result.get('price', 0)
                change_24h = ticker_result.get('change_24h', 0)
                print(f"✅ {symbol} Ticker: ${price:,.2f} ({change_24h:+.2f}%)")
                
                # Test individual symbols
        for symbol in test_symbols:
            print(f"\n📊 Testing {symbol}:")
            
            # Test ticker
            ticker_result = provider.get_futures_ticker(symbol)
            if 'error' not in ticker_result:
                price = ticker_result.get('price', 0)
                funding = ticker_result.get('funding_rate', 0)
                print(f"✅ {symbol} Ticker: ${price:.2f}, Funding: {funding*100:.4f}%")
                
                # Check if data looks real
                if price > 0 and price not in [1, 1000]:
                    print(f"✅ {symbol} price data appears real-time")
                    test_results[f'{symbol}_ticker'] = True
                else:
                    print(f"⚠️ {symbol} price data may be dummy: ${price}")
                    test_results[f'{symbol}_ticker'] = False
            else:
                print(f"❌ {symbol} ticker failed: {ticker_result.get('error')}")
                test_results[f'{symbol}_ticker'] = False
            
            # Test OI
            oi_result = provider.get_open_interest(symbol)
            if 'error' not in oi_result:
                oi_value = oi_result.get('open_interest', 0)
                oi_change = oi_result.get('oi_change_percent', 0)
                print(f"✅ {symbol} OI: ${oi_value/1000000:.1f}M ({oi_change:+.1f}%)")
                test_results[f'{symbol}_oi'] = True
            else:
                print(f"❌ {symbol} OI failed: {oi_result.get('error')}")
                test_results[f'{symbol}_oi'] = False
            
            # Test funding
            funding_result = provider.get_funding_rate(symbol)
            if 'error' not in funding_result:
                funding_rate = funding_result.get('funding_rate', 0)
                exchange = funding_result.get('exchange', 'Unknown')
                print(f"✅ {symbol} Funding: {funding_rate*100:.4f}% ({exchange})")
                test_results[f'{symbol}_funding'] = True
            else:
                print(f"❌ {symbol} funding failed: {funding_result.get('error')}")
                test_results[f'{symbol}_funding'] = False
                
            time.sleep(0.5)  # Rate limiting
        
        # Test with AI Assistant
        print(f"\n🤖 Testing AI Assistant integration:")
        try:
            from ai_assistant import # Test with AI Assistant
        try:
            from ai_assistant import AIAssistant
            
            ai = AIAssistant()
            if ai.coinglass_provider:
                print("✅ AI Assistant CoinGlass V4 provider initialized")
                
                # Test comprehensive analysis
                analysis = ai._get_advanced_coinglass_startup_data('BTC')
                if 'error' not in analysis:
                    print(f"✅ AI comprehensive analysis working")
                    print(f"📊 Data quality: {analysis.get('data_quality', 'unknown')}")
                    print(f"📡 Plan: {analysis.get('plan', 'unknown')}")
                    print(f"✅ Successful endpoints: {analysis.get('endpoints_successful', 0)}/{analysis.get('endpoints_called', 0)}")
                else:
                    print(f"❌ AI analysis failed: {analysis.get('error')}")
            else:
                print("❌ AI Assistant CoinGlass provider not initialized")
                
        except Exception as e:
            print(f"❌ AI Assistant test failed: {e}")
        
        # Final verdict
        success_count = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
        
        if success_rate >= 66:
            print(f"\n🎉 CoinGlass V4 STARTUP Plan is working well!")
            print(f"✅ Real-time data access confirmed")
            print(f"✅ Integration successful")
            return True
        else:
            print(f"\n⚠️ CoinGlass V4 STARTUP Plan has issues")
            print(f"❌ Some endpoints failing")
            print(f"💡 Check API key permissions and plan limits")
            return Falsets")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print(f"⏰ Test started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    success = test_coinglass_v4_startup()
    
    if success:
        print(f"\n🎯 Result: STARTUP Plan integration successful!")
        print(f"💡 You can now use CoinGlass V4 real-time data in your bot")
    else:
        print(f"\n❌ Result: Integration needs attention")
        print(f"💡 Check your COINGLASS_API_KEY and plan status")
    
    print(f"⏰ Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#!/usr/bin/env python3
"""
Test CoinGlass V4 STARTUP Plan Implementation
Verifies all endpoints and data quality
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from coinglass_provider import CoinGlassProvider, run_startup_test

def main():
    print("🧪 CoinGlass V4 STARTUP Plan Test Suite")
    print("=" * 60)
    print(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check API key
    api_key = os.getenv("COINGLASS_API_KEY") or os.getenv("COINGLASS_SECRET")
    if api_key:
        print(f"🔑 API Key: ✅ Configured (...{api_key[-4:]})")
    else:
        print("🔑 API Key: ❌ Not found")
        print("💡 Please set COINGLASS_API_KEY in Replit Secrets")
        return
    
    print("\n" + "=" * 60)
    
    # Run the requested test
    test_results = run_startup_test()
    
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY:")
    print(f"✅ Success Rate: {test_results.get('success_rate', 0):.1f}%")
    print(f"📈 Endpoints Working: {test_results.get('successful_endpoints', 0)}/{test_results.get('total_endpoints', 0)}")
    
    if test_results.get('success_rate', 0) >= 80:
        print("🟢 Status: EXCELLENT - STARTUP plan working perfectly")
    elif test_results.get('success_rate', 0) >= 50:
        print("🟡 Status: GOOD - Partial STARTUP plan access")
    else:
        print("🔴 Status: LIMITED - Check API key and plan")
    
    print("\n💡 Next Steps:")
    print("1. If tests pass → Integration ready for bot")
    print("2. If tests fail → Check API key in Replit Secrets")
    print("3. Monitor data quality for real-time validation")

if __name__ == "__main__":
    main()
