#!/usr/bin/env python3
"""
Test StackMentor Integration
Verify that all components work together correctly
"""

import sys
import os

# Add Bismillah to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

def test_imports():
    """Test that all imports work"""
    print("🧪 Testing imports...")
    
    try:
        from app.stackmentor import (
            STACKMENTOR_CONFIG,
            calculate_stackmentor_levels,
            calculate_qty_splits,
            register_stackmentor_position,
            monitor_stackmentor_positions,
        )
        print("✅ StackMentor imports successful")
    except Exception as e:
        print(f"❌ StackMentor import failed: {e}")
        return False
    
    try:
        from app.autotrade_engine import ENGINE_CONFIG
        print("✅ AutoTrade engine imports successful")
    except Exception as e:
        print(f"❌ AutoTrade engine import failed: {e}")
        return False
    
    try:
        from app.trade_history import save_trade_open
        print("✅ Trade history imports successful")
    except Exception as e:
        print(f"❌ Trade history import failed: {e}")
        return False
    
    return True


def test_config():
    """Test that ENGINE_CONFIG has StackMentor enabled"""
    print("\n🧪 Testing configuration...")
    
    from app.autotrade_engine import ENGINE_CONFIG
    
    if ENGINE_CONFIG.get("use_stackmentor"):
        print("✅ StackMentor is ENABLED in ENGINE_CONFIG")
    else:
        print("⚠️  StackMentor is DISABLED in ENGINE_CONFIG")
    
    print(f"   use_stackmentor: {ENGINE_CONFIG.get('use_stackmentor')}")
    
    from app.stackmentor import STACKMENTOR_CONFIG
    print(f"\n📊 StackMentor Config:")
    print(f"   TP1: {STACKMENTOR_CONFIG['tp1_pct']*100:.0f}% at R:R 1:{STACKMENTOR_CONFIG['tp1_rr']}")
    print(f"   TP2: {STACKMENTOR_CONFIG['tp2_pct']*100:.0f}% at R:R 1:{STACKMENTOR_CONFIG['tp2_rr']}")
    print(f"   TP3: {STACKMENTOR_CONFIG['tp3_pct']*100:.0f}% at R:R 1:{STACKMENTOR_CONFIG['tp3_rr']}")
    print(f"   Breakeven after TP1: {STACKMENTOR_CONFIG['breakeven_after_tp1']}")
    
    return True


def test_calculations():
    """Test StackMentor calculations"""
    print("\n🧪 Testing calculations...")
    
    from app.stackmentor import calculate_stackmentor_levels, calculate_qty_splits
    
    # Test LONG position
    entry = 43000.0
    sl = 42000.0
    side = "LONG"
    
    tp1, tp2, tp3 = calculate_stackmentor_levels(entry, sl, side)
    
    print(f"\n📈 LONG Position Test:")
    print(f"   Entry: ${entry:.2f}")
    print(f"   SL:    ${sl:.2f}")
    print(f"   TP1:   ${tp1:.2f} (R:R 1:2)")
    print(f"   TP2:   ${tp2:.2f} (R:R 1:3)")
    print(f"   TP3:   ${tp3:.2f} (R:R 1:10)")
    
    # Verify R:R ratios
    sl_dist = abs(entry - sl)
    rr1 = abs(tp1 - entry) / sl_dist
    rr2 = abs(tp2 - entry) / sl_dist
    rr3 = abs(tp3 - entry) / sl_dist
    
    print(f"\n   Actual R:R ratios:")
    print(f"   TP1: 1:{rr1:.1f} {'✅' if abs(rr1 - 2.0) < 0.01 else '❌'}")
    print(f"   TP2: 1:{rr2:.1f} {'✅' if abs(rr2 - 3.0) < 0.01 else '❌'}")
    print(f"   TP3: 1:{rr3:.1f} {'✅' if abs(rr3 - 10.0) < 0.01 else '❌'}")
    
    # Test quantity splits
    total_qty = 0.123
    qty_tp1, qty_tp2, qty_tp3 = calculate_qty_splits(total_qty, precision=3)
    
    print(f"\n📦 Quantity Split Test:")
    print(f"   Total:  {total_qty}")
    print(f"   TP1:    {qty_tp1} ({qty_tp1/total_qty*100:.0f}%)")
    print(f"   TP2:    {qty_tp2} ({qty_tp2/total_qty*100:.0f}%)")
    print(f"   TP3:    {qty_tp3} ({qty_tp3/total_qty*100:.0f}%)")
    print(f"   Sum:    {qty_tp1 + qty_tp2 + qty_tp3} {'✅' if abs((qty_tp1 + qty_tp2 + qty_tp3) - total_qty) < 0.001 else '❌'}")
    
    # Test SHORT position
    entry = 43000.0
    sl = 44000.0
    side = "SHORT"
    
    tp1, tp2, tp3 = calculate_stackmentor_levels(entry, sl, side)
    
    print(f"\n📉 SHORT Position Test:")
    print(f"   Entry: ${entry:.2f}")
    print(f"   SL:    ${sl:.2f}")
    print(f"   TP1:   ${tp1:.2f} (R:R 1:2)")
    print(f"   TP2:   ${tp2:.2f} (R:R 1:3)")
    print(f"   TP3:   ${tp3:.2f} (R:R 1:10)")
    
    return True


def test_trade_history_signature():
    """Test that save_trade_open has StackMentor parameters"""
    print("\n🧪 Testing trade_history signature...")
    
    from app.trade_history import save_trade_open
    import inspect
    
    sig = inspect.signature(save_trade_open)
    params = list(sig.parameters.keys())
    
    required_params = ['tp1_price', 'tp2_price', 'tp3_price', 'qty_tp1', 'qty_tp2', 'qty_tp3', 'strategy']
    
    print(f"   Function parameters: {len(params)}")
    
    for param in required_params:
        if param in params:
            print(f"   ✅ {param}")
        else:
            print(f"   ❌ {param} MISSING")
            return False
    
    return True


def main():
    print("=" * 60)
    print("StackMentor Integration Test")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Calculations", test_calculations),
        ("Trade History Signature", test_trade_history_signature),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Ready for deployment!")
    else:
        print("⚠️  SOME TESTS FAILED - Fix issues before deployment")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
