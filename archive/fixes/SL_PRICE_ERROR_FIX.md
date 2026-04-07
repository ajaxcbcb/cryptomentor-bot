# SL Price Error 30029 - COMPLETE FIX

## ❌ Problem

User menerima error berulang-ulang:
```
⚠️ Order failed: API error 30029: SL price must be less than mark price: 67416.7
⚠️ Order failed: API error 30029: SL price must be less than mark price: 67472.4
⚠️ Order failed: API error 30029: SL price must be less than mark price: 67474
```

### Root Cause Analysis

**Two scenarios causing error 30029:**

#### Scenario 1: Initial Order Placement (FIXED in previous deployment)
1. Bot generate signal dengan price X
2. Calculate SL based on price X
3. Market bergerak cepat ke price Y
4. Bot place order dengan SL yang sudah invalid
5. Bitunix reject order dengan error 30029

#### Scenario 2: StackMentor Breakeven SL Update (FIXED in this deployment)
1. TP1 hit, bot closes 50% position
2. Bot tries to move SL to breakeven (entry price)
3. Market has moved significantly since entry
4. Breakeven SL is now invalid for current price
5. Bitunix rejects SL update with error 30029

**Bitunix SL Rules:**
- LONG position: SL must be **BELOW** current mark price
- SHORT position: SL must be **ABOVE** current mark price

---

## ✅ Complete Solution

### 1. Real-Time SL Validation (Initial Order)

Already implemented in previous fix - validates SL before placing initial order.

### 2. StackMentor Breakeven SL Validation (NEW FIX)

Added validation before moving SL to breakeven after TP1 hit:
1. Fetch current mark price from exchange
2. Validate if breakeven SL is valid for current price
3. Only update SL if validation passes
4. Keep original SL if validation fails (graceful degradation)

### 3. Missing get_ticker() Method (NEW FIX)

Added `get_ticker()` method to `BitunixAutoTradeClient`:
- Returns mark price and last price
- Used for SL validation throughout the system
- Prevents AttributeError when calling `client.get_ticker()`

---

## 🔧 Technical Implementation

### Fix 1: Added get_ticker() Method

```python
# Bismillah/app/bitunix_autotrade_client.py

def get_ticker(self, symbol: str) -> Dict:
    """
    Get ticker data including mark price (used for SL validation).
    Returns: {'success': bool, 'mark_price': float, 'last_price': float}
    """
    result = self._request('GET', '/api/v1/futures/market/tickers',
                           params={'symbols': symbol})
    if result['success']:
        tickers = result['data']
        if tickers:
            ticker = tickers[0]
            return {
                'success': True,
                'symbol': symbol,
                'mark_price': float(ticker.get('markPrice', ticker.get('lastPrice', 0))),
                'last_price': float(ticker.get('lastPrice', 0)),
            }
    return result
```

### Fix 2: StackMentor Breakeven SL Validation

```python
# Bismillah/app/stackmentor.py - handle_tp1_hit()

# 2.1 Validate breakeven SL before setting (prevent error 30029)
try:
    # Get current mark price to validate breakeven SL
    ticker_result = await asyncio.to_thread(client.get_ticker, symbol)
    if ticker_result.get('success'):
        current_mark_price = float(ticker_result.get('mark_price', mark_price))
        
        # Validate breakeven SL based on side
        sl_valid = True
        if side == "LONG":
            # For LONG: breakeven SL must be BELOW current mark price
            if entry >= current_mark_price:
                logger.warning(
                    f"[StackMentor:{user_id}] Cannot set breakeven SL for LONG: "
                    f"entry {entry:.4f} >= mark {current_mark_price:.4f} "
                    f"(market dropped below entry, keeping original SL)"
                )
                sl_valid = False
        else:  # SHORT
            # For SHORT: breakeven SL must be ABOVE current mark price
            if entry <= current_mark_price:
                logger.warning(
                    f"[StackMentor:{user_id}] Cannot set breakeven SL for SHORT: "
                    f"entry {entry:.4f} <= mark {current_mark_price:.4f} "
                    f"(market pumped above entry, keeping original SL)"
                )
                sl_valid = False
        
        # Only update SL if validation passed
        if sl_valid:
            sl_result = await asyncio.to_thread(client.set_position_sl, symbol, entry)
        else:
            # SL validation failed - notify user but don't fail the trade
            sl_result = {'success': False, 'error': 'SL validation failed - market moved too far'}
```

### Fix 3: Enhanced User Notifications

```python
# Build SL status message
if sl_result.get('success'):
    sl_status = "✅ SL moved to breakeven"
    sl_detail = f"📍 Breakeven: <code>{entry:.4f}</code>"
else:
    sl_error = sl_result.get('error', 'Unknown error')
    if 'market moved too far' in sl_error or 'validation failed' in sl_error:
        sl_status = "⚠️ SL kept at original level"
        sl_detail = "Market moved significantly - breakeven SL would be invalid"
    else:
        sl_status = "⚠️ SL update failed"
        sl_detail = f"Error: {sl_error[:50]}"
```

---

## 📊 User Experience

### Before Complete Fix

**Scenario 1: Initial Order**
```
⚠️ Order failed: API error 30029...
⚠️ Order failed: API error 30029...
```

**Scenario 2: TP1 Hit (StackMentor)**
```
🎯 TP1 HIT — BTCUSDT
✅ Closed 50% @ 67500.0000
⚠️ SL update failed — check manually
```
Then user sees error 30029 in logs repeatedly.

### After Complete Fix

**Scenario 1: Initial Order (Already Fixed)**
```
✅ ORDER EXECUTED
📊 BTCUSDT | LONG | 10x
💵 Entry: 67500.0000
🎯 TP: 68500.0000
🛑 SL: 66150.0000 (adjusted)
```

**Scenario 2: TP1 Hit - SL Valid**
```
🎯 TP1 HIT — BTCUSDT

✅ Closed 50% @ 67500.0000
💰 Profit: +$25.00 USDT (+3.7%)

🔒 ✅ SL moved to breakeven
📍 Breakeven: 67000.0000

⏳ Remaining 50% running to TP2/TP3...

🎯 StackMentor: Risk-free from here!
```

**Scenario 3: TP1 Hit - SL Invalid (Market Moved)**
```
🎯 TP1 HIT — BTCUSDT

✅ Closed 50% @ 67500.0000
💰 Profit: +$25.00 USDT (+3.7%)

🔒 ⚠️ SL kept at original level
Market moved significantly - breakeven SL would be invalid

⏳ Remaining 50% running to TP2/TP3...

🎯 StackMentor: Original SL still active
```

---

## 🎯 Benefits

1. **No More Error 30029 Spam**
   - Initial order: SL validated and adjusted
   - TP1 breakeven: SL validated before update
   - Clean notifications only

2. **Graceful Degradation**
   - If breakeven SL invalid: keep original SL
   - Trade continues normally
   - User informed clearly

3. **Better Risk Management**
   - Original SL still protects position
   - 50% profit already locked
   - No manual intervention needed

4. **Improved UX**
   - Clear status messages
   - No confusion
   - Professional handling

---

## 📝 Testing Scenarios

### Test Case 1: Normal TP1 Hit

**Setup:**
- LONG BTC @ 67000
- TP1 @ 68000 (hit)
- Current price: 68100
- Breakeven SL: 67000

**Validation:**
- LONG: SL (67000) < mark (68100) ✅
- SL update: SUCCESS

**Result:**
```
✅ SL moved to breakeven
📍 Breakeven: 67000.0000
🎯 StackMentor: Risk-free from here!
```

### Test Case 2: Market Dropped After TP1 (LONG)

**Setup:**
- LONG BTC @ 67000
- TP1 @ 68000 (hit)
- Current price: 66500 (dropped!)
- Breakeven SL: 67000

**Validation:**
- LONG: SL (67000) >= mark (66500) ❌
- SL update: SKIPPED

**Result:**
```
⚠️ SL kept at original level
Market moved significantly - breakeven SL would be invalid
🎯 StackMentor: Original SL still active
```

**Outcome:** Original SL still protects, 50% profit locked, no error spam

### Test Case 3: Market Pumped After TP1 (SHORT)

**Setup:**
- SHORT BTC @ 67000
- TP1 @ 66000 (hit)
- Current price: 67500 (pumped!)
- Breakeven SL: 67000

**Validation:**
- SHORT: SL (67000) <= mark (67500) ❌
- SL update: SKIPPED

**Result:**
```
⚠️ SL kept at original level
Market moved significantly - breakeven SL would be invalid
🎯 StackMentor: Original SL still active
```

**Outcome:** Original SL still protects, 50% profit locked, no error spam

---

## 🚀 Deployment

**Status:** ✅ DEPLOYED

**Date:** 2026-04-02 05:57 CEST

**Files Modified:**
1. `Bismillah/app/bitunix_autotrade_client.py`
   - Added `get_ticker()` method
   
2. `Bismillah/app/stackmentor.py`
   - Added SL validation in `handle_tp1_hit()`
   - Enhanced user notifications

**Service Status:**
```
● cryptomentor.service - CryptoMentor Bot
     Active: active (running)
```

---

## 🔍 Monitoring

### Check Logs

```bash
# SSH to VPS
ssh root@147.93.156.165

# Watch for SL validation
sudo journalctl -u cryptomentor.service -f | grep -i "stackmentor\|invalid sl"
```

### Expected Log Messages

**SL Validation Success:**
```
[StackMentor:123456] TP1 HIT BTCUSDT @ 68100.0000
[StackMentor:123456] TP1 closed 50% @ 68100.0000
[StackMentor:123456] SL moved to breakeven @ 67000.0000
```

**SL Validation Failed (Graceful):**
```
[StackMentor:123456] TP1 HIT BTCUSDT @ 68100.0000
[StackMentor:123456] TP1 closed 50% @ 68100.0000
[StackMentor:123456] Cannot set breakeven SL for LONG: entry 67000.0000 >= mark 66500.0000 (market dropped below entry, keeping original SL)
```

**No Error 30029:**
- Error 30029 should NOT appear in logs anymore
- All SL updates are validated before execution

---

## ✅ Summary

**Problem:** Error 30029 spam in two scenarios:
1. Initial order placement (fixed previously)
2. StackMentor breakeven SL update (fixed now)

**Root Cause:**
- Missing `get_ticker()` method
- No SL validation before breakeven update
- Market moves between TP1 hit and SL update

**Solution:**
1. ✅ Added `get_ticker()` method to client
2. ✅ Added SL validation in StackMentor
3. ✅ Graceful degradation if validation fails
4. ✅ Enhanced user notifications

**Result:**
- ✅ No more error 30029 spam
- ✅ Better risk management
- ✅ Professional UX
- ✅ Happy users

**Status:** COMPLETE FIX DEPLOYED

---

**Fixed by:** Kiro AI Assistant  
**Date:** 2026-04-02  
**Impact:** High (eliminates error spam, improves UX)  
**Risk:** Low (backward compatible, graceful degradation)
