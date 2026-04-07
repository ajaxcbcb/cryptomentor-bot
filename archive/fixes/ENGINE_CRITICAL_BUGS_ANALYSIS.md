# Engine Critical Bugs - Root Cause Analysis

## Tanggal: 2026-04-05

## 🔴 Problem 1: Bot Tidak Auto-Close TP/Manual (Risk-Based Mode)

### Symptoms:
- User set risk-based mode
- Position hit TP tapi bot tidak close otomatis
- User harus close manual

### Root Cause Analysis:

**File:** `Bismillah/app/autotrade_engine.py` (Swing Mode)

```python
# Line 1000-1045: Logic monitoring position
# PROBLEM: Hanya check exchange position, tidak check mark_price vs TP/SL
```

**Current Logic:**
1. Bot fetch `open_positions` dari exchange
2. Jika position sudah tidak ada di exchange → assume closed
3. TIDAK ADA monitoring aktif mark_price vs TP/SL

**Why It Fails:**
- Exchange tidak punya limit TP/SL order (software-based monitoring)
- Bot hanya react ketika position sudah hilang dari exchange
- Tidak ada proactive checking: `if mark_price >= tp_price: close_position()`

### Solution:
Tambahkan monitoring loop seperti di scalping_engine:

```python
async def monitor_positions(self):
    for position in open_positions:
        mark_price = get_mark_price(position.symbol)
        
        # Check TP hit
        if position.side == "LONG" and mark_price >= position.tp_price:
            await close_position_tp(position)
        
        # Check SL hit
        if position.side == "LONG" and mark_price <= position.sl_price:
            await close_position_sl(position)
```

---

## 🔴 Problem 2: Bot Over-Leverage (Tidak Sesuai Risk Management)

### Symptoms:
- User set leverage 10x
- Bot auto-raise ke 50x tanpa consent
- Risk management jadi rusak

### Root Cause Analysis:

**File:** `Bismillah/app/scalping_engine.py` Line 767-812

```python
# Auto-leverage logic
if quantity_adjusted < min_qty:
    needed_leverage = int((min_qty / quantity_adjusted) * leverage) + 1
    needed_leverage = min(needed_leverage, MAX_AUTO_LEVERAGE)  # 50x!
    
    if needed_leverage > leverage:
        # PROBLEM: Langsung raise leverage tanpa validasi risk
        quantity_adjusted = quantity_adjusted * (needed_leverage / leverage)
        effective_leverage = needed_leverage
```

**Why It's Dangerous:**
1. User set 10x leverage untuk risk 2% per trade
2. Bot detect qty terlalu kecil (< min_qty)
3. Bot auto-raise ke 50x untuk meet min_qty
4. Risk per trade jadi 10% (5x lebih besar!)
5. User tidak aware leverage berubah

**Example:**
- Balance: $100
- Risk 2%: $2 per trade
- Leverage 10x: Position size $20
- Qty BTC: 0.0002 (< min 0.001)
- Bot raise to 50x: Position size $100
- Risk jadi 10%! (5x over-risk)

### Solution:
1. **NEVER auto-raise leverage** - Skip trade instead
2. Notify user: "Qty too small, increase balance or risk %"
3. Alternative: Use different pair with lower min_qty

```python
if quantity_adjusted < min_qty:
    logger.warning(
        f"[Scalping:{self.user_id}] {signal.symbol} qty={quantity_adjusted:.6f} "
        f"< min={min_qty}. Skipping trade to preserve risk management."
    )
    await self._notify_user(
        f"⚠️ Trade skipped: {signal.symbol}\n\n"
        f"Quantity too small ({quantity_adjusted:.6f} < {min_qty}).\n"
        f"To fix: Increase balance or risk % in settings."
    )
    return False  # Skip trade, DON'T raise leverage
```

---

## 🔴 Problem 3: Engine Selalu Aktif (Tidak Bisa Dimatikan)

### Symptoms:
- User click "Stop Engine"
- Engine tetap jalan
- Notifikasi terus masuk

### Root Cause Analysis:

**File:** `Bismillah/app/autotrade_engine.py` Line 698-703

```python
def stop_engine(user_id: int):
    t = _running_tasks.get(user_id)
    if t and not t.done():
        t.cancel()  # PROBLEM: Cancel task tapi loop tidak check cancellation
        logger.info(f"AutoTrade stopped for user {user_id}")
```

**File:** `Bismillah/app/autotrade_engine.py` Line 750+ (Main Loop)

```python
async def _trade_loop(...):
    while True:  # PROBLEM: Infinite loop tanpa check cancellation
        try:
            # ... trading logic ...
            await asyncio.sleep(60)
        except Exception as e:
            # ... error handling ...
            await asyncio.sleep(60)
    # NEVER checks if task.cancelled()!
```

**Why It Fails:**
1. `task.cancel()` hanya set cancellation flag
2. Loop tidak check `asyncio.current_task().cancelled()`
3. Loop continue forever sampai exception

**Scalping Engine (Working):**
```python
async def run(self):
    self.running = True
    while self.running:  # ✅ Check flag
        # ... trading logic ...
    
def stop(self):
    self.running = False  # ✅ Set flag
```

### Solution:
Add cancellation check in main loop:

```python
async def _trade_loop(...):
    while True:
        try:
            # Check if task cancelled
            if asyncio.current_task().cancelled():
                logger.info(f"[Engine:{user_id}] Task cancelled, exiting loop")
                break
            
            # ... trading logic ...
            await asyncio.sleep(60)
            
        except asyncio.CancelledError:
            logger.info(f"[Engine:{user_id}] CancelledError caught, exiting")
            break
        except Exception as e:
            # ... error handling ...
```

---

## 📊 Impact Assessment

### Problem 1 (No Auto-Close TP/Manual)
- **Severity:** HIGH
- **Impact:** User miss TP, position reverse, loss instead of profit
- **Affected:** All swing mode users with risk-based mode
- **Frequency:** Every trade

### Problem 2 (Over-Leverage)
- **Severity:** CRITICAL
- **Impact:** 5x over-risk, potential account blow-up
- **Affected:** Scalping mode users with small balance
- **Frequency:** ~30% of trades (when qty < min_qty)

### Problem 3 (Engine Won't Stop)
- **Severity:** MEDIUM
- **Impact:** User frustration, unwanted trades
- **Affected:** All users trying to stop engine
- **Frequency:** Every stop attempt

---

## 🔧 Fix Priority

1. **CRITICAL:** Problem 2 (Over-Leverage) - Can blow accounts
2. **HIGH:** Problem 1 (No Auto-Close) - Miss profits
3. **MEDIUM:** Problem 3 (Won't Stop) - UX issue

---

## 📝 Implementation Plan

### Fix 1: Add TP/SL Monitoring to Swing Mode
**File:** `Bismillah/app/autotrade_engine.py`
**Changes:**
- Add `monitor_positions()` method
- Check mark_price vs TP/SL every cycle
- Close position when hit

### Fix 2: Remove Auto-Leverage
**File:** `Bismillah/app/scalping_engine.py`
**Changes:**
- Remove auto-leverage logic (line 781-812)
- Skip trade if qty < min_qty
- Notify user to increase balance/risk

### Fix 3: Add Cancellation Check
**File:** `Bismillah/app/autotrade_engine.py`
**Changes:**
- Add `asyncio.CancelledError` handler
- Check `asyncio.current_task().cancelled()` in loop
- Clean exit on cancellation

---

## ✅ Testing Checklist

### Problem 1 Fix:
- [ ] Position hit TP → auto-close
- [ ] Position hit SL → auto-close
- [ ] Notification sent on close
- [ ] PnL calculated correctly

### Problem 2 Fix:
- [ ] Qty < min_qty → trade skipped
- [ ] No leverage auto-raise
- [ ] User notified about skip
- [ ] Risk management preserved

### Problem 3 Fix:
- [ ] Stop button → engine stops
- [ ] No more notifications after stop
- [ ] Clean task cancellation
- [ ] Can restart after stop

---

**Status:** Analysis Complete - Ready for Implementation
**Next Step:** Implement fixes in order of priority
