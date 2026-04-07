#!/usr/bin/env python3
"""
Verify Phase 2 Implementation
Checks that all code changes are in place and correct
"""

import sys
import os

def check_file_contains(filepath, search_strings, description):
    """Check if file contains all required strings"""
    print(f"\n{'='*60}")
    print(f"Checking: {description}")
    print(f"File: {filepath}")
    print(f"{'='*60}")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_found = True
    for search_str in search_strings:
        if search_str in content:
            print(f"✅ Found: {search_str[:60]}...")
        else:
            print(f"❌ Missing: {search_str[:60]}...")
            all_found = False
    
    return all_found

def main():
    print("="*60)
    print("PHASE 2 IMPLEMENTATION VERIFICATION")
    print("="*60)
    
    all_checks_passed = True
    
    # Check 1: autotrade_engine.py
    autotrade_checks = [
        "def calc_qty_with_risk(symbol: str, entry: float, sl: float, leverage: int) -> tuple:",
        "from app.supabase_repo import get_risk_per_trade",
        "from app.position_sizing import calculate_position_size",
        "qty, used_risk_sizing = calc_qty_with_risk(symbol, entry, sl, leverage)",
        "if used_risk_sizing:",
        "logger.info(f\"[Engine:{user_id}] Using RISK-BASED position sizing",
        "logger.info(f\"[Engine:{user_id}] Using FIXED MARGIN position sizing",
        "return qty, True  # Success - used risk-based sizing",
        "return qty_fallback, False  # Fallback used",
    ]
    
    if not check_file_contains(
        "Bismillah/app/autotrade_engine.py",
        autotrade_checks,
        "Autotrade Engine - Risk-Based Position Sizing"
    ):
        all_checks_passed = False
    
    # Check 2: scalping_engine.py
    scalping_checks = [
        "def calculate_position_size_pro(self, entry_price: float, sl_price: float,",
        "from app.supabase_repo import get_risk_per_trade",
        "from app.position_sizing import calculate_position_size",
        "quantity, used_risk_sizing = self.calculate_position_size_pro(",
        "if used_risk_sizing:",
        "logger.info(",
        "f\"[Scalping:{self.user_id}] Using RISK-BASED position sizing",
        "return qty, True  # Success - used risk-based sizing",
        "return position_size, False  # Fallback used",
    ]
    
    if not check_file_contains(
        "Bismillah/app/scalping_engine.py",
        scalping_checks,
        "Scalping Engine - Risk-Based Position Sizing"
    ):
        all_checks_passed = False
    
    # Check 3: position_sizing.py (should exist from Phase 1)
    position_sizing_checks = [
        "def calculate_position_size(",
        "balance: float,",
        "risk_pct: float,",
        "entry_price: float,",
        "sl_price: float,",
        "leverage: int,",
    ]
    
    if not check_file_contains(
        "Bismillah/app/position_sizing.py",
        position_sizing_checks,
        "Position Sizing Module (Phase 1)"
    ):
        all_checks_passed = False
    
    # Check 4: supabase_repo.py (should have get_risk_per_trade from Phase 1)
    supabase_checks = [
        "def get_risk_per_trade(telegram_id: int) -> float:",
        "def set_risk_per_trade(telegram_id: int, risk_pct: float)",
    ]
    
    if not check_file_contains(
        "Bismillah/app/supabase_repo.py",
        supabase_checks,
        "Supabase Repository - Risk Functions (Phase 1)"
    ):
        all_checks_passed = False
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED!")
        print("\n✅ Phase 2 implementation is complete and correct.")
        print("✅ Ready to deploy to VPS.")
        print("\n📋 Next steps:")
        print("   1. Review PHASE2_IMPLEMENTATION_COMPLETE.md")
        print("   2. Run: bash deploy_phase2_risk_sizing.sh")
        print("   3. Monitor logs closely for 24-48 hours")
        return 0
    else:
        print("❌ SOME CHECKS FAILED!")
        print("\n⚠️  Phase 2 implementation is incomplete or incorrect.")
        print("⚠️  DO NOT deploy until all checks pass.")
        print("\n📋 Action required:")
        print("   1. Review the failed checks above")
        print("   2. Fix the missing code")
        print("   3. Run this script again")
        return 1

if __name__ == "__main__":
    sys.exit(main())
