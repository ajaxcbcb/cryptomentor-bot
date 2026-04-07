# Professional Risk Management System - Specification

**Date:** April 2, 2026  
**Feature:** Risk Per Trade Selection  
**Goal:** Professional money management with compounding capability

---

## Problem Statement

**Current System:**
- User sets fixed margin amount (e.g., $10 per trade)
- No compounding - profit doesn't grow position size
- Risk not proportional to account balance
- Can blow account with consecutive losses

**Example Problem:**
```
Balance: $100
Margin per trade: $10 (10% of account)
Leverage: 10x

Trade 1: -$10 → Balance: $90
Trade 2: -$10 → Balance: $80
Trade 3: -$10 → Balance: $70
...
Trade 10: -$10 → Balance: $0 (BLOWN!)
```

---

## Solution: Risk Per Trade System

### Professional Approach:

**Risk % of Balance:**
- User selects risk per trade: 1%, 2%, 3%, 5%
- Position size calculated from current balance
- Automatic compounding as balance grows
- Protected from account blow-up

**Example with 2% Risk:**
```
Balance: $100
Risk per trade: 2% = $2
Leverage: 10x
Position size: $20 (2% risk, 10x leverage)

Trade 1: -$2 → Balance: $98
Trade 2: -$2 (2% of $98 = $1.96) → Balance: $96.04
Trade 3: -$2 (2% of $96.04 = $1.92) → Balance: $94.12
...
Trade 50: Still have $36.42 (NOT BLOWN!)

With wins mixed in:
Trade 1: +$4 (2:1 RR) → Balance: $104
Trade 2: +$4.16 (2% of $104) → Balance: $108.16
Trade 3: +$4.33 → Balance: $112.49 (COMPOUNDING!)
```

---

## Risk Levels

### Conservative (1% Risk):
- **Max loss per trade:** 1% of balance
- **Survivability:** 100+ consecutive losses
- **Best for:** Beginners, small accounts
- **Growth:** Slow but steady

### Moderate (2% Risk):
- **Max loss per trade:** 2% of balance
- **Survivability:** 50+ consecutive losses
- **Best for:** Intermediate traders
- **Growth:** Balanced

### Aggressive (3% Risk):
- **Max loss per trade:** 3% of balance
- **Survivability:** 33+ consecutive losses
- **Best for:** Experienced traders
- **Growth:** Fast

### Very Aggressive (5% Risk):
- **Max loss per trade:** 5% of balance
- **Survivability:** 20+ consecutive losses
- **Best for:** Pro traders only
- **Growth:** Very fast (but risky)

---

## Position Sizing Formula

### Professional Calculation:

```python
# Get current balance
balance = get_account_balance()  # e.g., $100

# User's risk percentage
risk_pct = 0.02  # 2%

# Calculate risk amount
risk_amount = balance * risk_pct  # $100 * 0.02 = $2

# Get signal with SL distance
signal = compute_signal()
entry_price = signal['entry']  # e.g., $50,000
sl_price = signal['sl']        # e.g., $49,000
sl_distance_pct = abs(entry_price - sl_price) / entry_price  # 2%

# Calculate position size
# Risk amount = Position size * SL distance
# $2 = Position size * 0.02
position_size = risk_amount / sl_distance_pct  # $2 / 0.02 = $100

# With leverage
leverage = 10
margin_required = position_size / leverage  # $100 / 10 = $10

# Quantity to buy
qty = position_size / entry_price  # $100 / $50,000 = 0.002 BTC
```

### Example Scenarios:

**Scenario 1: Tight SL (1% distance)**
```
Balance: $100
Risk: 2% = $2
SL distance: 1%
Position size: $2 / 0.01 = $200
Leverage: 10x
Margin: $20
```

**Scenario 2: Wide SL (4% distance)**
```
Balance: $100
Risk: 2% = $2
SL distance: 4%
Position size: $2 / 0.04 = $50
Leverage: 10x
Margin: $5
```

**Key Insight:** Wider SL = Smaller position size (same risk!)

---

## Database Schema

### Add to autotrade_sessions table:

```sql
ALTER TABLE autotrade_sessions 
ADD COLUMN risk_per_trade DECIMAL(5,2) DEFAULT 2.00;  -- 2% default

-- Values: 1.00, 2.00, 3.00, 5.00 (1%, 2%, 3%, 5%)
```

### Migration Script:

```sql
-- db/add_risk_per_trade.sql

-- Add risk_per_trade column
ALTER TABLE autotrade_sessions 
ADD COLUMN IF NOT EXISTS risk_per_trade DECIMAL(5,2) DEFAULT 2.00;

-- Set default for existing users (2% - moderate)
UPDATE autotrade_sessions 
SET risk_per_trade = 2.00 
WHERE risk_per_trade IS NULL;

-- Add constraint: risk must be between 0.5% and 10%
ALTER TABLE autotrade_sessions 
ADD CONSTRAINT risk_per_trade_range 
CHECK (risk_per_trade >= 0.5 AND risk_per_trade <= 10.0);
```

---

## UI/UX Design

### Dashboard Button:

```
📊 AutoTrade Dashboard

Status: 🟢 Active
Mode: Swing Trading
Balance: $125.50
Risk per trade: 2% ($2.51)

[⚙️ Risk Settings]  [📊 Performance]  [⏸️ Pause]
```

### Risk Settings Modal:

```
⚙️ Risk Management Settings

Current Balance: $125.50

Select Risk Per Trade:
○ 1% - Conservative ($1.26 per trade)
  └─ Survivability: 100+ losses
  └─ Best for: Beginners

● 2% - Moderate ($2.51 per trade)  ✓ RECOMMENDED
  └─ Survivability: 50+ losses
  └─ Best for: Most traders

○ 3% - Aggressive ($3.77 per trade)
  └─ Survivability: 33+ losses
  └─ Best for: Experienced

○ 5% - Very Aggressive ($6.28 per trade)
  └─ Survivability: 20+ losses
  └─ Best for: Pro traders only

⚠️ Note: Position size will be calculated automatically
based on your balance and stop loss distance.

[Cancel]  [Save Changes]
```

### Confirmation Message:

```
✅ Risk Settings Updated

New risk per trade: 2%
Current balance: $125.50
Max loss per trade: $2.51

Your position sizes will now be calculated automatically
to risk exactly 2% per trade, regardless of stop loss distance.

This enables safe compounding as your balance grows! 📈
```

---

## Implementation Files

### 1. Database Migration

**File:** `db/add_risk_per_trade.sql`

### 2. Supabase Repository

**File:** `Bismillah/app/supabase_repo.py`

**Add functions:**
```python
def get_risk_per_trade(telegram_id: int) -> float:
    """Get user's risk per trade percentage"""
    
def set_risk_per_trade(telegram_id: int, risk_pct: float) -> bool:
    """Update user's risk per trade percentage"""
```

### 3. Position Sizing Module

**File:** `Bismillah/app/position_sizing.py` (NEW)

**Functions:**
```python
def calculate_position_size(
    balance: float,
    risk_pct: float,
    entry_price: float,
    sl_price: float,
    leverage: int
) -> dict:
    """
    Calculate position size based on risk percentage.
    
    Returns:
        {
            'position_size_usdt': float,  # Total position value
            'margin_required': float,      # Margin needed
            'qty': float,                  # Quantity to buy
            'risk_amount': float,          # Max loss in USDT
            'sl_distance_pct': float,      # SL distance %
        }
    """
```

### 4. AutoTrade Engine

**File:** `Bismillah/app/autotrade_engine.py`

**Changes:**
- Remove fixed `amount` parameter
- Get `risk_per_trade` from database
- Calculate position size dynamically
- Update position sizing logic

### 5. Handlers

**File:** `Bismillah/app/handlers_autotrade.py`

**Add callbacks:**
- `at_risk_settings` - Show risk settings modal
- `at_set_risk_1` - Set 1% risk
- `at_set_risk_2` - Set 2% risk
- `at_set_risk_3` - Set 3% risk
- `at_set_risk_5` - Set 5% risk

**Update dashboard:**
- Show current risk percentage
- Show calculated risk amount
- Add "Risk Settings" button

---

## Pro Trader Analysis Improvements

### Current Analysis (Good):
- Multi-timeframe confluence (1H + 15M)
- SMC concepts (CHoCH, BOS, FVG, OB)
- Volume confirmation
- RSI filters
- ATR-based SL/TP

### Enhancements Needed:

**1. Market Structure Analysis:**
```python
def analyze_market_structure(klines_1h, klines_15m):
    """
    Professional market structure analysis:
    - Identify swing highs/lows
    - Detect CHoCH (Change of Character)
    - Find BOS (Break of Structure)
    - Map supply/demand zones
    """
```

**2. Liquidity Analysis:**
```python
def identify_liquidity_zones(klines):
    """
    Find liquidity pools:
    - Equal highs/lows (liquidity grab zones)
    - Previous day high/low
    - Round numbers (psychological levels)
    - High volume nodes
    """
```

**3. Order Flow Analysis:**
```python
def analyze_order_flow(klines):
    """
    Institutional order flow:
    - Buying/selling pressure
    - Volume profile
    - Delta (buy vol - sell vol)
    - Absorption patterns
    """
```

**4. Multi-Timeframe Confluence:**
```python
def check_mtf_confluence(signal_15m, bias_1h, bias_4h):
    """
    Ensure alignment across timeframes:
    - 4H: Overall trend direction
    - 1H: Intermediate structure
    - 15M: Entry timing
    
    Only trade when all aligned!
    """
```

**5. Risk:Reward Validation:**
```python
def validate_rr_ratio(entry, sl, tp, min_rr=2.0):
    """
    Professional RR validation:
    - Min 1:2 RR required
    - Prefer 1:3+ for swing trades
    - Account for spread/slippage
    - Ensure TP at logical level (not arbitrary)
    """
```

---

## Testing Plan

### Unit Tests:

**Test position sizing:**
```python
def test_position_sizing():
    # Test 1: Normal scenario
    result = calculate_position_size(
        balance=100,
        risk_pct=2.0,
        entry_price=50000,
        sl_price=49000,
        leverage=10
    )
    assert result['risk_amount'] == 2.0
    assert result['sl_distance_pct'] == 0.02
    assert result['position_size_usdt'] == 100
    assert result['margin_required'] == 10
    
    # Test 2: Tight SL
    result = calculate_position_size(
        balance=100,
        risk_pct=2.0,
        entry_price=50000,
        sl_price=49500,  # 1% SL
        leverage=10
    )
    assert result['position_size_usdt'] == 200  # Larger position
    assert result['margin_required'] == 20
    
    # Test 3: Wide SL
    result = calculate_position_size(
        balance=100,
        risk_pct=2.0,
        entry_price=50000,
        sl_price=48000,  # 4% SL
        leverage=10
    )
    assert result['position_size_usdt'] == 50  # Smaller position
    assert result['margin_required'] == 5
```

### Integration Tests:

**Test full flow:**
1. User sets risk to 2%
2. Signal generated with SL
3. Position size calculated
4. Order placed
5. Verify risk = 2% of balance

---

## Deployment Checklist

- [ ] Create migration script
- [ ] Add position_sizing.py module
- [ ] Update supabase_repo.py
- [ ] Update autotrade_engine.py
- [ ] Update handlers_autotrade.py
- [ ] Add UI buttons and modals
- [ ] Write unit tests
- [ ] Test on staging
- [ ] Deploy to production
- [ ] Monitor for issues

---

## Expected Benefits

### For Users:

✅ **Safe Compounding:**
- Profits automatically increase position size
- Losses automatically decrease position size
- Natural risk management

✅ **Account Protection:**
- Can't blow account with consecutive losses
- Risk always proportional to balance
- Professional money management

✅ **Simplicity:**
- No need to calculate position size
- No need to adjust margin manually
- Set and forget

### For Platform:

✅ **Higher Trading Volume:**
- Users trade with confidence
- Larger positions as accounts grow
- More fees for platform

✅ **Better User Retention:**
- Users don't blow accounts
- Sustainable growth
- Happy customers

✅ **Professional Image:**
- Industry-standard risk management
- Attracts serious traders
- Competitive advantage

---

## Risk Comparison

### Old System (Fixed Margin):

```
Starting balance: $100
Fixed margin: $10 per trade
Leverage: 10x

10 consecutive losses:
$100 → $90 → $80 → $70 → $60 → $50 → $40 → $30 → $20 → $10 → $0
ACCOUNT BLOWN! ❌
```

### New System (2% Risk):

```
Starting balance: $100
Risk per trade: 2%
Leverage: 10x

10 consecutive losses:
$100 → $98 → $96.04 → $94.12 → $92.24 → $90.39 → $88.59 → $86.81 → $85.08 → $83.38
Still have $83.38! ✅

50 consecutive losses:
Still have $36.42! ✅

100 consecutive losses:
Still have $13.26! ✅
```

---

## Success Metrics

### Week 1:
- [ ] 50%+ users adopt risk per trade
- [ ] No account blow-ups
- [ ] Positive user feedback

### Month 1:
- [ ] 80%+ users using risk per trade
- [ ] Average account growth: +10%
- [ ] User retention: +20%

### Quarter 1:
- [ ] 95%+ adoption
- [ ] Average account growth: +30%
- [ ] Platform volume: +50%

---

## Conclusion

This professional risk management system will:

1. **Protect users** from account blow-ups
2. **Enable compounding** for sustainable growth
3. **Simplify trading** with automatic position sizing
4. **Increase volume** as accounts grow
5. **Improve retention** with better results

It's a win-win for users and platform! 🚀

---

**Designed By:** Kiro AI  
**Date:** April 2, 2026  
**Status:** READY TO IMPLEMENT  
**Priority:** HIGH (Game-changer feature)
