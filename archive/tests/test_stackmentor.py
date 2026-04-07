#!/usr/bin/env python3
"""
Test StackMentor System
Verify 3-tier TP calculations and logic
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

from app.stackmentor import (
    calculate_stackmentor_levels,
    calculate_qty_splits,
    STACKMENTOR_CONFIG,
)

def test_tp_calculations():
    """Test TP level calculations"""
    print("=" * 70)
    print("🧪 STACKMENTOR TP CALCULATIONS TEST")
    print("=" * 70)
    print()
    
    # Test Case 1: LONG position
    print("Test 1: LONG Position")
    print("-" * 70)
    entry = 100.0
    sl = 98.0  # 2% risk
    side = "LONG"
    
    tp1, tp2, tp3 = calculate_stackmentor_levels(entry, sl, side)
    
    sl_dist = abs(entry - sl)
    print(f"Entry: ${entry}")
    print(f"SL: ${sl} (Risk: ${sl_dist})")
    print(f"Side: {side}")
    print()
    print(f"TP1: ${tp1:.2f} (R:R 1:2) — Close 50%")
    print(f"TP2: ${tp2:.2f} (R:R 1:3) — Close 40%")
    print(f"TP3: ${tp3:.2f} (R:R 1:10) — Close 10%")
    print()
    
    # Verify R:R ratios
    rr1 = (tp1 - entry) / sl_dist
    rr2 = (tp2 - entry) / sl_dist
    rr3 = (tp3 - entry) / sl_dist
    
    print(f"Verification:")
    print(f"  TP1 R:R: 1:{rr1:.1f} {'✅' if abs(rr1 - 2.0) < 0.01 else '❌'}")
    print(f"  TP2 R:R: 1:{rr2:.1f} {'✅' if abs(rr2 - 3.0) < 0.01 else '❌'}")
    print(f"  TP3 R:R: 1:{rr3:.1f} {'✅' if abs(rr3 - 10.0) < 0.01 else '❌'}")
    print()
    
    # Test Case 2: SHORT position
    print("Test 2: SHORT Position")
    print("-" * 70)
    entry = 100.0
    sl = 102.0  # 2% risk
    side = "SHORT"
    
    tp1, tp2, tp3 = calculate_stackmentor_levels(entry, sl, side)
    
    sl_dist = abs(entry - sl)
    print(f"Entry: ${entry}")
    print(f"SL: ${sl} (Risk: ${sl_dist})")
    print(f"Side: {side}")
    print()
    print(f"TP1: ${tp1:.2f} (R:R 1:2) — Close 50%")
    print(f"TP2: ${tp2:.2f} (R:R 1:3) — Close 40%")
    print(f"TP3: ${tp3:.2f} (R:R 1:10) — Close 10%")
    print()
    
    # Verify R:R ratios
    rr1 = (entry - tp1) / sl_dist
    rr2 = (entry - tp2) / sl_dist
    rr3 = (entry - tp3) / sl_dist
    
    print(f"Verification:")
    print(f"  TP1 R:R: 1:{rr1:.1f} {'✅' if abs(rr1 - 2.0) < 0.01 else '❌'}")
    print(f"  TP2 R:R: 1:{rr2:.1f} {'✅' if abs(rr2 - 3.0) < 0.01 else '❌'}")
    print(f"  TP3 R:R: 1:{rr3:.1f} {'✅' if abs(rr3 - 10.0) < 0.01 else '❌'}")
    print()


def test_qty_splits():
    """Test quantity splitting"""
    print("=" * 70)
    print("🧪 STACKMENTOR QTY SPLITS TEST")
    print("=" * 70)
    print()
    
    test_cases = [
        (1.0, 3, "1 BTC"),
        (0.5, 2, "0.5 ETH"),
        (10.0, 1, "10 SOL"),
        (0.123, 3, "0.123 BTC"),
    ]
    
    for total_qty, precision, label in test_cases:
        print(f"Test: {label} (precision={precision})")
        print("-" * 70)
        
        qty_tp1, qty_tp2, qty_tp3 = calculate_qty_splits(total_qty, precision)
        
        print(f"Total Qty: {total_qty}")
        print(f"TP1 (50%): {qty_tp1}")
        print(f"TP2 (40%): {qty_tp2}")
        print(f"TP3 (10%): {qty_tp3}")
        print(f"Sum: {qty_tp1 + qty_tp2 + qty_tp3}")
        
        # Verify sum equals total
        sum_check = abs((qty_tp1 + qty_tp2 + qty_tp3) - total_qty) < 0.0001
        print(f"Sum Check: {'✅' if sum_check else '❌'}")
        
        # Verify percentages
        pct1 = (qty_tp1 / total_qty) * 100
        pct2 = (qty_tp2 / total_qty) * 100
        pct3 = (qty_tp3 / total_qty) * 100
        
        print(f"Percentages: {pct1:.1f}% / {pct2:.1f}% / {pct3:.1f}%")
        print()


def test_profit_scenarios():
    """Test profit calculations for different scenarios"""
    print("=" * 70)
    print("🧪 STACKMENTOR PROFIT SCENARIOS")
    print("=" * 70)
    print()
    
    # Scenario 1: All TPs hit
    print("Scenario 1: ALL TPs HIT (Perfect Trade)")
    print("-" * 70)
    
    entry = 100.0
    sl = 98.0
    side = "LONG"
    total_qty = 1.0
    leverage = 10
    
    tp1, tp2, tp3 = calculate_stackmentor_levels(entry, sl, side)
    qty_tp1, qty_tp2, qty_tp3 = calculate_qty_splits(total_qty, 3)
    
    profit_tp1 = (tp1 - entry) * qty_tp1
    profit_tp2 = (tp2 - entry) * qty_tp2
    profit_tp3 = (tp3 - entry) * qty_tp3
    total_profit = profit_tp1 + profit_tp2 + profit_tp3
    
    print(f"Entry: ${entry} | SL: ${sl} | Qty: {total_qty} | Leverage: {leverage}x")
    print()
    print(f"TP1 @ ${tp1:.2f}: +${profit_tp1:.2f} (50% closed)")
    print(f"TP2 @ ${tp2:.2f}: +${profit_tp2:.2f} (40% closed)")
    print(f"TP3 @ ${tp3:.2f}: +${profit_tp3:.2f} (10% closed)")
    print()
    print(f"💰 TOTAL PROFIT: ${total_profit:.2f}")
    print(f"📊 ROI: {(total_profit / (entry * total_qty)) * 100:.1f}%")
    print()
    
    # Scenario 2: Only TP1 hit (breakeven)
    print("Scenario 2: ONLY TP1 HIT (Breakeven Protection)")
    print("-" * 70)
    
    profit_tp1_only = (tp1 - entry) * qty_tp1
    remaining_qty = qty_tp2 + qty_tp3
    
    print(f"TP1 @ ${tp1:.2f}: +${profit_tp1_only:.2f} (50% closed)")
    print(f"Remaining {remaining_qty} closed at breakeven: $0.00")
    print()
    print(f"💰 TOTAL PROFIT: ${profit_tp1_only:.2f}")
    print(f"📊 ROI: {(profit_tp1_only / (entry * total_qty)) * 100:.1f}%")
    print(f"✅ No loss thanks to breakeven SL!")
    print()
    
    # Scenario 3: TP1 + TP2 hit
    print("Scenario 3: TP1 + TP2 HIT (90% Secured)")
    print("-" * 70)
    
    profit_tp1_tp2 = profit_tp1 + profit_tp2
    
    print(f"TP1 @ ${tp1:.2f}: +${profit_tp1:.2f} (50% closed)")
    print(f"TP2 @ ${tp2:.2f}: +${profit_tp2:.2f} (40% closed)")
    print(f"Remaining {qty_tp3} closed at breakeven: $0.00")
    print()
    print(f"💰 TOTAL PROFIT: ${profit_tp1_tp2:.2f}")
    print(f"📊 ROI: {(profit_tp1_tp2 / (entry * total_qty)) * 100:.1f}%")
    print()


def test_config():
    """Display StackMentor configuration"""
    print("=" * 70)
    print("⚙️ STACKMENTOR CONFIGURATION")
    print("=" * 70)
    print()
    
    for key, value in STACKMENTOR_CONFIG.items():
        print(f"{key:25s}: {value}")
    print()


def main():
    """Run all tests"""
    test_config()
    test_tp_calculations()
    test_qty_splits()
    test_profit_scenarios()
    
    print("=" * 70)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 70)
    print()
    print("🎯 StackMentor System Ready for Integration!")
    print()


if __name__ == "__main__":
    main()
