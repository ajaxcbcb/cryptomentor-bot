
#!/usr/bin/env python3
"""
Test script for enhanced futures signals system
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crypto_api import CryptoAPI
from ai_assistant import AIAssistant
from database import Database

async def test_enhanced_futures():
    """Test the enhanced futures signals system"""
    print("🧪 Testing Enhanced Futures Signals System")
    print("=" * 50)
    
    # Initialize components
    crypto_api = CryptoAPI()
    ai = AIAssistant()
    db = Database()
    
    # Test 1: CoinAPI connectivity
    print("\n1️⃣ Testing CoinAPI connectivity...")
    test_result = crypto_api.test_coinapi_connectivity('BTC')
    print(f"   Overall Health: {'✅ GOOD' if test_result.get('overall_health') else '❌ POOR'}")
    if test_result.get('price_value'):
        print(f"   BTC Price: ${test_result.get('price_value'):,.2f}")
    
    # Test 2: CoinMarketCap integration
    print("\n2️⃣ Testing CoinMarketCap integration...")
    cmc_status = crypto_api.cmc_provider.check_api_status()
    print(f"   API Status: {'✅ WORKING' if cmc_status.get('overall_health') else '❌ FAILED'}")
    if cmc_status.get('btc_price'):
        print(f"   BTC Price (CMC): ${cmc_status.get('btc_price'):,.2f}")
    
    # Test 3: Individual futures analysis
    print("\n3️⃣ Testing individual futures analysis...")
    test_symbols = ['BTC', 'ETH', 'SOL']
    
    for symbol in test_symbols:
        print(f"\n   📊 Testing {symbol} futures analysis...")
        try:
            analysis = ai.get_futures_analysis(symbol, '1h', 'id', crypto_api)
            if analysis and len(analysis) > 100:
                print(f"   ✅ {symbol}: Analysis generated ({len(analysis)} chars)")
            else:
                print(f"   ❌ {symbol}: Analysis failed or too short")
        except Exception as e:
            print(f"   ❌ {symbol}: Error - {str(e)}")
    
    # Test 4: Futures signals generation
    print("\n4️⃣ Testing futures signals generation...")
    try:
        signals = ai.generate_futures_signals('id', crypto_api)
        if signals and len(signals) > 200:
            print(f"   ✅ Signals generated successfully ({len(signals)} chars)")
        else:
            print(f"   ⚠️ Signals generated but short ({len(signals) if signals else 0} chars)")
    except Exception as e:
        print(f"   ❌ Signals generation error: {str(e)}")
    
    # Test 5: Database connectivity
    print("\n5️⃣ Testing database connectivity...")
    try:
        db.cursor.execute("SELECT COUNT(*) FROM users")
        user_count = db.cursor.fetchone()[0]
        print(f"   ✅ Database connected, {user_count} users found")
    except Exception as e:
        print(f"   ❌ Database error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_futures())} chars)")
            else:
                print(f"   ❌ {symbol}: Analysis too short or failed")
        except Exception as e:
            print(f"   ❌ {symbol}: Error - {e}")
    
    # Test 4: Futures signals generation
    print("\n4️⃣ Testing futures signals generation...")
    try:
        signals = ai.generate_futures_signals('id', crypto_api)
        if signals and len(signals) > 200:
            print(f"   ✅ Signals generated successfully ({len(signals)} chars)")
            # Check for key elements
            if 'Entry sesuai SnD' in signals:
                print("   ✅ Contains SnD entry points")
            if 'TP 1' in signals and 'TP 2' in signals:
                print("   ✅ Contains TP levels")
            if 'SL' in signals:
                print("   ✅ Contains stop loss")
            if 'Confidence' in signals:
                print("   ✅ Contains confidence levels")
        else:
            print("   ❌ Signals generation failed or too short")
    except Exception as e:
        print(f"   ❌ Signals generation error: {e}")
    
    # Test 5: Auto signals eligibility
    print("\n5️⃣ Testing auto signals user eligibility...")
    try:
        eligible_users = db.get_eligible_auto_signal_users()
        print(f"   📊 Eligible users: {len(eligible_users)}")
        if eligible_users:
            print(f"   👥 User IDs: {eligible_users}")
        else:
            print("   ⚠️ No eligible users found (need admin + lifetime premium users)")
    except Exception as e:
        print(f"   ❌ Eligibility check error: {e}")
    
    # Test 6: Market overview with CoinMarketCap
    print("\n6️⃣ Testing market overview...")
    try:
        market_overview = crypto_api.get_market_overview()
        if 'error' not in market_overview:
            total_cap = market_overview.get('total_market_cap', 0)
            btc_dominance = market_overview.get('btc_dominance', 0)
            print(f"   ✅ Market data retrieved")
            print(f"   💰 Total Market Cap: ${total_cap:,.0f}")
            print(f"   🪙 BTC Dominance: {btc_dominance:.1f}%")
        else:
            print(f"   ❌ Market overview error: {market_overview.get('error')}")
    except Exception as e:
        print(f"   ❌ Market overview exception: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Enhanced Futures Test Complete")
    print(f"⏰ Test completed at: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_futures())
