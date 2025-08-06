
#!/usr/bin/env python3
import os
from coinglass_provider import CoinglassProvider

def test_coinglass_connection():
    """Test if CoinGlass connection is working with real data"""
    
    print("🧪 TESTING COINGLASS CONNECTION AFTER FIXES")
    print("=" * 50)
    
    # Initialize provider
    provider = CoinglassProvider()
    
    if not provider.api_key:
        print("❌ No API key found!")
        return False
    
    print(f"✅ API Key: {provider.api_key[:8]}...{provider.api_key[-4:]}")
    print(f"🌐 Base URL: {provider.base_url}")
    
    # Test with major coins
    test_symbols = ['BTC', 'ETH', 'SOL']
    
    for symbol in test_symbols:
        print(f"\n🔍 Testing {symbol}:")
        
        # Test ticker data
        print(f"   📊 Getting ticker data...")
        ticker_data = provider.get_futures_ticker(symbol)
        
        if 'error' not in ticker_data:
            price = ticker_data.get('price', 0)
            print(f"   ✅ Ticker: ${price:,.2f} - {'REAL' if price > 1000 else 'SUSPICIOUS'}")
        else:
            print(f"   ❌ Ticker: {ticker_data['error']}")
        
        # Test long/short data
        print(f"   📈 Getting long/short data...")
        ls_data = provider.get_long_short_ratio(symbol)
        
        if 'error' not in ls_data:
            long_ratio = ls_data.get('long_ratio', 0)
            print(f"   ✅ L/S Ratio: {long_ratio:.1f}% Long - {'REAL' if 20 <= long_ratio <= 80 else 'SUSPICIOUS'}")
        else:
            print(f"   ❌ L/S Ratio: {ls_data['error']}")
        
        print("-" * 30)
    
    # Test comprehensive data
    print(f"\n🎯 Testing comprehensive futures data for BTC...")
    comprehensive = provider.get_comprehensive_futures_data('BTC')
    
    if 'error' not in comprehensive:
        successful = comprehensive.get('successful_calls', 0)
        total = comprehensive.get('total_calls', 5)
        quality = comprehensive.get('data_quality', 'unknown')
        
        print(f"✅ Comprehensive: {successful}/{total} calls successful")
        print(f"📊 Data Quality: {quality.upper()}")
        
        if successful >= 2:
            print("🎉 CoinGlass integration is WORKING!")
            return True
        else:
            print("⚠️ Limited data availability")
            return False
    else:
        print(f"❌ Comprehensive: {comprehensive['error']}")
        return False

if __name__ == "__main__":
    success = test_coinglass_connection()
    
    if success:
        print("\n🎉 COINGLASS INTEGRATION SUCCESSFUL!")
        print("💡 Bot should work properly now")
    else:
        print("\n❌ COINGLASS ISSUES REMAIN")
        print("💡 Check API key validity or contact CoinGlass support")
