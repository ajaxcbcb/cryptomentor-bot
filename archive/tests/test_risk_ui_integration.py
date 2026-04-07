"""
Test Risk Per Trade UI Integration
Verify that all UI callbacks are properly registered and work.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv("Bismillah/.env")

# Add Bismillah to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Bismillah"))

def test_imports():
    """Test that all modules import correctly"""
    print("\n" + "="*60)
    print("TEST 1: Module Imports")
    print("="*60)
    
    try:
        # Test supabase_repo imports
        from app.supabase_repo import (
            get_risk_per_trade,
            set_risk_per_trade,
            get_user_balance_from_exchange
        )
        print("✅ supabase_repo functions imported")
        
        # Test position_sizing imports
        from app.position_sizing import (
            calculate_position_size,
            format_risk_info,
            get_recommended_risk
        )
        print("✅ position_sizing functions imported")
        
        # Test handlers imports
        from app.handlers_autotrade import (
            callback_risk_settings,
            callback_set_risk,
            callback_risk_education,
            callback_risk_simulator
        )
        print("✅ handlers_autotrade callbacks imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_callback_patterns():
    """Test that callback patterns are correct"""
    print("\n" + "="*60)
    print("TEST 2: Callback Pattern Validation")
    print("="*60)
    
    try:
        import re
        
        # Read handlers file
        with open("Bismillah/app/handlers_autotrade.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for risk management handlers registration
        patterns_to_check = [
            (r'CallbackQueryHandler\(callback_risk_settings.*pattern=".*at_risk_settings', "at_risk_settings"),
            (r'CallbackQueryHandler\(callback_set_risk.*pattern=".*at_set_risk', "at_set_risk"),
            (r'CallbackQueryHandler\(callback_risk_education.*pattern=".*at_risk_edu', "at_risk_edu"),
            (r'CallbackQueryHandler\(callback_risk_simulator.*pattern=".*at_risk_sim', "at_risk_sim"),
        ]
        
        all_found = True
        for pattern, name in patterns_to_check:
            if re.search(pattern, content):
                print(f"✅ Handler registered: {name}")
            else:
                print(f"❌ Handler NOT registered: {name}")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"❌ Pattern check failed: {e}")
        return False


def test_callback_functions_exist():
    """Test that all callback functions are defined"""
    print("\n" + "="*60)
    print("TEST 3: Callback Functions Existence")
    print("="*60)
    
    try:
        from app import handlers_autotrade
        
        functions_to_check = [
            "callback_risk_settings",
            "callback_set_risk",
            "callback_risk_education",
            "callback_risk_simulator",
        ]
        
        all_exist = True
        for func_name in functions_to_check:
            if hasattr(handlers_autotrade, func_name):
                func = getattr(handlers_autotrade, func_name)
                if callable(func):
                    print(f"✅ Function exists and callable: {func_name}")
                else:
                    print(f"❌ Function exists but not callable: {func_name}")
                    all_exist = False
            else:
                print(f"❌ Function NOT found: {func_name}")
                all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"❌ Function check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_settings_menu_updated():
    """Test that settings menu includes risk management button"""
    print("\n" + "="*60)
    print("TEST 4: Settings Menu Update")
    print("="*60)
    
    try:
        # Read handlers file
        with open("Bismillah/app/handlers_autotrade.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Find callback_settings function
        import re
        settings_func = re.search(
            r'async def callback_settings\(.*?\):(.*?)(?=async def|\Z)',
            content,
            re.DOTALL
        )
        
        if not settings_func:
            print("❌ callback_settings function not found")
            return False
        
        settings_code = settings_func.group(1)
        
        # Check for risk management elements
        checks = [
            ("get_risk_per_trade", "Gets risk percentage from database"),
            ("Risk per trade:", "Displays risk in settings"),
            ("at_risk_settings", "Risk Management button callback"),
        ]
        
        all_found = True
        for check_str, description in checks:
            if check_str in settings_code:
                print(f"✅ {description}")
            else:
                print(f"❌ Missing: {description}")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"❌ Settings menu check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_sizing_integration():
    """Test position sizing with real-world scenarios"""
    print("\n" + "="*60)
    print("TEST 5: Position Sizing Integration")
    print("="*60)
    
    try:
        from app.position_sizing import calculate_position_size
        
        test_cases = [
            {
                "name": "Small account, conservative",
                "balance": 50,
                "risk_pct": 1.0,
                "entry": 50000,
                "sl": 49000,
                "leverage": 10,
                "expected_valid": True
            },
            {
                "name": "Medium account, moderate",
                "balance": 200,
                "risk_pct": 2.0,
                "entry": 3000,
                "sl": 2940,
                "leverage": 10,
                "expected_valid": True
            },
            {
                "name": "Large account, aggressive",
                "balance": 1000,
                "risk_pct": 3.0,
                "entry": 100,
                "sl": 98,
                "leverage": 10,
                "expected_valid": True
            },
            {
                "name": "Invalid: SL too tight",
                "balance": 100,
                "risk_pct": 2.0,
                "entry": 50000,
                "sl": 49995,  # Only 0.01% SL
                "leverage": 10,
                "expected_valid": False
            },
            {
                "name": "Invalid: Risk too high",
                "balance": 100,
                "risk_pct": 15.0,  # Over 10% limit
                "entry": 50000,
                "sl": 49000,
                "leverage": 10,
                "expected_valid": False
            },
        ]
        
        all_passed = True
        for i, case in enumerate(test_cases, 1):
            result = calculate_position_size(
                balance=case["balance"],
                risk_pct=case["risk_pct"],
                entry_price=case["entry"],
                sl_price=case["sl"],
                leverage=case["leverage"],
                symbol="BTCUSDT"
            )
            
            if result['valid'] == case['expected_valid']:
                print(f"✅ Case {i}: {case['name']}")
                if result['valid']:
                    print(f"   Position: ${result['position_size_usdt']:.2f}, "
                          f"Margin: ${result['margin_required']:.2f}, "
                          f"Qty: {result['qty']}")
            else:
                print(f"❌ Case {i}: {case['name']}")
                print(f"   Expected valid={case['expected_valid']}, got {result['valid']}")
                if not result['valid']:
                    print(f"   Error: {result['error']}")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"❌ Position sizing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all UI integration tests"""
    print("\n" + "="*60)
    print("RISK PER TRADE UI INTEGRATION TESTS")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Callback Patterns", test_callback_patterns()))
    results.append(("Callback Functions", test_callback_functions_exist()))
    results.append(("Settings Menu", test_settings_menu_updated()))
    results.append(("Position Sizing", test_position_sizing_integration()))
    
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
        print("\n🎉 All UI integration tests passed!")
        print("\n📋 Next Steps:")
        print("1. Deploy to VPS")
        print("2. Test in Telegram bot")
        print("3. Verify risk settings work end-to-end")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Fix issues before deployment.")


if __name__ == "__main__":
    main()
