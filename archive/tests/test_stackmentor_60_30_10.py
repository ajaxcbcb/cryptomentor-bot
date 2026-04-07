"""
Test StackMentor 60/30/10 Configuration
Verify quantity splits and TP levels are calculated correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

from app.stackmentor import (
    STACKMENTOR_CONFIG,
    calculate_stackmentor_levels,
    calculate_qty_splits
)


def test_configuration():
    """Test that configuration is correct"""
    print("=" * 60)
    print("TEST 1: Configuration Values")
    print("=" * 60)
    
    assert STACKMENTOR_CONFIG["tp1_pct"] == 0.60, "TP1 should be 60%"
    assert STACKMENTOR_CONFIG["tp2_pct"] == 0.30, "TP2 should be 30%"
    assert STACKMENTOR_CONFIG["tp3_pct"] == 0.10, "TP3 should be 10%"
    assert STACKMENTOR_CONFIG["tp1_rr"] == 2.0, "TP1 R:R should be 1:2"
    assert STACKMENTOR_CONFIG["tp2_rr"] == 3.0, "TP2 R:R should be 1:3"
    assert STACKMENTOR_CONFIG["tp3_rr"] == 5.0, "TP3 R:R should be 1:5"
    
    print("✅ Configuration correct:")
    print(f"   TP1: {STACKMENTOR_CONFIG['tp1_pct']*100:.0f}% @ R:R 1:{STACKMENTOR_CONFIG['tp1_rr']:.0f}")
    print(f"   TP2: {STACKMENTOR_CONFIG['tp2_pct']*100:.0f}% @ R:R 1:{STACKMENTOR_CONFIG['tp2_rr']:.0f}")
    print(f"   TP3: {STACKMENTOR_CONFIG['tp3_pct']*100:.0f}% @ R:R 1:{STACKMENTOR_CONFIG['tp3_rr']:.0f}")
    print()


def test_tp_levels_long():
    """Test TP level calculation for LONG position"""
    print("=" * 60)
    print("TEST 2: TP Levels Calculation (LONG)")
    print("=" * 60)
    
    entry = 50000.0
    sl = 49000.0
    side = "LONG"
    
    tp1, tp2, tp3 = calculate_stackmentor_levels(entry, sl, side)
    
    # Expected values
    risk = entry - sl  # 1000
    expected_tp1 = entry + (risk * 2.0)  # 52000
    expected_tp2 = entry + (risk * 3.0)  # 53000
    expected_tp3 = entry + (risk * 5.0)  # 55000
    
    print(f"Entry: ${entry:,.2f}")
    print(f"SL:    ${sl:,.2f}")
    print(f"Risk:  ${risk:,.2f}")
    print()
    print(f"TP1: ${tp1:,.2f} (expected ${expected_tp1:,.2f}) - R:R 1:2")
    print(f"TP2: ${tp2:,.2f} (expected ${expected_tp2:,.2f}) - R:R 1:3")
    print(f"TP3: ${tp3:,.2f} (expected ${expected_tp3:,.2f}) - R:R 1:5")
    
    assert tp1 == expected_tp1, f"TP1 mismatch: {tp1} != {expected_tp1}"
    assert tp2 == expected_tp2, f"TP2 mismatch: {tp2} != {expected_tp2}"
    assert tp3 == expected_tp3, f"TP3 mismatch: {tp3} != {expected_tp3}"
    
    print("✅ TP levels correct for LONG")
    print()


def test_tp_levels_short():
    """Test TP level calculation for SHORT position"""
    print("=" * 60)
    print("TEST 3: TP Levels Calculation (SHORT)")
    print("=" * 60)
    
    entry = 50000.0
    sl = 51000.0
    side = "SHORT"
    
    tp1, tp2, tp3 = calculate_stackmentor_levels(entry, sl, side)
    
    # Expected values
    risk = sl - entry  # 1000
    expected_tp1 = entry - (risk * 2.0)  # 48000
    expected_tp2 = entry - (risk * 3.0)  # 47000
    expected_tp3 = entry - (risk * 5.0)  # 45000
    
    print(f"Entry: ${entry:,.2f}")
    print(f"SL:    ${sl:,.2f}")
    print(f"Risk:  ${risk:,.2f}")
    print()
    print(f"TP1: ${tp1:,.2f} (expected ${expected_tp1:,.2f}) - R:R 1:2")
    print(f"TP2: ${tp2:,.2f} (expected ${expected_tp2:,.2f}) - R:R 1:3")
    print(f"TP3: ${tp3:,.2f} (expected ${expected_tp3:,.2f}) - R:R 1:5")
    
    assert tp1 == expected_tp1, f"TP1 mismatch: {tp1} != {expected_tp1}"
    assert tp2 == expected_tp2, f"TP2 mismatch: {tp2} != {expected_tp2}"
    assert tp3 == expected_tp3, f"TP3 mismatch: {tp3} != {expected_tp3}"
    
    print("✅ TP levels correct for SHORT")
    print()


def test_qty_splits():
    """Test quantity splitting"""
    print("=" * 60)
    print("TEST 4: Quantity Splits")
    print("=" * 60)
    
    test_cases = [
        (1.0, 3, "Standard BTC position"),
        (0.1, 3, "Small BTC position"),
        (10.0, 2, "ETH position"),
        (100.0, 1, "SOL position"),
        (1000.0, 0, "DOGE position"),
    ]
    
    for total_qty, precision, description in test_cases:
        qty_tp1, qty_tp2, qty_tp3 = calculate_qty_splits(total_qty, precision)
        
        print(f"\n{description}:")
        print(f"  Total:  {total_qty}")
        print(f"  TP1 (60%): {qty_tp1}")
        print(f"  TP2 (30%): {qty_tp2}")
        print(f"  TP3 (10%): {qty_tp3}")
        print(f"  Sum:    {qty_tp1 + qty_tp2 + qty_tp3}")
        
        # Verify sum equals total (with floating point tolerance)
        sum_qty = qty_tp1 + qty_tp2 + qty_tp3
        assert abs(sum_qty - total_qty) < 0.0001, \
            f"Sum mismatch: {sum_qty} != {total_qty}"
        
        # Verify percentages are approximately correct
        pct_tp1 = qty_tp1 / total_qty
        pct_tp2 = qty_tp2 / total_qty
        pct_tp3 = qty_tp3 / total_qty
        
        assert 0.55 <= pct_tp1 <= 0.65, f"TP1 % out of range: {pct_tp1*100:.1f}%"
        assert 0.25 <= pct_tp2 <= 0.35, f"TP2 % out of range: {pct_tp2*100:.1f}%"
        assert 0.05 <= pct_tp3 <= 0.15, f"TP3 % out of range: {pct_tp3*100:.1f}%"
        
        print(f"  Actual: {pct_tp1*100:.1f}% / {pct_tp2*100:.1f}% / {pct_tp3*100:.1f}%")
    
    print("\n✅ All quantity splits correct")
    print()


def test_profit_calculation():
    """Test profit calculation example"""
    print("=" * 60)
    print("TEST 5: Profit Calculation Example")
    print("=" * 60)
    
    # Example trade
    entry = 50000.0
    sl = 49000.0
    side = "LONG"
    total_qty = 0.1  # 0.1 BTC
    leverage = 10
    
    tp1, tp2, tp3 = calculate_stackmentor_levels(entry, sl, side)
    qty_tp1, qty_tp2, qty_tp3 = calculate_qty_splits(total_qty, 3)
    
    # Calculate profits
    profit_tp1 = (tp1 - entry) * qty_tp1
    profit_tp2 = (tp2 - entry) * qty_tp2
    profit_tp3 = (tp3 - entry) * qty_tp3
    total_profit = profit_tp1 + profit_tp2 + profit_tp3
    
    # Calculate loss if SL hit
    max_loss = (entry - sl) * total_qty
    
    print(f"Position: {total_qty} BTC @ ${entry:,.0f}")
    print(f"Leverage: {leverage}x")
    print(f"SL: ${sl:,.0f}")
    print()
    print("If all TPs hit:")
    print(f"  TP1 ({qty_tp1} BTC @ ${tp1:,.0f}): +${profit_tp1:,.2f}")
    print(f"  TP2 ({qty_tp2} BTC @ ${tp2:,.0f}): +${profit_tp2:,.2f}")
    print(f"  TP3 ({qty_tp3} BTC @ ${tp3:,.0f}): +${profit_tp3:,.2f}")
    print(f"  TOTAL PROFIT: +${total_profit:,.2f}")
    print()
    print(f"If SL hit before TP1: -${max_loss:,.2f}")
    print()
    print(f"Risk:Reward Ratio: 1:{total_profit/max_loss:.2f}")
    
    # Verify R:R is reasonable
    rr_ratio = total_profit / max_loss
    assert rr_ratio >= 2.5, f"R:R too low: {rr_ratio:.2f}"
    
    print("✅ Profit calculation correct")
    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("STACKMENTOR 60/30/10 CONFIGURATION TEST")
    print("=" * 60)
    print()
    
    try:
        test_configuration()
        test_tp_levels_long()
        test_tp_levels_short()
        test_qty_splits()
        test_profit_calculation()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("StackMentor 60/30/10 configuration is correct!")
        print("Ready for deployment.")
        print()
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        return 1
    
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ UNEXPECTED ERROR")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
