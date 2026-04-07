# Risk Calculator - Ready to Deploy

## Status: ✅ READY FOR DEPLOYMENT

## Summary

Modul risk management deterministik telah selesai dibuat dan diuji. Modul ini **FULLY SUPPORTS MULTIPLE CONCURRENT POSITIONS** (max 4 posisi bersamaan).

## Pertanyaan User: "Berarti ini maximal hanya bisa 1 posisi saja di saat yang bersamaan ya?"

### Jawaban: TIDAK! ❌

Modul ini **DIRANCANG untuk multiple concurrent positions**:

- ✅ Setiap posisi dihitung independen dengan risk % yang sama
- ✅ Max concurrent positions: 4 (configurable di engine)
- ✅ Total risk exposure = risk_per_trade × jumlah_posisi_terbuka
- ✅ Contoh: 2% per trade × 4 posisi = 8% total exposure

### Contoh Real-World:

```
Balance: $1,000
Risk per trade: 2%
Max concurrent: 4 posisi

Posisi 1 (BTC): Entry $66,500, SL $65,500 → Risk $20, Size 0.02 BTC
Posisi 2 (ETH): Entry $3,200, SL $3,100 → Risk $20, Size 0.2 ETH
Posisi 3 (SOL): Entry $150, SL $145 → Risk $20, Size 4 SOL
Posisi 4 (BNB): Entry $580, SL $570 → Risk $20, Size 2 BNB

Total Risk Exposure: $80 (8% dari balance)
```

Lihat file `example_multiple_positions.py` untuk demo lengkap!

## Files Created

1. ✅ **`Bismillah/app/risk_calculator.py`** - Core module (deterministic, 8-decimal precision)
2. ✅ **`test_risk_calculator.py`** - Test suite (8 tests, all passing)
3. ✅ **`show_risk_examples.py`** - 9 practical scenarios
4. ✅ **`demo_risk_management.py`** - Interactive demo
5. ✅ **`example_multiple_positions.py`** - Multiple positions demo
6. ✅ **`RISK_CALCULATOR_IMPLEMENTATION.md`** - Full documentation
7. ✅ **`RISK_MANAGEMENT_EXAMPLES_SUMMARY.md`** - Examples summary

## Key Features

### 1. Deterministic Calculations
- No approximations or guesses
- Same inputs → same outputs (always)
- 8-decimal precision for all floats

### 2. Pure Risk-Based Formula
```python
Risk Amount = balance × (risk% / 100)
Price Delta = |entry - stop_loss|
Position Size = Risk Amount / Price Delta
```

### 3. Multiple Positions Support
- Each position calculated independently
- Same risk % for all positions
- Total exposure = risk% × number_of_positions

### 4. Strict Validation
- Division-by-zero protection
- Input validation (positive values)
- Error handling with clear messages

## Comparison: Old vs New

### Current System (position_sizing.py)
```python
# Uses leverage in calculation
position_size_usdt = risk_amount / sl_distance_pct
margin_required = position_size_usdt / leverage
qty = position_size_usdt / entry_price
```

**Issues:**
- Mixes leverage with risk calculation
- More complex (harder to verify)
- SL distance as percentage (less precise)

### New System (risk_calculator.py)
```python
# Pure risk calculation
risk_amount = balance * (risk_pct / 100)
price_delta = abs(entry - sl)
position_size = risk_amount / price_delta
```

**Advantages:**
- ✅ Simpler and more direct
- ✅ Easier to verify mathematically
- ✅ 8-decimal precision
- ✅ No leverage mixing
- ✅ Deterministic output

## Integration Plan

### Current Code (autotrade_engine.py line 815-838)
```python
from app.position_sizing import calculate_position_size
sizing = calculate_position_size(
    balance=balance,
    risk_pct=risk_pct,
    entry_price=entry,
    sl_price=sl,
    leverage=leverage,
    symbol=symbol
)

if not sizing['valid']:
    raise Exception(f"Position sizing invalid: {sizing['error']}")

qty = sizing['qty']
```

### New Code (with risk_calculator.py)
```python
from app.risk_calculator import calculate_position_size as calc_risk
from app.autotrade_engine import QTY_PRECISION

# Calculate position size using new risk calculator
calc = calc_risk(
    last_balance=balance,
    risk_percentage=risk_pct,
    entry_price=entry,
    stop_loss_price=sl
)

if calc['status'] != 'success':
    raise Exception(f"Risk calculation failed: {calc['error_message']}")

# Get quantity with proper precision
position_size = calc['position_size']
precision = QTY_PRECISION.get(symbol, 3)
qty = round(position_size, precision)

# Validate minimum quantity
min_qty = 10 ** (-precision) if precision > 0 else 1
if qty < min_qty:
    raise Exception(f"Quantity {qty} below minimum {min_qty}")

logger.info(
    f"[RiskCalc:{user_id}] {symbol} - "
    f"Balance=${balance:.2f}, Risk={risk_pct}%, "
    f"Entry=${entry:.2f}, SL=${sl:.2f}, "
    f"Risk_Amt=${calc['risk_amount']:.2f}, "
    f"Position_Size={position_size:.8f}, "
    f"Qty={qty}"
)
```

## Deployment Steps

### Option 1: Direct Replacement (Recommended)

1. **Deploy new module to VPS:**
```bash
scp Bismillah/app/risk_calculator.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
```

2. **Update autotrade_engine.py** (replace lines 815-838)

3. **Test on VPS:**
```bash
ssh root@147.93.156.165
cd /root/cryptomentor-bot
python3 -c "from Bismillah.app.risk_calculator import calculate_position_size; print(calculate_position_size(1000, 2, 66500, 65500))"
```

4. **Restart service:**
```bash
systemctl restart cryptomentor.service
```

### Option 2: Gradual Migration (Safer)

1. **Deploy new module alongside old one**
2. **Add feature flag in config**
3. **Test with select users first**
4. **Monitor for 24-48 hours**
5. **Roll out to all users**

## Testing Verification

All tests passing:
```bash
$ python test_risk_calculator.py

test_basic_calculation (__main__.TestRiskCalculator) ... ok
test_division_by_zero (__main__.TestRiskCalculator) ... ok
test_missing_input (__main__.TestRiskCalculator) ... ok
test_negative_balance (__main__.TestRiskCalculator) ... ok
test_precision_8_decimals (__main__.TestRiskCalculator) ... ok
test_short_position (__main__.TestRiskCalculator) ... ok
test_position_validation (__main__.TestRiskCalculator) ... ok
test_real_world_scenario (__main__.TestRiskCalculator) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.003s

OK
```

## Real-World Examples

### Example 1: Small Account
```python
calculate_position_size(
    last_balance=50.0,
    risk_percentage=1.0,
    entry_price=50000.0,
    stop_loss_price=49000.0
)
# Result: risk=$0.50, position=0.0005 BTC
```

### Example 2: Medium Account
```python
calculate_position_size(
    last_balance=500.0,
    risk_percentage=2.0,
    entry_price=3200.0,
    stop_loss_price=3300.0
)
# Result: risk=$10, position=0.1 ETH
```

### Example 3: Large Account
```python
calculate_position_size(
    last_balance=10000.0,
    risk_percentage=3.0,
    entry_price=150.0,
    stop_loss_price=145.0
)
# Result: risk=$300, position=60 SOL
```

## Multiple Positions Demo

Run this to see multiple positions in action:
```bash
python example_multiple_positions.py
```

Output shows:
- 4 concurrent positions with same risk %
- Total risk exposure calculation
- Progressive position opening
- Dynamic balance adjustment
- Mixed win/loss scenarios
- Risk allocation strategies

## Safety Features

### 1. Circuit Breaker (Already Active)
- Daily loss limit: 5%
- Verified working on VPS (see DAILY_LOSS_LIMIT_VERIFICATION.md)
- Triggered 7 times on March 31, 2026

### 2. Max Concurrent Positions
- Default: 4 positions
- Configurable in engine
- Prevents over-exposure

### 3. Input Validation
- All inputs must be positive
- Division-by-zero protection
- Clear error messages

### 4. Precision Control
- 8-decimal precision for calculations
- Exchange-specific rounding for orders
- Minimum quantity validation

## Risk Exposure Examples

### Conservative (1% per trade, max 4 positions)
- Risk per trade: 1%
- Max positions: 4
- Total exposure: 4%
- Survivability: 25+ consecutive losses

### Standard (2% per trade, max 4 positions)
- Risk per trade: 2%
- Max positions: 4
- Total exposure: 8%
- Survivability: 12+ consecutive losses

### Aggressive (3% per trade, max 4 positions)
- Risk per trade: 3%
- Max positions: 4
- Total exposure: 12%
- Survivability: 8+ consecutive losses

## Next Steps

### Waiting for Your Approval:

1. ✅ Module created and tested
2. ✅ Multiple positions support verified
3. ✅ Documentation complete
4. ⏳ **AWAITING DEPLOYMENT APPROVAL**

### After Approval:

1. Deploy `risk_calculator.py` to VPS
2. Update `autotrade_engine.py` integration
3. Restart service
4. Monitor first 24 hours
5. Verify calculations in production
6. Collect user feedback

## Questions?

- **Q: Apakah ini hanya 1 posisi?**
  - A: TIDAK! Mendukung 4 posisi bersamaan (configurable)

- **Q: Bagaimana dengan leverage?**
  - A: Leverage dihandle oleh exchange, modul ini fokus pada risk calculation

- **Q: Apakah balance update otomatis?**
  - A: Ya, setiap trade menggunakan balance terbaru dari exchange

- **Q: Bagaimana jika balance berubah?**
  - A: Position size menyesuaikan otomatis (risk % tetap konsisten)

## Ready to Deploy! 🚀

Modul ini:
- ✅ Mathematically sound
- ✅ Thoroughly tested
- ✅ Multiple positions support
- ✅ Well documented
- ✅ Production ready

**Menunggu approval untuk deployment ke VPS.**
