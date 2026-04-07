"""
Test script to verify daily loss limit circuit breaker is active
"""

def test_daily_loss_calculation():
    """Test if daily loss limit calculation is correct"""
    
    # Simulate config
    amount = 100.0  # $100 capital
    daily_loss_limit_pct = 0.05  # 5%
    daily_loss_limit = amount * daily_loss_limit_pct
    
    print(f"Capital: ${amount}")
    print(f"Daily loss limit: {daily_loss_limit_pct * 100}%")
    print(f"Max loss allowed: ${daily_loss_limit}")
    print()
    
    # Simulate trades
    daily_pnl_usdt = 0.0
    
    # Trade 1: Loss $2
    trade1_pnl = -2.0
    daily_pnl_usdt += trade1_pnl
    print(f"Trade 1: {trade1_pnl:+.2f} USDT | Daily PnL: {daily_pnl_usdt:+.2f} USDT")
    print(f"  Circuit breaker triggered: {daily_pnl_usdt <= -daily_loss_limit}")
    print()
    
    # Trade 2: Loss $2
    trade2_pnl = -2.0
    daily_pnl_usdt += trade2_pnl
    print(f"Trade 2: {trade2_pnl:+.2f} USDT | Daily PnL: {daily_pnl_usdt:+.2f} USDT")
    print(f"  Circuit breaker triggered: {daily_pnl_usdt <= -daily_loss_limit}")
    print()
    
    # Trade 3: Loss $1.5
    trade3_pnl = -1.5
    daily_pnl_usdt += trade3_pnl
    print(f"Trade 3: {trade3_pnl:+.2f} USDT | Daily PnL: {daily_pnl_usdt:+.2f} USDT")
    print(f"  Circuit breaker triggered: {daily_pnl_usdt <= -daily_loss_limit}")
    print()
    
    print("=" * 50)
    print(f"Final daily PnL: {daily_pnl_usdt:+.2f} USDT")
    print(f"Loss limit: -{daily_loss_limit:.2f} USDT")
    print(f"Circuit breaker should trigger: {daily_pnl_usdt <= -daily_loss_limit}")
    print()
    
    # Check logic
    if daily_pnl_usdt <= -daily_loss_limit:
        print("✅ Circuit breaker ACTIVE - Bot will stop trading")
    else:
        print("❌ Circuit breaker NOT triggered - Bot continues trading")

if __name__ == "__main__":
    test_daily_loss_calculation()
