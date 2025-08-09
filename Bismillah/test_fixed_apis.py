
#!/usr/bin/env python3
"""
Test script untuk API yang sudah diperbaiki
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crypto_api import CryptoAPI
from coinmarketcap_provider import CoinMarketCapProvider
from coinglass_provider import CoinGlassProvider

def test_coinmarketcap():
    """Test CoinMarketCap Provider"""
    print("🔍 Testing CoinMarketCap Provider...")
    
    cmc = CoinMarketCapProvider()
    
    # Test connection
    connection_test = cmc.test_connection()
    print(f"Connection Test: {connection_test}")
    
    if connection_test['status'] == 'success':
        # Test BTC quotes
        btc_data = cmc.get_cryptocurrency_quotes('BTC')
        print(f"BTC Data: ${btc_data.get('price', 0):,.2f}")
        
        # Test market overview
        market_data = cmc.get_enhanced_market_overview()
        global_cap = market_data.get('global_metrics', {}).get('total_market_cap', 0)
        print(f"Global Market Cap: ${global_cap/1e12:.2f}T")
    
    print()

def test_coinglass():
    """Test CoinGlass Provider"""
    print("🔍 Testing CoinGlass Provider...")
    
    cg = CoinGlassProvider()
    
    # Test connection
    connection_test = cg.test_connection()
    print(f"Connection Test: {connection_test}")
    
    if connection_test['status'] == 'success':
        # Test BTC ticker
        btc_ticker = cg.get_futures_ticker('BTC')
        print(f"BTC Futures: ${btc_ticker.get('price', 0):,.2f}, Funding: {btc_ticker.get('funding_rate', 0)*100:.4f}%")
        
        # Test Open Interest
        btc_oi = cg.get_open_interest('BTC')
        print(f"BTC OI: ${btc_oi.get('total_open_interest', 0)/1e9:.2f}B")
        
        # Test Long/Short Ratio
        btc_ls = cg.get_long_short_ratio('BTC')
        print(f"BTC L/S Ratio: {btc_ls.get('long_ratio', 50):.1f}% / {btc_ls.get('short_ratio', 50):.1f}%")
    
    print()

def test_crypto_api():
    """Test Unified CryptoAPI"""
    print("🔍 Testing Unified CryptoAPI...")
    
    api = CryptoAPI()
    
    # Test all connections
    connection_test = api.test_all_connections()
    print(f"Overall Status: {connection_test['overall_status'].upper()}")
    print(f"Working APIs: {connection_test['working_apis']}/{connection_test['total_apis']}")
    
    # Test price data
    symbols = ['BTC', 'ETH', 'BNB']
    
    for symbol in symbols:
        price_data = api.get_crypto_price(symbol)
        
        if 'error' not in price_data:
            price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)
            source = price_data.get('source', 'unknown')
            
            print(f"{symbol}: ${price:,.2f} ({change_24h:+.2f}%) - {source}")
        else:
            print(f"{symbol}: ❌ {price_data['error']}")
    
    print()

def test_futures_data():
    """Test comprehensive futures data"""
    print("🔍 Testing Comprehensive Futures Data...")
    
    api = CryptoAPI()
    
    symbols = ['BTC', 'ETH']
    
    for symbol in symbols:
        futures_data = api.get_comprehensive_futures_data(symbol)
        
        if 'error' not in futures_data:
            quality = futures_data.get('data_quality', {})
            success_rate = quality.get('quality_score', 0)
            
            print(f"{symbol} Futures Data Quality: {success_rate:.1f}%")
            
            # Show key metrics
            ticker = futures_data.get('ticker_data', {})
            oi = futures_data.get('open_interest_data', {})
            
            if 'error' not in ticker:
                price = ticker.get('price', 0)
                funding = ticker.get('funding_rate', 0)
                print(f"  Price: ${price:,.2f}, Funding: {funding*100:.4f}%")
            
            if 'error' not in oi:
                total_oi = oi.get('total_open_interest', 0)
                oi_change = oi.get('oi_change_percent', 0)
                print(f"  OI: ${total_oi/1e9:.2f}B ({oi_change:+.1f}%)")
        else:
            print(f"{symbol}: ❌ {futures_data['error']}")
    
    print()

def main():
    """Run all tests"""
    print("🚀 CryptoMentor AI - API Testing Suite")
    print("=" * 50)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check environment variables
    cmc_key = os.getenv("COINMARKETCAP_API_KEY") or os.getenv("CMC_API_KEY")
    cg_key = os.getenv("COINGLASS_API_KEY") or os.getenv("COINGLASS_SECRET")
    
    print(f"🔑 API Keys Status:")
    print(f"  CoinMarketCap: {'✅ Available' if cmc_key else '❌ Missing'}")
    print(f"  CoinGlass: {'✅ Available' if cg_key else '❌ Missing'}")
    print()
    
    if not cmc_key and not cg_key:
        print("❌ No API keys found! Please set environment variables:")
        print("  - COINMARKETCAP_API_KEY or CMC_API_KEY")
        print("  - COINGLASS_API_KEY or COINGLASS_SECRET")
        return
    
    # Run tests
    if cmc_key:
        test_coinmarketcap()
    
    if cg_key:
        test_coinglass()
    
    if cmc_key or cg_key:
        test_crypto_api()
        test_futures_data()
    
    print("✅ Testing completed!")
    print("🎯 If all tests pass, your APIs are working correctly.")
    print("💡 Run your bot now to see real data instead of zeros!")

if __name__ == "__main__":
    main()
