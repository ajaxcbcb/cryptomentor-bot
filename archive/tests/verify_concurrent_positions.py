#!/usr/bin/env python3
"""
Verify Concurrent Positions Configuration
Checks that both scalping and swing modes support 4 concurrent positions
"""

import sys
import os

# Add Bismillah to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

def verify_scalping_config():
    """Verify scalping mode configuration"""
    print("\n" + "="*60)
    print("SCALPING MODE CONFIGURATION")
    print("="*60)
    
    try:
        from app.trading_mode import ScalpingConfig
        
        config = ScalpingConfig()
        
        print(f"\n✅ ScalpingConfig loaded successfully")
        print(f"\n📊 Configuration:")
        print(f"   - Max Concurrent Positions: {config.max_concurrent_positions}")
        print(f"   - Timeframe: {config.timeframe}")
        print(f"   - Scan Interval: {config.scan_interval}s")
        print(f"   - Min Confidence: {config.min_confidence * 100:.0f}%")
        print(f"   - Min R:R: 1:{config.min_rr}")
        print(f"   - Max Hold Time: {config.max_hold_time}s ({config.max_hold_time // 60} minutes)")
        print(f"   - Cooldown: {config.cooldown_seconds}s ({config.cooldown_seconds // 60} minutes)")
        print(f"   - Trading Pairs: {len(config.pairs)} pairs")
        print(f"   - Daily Loss Limit: {config.daily_loss_limit * 100:.0f}%")
        
        # Verify max_concurrent_positions
        if config.max_concurrent_positions == 4:
            print(f"\n✅ PASS: Scalping supports 4 concurrent positions")
            return True
        else:
            print(f"\n❌ FAIL: Scalping max_concurrent_positions = {config.max_concurrent_positions} (expected 4)")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR loading ScalpingConfig: {e}")
        return False


def verify_swing_config():
    """Verify swing mode configuration"""
    print("\n" + "="*60)
    print("SWING MODE CONFIGURATION")
    print("="*60)
    
    try:
        from app.autotrade_engine import ENGINE_CONFIG
        
        print(f"\n✅ ENGINE_CONFIG loaded successfully")
        print(f"\n📊 Configuration:")
        print(f"   - Max Concurrent: {ENGINE_CONFIG['max_concurrent']}")
        print(f"   - Scan Interval: {ENGINE_CONFIG['scan_interval']}s")
        print(f"   - Min Confidence: {ENGINE_CONFIG['min_confidence']}%")
        print(f"   - Min R:R Ratio: 1:{ENGINE_CONFIG['min_rr_ratio']}")
        print(f"   - Max Trades/Day: {ENGINE_CONFIG['max_trades_per_day']}")
        print(f"   - Trading Pairs: {len(ENGINE_CONFIG['symbols'])} pairs")
        print(f"   - Daily Loss Limit: {ENGINE_CONFIG['daily_loss_limit'] * 100:.0f}%")
        print(f"   - StackMentor Enabled: {ENGINE_CONFIG['use_stackmentor']}")
        
        # Verify max_concurrent
        if ENGINE_CONFIG['max_concurrent'] == 4:
            print(f"\n✅ PASS: Swing supports 4 concurrent positions")
            return True
        else:
            print(f"\n❌ FAIL: Swing max_concurrent = {ENGINE_CONFIG['max_concurrent']} (expected 4)")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR loading ENGINE_CONFIG: {e}")
        return False


def verify_engine_startup():
    """Verify both engines can be imported and initialized"""
    print("\n" + "="*60)
    print("ENGINE STARTUP VERIFICATION")
    print("="*60)
    
    results = {}
    
    # Test scalping engine import
    try:
        from app.scalping_engine import ScalpingEngine
        print(f"\n✅ ScalpingEngine imported successfully")
        results['scalping_import'] = True
    except Exception as e:
        print(f"\n❌ ERROR importing ScalpingEngine: {e}")
        results['scalping_import'] = False
    
    # Test swing engine import
    try:
        from app.autotrade_engine import start_engine, _trade_loop
        print(f"✅ Swing engine (_trade_loop) imported successfully")
        results['swing_import'] = True
    except Exception as e:
        print(f"❌ ERROR importing swing engine: {e}")
        results['swing_import'] = False
    
    # Test trading mode manager
    try:
        from app.trading_mode_manager import TradingModeManager, TradingMode
        print(f"✅ TradingModeManager imported successfully")
        print(f"   - Available modes: {[m.value for m in TradingMode]}")
        results['mode_manager'] = True
    except Exception as e:
        print(f"❌ ERROR importing TradingModeManager: {e}")
        results['mode_manager'] = False
    
    return all(results.values())


def main():
    """Run all verification checks"""
    print("\n" + "="*60)
    print("CONCURRENT POSITIONS VERIFICATION")
    print("="*60)
    print("\nVerifying that both scalping and swing modes support")
    print("4 concurrent positions for optimal trading volume...")
    
    results = []
    
    # Verify configurations
    results.append(verify_scalping_config())
    results.append(verify_swing_config())
    results.append(verify_engine_startup())
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    if all(results):
        print("\n✅ ALL CHECKS PASSED")
        print("\n📊 Both scalping and swing modes are configured correctly:")
        print("   - Scalping: 4 concurrent positions ✅")
        print("   - Swing: 4 concurrent positions ✅")
        print("   - Both engines can be imported ✅")
        print("\n🚀 System ready for multi-position trading!")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED")
        print("\nPlease review the errors above and fix configuration.")
        return 1


if __name__ == "__main__":
    exit(main())
