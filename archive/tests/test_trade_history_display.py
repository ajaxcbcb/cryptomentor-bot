"""
Test Trade History Display
Check data dari database dan format tampilan
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

def test_trade_history_format():
    """Test format tampilan trade history"""
    print("=" * 70)
    print("TEST TRADE HISTORY DISPLAY FORMAT")
    print("=" * 70)
    
    # Simulate trade data from screenshot
    trades = [
        {
            "side": "SHORT",
            "symbol": "ETHUSDT",
            "entry_price": 1988.1400,
            "exit_price": 1988.1400,
            "pnl_usdt": 0.0000,
            "status": "closed_tp",
            "leverage": 25,
            "confidence": 78,
            "opened_at": "2026-03-27T15:16:00",
            "is_flip": False,
            "loss_reasoning": ""
        },
        {
            "side": "SHORT",
            "symbol": "BTCUSDT",
            "entry_price": 66162.0000,
            "exit_price": 66162.6000,
            "pnl_usdt": 0.0000,
            "status": "closed_tp",
            "leverage": 25,
            "confidence": 78,
            "opened_at": "2026-03-27T15:15:00",
            "is_flip": False,
            "loss_reasoning": ""
        },
        {
            "side": "SHORT",
            "symbol": "BNBUSDT",
            "entry_price": 607.9200,
            "exit_price": 607.9200,
            "pnl_usdt": 0.0000,
            "status": "closed_tp",
            "leverage": 25,
            "confidence": 78,
            "opened_at": "2026-03-27T14:16:00",
            "is_flip": False,
            "loss_reasoning": ""
        },
        {
            "side": "SHORT",
            "symbol": "SOLUSDT",
            "entry_price": 92.8700,
            "exit_price": 92.8700,
            "pnl_usdt": 0.0000,
            "status": "closed_tp",
            "leverage": 25,
            "confidence": 95,
            "opened_at": "2026-03-27T14:15:00",
            "is_flip": False,
            "loss_reasoning": ""
        },
    ]
    
    print("\n📊 ISSUE DETECTED:")
    print("=" * 70)
    print("❌ All trades showing PnL: +0.0000 USDT")
    print("❌ Entry price = Exit price (no price movement)")
    print("❌ This indicates trades were closed immediately or data not saved properly")
    
    print("\n🔍 ANALYSIS:")
    print("=" * 70)
    for i, t in enumerate(trades, 1):
        print(f"\nTrade {i}: {t['symbol']} {t['side']}")
        print(f"  Entry: {t['entry_price']:.4f}")
        print(f"  Exit:  {t['exit_price']:.4f}")
        print(f"  Diff:  {t['exit_price'] - t['entry_price']:.4f}")
        print(f"  PnL:   {t['pnl_usdt']:.4f} USDT")
        print(f"  Status: {t['status']}")
        
        if t['entry_price'] == t['exit_price']:
            print(f"  ⚠️  WARNING: Entry = Exit (no price movement!)")
        if t['pnl_usdt'] == 0:
            print(f"  ⚠️  WARNING: PnL is zero!")
    
    print("\n" + "=" * 70)
    print("POSSIBLE CAUSES:")
    print("=" * 70)
    print("1. ❌ Trade closed immediately after opening (no time for price movement)")
    print("2. ❌ Exit price not updated properly in database")
    print("3. ❌ PnL calculation not working correctly")
    print("4. ❌ Quantity (qty) is zero or not saved")
    print("5. ❌ Trade closed by system error before price movement")
    
    print("\n" + "=" * 70)
    print("RECOMMENDED FIXES:")
    print("=" * 70)
    print("1. ✅ Check autotrade_engine.py - save_trade_close() calls")
    print("2. ✅ Verify PnL calculation formula")
    print("3. ✅ Check if qty is saved correctly")
    print("4. ✅ Add validation before closing trades")
    print("5. ✅ Add minimum time before allowing trade close")
    
    print("\n" + "=" * 70)
    print("CORRECT DISPLAY FORMAT:")
    print("=" * 70)
    
    # Show correct format
    correct_trade = {
        "side": "SHORT",
        "symbol": "ETHUSDT",
        "entry_price": 1988.1400,
        "exit_price": 1975.5000,  # Price moved down (profit for SHORT)
        "pnl_usdt": 12.50,  # Actual profit
        "status": "closed_tp",
        "leverage": 25,
        "confidence": 78,
        "opened_at": "2026-03-27T15:16:00",
        "is_flip": False,
        "loss_reasoning": ""
    }
    
    side_emoji = "🔴"
    status_emoji = "✅"
    symbol = correct_trade['symbol'].replace("USDT", "")
    
    print(f"\n{status_emoji} {side_emoji} <b>{symbol}</b> {correct_trade['side']} | {correct_trade['leverage']}x")
    print(f"   📍 Entry: {correct_trade['entry_price']:.4f} → Exit: {correct_trade['exit_price']:.4f}")
    print(f"   🧠 Conf: {correct_trade['confidence']}% | {correct_trade['opened_at'][:16].replace('T', ' ')}")
    print(f"   📈 PnL: <b>+{correct_trade['pnl_usdt']:.4f} USDT</b>")
    
    print("\n" + "=" * 70)


def check_pnl_calculation():
    """Check PnL calculation logic"""
    print("\n" + "=" * 70)
    print("PNL CALCULATION CHECK")
    print("=" * 70)
    
    print("\nFORMULA for SHORT position:")
    print("PnL = (Entry Price - Exit Price) * Quantity")
    print("If price goes DOWN → Profit")
    print("If price goes UP → Loss")
    
    print("\nEXAMPLE 1: Profitable SHORT")
    entry = 1988.14
    exit_price = 1975.50
    qty = 1.0
    pnl = (entry - exit_price) * qty
    print(f"Entry: ${entry}")
    print(f"Exit: ${exit_price}")
    print(f"Qty: {qty}")
    print(f"PnL: ${pnl:.2f} ✅ PROFIT")
    
    print("\nEXAMPLE 2: Loss SHORT")
    entry = 1988.14
    exit_price = 2000.00
    qty = 1.0
    pnl = (entry - exit_price) * qty
    print(f"Entry: ${entry}")
    print(f"Exit: ${exit_price}")
    print(f"Qty: {qty}")
    print(f"PnL: ${pnl:.2f} ❌ LOSS")
    
    print("\nEXAMPLE 3: No Movement (CURRENT ISSUE)")
    entry = 1988.14
    exit_price = 1988.14
    qty = 1.0
    pnl = (entry - exit_price) * qty
    print(f"Entry: ${entry}")
    print(f"Exit: ${exit_price}")
    print(f"Qty: {qty}")
    print(f"PnL: ${pnl:.2f} ⚠️ ZERO (No price movement!)")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_trade_history_format()
    check_pnl_calculation()
    
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print("The issue is NOT with the display format.")
    print("The issue is with the DATA itself:")
    print("  - Entry price = Exit price")
    print("  - PnL = 0.0000")
    print("\nThis means trades are being closed immediately")
    print("without any price movement, or exit price is not")
    print("being updated correctly in the database.")
    print("\nNeed to check autotrade_engine.py for:")
    print("  1. When trades are closed")
    print("  2. How exit_price is calculated")
    print("  3. How PnL is calculated")
    print("=" * 70)
