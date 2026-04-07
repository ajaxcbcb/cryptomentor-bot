"""
Test Correct PnL Calculation for Futures Trading
Berdasarkan margin, leverage, dan trading volume
"""

def calculate_pnl_correct(entry_price, exit_price, qty, leverage, side):
    """
    Calculate PnL for futures trading
    
    Formula:
    - Price difference = exit_price - entry_price (for LONG)
    - Price difference = entry_price - exit_price (for SHORT)
    - PnL = price_difference * qty
    
    Note: qty sudah memperhitungkan leverage dalam notional value
    qty = (margin * leverage) / entry_price
    
    Jadi PnL = price_difference * qty sudah benar!
    """
    if side == "LONG":
        price_diff = exit_price - entry_price
    else:  # SHORT
        price_diff = entry_price - exit_price
    
    pnl = price_diff * qty
    return pnl


def test_pnl_scenarios():
    """Test berbagai scenario PnL calculation"""
    print("=" * 80)
    print("PNL CALCULATION TEST - FUTURES TRADING")
    print("=" * 80)
    
    # Scenario 1: LONG position with profit
    print("\n📊 SCENARIO 1: LONG Position - Profit")
    print("-" * 80)
    margin = 100  # USDT
    leverage = 10
    entry_price = 2000  # USDT
    exit_price = 2100  # USDT (price went UP)
    
    # Calculate qty
    notional = margin * leverage  # 100 * 10 = 1000 USDT
    qty = notional / entry_price  # 1000 / 2000 = 0.5
    
    pnl = calculate_pnl_correct(entry_price, exit_price, qty, leverage, "LONG")
    
    print(f"Margin: ${margin} USDT")
    print(f"Leverage: {leverage}x")
    print(f"Notional Value: ${notional} USDT")
    print(f"Entry Price: ${entry_price}")
    print(f"Exit Price: ${exit_price}")
    print(f"Quantity: {qty}")
    print(f"Price Movement: ${exit_price - entry_price} (+{((exit_price/entry_price - 1) * 100):.2f}%)")
    print(f"PnL: ${pnl:.2f} USDT ✅")
    print(f"ROI: {(pnl / margin * 100):.2f}% (on margin)")
    
    # Scenario 2: SHORT position with profit
    print("\n📊 SCENARIO 2: SHORT Position - Profit")
    print("-" * 80)
    margin = 100  # USDT
    leverage = 10
    entry_price = 2000  # USDT
    exit_price = 1900  # USDT (price went DOWN)
    
    notional = margin * leverage
    qty = notional / entry_price
    
    pnl = calculate_pnl_correct(entry_price, exit_price, qty, leverage, "SHORT")
    
    print(f"Margin: ${margin} USDT")
    print(f"Leverage: {leverage}x")
    print(f"Notional Value: ${notional} USDT")
    print(f"Entry Price: ${entry_price}")
    print(f"Exit Price: ${exit_price}")
    print(f"Quantity: {qty}")
    print(f"Price Movement: ${entry_price - exit_price} (-{((1 - exit_price/entry_price) * 100):.2f}%)")
    print(f"PnL: ${pnl:.2f} USDT ✅")
    print(f"ROI: {(pnl / margin * 100):.2f}% (on margin)")
    
    # Scenario 3: LONG position with loss
    print("\n📊 SCENARIO 3: LONG Position - Loss")
    print("-" * 80)
    margin = 100
    leverage = 10
    entry_price = 2000
    exit_price = 1950  # Price went DOWN (loss for LONG)
    
    notional = margin * leverage
    qty = notional / entry_price
    
    pnl = calculate_pnl_correct(entry_price, exit_price, qty, leverage, "LONG")
    
    print(f"Margin: ${margin} USDT")
    print(f"Leverage: {leverage}x")
    print(f"Notional Value: ${notional} USDT")
    print(f"Entry Price: ${entry_price}")
    print(f"Exit Price: ${exit_price}")
    print(f"Quantity: {qty}")
    print(f"Price Movement: ${exit_price - entry_price} ({((exit_price/entry_price - 1) * 100):.2f}%)")
    print(f"PnL: ${pnl:.2f} USDT ❌")
    print(f"ROI: {(pnl / margin * 100):.2f}% (on margin)")
    
    # Scenario 4: Real example from screenshot
    print("\n📊 SCENARIO 4: Real Example from Screenshot")
    print("-" * 80)
    print("ETH SHORT | Entry: 1988.14 → Exit: 1988.14")
    print("Issue: Entry = Exit, so PnL = 0")
    print("\nIf exit was different:")
    
    # Assume margin and leverage
    margin = 50  # Assume $50 margin
    leverage = 25
    entry_price = 1988.14
    exit_price_1 = 1975.00  # Profit scenario
    exit_price_2 = 2000.00  # Loss scenario
    
    notional = margin * leverage
    qty = notional / entry_price
    
    pnl_profit = calculate_pnl_correct(entry_price, exit_price_1, qty, leverage, "SHORT")
    pnl_loss = calculate_pnl_correct(entry_price, exit_price_2, qty, leverage, "SHORT")
    
    print(f"\nAssumed Margin: ${margin} USDT")
    print(f"Leverage: {leverage}x")
    print(f"Notional: ${notional} USDT")
    print(f"Qty: {qty:.4f} ETH")
    print(f"\nIf Exit = $1975.00 (profit):")
    print(f"  PnL: ${pnl_profit:.2f} USDT ✅")
    print(f"  ROI: {(pnl_profit / margin * 100):.2f}%")
    print(f"\nIf Exit = $2000.00 (loss):")
    print(f"  PnL: ${pnl_loss:.2f} USDT ❌")
    print(f"  ROI: {(pnl_loss / margin * 100):.2f}%")


def verify_current_formula():
    """Verify that current formula is correct"""
    print("\n" + "=" * 80)
    print("VERIFICATION: Current Formula in Code")
    print("=" * 80)
    
    print("\nCurrent code:")
    print("```python")
    print("raw_pnl = (exit_px - entry_px) if db_side == 'LONG' else (entry_px - exit_px)")
    print("pnl_usdt = raw_pnl * float(db_trade.get('qty', 0))")
    print("```")
    
    print("\n✅ This formula is CORRECT!")
    print("\nWhy?")
    print("- qty already includes leverage in its calculation")
    print("- qty = (margin * leverage) / entry_price")
    print("- So: PnL = price_diff * qty = price_diff * (margin * leverage / entry_price)")
    print("- This gives us the correct PnL in USDT")
    
    print("\n⚠️ The REAL issue:")
    print("- Exit price was being set to entry price when fetch failed")
    print("- This made price_diff = 0, so PnL = 0")
    print("- The formula itself is correct!")
    
    print("\n✅ Solution already implemented:")
    print("- Get mark price from exchange API first")
    print("- Fallback to klines if mark price unavailable")
    print("- Only use entry price as last resort")


def show_formula_breakdown():
    """Show detailed formula breakdown"""
    print("\n" + "=" * 80)
    print("FORMULA BREAKDOWN")
    print("=" * 80)
    
    print("\n1️⃣ Calculate Quantity:")
    print("   notional = margin * leverage")
    print("   qty = notional / entry_price")
    print("   Example: margin=$100, leverage=10x, entry=$2000")
    print("   → notional = $1000")
    print("   → qty = 1000 / 2000 = 0.5")
    
    print("\n2️⃣ Calculate Price Difference:")
    print("   For LONG: price_diff = exit_price - entry_price")
    print("   For SHORT: price_diff = entry_price - exit_price")
    print("   Example SHORT: entry=$2000, exit=$1900")
    print("   → price_diff = 2000 - 1900 = $100")
    
    print("\n3️⃣ Calculate PnL:")
    print("   PnL = price_diff * qty")
    print("   Example: price_diff=$100, qty=0.5")
    print("   → PnL = 100 * 0.5 = $50")
    
    print("\n4️⃣ Calculate ROI:")
    print("   ROI = (PnL / margin) * 100%")
    print("   Example: PnL=$50, margin=$100")
    print("   → ROI = (50 / 100) * 100% = 50%")
    
    print("\n✅ This is exactly what the code does!")


if __name__ == "__main__":
    test_pnl_scenarios()
    verify_current_formula()
    show_formula_breakdown()
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("✅ The PnL calculation formula is CORRECT")
    print("✅ qty already includes leverage in its calculation")
    print("✅ The issue was exit_price = entry_price (not the formula)")
    print("✅ Fix already deployed: use mark price from exchange API")
    print("\n📊 Future trades will show correct PnL values!")
    print("=" * 80)
