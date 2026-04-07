"""
Risk Management Examples - All Scenarios
Shows all examples without requiring user input
"""

import sys
sys.path.insert(0, 'Bismillah')

from app.risk_calculator import calculate_position_size, validate_position_size


def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_scenario(num, title):
    print(f"\n{'─' * 80}")
    print(f"SCENARIO {num}: {title}")
    print(f"{'─' * 80}")


def show_example(balance, risk_pct, entry, sl, symbol="BTC", side="LONG"):
    """Show a complete risk management example"""
    
    print(f"\n📊 Setup:")
    print(f"   Balance: ${balance:,.2f} | Risk: {risk_pct}% | {side} {symbol}")
    print(f"   Entry: ${entry:,.2f} | Stop Loss: ${sl:,.2f}")
    
    result = calculate_position_size(balance, risk_pct, entry, sl)
    
    if result["status"] == "success":
        risk_amt = result["risk_amount"]
        pos_size = result["position_size"]
        delta = abs(entry - sl)
        
        print(f"\n💡 Calculation:")
        print(f"   Risk Amount = ${balance:,.2f} × {risk_pct}% = ${risk_amt:.2f}")
        print(f"   Price Delta = ${delta:,.2f}")
        print(f"   Position Size = ${risk_amt:.2f} ÷ ${delta:,.2f} = {pos_size:.8f} {symbol}")
        
        print(f"\n📈 Result:")
        print(f"   Position: {pos_size:.8f} {symbol} (${pos_size * entry:,.2f} value)")
        print(f"   Max Loss: ${risk_amt:.2f} ({risk_pct}% of capital)")
        print(f"   Potential Profit (1:2 R:R): ${risk_amt * 2:.2f} ({risk_pct * 2}% of capital)")
    else:
        print(f"\n❌ Error: {result['error_message']}")


# ============================================================================
# EXAMPLES
# ============================================================================

print_header("RISK MANAGEMENT CALCULATOR - PRACTICAL EXAMPLES")

# Example 1: Small Account
print_scenario(1, "Small Account ($50) - Conservative 1% Risk")
show_example(50.0, 1.0, 66500.0, 65500.0, "BTC", "LONG")

# Example 2: Medium Account
print_scenario(2, "Medium Account ($500) - Standard 2% Risk")
show_example(500.0, 2.0, 3200.0, 3300.0, "ETH", "SHORT")

# Example 3: Large Account
print_scenario(3, "Large Account ($10,000) - Aggressive 3% Risk")
show_example(10000.0, 3.0, 150.0, 145.0, "SOL", "LONG")

# Example 4: Tight Stop Loss
print_scenario(4, "Scalping - Tight Stop Loss ($200)")
show_example(1000.0, 1.5, 66500.0, 66300.0, "BTC", "LONG")

# Example 5: Wide Stop Loss
print_scenario(5, "Swing Trading - Wide Stop Loss ($3,000)")
show_example(2000.0, 2.0, 66500.0, 63500.0, "BTC", "LONG")

# Example 6: Comparison Table
print_scenario(6, "Risk Percentage Comparison")
print("\nSame trade with different risk percentages:")
print(f"\n{'Risk %':<10} {'Risk Amount':<15} {'Position Size':<20} {'Potential Profit':<20}")
print("─" * 70)

for risk in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
    r = calculate_position_size(1000.0, risk, 66500.0, 65500.0)
    if r["status"] == "success":
        print(f"{risk}%{'':<7} ${r['risk_amount']:<14.2f} {r['position_size']:.8f} BTC{'':<5} ${r['risk_amount'] * 2:<19.2f}")

# Example 7: Multiple Trades
print_scenario(7, "Multiple Trades - Compounding Effect")
print("\nStarting with $1,000, 2% risk per trade, 1:2 R:R:")
print(f"\n{'Trade':<10} {'Balance':<12} {'Risk':<12} {'Outcome':<12} {'New Balance':<12}")
print("─" * 60)

balance = 1000.0
trades = [
    ("Trade 1", "WIN"),
    ("Trade 2", "WIN"),
    ("Trade 3", "LOSS"),
    ("Trade 4", "WIN"),
    ("Trade 5", "WIN"),
]

for trade_name, outcome in trades:
    r = calculate_position_size(balance, 2.0, 66500.0, 65500.0)
    risk_amt = r["risk_amount"]
    
    if outcome == "WIN":
        profit = risk_amt * 2
        new_balance = balance + profit
        outcome_str = f"+${profit:.2f}"
    else:
        new_balance = balance - risk_amt
        outcome_str = f"-${risk_amt:.2f}"
    
    print(f"{trade_name:<10} ${balance:<11.2f} ${risk_amt:<11.2f} {outcome_str:<12} ${new_balance:<11.2f}")
    balance = new_balance

print(f"\nFinal Balance: ${balance:.2f} (Profit: ${balance - 1000:.2f} or {((balance/1000 - 1) * 100):.1f}%)")

# Example 8: Different Account Sizes
print_scenario(8, "Scaling Across Account Sizes")
print("\nSame 2% risk, same trade, different account sizes:")
print(f"\n{'Account Size':<15} {'Risk Amount':<15} {'Position Size':<20}")
print("─" * 55)

for acc_size in [100, 500, 1000, 5000, 10000, 50000]:
    r = calculate_position_size(acc_size, 2.0, 66500.0, 65500.0)
    if r["status"] == "success":
        print(f"${acc_size:<14,.2f} ${r['risk_amount']:<14.2f} {r['position_size']:.8f} BTC")

# Example 9: Error Cases
print_scenario(9, "Error Handling")

print("\n🔴 Case 1: Entry = Stop Loss (Division by Zero)")
r1 = calculate_position_size(1000.0, 2.0, 66500.0, 66500.0)
print(f"   Status: {r1['status']}")
print(f"   Error: {r1['error_message']}")

print("\n🔴 Case 2: Negative Balance")
r2 = calculate_position_size(-1000.0, 2.0, 66500.0, 65500.0)
print(f"   Status: {r2['status']}")
print(f"   Error: {r2['error_message']}")

print("\n🔴 Case 3: Zero Risk")
r3 = calculate_position_size(1000.0, 0.0, 66500.0, 65500.0)
print(f"   Status: {r3['status']}")
print(f"   Error: {r3['error_message']}")

# Summary
print_header("SUMMARY")
print("""
✅ Key Features Demonstrated:

1. Deterministic Calculations
   - Same inputs always produce same outputs
   - 8-decimal precision for all calculations
   - No approximations or rounding errors

2. Flexible Risk Management
   - Works with any account size ($50 to $50,000+)
   - Supports any risk percentage (0.5% to 5%+)
   - Handles both LONG and SHORT positions

3. Automatic Position Sizing
   - Calculates exact position size based on risk
   - Adjusts for tight or wide stop losses
   - Maintains consistent risk across all trades

4. Robust Error Handling
   - Validates all inputs
   - Prevents division by zero
   - Returns clear error messages

5. Real-World Application
   - Compounding effect over multiple trades
   - Scales across different account sizes
   - Supports various trading styles (scalping, swing, etc.)

The module is production-ready and can be integrated into the autotrade engine! 🚀
""")
