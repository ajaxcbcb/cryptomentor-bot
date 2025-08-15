
#!/usr/bin/env python3
"""
Test script for new CoinAPI implementation
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_coinapi_connection():
    """Test CoinAPI connection and basic functionality"""
    print("🔍 Testing CoinAPI Connection...")
    
    try:
        from app.providers.coinapi import get_price_spot, get_ohlcv
        
        # Test price fetch
        print("📊 Testing price fetch for BTC...")
        btc_price = await get_price_spot("BTC")
        print(f"✅ BTC Price: ${btc_price:.2f}")
        
        # Test OHLCV data
        print("📈 Testing OHLCV data for ETH...")
        eth_ohlcv = await get_ohlcv("ETH", period="5MIN", limit=50)
        print(f"✅ ETH OHLCV: {len(eth_ohlcv)} candles retrieved")
        
        return True
        
    except Exception as e:
        print(f"❌ CoinAPI test failed: {e}")
        return False

async def test_analysis_services():
    """Test analysis services"""
    print("🔬 Testing Analysis Services...")
    
    try:
        from app.services.analysis import analyze_coin, futures_entry, futures_signals, market_overview
        
        # Test analyze_coin
        print("📊 Testing analyze_coin for BTC...")
        btc_analysis = await analyze_coin("BTC")
        print(f"✅ BTC Analysis: Price=${btc_analysis['price']:.2f}, Trend={btc_analysis['trend']}")
        
        # Test futures_entry
        print("🎯 Testing futures_entry for ETH...")
        eth_futures = await futures_entry("ETH")
        print(f"✅ ETH Futures: Entry=${eth_futures['entry']:.2f}")
        
        # Test futures_signals
        print("🚨 Testing futures_signals...")
        signals = await futures_signals(["BTC", "ETH"])
        print(f"✅ Signals: {len(signals)} coins analyzed")
        
        # Test market_overview
        print("🌐 Testing market_overview...")
        market = await market_overview(["BTC", "ETH", "SOL"])
        print(f"✅ Market: {len(market['coins'])} coins in overview")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis services test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 CryptoMentor AI - New CoinAPI Implementation Test")
    print("=" * 50)
    
    # Check environment variables
    coinapi_key = os.getenv("COINAPI_API_KEY") or os.getenv("COIN_API_KEY")
    if not coinapi_key:
        print("⚠️ WARNING: COINAPI_API_KEY not found in environment")
        print("💡 Please set COINAPI_API_KEY in Replit Secrets")
        return False
    else:
        print("✅ COINAPI_API_KEY found")
    
    # Run tests
    coinapi_ok = await test_coinapi_connection()
    analysis_ok = await test_analysis_services()
    
    print("\n" + "=" * 50)
    if coinapi_ok and analysis_ok:
        print("✅ All tests passed! New CoinAPI implementation is ready.")
        print("\n🎯 Available Commands:")
        print("   • /analyze_new <symbol>")
        print("   • /futures_new <symbol>") 
        print("   • /futures_signals_new")
        print("   • /market_new")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return coinapi_ok and analysis_ok

if __name__ == "__main__":
    asyncio.run(main())
