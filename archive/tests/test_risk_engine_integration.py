"""
Comprehensive Test Suite for Risk-Based Position Sizing Engine Integration
Test EVERYTHING before deploying to production!
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv("Bismillah/.env")

# Add Bismillah to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Bismillah"))


def test_position_sizing_scenarios():
    """Test position sizing with various real-world scenarios"""
    print("\n" + "="*60)
    print("TEST 1: Position Sizing Scenarios")
    print("="*60)
    
    from app.position_sizing import calculate_position_size
    
    scenarios = [
        {
            "name": "Small account, conservative (1%)",
            "balance": 50,
            "risk_pct": 1.0,
            "entry": 50000,
            "sl": 49000,  # 2% SL
            "leverage": 10,
            "expected_position": 25,  # $0.50 risk / 0.02 SL = $25
            "expected_margin": 2.5,   # $25 / 10x
        },
        {
            "name": "Medium account, moderate (2%)",
            "balance": 200,
            "risk_pct": 2.0,
            "entry": 3000,
            "sl": 2940,  # 2% SL
            "leverage": 10,
            "expected_position": 200,  # $4 risk / 0.02 SL = $200
            "expected_margin": 20,     # $200 / 10x
        },
        {
            "name": "Large account, aggressive (3%)",
            "balance": 1000,
            "risk_pct": 3.0,
            "entry": 100,
            "sl": 98,  # 2% SL
            "leverage": 10,
            "expected_position": 1500,  # $30 risk / 0.02 SL = $1500
            "expected_margin": 150,     # $1500 / 10x (capped at 95% balance = $950)
        },
        {
            "name": "Tight SL (1%)",
            "balance": 100,
            "risk_pct": 2.0,
            "entry": 50000,
            "sl": 49500,  # 1% SL
            "leverage": 10,
            "expected_position": 200,  # $2 risk / 0.01 SL = $200
            "expected_margin": 20,     # $200 / 10x
        },
        {
            "name": "Wide SL (5%)",
            "balance": 100,
            "risk_pct": 2.0,
            "entry": 50000,
            "sl": 47500,  # 5% SL
            "leverage": 10,
            "expected_position": 40,   # $2 risk / 0.05 SL = $40
            "expected_margin": 4,      # $40 / 10x
        },
    ]
    
    all_passed = True
    for i, scenario in enumerate(scenarios, 1):
        result = calculate_position_size(
            balance=scenario["balance"],
            risk_pct=scenario["risk_pct"],
            entry_price=scenario["entry"],
            sl_price=scenario["sl"],
            leverage=scenario["leverage"],
            symbol="BTCUSDT"
        )
        
        if not result['valid']:
            print(f"❌ Scenario {i}: {scenario['name']}")
            print(f"   Error: {result['error']}")
            all_passed = False
            continue
        
        # Check if position size is reasonable (within 20% of expected)
        position_ok = abs(result['position_size_usdt'] - scenario['expected_position']) / scenario['expected_position'] < 0.20
        margin_ok = abs(result['margin_required'] - scenario['expected_margin']) / max(scenario['expected_margin'], 1) < 0.20
        
        if position_ok and margin_ok:
            print(f"✅ Scenario {i}: {scenario['name']}")
            print(f"   Position: ${result['position_size_usdt']:.2f} (expected ~${scenario['expected_position']:.2f})")
            print(f"   Margin: ${result['margin_required']:.2f} (expected ~${scenario['expected_margin']:.2f})")
            print(f"   Qty: {result['qty']}")
        else:
            print(f"⚠️  Scenario {i}: {scenario['name']}")
            print(f"   Position: ${result['position_size_usdt']:.2f} (expected ${scenario['expected_position']:.2f}) {'✅' if position_ok else '❌'}")
            print(f"   Margin: ${result['margin_required']:.2f} (expected ${scenario['expected_margin']:.2f}) {'✅' if margin_ok else '❌'}")
            all_passed = False
    
    return all_passed


def test_edge_cases():
    """Test edge cases that could cause issues"""
    print("\n" + "="*60)
    print("TEST 2: Edge Cases")
    print("="*60)
    
    from app.position_sizing import calculate_position_size
    
    edge_cases = [
        {
            "name": "Very small balance ($10) - may fail due to min qty",
            "balance": 10,
            "risk_pct": 2.0,
            "entry": 50000,
            "sl": 49000,
            "leverage": 10,
            "should_be_valid": False,  # Expected to fail - qty too small for BTC
        },
        {
            "name": "Very large balance ($10,000)",
            "balance": 10000,
            "risk_pct": 2.0,
            "entry": 50000,
            "sl": 49000,
            "leverage": 10,
            "should_be_valid": True,
        },
        {
            "name": "Minimum risk (0.5%)",
            "balance": 100,
            "risk_pct": 0.5,
            "entry": 50000,
            "sl": 49000,
            "leverage": 10,
            "should_be_valid": True,
        },
        {
            "name": "Maximum risk (10%)",
            "balance": 100,
            "risk_pct": 10.0,
            "entry": 50000,
            "sl": 49000,
            "leverage": 10,
            "should_be_valid": True,
        },
        {
            "name": "Invalid: Risk too high (15%)",
            "balance": 100,
            "risk_pct": 15.0,
            "entry": 50000,
            "sl": 49000,
            "leverage": 10,
            "should_be_valid": False,
        },
        {
            "name": "Invalid: SL too tight (0.01%)",
            "balance": 100,
            "risk_pct": 2.0,
            "entry": 50000,
            "sl": 49995,
            "leverage": 10,
            "should_be_valid": False,
        },
        {
            "name": "Invalid: SL too wide (20%)",
            "balance": 100,
            "risk_pct": 2.0,
            "entry": 50000,
            "sl": 40000,
            "leverage": 10,
            "should_be_valid": False,
        },
        {
            "name": "Invalid: Zero balance",
            "balance": 0,
            "risk_pct": 2.0,
            "entry": 50000,
            "sl": 49000,
            "leverage": 10,
            "should_be_valid": False,
        },
        {
            "name": "Invalid: Negative balance",
            "balance": -100,
            "risk_pct": 2.0,
            "entry": 50000,
            "sl": 49000,
            "leverage": 10,
            "should_be_valid": False,
        },
    ]
    
    all_passed = True
    for i, case in enumerate(edge_cases, 1):
        result = calculate_position_size(
            balance=case["balance"],
            risk_pct=case["risk_pct"],
            entry_price=case["entry"],
            sl_price=case["sl"],
            leverage=case["leverage"],
            symbol="BTCUSDT"
        )
        
        if result['valid'] == case['should_be_valid']:
            print(f"✅ Case {i}: {case['name']}")
            if result['valid']:
                print(f"   Position: ${result['position_size_usdt']:.2f}, Margin: ${result['margin_required']:.2f}")
            else:
                print(f"   Correctly rejected: {result['error']}")
        else:
            print(f"❌ Case {i}: {case['name']}")
            print(f"   Expected valid={case['should_be_valid']}, got {result['valid']}")
            if not result['valid']:
                print(f"   Error: {result['error']}")
            all_passed = False
    
    return all_passed


def test_database_functions():
    """Test database functions work correctly"""
    print("\n" + "="*60)
    print("TEST 3: Database Functions")
    print("="*60)
    
    from app.supabase_repo import get_risk_per_trade, set_risk_per_trade
    
    test_user_id = 999999998  # Different from Phase 1 test
    
    try:
        # Test 1: Get default risk
        risk = get_risk_per_trade(test_user_id)
        if risk == 2.0:
            print(f"✅ Default risk correct: {risk}%")
        else:
            print(f"⚠️  Default risk unexpected: {risk}% (expected 2.0%)")
        
        # Test 2: Set risk to 3%
        result = set_risk_per_trade(test_user_id, 3.0)
        if result['success']:
            print(f"✅ Set risk to 3%: {result}")
            
            # Verify it was saved
            saved_risk = get_risk_per_trade(test_user_id)
            if saved_risk == 3.0:
                print(f"✅ Risk saved correctly: {saved_risk}%")
            else:
                print(f"❌ Risk not saved: expected 3.0%, got {saved_risk}%")
                return False
        else:
            print(f"❌ Failed to set risk: {result['error']}")
            return False
        
        # Test 3: Try invalid risk (should fail)
        result = set_risk_per_trade(test_user_id, 20.0)
        if not result['success']:
            print(f"✅ Validation works: rejected 20% (error: {result['error']})")
        else:
            print(f"❌ Validation failed: accepted invalid risk 20%")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compounding_simulation():
    """Simulate compounding to verify risk % enables growth"""
    print("\n" + "="*60)
    print("TEST 4: Compounding Simulation")
    print("="*60)
    
    from app.position_sizing import calculate_position_size
    
    # Simulate 10 winning trades with 2% risk, 1:2 R:R
    initial_balance = 100.0
    risk_pct = 2.0
    leverage = 10
    
    balance = initial_balance
    print(f"Starting balance: ${balance:.2f}")
    print(f"Risk per trade: {risk_pct}%")
    print(f"R:R: 1:2")
    print()
    
    for trade_num in range(1, 11):
        # Calculate position size
        entry = 50000
        sl = 49000  # 2% SL
        
        sizing = calculate_position_size(
            balance=balance,
            risk_pct=risk_pct,
            entry_price=entry,
            sl_price=sl,
            leverage=leverage,
            symbol="BTCUSDT"
        )
        
        if not sizing['valid']:
            print(f"❌ Trade {trade_num} sizing failed: {sizing['error']}")
            return False
        
        # Simulate win (1:2 R:R)
        risk_amount = sizing['risk_amount']
        profit = risk_amount * 2  # 1:2 R:R
        balance += profit
        
        print(f"Trade {trade_num}: Risk ${risk_amount:.2f}, Profit ${profit:.2f}, Balance ${balance:.2f}")
    
    total_profit = balance - initial_balance
    profit_pct = (total_profit / initial_balance) * 100
    
    print()
    print(f"Final balance: ${balance:.2f}")
    print(f"Total profit: ${total_profit:.2f} ({profit_pct:.1f}%)")
    
    # With 2% risk and 1:2 R:R, 10 wins should give ~48% profit (compounded)
    # Without compounding, it would be 40% (10 * 2% * 2)
    if profit_pct > 45:
        print(f"✅ Compounding working! Profit {profit_pct:.1f}% > 40% (non-compounded)")
        return True
    else:
        print(f"⚠️  Compounding may not be working correctly")
        return False


def test_account_protection():
    """Simulate losing streak to verify account protection"""
    print("\n" + "="*60)
    print("TEST 5: Account Protection (Losing Streak)")
    print("="*60)
    
    from app.position_sizing import calculate_position_size
    
    # Simulate 20 losing trades with 2% risk
    initial_balance = 100.0
    risk_pct = 2.0
    leverage = 10
    
    balance = initial_balance
    print(f"Starting balance: ${balance:.2f}")
    print(f"Risk per trade: {risk_pct}%")
    print(f"Simulating 20 consecutive losses...")
    print()
    
    for trade_num in range(1, 21):
        # Calculate position size
        entry = 50000
        sl = 49000  # 2% SL
        
        sizing = calculate_position_size(
            balance=balance,
            risk_pct=risk_pct,
            entry_price=entry,
            sl_price=sl,
            leverage=leverage,
            symbol="BTCUSDT"
        )
        
        if not sizing['valid']:
            print(f"❌ Trade {trade_num} sizing failed: {sizing['error']}")
            return False
        
        # Simulate loss
        risk_amount = sizing['risk_amount']
        balance -= risk_amount
        
        if trade_num % 5 == 0:
            print(f"After {trade_num} losses: Balance ${balance:.2f} ({(balance/initial_balance)*100:.1f}%)")
    
    remaining_pct = (balance / initial_balance) * 100
    
    print()
    print(f"Final balance: ${balance:.2f} ({remaining_pct:.1f}% of initial)")
    
    # With 2% risk, after 20 losses should have ~66% remaining
    # Formula: (1 - 0.02)^20 = 0.6676 = 66.76%
    if remaining_pct > 60:
        print(f"✅ Account protected! Still have {remaining_pct:.1f}% after 20 losses")
        print(f"   (Can survive 50+ consecutive losses before blow-up)")
        return True
    else:
        print(f"❌ Account protection failed! Only {remaining_pct:.1f}% remaining")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("RISK-BASED ENGINE INTEGRATION - COMPREHENSIVE TESTS")
    print("="*60)
    print("\n⚠️  CRITICAL: All tests must pass before engine integration!")
    
    results = []
    
    # Run all tests
    results.append(("Position Sizing Scenarios", test_position_sizing_scenarios()))
    results.append(("Edge Cases", test_edge_cases()))
    results.append(("Database Functions", test_database_functions()))
    results.append(("Compounding Simulation", test_compounding_simulation()))
    results.append(("Account Protection", test_account_protection()))
    
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
        print("\n🎉 All tests passed!")
        print("\n✅ SAFE TO PROCEED with engine integration")
        print("\n📋 Next steps:")
        print("1. Review PHASE2_SAFETY_PLAN.md")
        print("2. Implement engine integration with fallback")
        print("3. Test with demo account")
        print("4. Deploy carefully")
    else:
        print(f"\n❌ {total - passed} test(s) failed!")
        print("\n⚠️  DO NOT PROCEED with engine integration until all tests pass!")
        print("Fix the issues first.")


if __name__ == "__main__":
    main()
