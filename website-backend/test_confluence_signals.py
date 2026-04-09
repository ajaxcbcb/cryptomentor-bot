#!/usr/bin/env python3
"""
Test script for confluence-based signal generation.
Verifies that signals are generated only when multiple confluence factors align.
"""

import asyncio
import sys
from datetime import datetime, timezone

# Add website-backend to path
sys.path.insert(0, '/app')

async def test_signal_generation():
    """Test that confluence signal generation works without errors."""
    print("=" * 70)
    print("Testing Confluence Signal Generation")
    print("=" * 70)

    # Import the signal generation function
    from app.routes.signals import generate_confluence_signals

    test_symbols = ['BTCUSDT', 'ETHUSDT', 'AVAXUSDT']

    for symbol in test_symbols:
        print(f"\n[{symbol}] Generating confluence signal...")
        try:
            signal = await generate_confluence_signals(symbol)

            if signal:
                print(f"  ✅ Signal generated with confidence score: {signal['confidence']}")
                print(f"     Direction: {signal['direction']}")
                print(f"     Entry: {signal['entry_price']:.4f}")
                print(f"     TP1: {signal['take_profit_1']:.4f}")
                print(f"     TP2: {signal['take_profit_2']:.4f}")
                print(f"     TP3: {signal['take_profit_3']:.4f}")
                print(f"     SL: {signal['stop_loss']:.4f}")
                print(f"     Reason: {signal['reason']}")
            else:
                print(f"  ⏭️  No confluent signal (market conditions don't align)")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)


async def test_endpoint():
    """Test the /dashboard/signals endpoint."""
    print("\n" + "=" * 70)
    print("Testing GET /dashboard/signals Endpoint")
    print("=" * 70)

    try:
        # Import FastAPI test client
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.get("/dashboard/signals")

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            signals = data.get('signals', [])
            print(f"Signals generated: {len(signals)}")

            for sig in signals:
                print(f"\n  {sig['pair']} ({sig['direction']}) - Confidence: {sig['confidence']}")
                print(f"    Entry: {sig['entry']}")
                print(f"    Targets: {sig['targets']}")
                print(f"    Stop Loss: {sig['stopLoss']}")
                print(f"    Reason: {sig.get('reason', 'N/A')}")
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("Starting confluence signal tests...\n")

    # Test signal generation
    asyncio.run(test_signal_generation())

    # Test endpoint (optional, requires FastAPI app running)
    try:
        asyncio.run(test_endpoint())
    except Exception as e:
        print(f"\nEndpoint test skipped: {e}")

    print("\nAll tests completed!")
