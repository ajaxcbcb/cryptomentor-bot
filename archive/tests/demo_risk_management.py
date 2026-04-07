"""
Interactive Demo: Senior Risk Management Module
Demonstrates various trading scenarios with detailed calculations
"""

import sys
sys.path.insert(0, 'Bismillah')

from app.risk_calculator import calculate_position_size, validate_position_size
import json


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_scenario(scenario_num, description):
    """Print scenario header"""
    print(f"\n{'─' * 80}")
    print(f"SCENARIO {scenario_num}: {description}")
    print(f"{'─' * 80}")


def format_currency(amount):
    """Format currency with 2 decimals"""
    return f"${amount:,.2f}"


def format_crypto(amount, symbol="BTC"):
    """Format crypto with 8 decimals"""
    return f"{amount:.8f} {symbol}"


def calculate_and_display(balance, risk_pct, entry, sl, symbol="BTC", side="LONG"):
    """Calculate position size and display detailed breakdown"""
    
    print(f"\n📊 INPUT PARAMETERS:")
    print(f"   Account Balance:  {format_currency(balance)}")
    print(f"   Risk per Trade:   {risk_pct}%")
    print(f"   Position Type:    {side}")
    print(f"   Entry Price:      {format_currency(entry)}")
    print(f"   Stop Loss:        {format_currency(sl)}")
    
    # Calculate
    result = calculate_position_size(
        last_balance=balance,
        risk_percentage=risk_pct,
        entry_price=entry,
        stop_loss_price=sl
    )
    
    print(f"\n🔢 CALCULATION STEPS:")
    
    if result["status"] == "success":
        risk_amount = result["risk_amount"]
        position_size = result["position_size"]
        price_delta = abs(entry - sl)
        
        print(f"   Step 1: Risk Amount = {format_currency(balance)} × {risk_pct}%")
        print(f"           = {format_currency(risk_amount)}")
        
        print(f"\n   Step 2: Price Delta = |{format_currency(entry)} - {format_currency(sl)}|")
        print(f"           = {format_currency(price_delta)}")
        
        print(f"\n   Step 3: Position Size = {format_currency(risk_amount)} ÷ {format_currency(price_delta)}")
        print(f"           = {format_crypto(position_size, symbol)}")
        
        # Calculate potential outcomes
        if side == "LONG":
            tp_price = entry + (price_delta * 2)  # 1:2 R:R
        else:
            tp_price = entry - (price_delta * 2)
        
        potential_profit = risk_amount * 2  # 1:2 R:R
        
        print(f"\n💰 RISK/REWARD ANALYSIS:")
        print(f"   Max Loss (if SL hit):     {format_currency(risk_amount)} ({risk_pct}% of capital)")
        print(f"   Potential Profit (1:2):   {format_currency(potential_profit)} ({risk_pct * 2}% of capital)")
        print(f"   Risk:Reward Ratio:        1:2")
        print(f"   Target Price (TP):        {format_currency(tp_price)}")
        
        print(f"\n📈 POSITION DETAILS:")
        print(f"   Position Size:            {format_crypto(position_size, symbol)}")
        print(f"   Position Value:           {format_currency(position_size * entry)}")
        print(f"   Entry Price:              {format_currency(entry)}")
        print(f"   Stop Loss:                {format_currency(sl)}")
        print(f"   Take Profit:              {format_currency(tp_price)}")
        
        # Validate position size
        validation = validate_position_size(position_size, min_size=0.001, max_size=100.0)
        
        print(f"\n✅ VALIDATION:")
        if validation["valid"]:
            print(f"   Status: VALID ✓")
            print(f"   Final Size: {format_crypto(validation['adjusted_size'], symbol)}")
        else:
            print(f"   Status: ADJUSTED ⚠️")
            print(f"   Reason: {validation['reason']}")
            print(f"   Adjusted Size: {format_crypto(validation['adjusted_size'], symbol)}")
        
        return result
    else:
        print(f"\n❌ ERROR:")
        print(f"   {result['error_message']}")
        return result


def demo_beginner_trader():
    """Demo: Beginner trader with small account"""
    print_scenario(1, "Beginner Trader - Small Account")
    
    print("""
👤 Profile: New trader starting with minimal capital
💼 Account: $50
🎯 Strategy: Conservative 1% risk per trade
📚 Goal: Learn while preserving capital
    """)
    
    calculate_and_display(
        balance=50.0,
        risk_pct=1.0,
        entry=66500.0,
        sl=65500.0,
        symbol="BTC",
        side="LONG"
    )


def demo_intermediate_trader():
    """Demo: Intermediate trader with moderate account"""
    print_scenario(2, "Intermediate Trader - Moderate Account")
    
    print("""
👤 Profile: Experienced trader with proven strategy
💼 Account: $500
🎯 Strategy: Standard 2% risk per trade
📚 Goal: Consistent growth with controlled risk
    """)
    
    calculate_and_display(
        balance=500.0,
        risk_pct=2.0,
        entry=3200.0,
        sl=3300.0,
        symbol="ETH",
        side="SHORT"
    )


def demo_advanced_trader():
    """Demo: Advanced trader with larger account"""
    print_scenario(3, "Advanced Trader - Large Account")
    
    print("""
👤 Profile: Professional trader with substantial capital
💼 Account: $10,000
🎯 Strategy: Aggressive 3% risk per trade
📚 Goal: Maximize returns with higher risk tolerance
    """)
    
    calculate_and_display(
        balance=10000.0,
        risk_pct=3.0,
        entry=150.0,
        sl=145.0,
        symbol="SOL",
        side="LONG"
    )


def demo_tight_stop_loss():
    """Demo: Trade with very tight stop loss"""
    print_scenario(4, "Tight Stop Loss - Scalping Strategy")
    
    print("""
👤 Profile: Scalper looking for quick profits
💼 Account: $1,000
🎯 Strategy: 1.5% risk with tight SL
📚 Goal: Multiple small wins with minimal risk per trade
    """)
    
    calculate_and_display(
        balance=1000.0,
        risk_pct=1.5,
        entry=66500.0,
        sl=66300.0,  # Only $200 SL
        symbol="BTC",
        side="LONG"
    )


def demo_wide_stop_loss():
    """Demo: Trade with wide stop loss"""
    print_scenario(5, "Wide Stop Loss - Swing Trading")
    
    print("""
👤 Profile: Swing trader holding for days/weeks
💼 Account: $2,000
🎯 Strategy: 2% risk with wide SL for volatility
📚 Goal: Capture larger moves with room to breathe
    """)
    
    calculate_and_display(
        balance=2000.0,
        risk_pct=2.0,
        entry=66500.0,
        sl=63500.0,  # $3,000 SL
        symbol="BTC",
        side="LONG"
    )


def demo_comparison_table():
    """Demo: Comparison of different risk percentages"""
    print_scenario(6, "Risk Percentage Comparison")
    
    print("""
👤 Profile: Trader analyzing different risk levels
💼 Account: $1,000
🎯 Strategy: Compare 1%, 2%, 3%, 5% risk
📚 Goal: Understand impact of risk percentage on position size
    """)
    
    balance = 1000.0
    entry = 66500.0
    sl = 65500.0
    
    print(f"\n{'Risk %':<10} {'Risk $':<15} {'Position Size':<20} {'Max Loss':<15}")
    print("─" * 70)
    
    for risk_pct in [1.0, 2.0, 3.0, 5.0]:
        result = calculate_position_size(balance, risk_pct, entry, sl)
        if result["status"] == "success":
            print(f"{risk_pct}%{'':<7} "
                  f"${result['risk_amount']:<14.2f} "
                  f"{result['position_size']:.8f} BTC{'':<5} "
                  f"${result['risk_amount']:<14.2f}")


def demo_multiple_trades():
    """Demo: Multiple consecutive trades"""
    print_scenario(7, "Multiple Trades - Compounding Effect")
    
    print("""
👤 Profile: Trader executing multiple trades
💼 Account: $1,000
🎯 Strategy: 2% risk per trade, 1:2 R:R
📚 Goal: See compounding effect over multiple wins
    """)
    
    balance = 1000.0
    risk_pct = 2.0
    
    print(f"\n{'Trade':<8} {'Balance':<15} {'Risk $':<12} {'Position':<20} {'Outcome':<15} {'New Balance':<15}")
    print("─" * 95)
    
    trades = [
        ("Trade 1", 66500.0, 65500.0, "WIN"),
        ("Trade 2", 66000.0, 65000.0, "WIN"),
        ("Trade 3", 67000.0, 66000.0, "LOSS"),
        ("Trade 4", 66500.0, 65500.0, "WIN"),
    ]
    
    for i, (trade_name, entry, sl, outcome) in enumerate(trades, 1):
        result = calculate_position_size(balance, risk_pct, entry, sl)
        risk_amount = result["risk_amount"]
        position_size = result["position_size"]
        
        if outcome == "WIN":
            profit = risk_amount * 2  # 1:2 R:R
            new_balance = balance + profit
            outcome_str = f"+${profit:.2f}"
        else:
            new_balance = balance - risk_amount
            outcome_str = f"-${risk_amount:.2f}"
        
        print(f"{trade_name:<8} "
              f"${balance:<14.2f} "
              f"${risk_amount:<11.2f} "
              f"{position_size:.8f} BTC{'':<5} "
              f"{outcome_str:<15} "
              f"${new_balance:<14.2f}")
        
        balance = new_balance
    
    print(f"\n📊 SUMMARY:")
    print(f"   Starting Balance: $1,000.00")
    print(f"   Ending Balance:   ${balance:.2f}")
    print(f"   Total Profit:     ${balance - 1000:.2f} ({((balance/1000 - 1) * 100):.2f}%)")
    print(f"   Win Rate:         75% (3 wins, 1 loss)")


def demo_error_cases():
    """Demo: Error handling"""
    print_scenario(8, "Error Handling - Edge Cases")
    
    print("\n🔴 Case 1: Division by Zero (Entry = Stop Loss)")
    result1 = calculate_position_size(1000.0, 2.0, 66500.0, 66500.0)
    print(f"   Status: {result1['status']}")
    print(f"   Error: {result1['error_message']}")
    
    print("\n🔴 Case 2: Negative Balance")
    result2 = calculate_position_size(-1000.0, 2.0, 66500.0, 65500.0)
    print(f"   Status: {result2['status']}")
    print(f"   Error: {result2['error_message']}")
    
    print("\n🔴 Case 3: Missing Input")
    result3 = calculate_position_size(1000.0, None, 66500.0, 65500.0)
    print(f"   Status: {result3['status']}")
    print(f"   Error: {result3['error_message']}")
    
    print("\n🔴 Case 4: Zero Risk Percentage")
    result4 = calculate_position_size(1000.0, 0.0, 66500.0, 65500.0)
    print(f"   Status: {result4['status']}")
    print(f"   Error: {result4['error_message']}")


def main():
    """Run all demos"""
    print_header("SENIOR RISK MANAGEMENT MODULE - INTERACTIVE DEMO")
    
    print("""
This demo showcases the deterministic risk management calculator with various
real-world trading scenarios. Each scenario demonstrates:

✓ Precise mathematical calculations (8-decimal precision)
✓ Risk/reward analysis
✓ Position sizing based on account balance and risk percentage
✓ Validation against exchange limits
✓ Error handling for edge cases

Press Enter to continue through each scenario...
    """)
    
    input()
    
    # Run all demos
    demo_beginner_trader()
    input("\nPress Enter for next scenario...")
    
    demo_intermediate_trader()
    input("\nPress Enter for next scenario...")
    
    demo_advanced_trader()
    input("\nPress Enter for next scenario...")
    
    demo_tight_stop_loss()
    input("\nPress Enter for next scenario...")
    
    demo_wide_stop_loss()
    input("\nPress Enter for next scenario...")
    
    demo_comparison_table()
    input("\nPress Enter for next scenario...")
    
    demo_multiple_trades()
    input("\nPress Enter for next scenario...")
    
    demo_error_cases()
    
    print_header("DEMO COMPLETE")
    print("""
✅ All scenarios demonstrated successfully!

Key Takeaways:
1. Risk management is deterministic and precise
2. Position size automatically adjusts to maintain consistent risk
3. Works for any account size (from $50 to $10,000+)
4. Supports both LONG and SHORT positions
5. Handles tight and wide stop losses appropriately
6. Validates against exchange limits
7. Robust error handling for edge cases

The module is ready for production deployment! 🚀
    """)


if __name__ == "__main__":
    main()
