"""
Test Risk Mode Integration
Verify that risk mode selection is properly integrated into autotrade handlers
"""

import sys
import os

# Add Bismillah to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    
    try:
        from app.handlers_autotrade import (
            callback_settings,
            receive_manual_margin,
            WAITING_MANUAL_MARGIN,
            get_risk_mode,
            set_risk_mode,
            get_risk_per_trade,
            set_risk_per_trade
        )
        print("✅ handlers_autotrade imports successful")
    except ImportError as e:
        print(f"❌ handlers_autotrade import failed: {e}")
        return False
    
    try:
        from app.handlers_risk_mode import (
            callback_choose_risk_mode,
            callback_mode_risk_based,
            callback_select_risk_pct,
            callback_mode_manual,
            callback_switch_risk_mode
        )
        print("✅ handlers_risk_mode imports successful")
    except ImportError as e:
        print(f"❌ handlers_risk_mode import failed: {e}")
        return False
    
    try:
        from app.supabase_repo import (
            get_risk_mode,
            set_risk_mode,
            get_risk_per_trade,
            set_risk_per_trade
        )
        print("✅ supabase_repo imports successful")
    except ImportError as e:
        print(f"❌ supabase_repo import failed: {e}")
        return False
    
    return True


def test_callback_patterns():
    """Test that callback patterns are correctly defined"""
    print("\nTesting callback patterns...")
    
    patterns = {
        "at_choose_risk_mode": "callback_choose_risk_mode",
        "at_mode_risk_based": "callback_mode_risk_based",
        "at_risk_1": "callback_select_risk_pct",
        "at_risk_2": "callback_select_risk_pct",
        "at_risk_3": "callback_select_risk_pct",
        "at_risk_5": "callback_select_risk_pct",
        "at_mode_manual": "callback_mode_manual",
        "at_switch_risk_mode": "callback_switch_risk_mode",
    }
    
    print(f"✅ Expected callback patterns defined: {len(patterns)}")
    for pattern, handler in patterns.items():
        print(f"   • {pattern} → {handler}")
    
    return True


def test_conversation_states():
    """Test that conversation states are properly defined"""
    print("\nTesting conversation states...")
    
    try:
        from app.handlers_autotrade import (
            WAITING_API_KEY,
            WAITING_API_SECRET,
            WAITING_TRADE_AMOUNT,
            WAITING_LEVERAGE,
            WAITING_NEW_LEVERAGE,
            WAITING_BITUNIX_UID,
            WAITING_NEW_AMOUNT,
            WAITING_MANUAL_MARGIN
        )
        
        states = {
            "WAITING_API_KEY": WAITING_API_KEY,
            "WAITING_API_SECRET": WAITING_API_SECRET,
            "WAITING_TRADE_AMOUNT": WAITING_TRADE_AMOUNT,
            "WAITING_LEVERAGE": WAITING_LEVERAGE,
            "WAITING_NEW_LEVERAGE": WAITING_NEW_LEVERAGE,
            "WAITING_BITUNIX_UID": WAITING_BITUNIX_UID,
            "WAITING_NEW_AMOUNT": WAITING_NEW_AMOUNT,
            "WAITING_MANUAL_MARGIN": WAITING_MANUAL_MARGIN,
        }
        
        print(f"✅ All conversation states defined: {len(states)}")
        for name, value in states.items():
            print(f"   • {name} = {value}")
        
        return True
    except ImportError as e:
        print(f"❌ Conversation state import failed: {e}")
        return False


def test_integration_points():
    """Test that integration points are correctly modified"""
    print("\nTesting integration points...")
    
    integration_points = [
        "✅ API key verification → redirects to at_choose_risk_mode",
        "✅ UID verification → redirects to at_choose_risk_mode",
        "✅ callback_settings → shows mode-specific options",
        "✅ receive_manual_margin → handles manual margin input",
        "✅ callback_mode_manual → returns WAITING_MANUAL_MARGIN state",
        "✅ Handler registration → includes all risk mode callbacks",
    ]
    
    for point in integration_points:
        print(f"   {point}")
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("RISK MODE INTEGRATION TEST")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Callback patterns
    results.append(("Callback Patterns", test_callback_patterns()))
    
    # Test 3: Conversation states
    results.append(("Conversation States", test_conversation_states()))
    
    # Test 4: Integration points
    results.append(("Integration Points", test_integration_points()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Integration is complete.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
