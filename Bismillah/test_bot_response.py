
<line_number>1</line_number>
#!/usr/bin/env python3
"""
Simple test to check if bot can respond to commands
"""
import asyncio
from crypto_api import crypto_api
from ai_assistant import AIAssistant

async def test_futures_analysis():
    """Test futures analysis function directly"""
    print("🔍 Testing Futures Analysis Function...")
    
    try:
        # Initialize AI Assistant
        ai_assistant = AIAssistant()
        print("✅ AI Assistant initialized")
        
        # Test with BTC
        symbol = "BTC"
        timeframe = "4h"
        
        print(f"📊 Testing analysis for {symbol} on {timeframe}...")
        
        analysis = await ai_assistant.get_futures_analysis(
            symbol, timeframe, 'id', crypto_api, None, None
        )
        
        print("✅ Analysis completed!")
        print("📝 Analysis preview:")
        print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_simple_price():
    """Test simple price fetching"""
    print("\n💰 Testing Price Fetching...")
    
    try:
        price_data = crypto_api.get_crypto_price("BTC", force_refresh=True)
        
        if 'error' not in price_data:
            price = price_data.get('price', 0)
            change = price_data.get('change_24h', 0)
            print(f"✅ BTC Price: ${price:,.2f} ({change:+.2f}%)")
            return True
        else:
            print(f"❌ Price fetch failed: {price_data.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Price test failed: {e}")
        return False

async def main():
    print("🤖 Bot Response Test")
    print("=" * 40)
    
    # Test price fetching first
    price_ok = await test_simple_price()
    
    # Test futures analysis if price is working
    if price_ok:
        futures_ok = await test_futures_analysis()
    else:
        print("⏭️ Skipping futures test due to price fetch failure")
        futures_ok = False
    
    print("\n📊 TEST RESULTS:")
    print(f"{'✅' if price_ok else '❌'} Price Fetching: {'OK' if price_ok else 'FAILED'}")
    print(f"{'✅' if futures_ok else '❌'} Futures Analysis: {'OK' if futures_ok else 'FAILED'}")
    
    if price_ok and futures_ok:
        print("\n🎉 Bot should be working correctly!")
    else:
        print("\n⚠️ Bot has issues - check the errors above")

if __name__ == "__main__":
    asyncio.run(main())
