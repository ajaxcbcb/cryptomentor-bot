
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    print("🧪 Quick Health Check for CryptoMentor AI Services")
    print("=" * 50)
    
    try:
        from app.services import services_healthcheck, futures_signals
        
        print("1️⃣ Testing services healthcheck...")
        result = await services_healthcheck()
        
        if result.get("ok"):
            print(f"✅ Healthcheck passed!")
            print(f"   Sample BTC close: ${result.get('sample_close', 0):,.2f}")
        else:
            print(f"❌ Healthcheck failed: {result.get('error', 'Unknown')}")
            return
        
        print("\n2️⃣ Testing futures signals (top 5)...")
        signals = await futures_signals(None, threshold=70.0)  # Lower threshold for testing
        print(f"✅ Found {len(signals)} signals")
        
        if signals[:3]:
            print("   Sample signals:")
            for i, sig in enumerate(signals[:3], 1):
                print(f"   {i}. {sig.get('coin', 'N/A')}: {sig.get('confidence', 0):.1f}% confidence")
        
        print("\n✅ All services working correctly!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Runtime error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
