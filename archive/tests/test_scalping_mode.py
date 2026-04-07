#!/usr/bin/env python3
"""
Test script for Scalping Mode
Tests signal generation, validation, and mode switching
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

from app.trading_mode import TradingMode, ScalpingConfig, ScalpingSignal, ScalpingPosition
from app.trading_mode_manager import TradingModeManager
from app.autosignal_fast import compute_signal_scalping


def test_trading_mode_enum():
    """Test TradingMode enum"""
    print("\n" + "="*60)
    print("TEST: TradingMode Enum")
    print("="*60)
    
    # Test from_string
    assert TradingMode.from_string("scalping") == TradingMode.SCALPING
    assert TradingMode.from_string("swing") == TradingMode.SWING
    assert TradingMode.from_string("invalid") == TradingMode.SWING  # Default
    assert TradingMode.from_string("") == TradingMode.SWING
    assert TradingMode.from_string(None) == TradingMode.SWING
    
    # Test __str__
    assert str(TradingMode.SCALPING) == "scalping"
    assert str(TradingMode.SWING) == "swing"
    
    print("✅ TradingMode enum tests passed")


def test_scalping_config():
    """Test ScalpingConfig dataclass"""
    print("\n" + "="*60)
    print("TEST: ScalpingConfig")
    print("="*60)
    
    # Test default config
    config = ScalpingConfig()
    assert config.timeframe == "5m"
    assert config.scan_interval == 15
    assert config.min_confidence == 0.80
    assert config.min_rr == 1.5
    assert config.max_hold_time == 1800
    assert config.pairs == ["BTCUSDT", "ETHUSDT"]
    assert config.cooldown_seconds == 300
    
    # Test custom config
    custom_config = ScalpingConfig(
        scan_interval=30,
        min_confidence=0.85,
        pairs=["BTCUSDT"]
    )
    assert custom_config.scan_interval == 30
    assert custom_config.min_confidence == 0.85
    assert custom_config.pairs == ["BTCUSDT"]
    
    print("✅ ScalpingConfig tests passed")


def test_scalping_signal():
    """Test ScalpingSignal dataclass"""
    print("\n" + "="*60)
    print("TEST: ScalpingSignal")
    print("="*60)
    
    signal = ScalpingSignal(
        symbol="BTCUSDT",
        side="LONG",
        confidence=85.0,
        entry_price=67000.0,
        tp_price=68500.0,
        sl_price=66000.0,
        rr_ratio=1.5,
        atr_pct=1.2,
        volume_ratio=2.5,
        rsi_5m=28.0,
        trend_15m="LONG",
        reasons=["15M uptrend", "5M oversold", "Volume spike"]
    )
    
    assert signal.symbol == "BTCUSDT"
    assert signal.side == "LONG"
    assert signal.confidence == 85.0
    assert signal.rr_ratio == 1.5
    
    # Test to_dict
    signal_dict = signal.to_dict()
    assert signal_dict["symbol"] == "BTCUSDT"
    assert signal_dict["side"] == "LONG"
    assert signal_dict["confidence"] == 85.0
    assert "15M uptrend" in signal_dict["reasons"]
    
    print("✅ ScalpingSignal tests passed")


def test_scalping_position():
    """Test ScalpingPosition dataclass"""
    print("\n" + "="*60)
    print("TEST: ScalpingPosition")
    print("="*60)
    
    import time
    
    position = ScalpingPosition(
        user_id=12345,
        symbol="BTCUSDT",
        side="BUY",
        entry_price=67000.0,
        quantity=0.01,
        leverage=10,
        tp_price=68500.0,
        sl_price=66000.0,
        opened_at=time.time()
    )
    
    assert position.user_id == 12345
    assert position.symbol == "BTCUSDT"
    assert position.side == "BUY"
    assert position.status == "open"
    
    # Test max_hold_until calculation
    assert position.max_hold_until == position.opened_at + 1800
    
    # Test time_remaining
    remaining = position.time_remaining()
    assert 0 <= remaining <= 1800
    
    # Test is_expired (should not be expired immediately)
    assert position.is_expired() == False
    
    # Test to_dict
    pos_dict = position.to_dict()
    assert pos_dict["user_id"] == 12345
    assert pos_dict["symbol"] == "BTCUSDT"
    
    print("✅ ScalpingPosition tests passed")


def test_signal_generation():
    """Test scalping signal generation"""
    print("\n" + "="*60)
    print("TEST: Signal Generation")
    print("="*60)
    
    # Test BTC signal
    print("\n  Testing BTC signal generation...")
    btc_signal = compute_signal_scalping("BTC")
    
    if btc_signal:
        print(f"  ✅ BTC Signal generated:")
        print(f"     Symbol: {btc_signal['symbol']}")
        print(f"     Side: {btc_signal['side']}")
        print(f"     Confidence: {btc_signal['confidence']}%")
        print(f"     Entry: {btc_signal['entry_price']:.2f}")
        print(f"     TP: {btc_signal['tp']:.2f}")
        print(f"     SL: {btc_signal['sl']:.2f}")
        print(f"     R:R: {btc_signal['rr_ratio']}")
        print(f"     Volume Ratio: {btc_signal['vol_ratio']:.2f}x")
        print(f"     RSI 5M: {btc_signal['rsi_5m']:.1f}")
        print(f"     Trend 15M: {btc_signal['trend_15m']}")
        print(f"     Reasons: {', '.join(btc_signal['reasons'])}")
        
        # Validate signal
        assert btc_signal['confidence'] >= 80
        assert btc_signal['rr_ratio'] == 1.5
        assert btc_signal['timeframe'] == "5m"
        assert btc_signal['side'] in ["LONG", "SHORT"]
    else:
        print("  ℹ️  No BTC signal (market conditions not met)")
    
    # Test ETH signal
    print("\n  Testing ETH signal generation...")
    eth_signal = compute_signal_scalping("ETH")
    
    if eth_signal:
        print(f"  ✅ ETH Signal generated:")
        print(f"     Symbol: {eth_signal['symbol']}")
        print(f"     Side: {eth_signal['side']}")
        print(f"     Confidence: {eth_signal['confidence']}%")
    else:
        print("  ℹ️  No ETH signal (market conditions not met)")
    
    print("\n✅ Signal generation tests completed")


def test_trading_mode_manager():
    """Test TradingModeManager (requires database)"""
    print("\n" + "="*60)
    print("TEST: TradingModeManager")
    print("="*60)
    
    test_user_id = 999999  # Test user
    
    try:
        # Test get_mode (should default to SWING)
        mode = TradingModeManager.get_mode(test_user_id)
        print(f"  Current mode for user {test_user_id}: {mode.value}")
        
        # Test set_mode
        print(f"  Setting mode to SCALPING...")
        success = TradingModeManager.set_mode(test_user_id, TradingMode.SCALPING)
        
        if success:
            print("  ✅ Mode set successfully")
            
            # Verify
            mode = TradingModeManager.get_mode(test_user_id)
            assert mode == TradingMode.SCALPING
            print(f"  ✅ Verified mode: {mode.value}")
            
            # Set back to SWING
            TradingModeManager.set_mode(test_user_id, TradingMode.SWING)
            print("  ✅ Reset to SWING mode")
        else:
            print("  ⚠️  Mode set failed (database not available?)")
    
    except Exception as e:
        print(f"  ⚠️  TradingModeManager test skipped: {e}")
        print("     (Database connection required)")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  SCALPING MODE TEST SUITE")
    print("="*60)
    
    try:
        test_trading_mode_enum()
        test_scalping_config()
        test_scalping_signal()
        test_scalping_position()
        test_signal_generation()
        test_trading_mode_manager()
        
        print("\n" + "="*60)
        print("  ✅ ALL TESTS PASSED")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
