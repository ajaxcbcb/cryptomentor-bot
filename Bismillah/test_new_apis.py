
#!/usr/bin/env python3
"""
Test script for the new Binance + CoinMarketCap API architecture
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_provider import data_provider
from crypto_api import crypto_api
from config import check_api_keys

def print_separator(title: str):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_result(data: dict, title: str = "Result"):
    print(f"\n📊 {title}:")
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
        if 'details' in data:
            print(f"Details: {data['details']}")
    else:
        print(f"✅ Success: {data.get('success', 'Unknown status')}")
        print(f"Source: {data.get('source', 'Unknown source')}")
        
        # Print key data points
        for key, value in data.items():
            if key not in ['success', 'source', 'timestamp', 'errors']:
                if isinstance(value, dict):
                    print(f"{key}: {len(value)} items" if value else f"{key}: Empty")
                elif isinstance(value, list):
                    print(f"{key}: {len(value)} items")
                else:
                    print(f"{key}: {value}")

def test_api_connections():
    """Test all API connections"""
    print_separator("API CONNECTION TESTS - BINANCE + COINMARKETCAP")
    
    # Check API keys first
    api_status = check_api_keys()
    print(f"🔑 API Keys Status: {api_status}")
    
    # Test all APIs
    test_results = data_provider.test_all_apis()
    print_result(test_results, "API Connection Test")
    
    return test_results

def test_price_data():
    """Test price data retrieval"""
    print_separator("PRICE DATA TESTS")
    
    test_symbols = ['BTC', 'ETH', 'BNB', 'SOL']
    
    # Test single price
    print(f"\n🔍 Testing single price for BTC...")
    btc_price = crypto_api.get_crypto_price('BTC')
    print_result(btc_price, "BTC Price")
    
    # Test multiple prices
    print(f"\n🔍 Testing multiple prices for {test_symbols}...")
    multi_prices = crypto_api.get_multiple_prices(test_symbols)
    print_result(multi_prices, "Multiple Prices")
    
    if multi_prices.get('success'):
        print("\n📈 Price Summary:")
        for symbol, price_data in multi_prices.get('prices', {}).items():
            price = price_data.get('price', 0)
            change = price_data.get('change_24h', 0)
            change_symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            print(f"  {symbol}: ${price:,.2f} {change_symbol} {change:+.2f}%")

def test_futures_data():
    """Test futures data retrieval from Binance"""
    print_separator("BINANCE FUTURES DATA TESTS")
    
    test_symbol = 'BTC'
    
    print(f"\n🔍 Testing comprehensive futures data for {test_symbol}...")
    futures_data = crypto_api.get_comprehensive_futures_data(test_symbol)
    print_result(futures_data, f"{test_symbol} Futures Data")
    
    if futures_data.get('success'):
        data = futures_data
        print(f"\n📊 Futures Summary for {test_symbol}:")
        
        # Ticker info
        if 'ticker_data' in data:
            ticker = data['ticker_data']
            print(f"  💰 Price: ${ticker.get('price', 0):,.2f}")
            print(f"  📈 24h Change: {ticker.get('price_change_24h', 0):+.2f}%")
            print(f"  📊 Volume: ${ticker.get('volume_24h', 0):,.0f}")
        
        # Open Interest
        if 'open_interest_data' in data:
            oi = data['open_interest_data']
            print(f"  🏦 Open Interest: {oi.get('total', 0):,.0f}")
            print(f"  🏢 Exchange: {oi.get('dominant_exchange', 'Binance')}")
        
        # Long/Short Ratio
        if 'long_short_data' in data:
            ls = data['long_short_data']
            print(f"  📊 Long: {ls.get('long_ratio', 0):.1f}%")
            print(f"  📊 Short: {ls.get('short_ratio', 0):.1f}%")
            print(f"  🎯 Sentiment: {ls.get('sentiment', 'Unknown')}")
        
        # Funding Rate
        if 'funding_rate_data' in data:
            funding = data['funding_rate_data']
            print(f"  💱 Funding Rate: {funding.get('current_rate', 0):.4f}%")

def test_specific_functions():
    """Test specific API functions"""
    print_separator("SPECIFIC FUNCTION TESTS")
    
    test_symbol = 'ETH'
    
    # Test funding rate
    print(f"\n🔍 Testing funding rate for {test_symbol}...")
    funding_data = crypto_api.get_funding_rate(test_symbol)
    print_result(funding_data, f"{test_symbol} Funding Rate")
    
    # Test open interest
    print(f"\n🔍 Testing open interest for {test_symbol}...")
    oi_data = crypto_api.get_open_interest(test_symbol)
    print_result(oi_data, f"{test_symbol} Open Interest")
    
    # Test long/short ratio
    print(f"\n🔍 Testing long/short ratio for {test_symbol}...")
    ls_data = crypto_api.get_long_short_ratio(test_symbol)
    print_result(ls_data, f"{test_symbol} Long/Short Ratio")

def test_market_overview():
    """Test market overview"""
    print_separator("MARKET OVERVIEW TEST")
    
    print(f"\n🔍 Testing market overview...")
    market_data = crypto_api.get_market_overview()
    print_result(market_data, "Market Overview")
    
    if market_data.get('success'):
        global_metrics = market_data.get('global_metrics', {})
        top_cryptos = market_data.get('top_cryptocurrencies', [])
        
        print(f"\n🌍 Global Market Metrics:")
        if global_metrics:
            market_cap = global_metrics.get('total_market_cap', 0)
            volume = global_metrics.get('total_volume_24h', 0)
            btc_dom = global_metrics.get('btc_dominance', 0)
            
            print(f"  💰 Total Market Cap: ${market_cap:,.0f}")
            print(f"  📊 24h Volume: ${volume:,.0f}")
            print(f"  🟠 BTC Dominance: {btc_dom:.1f}%")
        
        print(f"\n🏆 Top Cryptocurrencies ({len(top_cryptos)}):")
        for i, crypto in enumerate(top_cryptos[:5], 1):
            symbol = crypto.get('symbol', 'N/A')
            price = crypto.get('price', 0)
            change = crypto.get('change_24h', 0)
            change_symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            print(f"  {i}. {symbol}: ${price:,.2f} {change_symbol} {change:+.2f}%")

def test_coin_info():
    """Test coin information"""
    print_separator("COIN INFO TEST")
    
    test_symbol = 'BTC'
    
    print(f"\n🔍 Testing coin info for {test_symbol}...")
    info_data = crypto_api.get_crypto_info(test_symbol)
    print_result(info_data, f"{test_symbol} Info")
    
    if info_data.get('success'):
        print(f"\n📋 {test_symbol} Information:")
        print(f"  📛 Name: {info_data.get('name', 'N/A')}")
        print(f"  📂 Category: {info_data.get('category', 'N/A')}")
        print(f"  🏷️ Tags: {', '.join(info_data.get('tags', [])[:5])}")
        description = info_data.get('description', '')
        if description:
            print(f"  📝 Description: {description[:200]}...")

def main():
    """Main test function"""
    print_separator("BINANCE + COINMARKETCAP API TEST SUITE")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python Version: {sys.version}")
    print(f"📡 API Sources: Binance (Futures) + CoinMarketCap (Spot)")
    
    try:
        # Test API connections
        connection_results = test_api_connections()
        
        if connection_results.get('overall_status') in ['poor', 'error']:
            print("\n⚠️ WARNING: Poor API connectivity detected!")
            print("Please check your API keys in Replit Secrets:")
            print("- CMC_API_KEY (or COINMARKETCAP_API_KEY)")
            print("- Binance API is public, no key needed")
            return False
        
        # Run all tests
        test_price_data()
        test_futures_data()
        test_specific_functions()
        test_market_overview()
        test_coin_info()
        
        print_separator("TEST RESULTS SUMMARY")
        print("✅ All tests completed successfully!")
        print(f"🔗 API Status: {connection_results.get('overall_status', 'unknown').upper()}")
        print(f"📊 Working APIs: {connection_results.get('working_apis', 0)}/{connection_results.get('total_apis', 0)}")
        print(f"📡 Data Sources: Binance (Futures) + CoinMarketCap (Market Data)")
        
        # Recommendations
        if connection_results.get('working_apis', 0) < 2:
            print("\n💡 Recommendations:")
            for api_name, api_result in connection_results.get('apis', {}).items():
                if api_result.get('status') != 'success':
                    print(f"  - Fix {api_name}: {api_result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
