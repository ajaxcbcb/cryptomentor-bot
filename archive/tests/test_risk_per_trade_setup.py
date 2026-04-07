"""
Test Risk Per Trade Setup
Verify database migration and repository functions work correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv("Bismillah/.env")

# Add Bismillah to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Bismillah"))

def test_database_migration():
    """Test that risk_per_trade column exists"""
    print("\n" + "="*60)
    print("TEST 1: Database Migration")
    print("="*60)
    
    try:
        from app.supabase_repo import _client
        
        # Try to query the column
        s = _client()
        result = s.table("autotrade_sessions").select("telegram_id, risk_per_trade").limit(1).execute()
        
        print("✅ Column 'risk_per_trade' exists in autotrade_sessions")
        
        if result.data:
            print(f"   Sample data: {result.data[0]}")
        else:
            print("   No data yet (table empty)")
        
        return True
    except Exception as e:
        print(f"❌ Migration check failed: {e}")
        print("\n⚠️  You need to run the migration first:")
        print("   1. Open Supabase SQL Editor")
        print("   2. Run: db/add_risk_per_trade.sql")
        return False


def test_get_risk_per_trade():
    """Test getting risk percentage"""
    print("\n" + "="*60)
    print("TEST 2: Get Risk Per Trade")
    print("="*60)
    
    try:
        from app.supabase_repo import get_risk_per_trade
        
        # Test with non-existent user (should return default 2.0)
        test_user_id = 999999999
        risk = get_risk_per_trade(test_user_id)
        
        print(f"✅ get_risk_per_trade({test_user_id}) = {risk}%")
        
        if risk == 2.0:
            print("   ✅ Default value correct (2.0%)")
        else:
            print(f"   ⚠️  Expected 2.0%, got {risk}%")
        
        return True
    except Exception as e:
        print(f"❌ get_risk_per_trade failed: {e}")
        return False


def test_set_risk_per_trade():
    """Test setting risk percentage"""
    print("\n" + "="*60)
    print("TEST 3: Set Risk Per Trade")
    print("="*60)
    
    try:
        from app.supabase_repo import set_risk_per_trade, get_risk_per_trade
        
        test_user_id = 999999999
        test_risk = 3.0
        
        # Set risk
        result = set_risk_per_trade(test_user_id, test_risk)
        
        if result['success']:
            print(f"✅ set_risk_per_trade({test_user_id}, {test_risk}%) succeeded")
            
            # Verify it was saved
            saved_risk = get_risk_per_trade(test_user_id)
            if saved_risk == test_risk:
                print(f"   ✅ Verification: risk saved correctly ({saved_risk}%)")
            else:
                print(f"   ⚠️  Verification failed: expected {test_risk}%, got {saved_risk}%")
        else:
            print(f"❌ set_risk_per_trade failed: {result['error']}")
            return False
        
        # Test validation (should reject > 10%)
        invalid_result = set_risk_per_trade(test_user_id, 15.0)
        if not invalid_result['success']:
            print(f"✅ Validation works: rejected 15% (error: {invalid_result['error']})")
        else:
            print("⚠️  Validation failed: accepted invalid risk 15%")
        
        return True
    except Exception as e:
        print(f"❌ set_risk_per_trade test failed: {e}")
        return False


def test_position_sizing():
    """Test position sizing calculations"""
    print("\n" + "="*60)
    print("TEST 4: Position Sizing Module")
    print("="*60)
    
    try:
        from app.position_sizing import calculate_position_size, format_risk_info
        
        # Test case: $100 balance, 2% risk, BTC entry
        balance = 100.0
        risk_pct = 2.0
        entry_price = 50000.0
        sl_price = 49000.0  # 2% SL
        leverage = 10
        
        result = calculate_position_size(
            balance=balance,
            risk_pct=risk_pct,
            entry_price=entry_price,
            sl_price=sl_price,
            leverage=leverage,
            symbol="BTCUSDT"
        )
        
        print(f"Test case:")
        print(f"  Balance: ${balance}")
        print(f"  Risk: {risk_pct}%")
        print(f"  Entry: ${entry_price}")
        print(f"  SL: ${sl_price}")
        print(f"  Leverage: {leverage}x")
        print(f"\nResult:")
        
        if result['valid']:
            print(f"  ✅ Valid calculation")
            print(f"  Position Size: ${result['position_size_usdt']:.2f}")
            print(f"  Margin Required: ${result['margin_required']:.2f}")
            print(f"  Quantity: {result['qty']}")
            print(f"  Risk Amount: ${result['risk_amount']:.2f}")
            print(f"  SL Distance: {result['sl_distance_pct']:.2f}%")
            
            # Verify math
            expected_risk = balance * (risk_pct / 100)
            if abs(result['risk_amount'] - expected_risk) < 0.01:
                print(f"  ✅ Risk amount correct (${expected_risk:.2f})")
            else:
                print(f"  ⚠️  Risk amount mismatch: expected ${expected_risk:.2f}")
        else:
            print(f"  ❌ Invalid: {result['error']}")
            return False
        
        # Test format_risk_info
        print(f"\nFormatted info:")
        info = format_risk_info(balance, risk_pct)
        print(info)
        
        return True
    except Exception as e:
        print(f"❌ Position sizing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("RISK PER TRADE SETUP TESTS")
    print("="*60)
    
    results = []
    
    # Test 1: Database migration
    results.append(("Database Migration", test_database_migration()))
    
    # Only continue if migration passed
    if not results[0][1]:
        print("\n" + "="*60)
        print("TESTS STOPPED - Run migration first!")
        print("="*60)
        return
    
    # Test 2-4: Repository functions
    results.append(("Get Risk Per Trade", test_get_risk_per_trade()))
    results.append(("Set Risk Per Trade", test_set_risk_per_trade()))
    results.append(("Position Sizing", test_position_sizing()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System ready for implementation.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Fix issues before proceeding.")


if __name__ == "__main__":
    main()
