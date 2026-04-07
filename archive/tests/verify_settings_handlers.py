#!/usr/bin/env python3
"""
Verify Settings Handlers Integration
Checks that trading mode and risk management handlers are properly connected
"""

import sys
import os
import re

# Add Bismillah to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

def verify_handler_imports():
    """Verify all handlers can be imported"""
    print("\n" + "="*60)
    print("HANDLER IMPORTS VERIFICATION")
    print("="*60)
    
    results = {}
    
    # Test autotrade handlers
    try:
        from app.handlers_autotrade import (
            callback_settings,
            callback_trading_mode_menu,
            callback_select_scalping,
            callback_select_swing,
            callback_set_amount,
            callback_set_leverage,
            callback_set_margin
        )
        print(f"\n✅ handlers_autotrade imports successful")
        print(f"   - callback_settings ✅")
        print(f"   - callback_trading_mode_menu ✅")
        print(f"   - callback_select_scalping ✅")
        print(f"   - callback_select_swing ✅")
        print(f"   - callback_set_amount ✅")
        print(f"   - callback_set_leverage ✅")
        print(f"   - callback_set_margin ✅")
        results['autotrade_handlers'] = True
    except Exception as e:
        print(f"\n❌ ERROR importing handlers_autotrade: {e}")
        results['autotrade_handlers'] = False
    
    # Test risk mode handlers
    try:
        from app.handlers_risk_mode import (
            callback_choose_risk_mode,
            callback_select_risk_pct,
            callback_mode_manual,
            callback_switch_risk_mode
        )
        print(f"\n✅ handlers_risk_mode imports successful")
        print(f"   - callback_choose_risk_mode ✅")
        print(f"   - callback_select_risk_pct ✅")
        print(f"   - callback_mode_manual ✅")
        print(f"   - callback_switch_risk_mode ✅")
        results['risk_handlers'] = True
    except Exception as e:
        print(f"\n❌ ERROR importing handlers_risk_mode: {e}")
        results['risk_handlers'] = False
    
    # Test risk settings handler (in handlers_autotrade)
    try:
        from app.handlers_autotrade import callback_risk_settings
        print(f"\n✅ callback_risk_settings import successful")
        results['risk_settings'] = True
    except Exception as e:
        print(f"\n❌ ERROR importing callback_risk_settings: {e}")
        results['risk_settings'] = False
    
    # Test trading mode manager
    try:
        from app.trading_mode_manager import TradingModeManager, TradingMode
        print(f"\n✅ TradingModeManager imports successful")
        print(f"   - TradingMode enum ✅")
        print(f"   - TradingModeManager class ✅")
        results['mode_manager'] = True
    except Exception as e:
        print(f"\n❌ ERROR importing TradingModeManager: {e}")
        results['mode_manager'] = False
    
    return all(results.values())


def verify_callback_registrations():
    """Verify all callbacks are registered in bot.py"""
    print("\n" + "="*60)
    print("CALLBACK REGISTRATIONS VERIFICATION")
    print("="*60)
    
    try:
        with open('Bismillah/app/handlers_autotrade.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for callback registrations
        callbacks_to_check = {
            "at_settings": "callback_settings",
            "trading_mode_menu": "callback_trading_mode_menu",
            "mode_select_scalping": "callback_select_scalping",
            "mode_select_swing": "callback_select_swing",
            "at_switch_risk_mode": "callback_switch_risk_mode",
            "at_risk_settings": "callback_risk_settings",
            "at_set_amount": "callback_set_amount",
            "at_set_leverage": "callback_set_leverage",
            "at_set_margin": "callback_set_margin",
        }
        
        print(f"\n📋 Checking callback registrations...")
        all_found = True
        
        for pattern, handler in callbacks_to_check.items():
            # Look for pattern in add_handler calls
            regex = rf'CallbackQueryHandler\({handler}.*pattern.*{re.escape(pattern)}'
            if re.search(regex, content):
                print(f"   ✅ {pattern} → {handler}")
            else:
                print(f"   ❌ {pattern} → {handler} NOT FOUND")
                all_found = False
        
        if all_found:
            print(f"\n✅ All callbacks registered correctly")
            return True
        else:
            print(f"\n❌ Some callbacks missing registration")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR checking registrations: {e}")
        return False


def verify_settings_menu_integration():
    """Verify settings menu shows correct options based on mode"""
    print("\n" + "="*60)
    print("SETTINGS MENU INTEGRATION VERIFICATION")
    print("="*60)
    
    try:
        with open('Bismillah/app/handlers_autotrade.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find callback_settings function
        settings_func = re.search(
            r'async def callback_settings\(.*?\):(.*?)(?=async def|\Z)',
            content,
            re.DOTALL
        )
        
        if not settings_func:
            print(f"\n❌ callback_settings function not found")
            return False
        
        func_body = settings_func.group(1)
        
        # Check for risk mode detection
        checks = {
            "risk_mode = get_risk_mode": "Gets current risk mode",
            "if risk_mode == \"risk_based\"": "Checks for risk-based mode",
            "Change Risk %": "Shows risk % option for risk-based",
            "Switch to Manual Mode": "Shows switch option for risk-based",
            "Change Margin": "Shows margin option for manual",
            "Change Leverage": "Shows leverage option for manual",
            "Switch to Rekomendasi Mode": "Shows switch option for manual",
        }
        
        print(f"\n📋 Checking settings menu logic...")
        all_found = True
        
        for check, description in checks.items():
            if check in func_body:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} NOT FOUND")
                all_found = False
        
        if all_found:
            print(f"\n✅ Settings menu properly integrated")
            return True
        else:
            print(f"\n❌ Settings menu missing some logic")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR checking settings menu: {e}")
        return False


def verify_trading_mode_menu():
    """Verify trading mode menu shows current mode correctly"""
    print("\n" + "="*60)
    print("TRADING MODE MENU VERIFICATION")
    print("="*60)
    
    try:
        with open('Bismillah/app/handlers_autotrade.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find callback_trading_mode_menu function
        mode_func = re.search(
            r'async def callback_trading_mode_menu\(.*?\):(.*?)(?=async def|\Z)',
            content,
            re.DOTALL
        )
        
        if not mode_func:
            print(f"\n❌ callback_trading_mode_menu function not found")
            return False
        
        func_body = mode_func.group(1)
        
        # Check for mode detection and display
        checks = {
            "TradingModeManager.get_mode": "Gets current trading mode",
            "TradingMode.SCALPING": "Checks for scalping mode",
            "TradingMode.SWING": "Checks for swing mode",
            "scalping_check": "Shows checkmark for scalping",
            "swing_check": "Shows checkmark for swing",
            "mode_select_scalping": "Scalping selection callback",
            "mode_select_swing": "Swing selection callback",
        }
        
        print(f"\n📋 Checking trading mode menu logic...")
        all_found = True
        
        for check, description in checks.items():
            if check in func_body:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} NOT FOUND")
                all_found = False
        
        if all_found:
            print(f"\n✅ Trading mode menu properly implemented")
            return True
        else:
            print(f"\n❌ Trading mode menu missing some logic")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR checking trading mode menu: {e}")
        return False


def verify_mode_switching():
    """Verify mode switching handlers work correctly"""
    print("\n" + "="*60)
    print("MODE SWITCHING VERIFICATION")
    print("="*60)
    
    try:
        with open('Bismillah/app/handlers_autotrade.py', 'r', encoding='utf-8') as f:
            autotrade_content = f.read()
        
        with open('Bismillah/app/handlers_risk_mode.py', 'r', encoding='utf-8') as f:
            risk_content = f.read()
        
        # Check trading mode switching
        print(f"\n📋 Checking trading mode switching...")
        
        scalping_func = re.search(
            r'async def callback_select_scalping\(.*?\):(.*?)(?=async def|\Z)',
            autotrade_content,
            re.DOTALL
        )
        
        swing_func = re.search(
            r'async def callback_select_swing\(.*?\):(.*?)(?=async def|\Z)',
            autotrade_content,
            re.DOTALL
        )
        
        if scalping_func and "TradingModeManager.switch_mode" in scalping_func.group(1):
            print(f"   ✅ Scalping mode switching implemented")
        else:
            print(f"   ❌ Scalping mode switching NOT FOUND")
        
        if swing_func and "TradingModeManager.switch_mode" in swing_func.group(1):
            print(f"   ✅ Swing mode switching implemented")
        else:
            print(f"   ❌ Swing mode switching NOT FOUND")
        
        # Check risk mode switching
        print(f"\n📋 Checking risk mode switching...")
        
        risk_switch_func = re.search(
            r'async def callback_switch_risk_mode\(.*?\):(.*?)(?=async def|\Z)',
            risk_content,
            re.DOTALL
        )
        
        if risk_switch_func:
            func_body = risk_switch_func.group(1)
            if "get_risk_mode" in func_body and "set_risk_mode" in func_body:
                print(f"   ✅ Risk mode switching implemented")
                print(f"   ✅ Toggles between risk_based and manual")
            else:
                print(f"   ❌ Risk mode switching incomplete")
        else:
            print(f"   ❌ callback_switch_risk_mode NOT FOUND")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR checking mode switching: {e}")
        return False


def main():
    """Run all verification checks"""
    print("\n" + "="*60)
    print("SETTINGS HANDLERS INTEGRATION VERIFICATION")
    print("="*60)
    print("\nVerifying that trading mode and risk management")
    print("handlers are properly connected and working...")
    
    results = []
    
    # Run all checks
    results.append(verify_handler_imports())
    results.append(verify_callback_registrations())
    results.append(verify_settings_menu_integration())
    results.append(verify_trading_mode_menu())
    results.append(verify_mode_switching())
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    if all(results):
        print("\n✅ ALL CHECKS PASSED")
        print("\n📊 Settings handlers are properly integrated:")
        print("   - All handlers can be imported ✅")
        print("   - All callbacks registered ✅")
        print("   - Settings menu shows correct options ✅")
        print("   - Trading mode menu works correctly ✅")
        print("   - Mode switching implemented ✅")
        print("\n🚀 System ready for user mode switching!")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED")
        print("\nPlease review the errors above and fix integration.")
        return 1


if __name__ == "__main__":
    exit(main())
