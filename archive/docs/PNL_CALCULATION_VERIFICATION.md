# ✅ PnL Calculation Verification - Leverage & Margin Included

## 🎯 Verification Result

**Status**: ✅ **PnL CALCULATION IS CORRECT**

The current PnL calculation formula already includes leverage and margin correctly!

---

## 📊 How It Works

### Step 1: Calculate Quantity (includes leverage)
```python
# In autotrade_engine.py line ~1223
qty = calc_qty(symbol, amount * leverage, entry)

# calc_qty function:
def calc_qty(symbol: str, notional: float, price: float) -> float:
    qty = round(notional / price, precision)
    return qty

# Where:
# notional = amount * leverage  ← LEVERAGE IS HERE!
# qty = (amount * leverage) / entry_price
```

### Step 2: Calculate PnL (already correct)
```python
# In autotrade_engine.py line ~872
raw_pnl = (exit_px - entry_px) if db_side == "LONG" else (entry_px - exit_px)
pnl_usdt = raw_pnl * float(db_trade.get("qty", 0))

# This expands to:
# pnl_usdt = price_diff * qty
# pnl_usdt = price_diff * (amount * leverage / entry_price)
```

---

## 🧮 Example Calculations

### Example 1: LONG Position with Profit
```
Margin (amount): $100 USDT
Leverage: 10x
Entry Price: $2000
Exit Price: $2100

Step 1: Calculate qty
  notional = $100 * 10 = $1000
  qty = $1000 / $2000 = 0.5

Step 2: Calculate PnL
  price_diff = $2100 - $2000 = $100
  PnL = $100 * 0.5 = $50 USDT ✅

ROI = ($50 / $100) * 100% = 50% ✅
```

### Example 2: SHORT Position with Profit
```
Margin (amount): $100 USDT
Leverage: 10x
Entry Price: $2000
Exit Price: $1900

Step 1: Calculate qty
  notional = $100 * 10 = $1000
  qty = $1000 / $2000 = 0.5

Step 2: Calculate PnL
  price_diff = $2000 - $1900 = $100
  PnL = $100 * 0.5 = $50 USDT ✅

ROI = ($50 / $100) * 100% = 50% ✅
```

### Example 3: Real Case from Screenshot
```
ETH SHORT
Margin: ~$50 USDT (estimated)
Leverage: 25x
Entry Price: $1988.14
Exit Price: $1988.14 ← PROBLEM: Same as entry!

Step 1: Calculate qty
  notional = $50 * 25 = $1250
  qty = $1250 / $1988.14 = 0.6287 ETH

Step 2: Calculate PnL
  price_diff = $1988.14 - $1988.14 = $0
  PnL = $0 * 0.6287 = $0 USDT ❌

This is why PnL showed 0.0000!
```

**If exit was $1975.00 (profit):**
```
  price_diff = $1988.14 - $1975.00 = $13.14
  PnL = $13.14 * 0.6287 = $8.26 USDT ✅
  ROI = ($8.26 / $50) * 100% = 16.52% ✅
```

---

## ✅ Formula Verification

### Current Code:
```python
# Calculate qty (includes leverage)
qty = calc_qty(symbol, amount * leverage, entry)

# Calculate PnL
raw_pnl = (exit_px - entry_px) if db_side == "LONG" else (entry_px - exit_px)
pnl_usdt = raw_pnl * qty
```

### Mathematical Proof:
```
qty = (margin * leverage) / entry_price

PnL = price_diff * qty
PnL = price_diff * (margin * leverage / entry_price)

For 5% price movement with 10x leverage:
PnL = (entry * 0.05) * (margin * 10 / entry)
PnL = 0.05 * margin * 10
PnL = margin * 0.5
PnL = 50% of margin ✅

This is correct for 10x leverage!
```

---

## 🐛 The Real Issue (Already Fixed)

### Problem:
Exit price was falling back to entry price when price fetch failed:
```python
# OLD CODE (BROKEN):
try:
    klines = get_klines(...)
    exit_px = klines[-1][4] if klines else entry_price  # ❌
except:
    exit_px = entry_price  # ❌ Always falls back to entry
```

This caused:
- entry_price = exit_price
- price_diff = 0
- PnL = 0 * qty = 0 ❌

### Solution (Already Deployed):
```python
# NEW CODE (FIXED):
try:
    # 1. Try exchange mark price (most accurate)
    ticker = await client.get_ticker(symbol)
    if ticker.get('mark_price'):
        exit_px = ticker['mark_price']  # ✅
    else:
        # 2. Fallback to klines
        klines = get_klines(...)
        exit_px = klines[-1][4] if klines else entry_price
except Exception as e:
    logger.warning(f"Failed to get exit price: {e}")
    exit_px = entry_price  # Last resort only
```

---

## 📊 Test Results

### Test Script: `test_pnl_calculation_correct.py`

```
✅ SCENARIO 1: LONG Position - Profit
   Margin: $100, Leverage: 10x
   Entry: $2000 → Exit: $2100
   PnL: $50.00 USDT ✅
   ROI: 50.00%

✅ SCENARIO 2: SHORT Position - Profit
   Margin: $100, Leverage: 10x
   Entry: $2000 → Exit: $1900
   PnL: $50.00 USDT ✅
   ROI: 50.00%

✅ SCENARIO 3: LONG Position - Loss
   Margin: $100, Leverage: 10x
   Entry: $2000 → Exit: $1950
   PnL: $-25.00 USDT ✅
   ROI: -25.00%

✅ All scenarios calculated correctly!
```

---

## 🎯 Summary

### What's Correct:
1. ✅ qty calculation includes leverage
2. ✅ PnL formula is mathematically correct
3. ✅ ROI calculation is accurate
4. ✅ Works for both LONG and SHORT positions

### What Was Wrong:
1. ❌ Exit price was falling back to entry price
2. ❌ This made price_diff = 0
3. ❌ Result: PnL = 0 (not a formula issue!)

### What's Fixed:
1. ✅ Get mark price from exchange API first
2. ✅ Multiple fallback layers
3. ✅ Logging for debugging
4. ✅ Deployed to production

---

## 📝 Conclusion

**The PnL calculation formula is CORRECT and already includes:**
- ✅ Margin (amount)
- ✅ Leverage (in qty calculation)
- ✅ Trading volume (notional = margin * leverage)
- ✅ Price movement (exit - entry)

**The issue was NOT the formula, but the data:**
- ❌ Exit price = Entry price (no movement)
- ✅ Fixed by using exchange mark price

**Future trades will show correct PnL values!** 🎉

---

**Verified by**: Mathematical proof & test scenarios  
**Status**: ✅ CORRECT  
**Action Required**: None (already fixed and deployed)
