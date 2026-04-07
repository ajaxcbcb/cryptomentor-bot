#!/usr/bin/env python3
"""Test StackMentor on VPS"""
import sys
sys.path.insert(0, '/root/cryptomentor-bot')

try:
    from app.stackmentor import (
        calculate_stackmentor_levels,
        calculate_qty_splits,
        STACKMENTOR_CONFIG
    )
    print("✅ StackMentor import successful")
    
    # Test calculation
    tp1, tp2, tp3 = calculate_stackmentor_levels(43000, 42000, "LONG")
    print(f"✅ TP calculation works: TP1={tp1} TP2={tp2} TP3={tp3}")
    
    # Test qty split
    qty1, qty2, qty3 = calculate_qty_splits(0.1, 3)
    print(f"✅ Qty split works: {qty1} / {qty2} / {qty3}")
    
    print("\n✅ All StackMentor tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
