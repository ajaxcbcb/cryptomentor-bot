# Senior Risk Management Module - Implementation Guide

## Overview

Modul risk management deterministik dengan perhitungan matematis presisi tinggi (8 desimal) untuk capital preservation.

## Features

✅ Deterministic calculations (no approximations)
✅ 8-decimal precision for all floats
✅ Strict input validation
✅ Division-by-zero protection
✅ JSON-compatible output
✅ Support for LONG and SHORT positions
✅ Position size validation against exchange limits

## Module Location

```
Bismillah/app/risk_calculator.py
```

## Core Function

### `calculate_position_size()`

```python
from app.risk_calculator import calculate_position_size

result = calculate_position_size(
    last_balance=1000.0,      # Current account balance
    risk_percentage=2.0,       # Risk per trade (2% = 2.0)
    entry_price=50000.0,       # Entry price
    stop_loss_price=49000.0    # Stop loss price
)
```

### Logic Engine

1. **Validation**: Ensure all inputs are present and positive
2. **Risk Calculation**: `Risk Amount = last_balance * (risk_percentage / 100)`
3. **Delta Calculation**: `Price Delta = ABS(entry_price - stop_loss_price)`
4. **Size Calculation**: `Position Size = Risk Amount / Price Delta`

### Output Format

```json
{
  "risk_amount": 20.0,
  "position_size": 0.02,
  "currency_risk_percent": 2.0,
  "status": "success",
  "error_message": null
}
```

### Error Handling

```json
{
  "risk_amount": 0.0,
  "position_size": 0.0,
  "currency_risk_percent": 0.0,
  "status": "error",
  "error_message": "Division by zero: entry_price equals stop_loss_price"
}
```

## Integration with AutoTrade Engine

### Example Integration

```python
from app.risk_calculator import calculate_position_size, validate_position_size

# Get user balance
balance = 1000.0  # From exchange API

# Get risk percentage from user settings
risk_pct = 2.0  # 2% per trade

# Signal data
entry_price = 66500.0
stop_loss_price = 65500.0

# Calculate position size
calc_result = calculate_position_size(
    last_balance=balance,
    risk_percentage=risk_pct,
    entry_price=entry_price,
    stop_loss_price=stop_loss_price
)

if calc_result["status"] == "success":
    position_size = calc_result["position_size"]
    risk_amount = calc_result["risk_amount"]
    
    # Validate against exchange limits
    validation = validate_position_size(
        position_size=position_size,
        min_size=0.001,  # Exchange minimum
        max_size=100.0   # Exchange maximum
    )
    
    if validation["valid"]:
        final_size = validation["adjusted_size"]
        print(f"✅ Position size: {final_size} BTC")
        print(f"💰 Risk amount: ${risk_amount}")
    else:
        print(f"⚠️ {validation['reason']}")
        final_size = validation["adjusted_size"]
else:
    print(f"❌ Error: {calc_result['error_message']}")
```

## Real-World Examples

### Example 1: BTC LONG Trade

```python
# Account: $100
# Risk: 2% per trade
# Entry: $66,500
# Stop Loss: $65,500

result = calculate_position_size(
    last_balance=100.0,
    risk_percentage=2.0,
    entry_price=66500.0,
    stop_loss_price=65500.0
)

# Output:
# {
#   "risk_amount": 2.0,        # $2 risk
#   "position_size": 0.002,    # 0.002 BTC
#   "status": "success"
# }
```

### Example 2: ETH SHORT Trade

```python
# Account: $500
# Risk: 1.5% per trade
# Entry: $3,200 (SHORT)
# Stop Loss: $3,300

result = calculate_position_size(
    last_balance=500.0,
    risk_percentage=1.5,
    entry_price=3200.0,
    stop_loss_price=3300.0
)

# Output:
# {
#   "risk_amount": 7.5,        # $7.5 risk
#   "position_size": 0.075,    # 0.075 ETH
#   "status": "success"
# }
```

### Example 3: Small Account

```python
# Account: $50
# Risk: 2% per trade
# Entry: $50,000
# Stop Loss: $49,000

result = calculate_position_size(
    last_balance=50.0,
    risk_percentage=2.0,
    entry_price=50000.0,
    stop_loss_price=49000.0
)

# Output:
# {
#   "risk_amount": 1.0,        # $1 risk
#   "position_size": 0.001,    # 0.001 BTC
#   "status": "success"
# }
```

## Advantages Over Current Implementation

### Current (position_sizing.py)
- Uses leverage-based calculations
- Less precise
- Harder to verify
- Mixed concerns (leverage + risk)

### New (risk_calculator.py)
- ✅ Pure risk-based calculations
- ✅ 8-decimal precision
- ✅ Easy to verify mathematically
- ✅ Single responsibility
- ✅ Deterministic output
- ✅ JSON-compatible

## Migration Path

### Phase 1: Add New Module (DONE)
- ✅ Create `risk_calculator.py`
- ✅ Add comprehensive tests
- ✅ Verify all edge cases

### Phase 2: Integrate with Engine
```python
# In autotrade_engine.py, replace current calculation with:

from app.risk_calculator import calculate_position_size

# Get balance from exchange
acc_info = client.get_account_info()
balance = acc_info["available"]

# Get user risk percentage
risk_pct = get_risk_per_trade(user_id) or 2.0

# Calculate position size
calc = calculate_position_size(
    last_balance=balance,
    risk_percentage=risk_pct,
    entry_price=entry,
    stop_loss_price=sl
)

if calc["status"] == "success":
    qty = calc["position_size"]
    # Round to exchange precision
    qty = round(qty, precision)
else:
    logger.error(f"Risk calc error: {calc['error_message']}")
    continue
```

### Phase 3: Deploy & Monitor
- Deploy to VPS
- Monitor calculations
- Verify risk amounts match expectations
- Collect user feedback

## Testing

Run comprehensive test suite:

```bash
python test_risk_calculator.py
```

All 8 tests should pass:
- ✅ Basic calculation
- ✅ Division by zero
- ✅ Missing input
- ✅ Negative balance
- ✅ 8-decimal precision
- ✅ SHORT position
- ✅ Position validation
- ✅ Real-world scenario

## API Reference

### calculate_position_size()

**Parameters:**
- `last_balance` (float): Current account balance
- `risk_percentage` (float): Risk per trade as percentage (e.g., 2.0 for 2%)
- `entry_price` (float): Entry price for the position
- `stop_loss_price` (float): Stop loss price

**Returns:** Dict with keys:
- `risk_amount` (float): Dollar amount at risk
- `position_size` (float): Calculated position size
- `currency_risk_percent` (float): Risk percentage (echoed back)
- `status` (str): "success" or "error"
- `error_message` (str|None): Error description if status is "error"

### validate_position_size()

**Parameters:**
- `position_size` (float): Calculated position size
- `min_size` (float): Minimum allowed size (default: 0.001)
- `max_size` (float): Maximum allowed size (default: 1000000.0)

**Returns:** Dict with keys:
- `valid` (bool): Whether size is within limits
- `adjusted_size` (float): Adjusted size if out of bounds
- `reason` (str|None): Reason if invalid

## Notes

- All calculations use 8-decimal precision
- Works for both LONG and SHORT positions (uses ABS for delta)
- No approximations or rounding until final exchange precision
- Fully deterministic - same inputs always produce same outputs
- Thread-safe (no shared state)

## Support

For questions or issues, check:
- Test suite: `test_risk_calculator.py`
- Module code: `Bismillah/app/risk_calculator.py`
- This documentation: `RISK_CALCULATOR_IMPLEMENTATION.md`
