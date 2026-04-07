# StackMentor Integration Guide

## Changes needed in `Bismillah/app/autotrade_engine.py`

### 1. Add Import (at top of file, after other imports)

```python
from app.stackmentor import (
    STACKMENTOR_CONFIG,
    calculate_stackmentor_levels,
    calculate_qty_splits,
    register_stackmentor_position,
    monitor_stackmentor_positions,
)
```

### 2. Update ENGINE_CONFIG (around line 30)

Replace the old dual TP config with StackMentor:

```python
# OLD (remove these lines):
"atr_tp1_multiplier": 4.0,      # TP1 = 4.0x ATR → R:R 1:2
"atr_tp2_multiplier": 6.0,      # TP2 = 6.0x ATR → R:R 1:3
"tp1_close_pct":      0.75,     # tutup 75% posisi di TP1

# NEW (add these lines):
"use_stackmentor":    True,     # Enable StackMentor for all users
"atr_tp_multiplier":  2.0,      # Base TP multiplier (StackMentor will calculate 3 levels)
```

### 3. Modify Order Placement Logic (around line 1220-1250)

Find the section where orders are placed. Replace TP/SL calculation:

```python
# OLD CODE (find and replace):
tp1 = sig['tp1']
tp2 = sig['tp2']
sl  = sig['sl']

# NEW CODE:
if cfg.get("use_stackmentor", True):
    # StackMentor: Calculate 3-tier TP
    tp1, tp2, tp3 = calculate_stackmentor_levels(
        entry_price=entry,
        sl_price=sl,
        side=side
    )
    
    # Calculate qty splits
    qty_tp1, qty_tp2, qty_tp3 = calculate_qty_splits(qty, precision)
    
    logger.info(
        f"[StackMentor:{user_id}] {symbol} {side} — "
        f"TP1={tp1:.4f}(50%) TP2={tp2:.4f}(40%) TP3={tp3:.4f}(10%)"
    )
else:
    # Legacy: Use signal TP
    tp1 = sig['tp1']
    tp2 = sig.get('tp2', tp1)
    tp3 = tp1
    qty_tp1 = qty
    qty_tp2 = 0
    qty_tp3 = 0
```

### 4. Update Order Placement Call (around line 1260)

```python
# Place order with TP1 as primary TP (exchange handles TP1)
# TP2 and TP3 will be monitored by StackMentor
order_result = await asyncio.to_thread(
    client.place_order_with_tpsl, symbol,
    "BUY" if side == "LONG" else "SELL",
    qty, tp1, sl  # Use TP1 as primary TP
)
```

### 5. Register StackMentor Position After Order Success (around line 1280)

```python
if order_result.get('success'):
    # ... existing success code ...
    
    # Register with StackMentor for monitoring
    if cfg.get("use_stackmentor", True):
        register_stackmentor_position(
            user_id=user_id,
            symbol=symbol,
            entry_price=entry,
            sl_price=sl,
            tp1=tp1,
            tp2=tp2,
            tp3=tp3,
            total_qty=qty,
            qty_tp1=qty_tp1,
            qty_tp2=qty_tp2,
            qty_tp3=qty_tp3,
            side=side,
            leverage=leverage
        )
    
    # ... rest of success code ...
```

### 6. Add StackMentor Monitor to Main Loop (around line 820, in _trade_loop)

Find the main while loop and add StackMentor monitoring:

```python
while True:
    try:
        # ... existing code ...
        
        # ── StackMentor Monitor: Check TP2/TP3 hits ──────────────
        if cfg.get("use_stackmentor", True):
            try:
                await monitor_stackmentor_positions(
                    bot=bot,
                    user_id=user_id,
                    client=client,
                    notify_chat_id=notify_chat_id
                )
            except Exception as _sm_err:
                logger.warning(f"[StackMentor:{user_id}] Monitor error: {_sm_err}")
        
        # ... rest of loop ...
```

### 7. Update Trade History Save (around line 1300)

When saving trade to database, include StackMentor fields:

```python
# In save_trade_open() call, add:
save_trade_open(
    telegram_id=user_id,
    symbol=symbol,
    side=side,
    entry_price=entry,
    qty=qty,
    leverage=leverage,
    tp_price=tp1,      # Primary TP
    sl_price=sl,
    signal=sig,
    order_id=order_result.get("order_id", ""),
    # StackMentor fields:
    tp1_price=tp1,
    tp2_price=tp2,
    tp3_price=tp3,
    qty_tp1=qty_tp1,
    qty_tp2=qty_tp2,
    qty_tp3=qty_tp3,
    strategy="stackmentor" if cfg.get("use_stackmentor") else "legacy",
)
```

### 8. Update trade_history.py save_trade_open()

Add StackMentor parameters to the function signature and INSERT:

```python
def save_trade_open(
    telegram_id: int,
    symbol: str,
    side: str,
    entry_price: float,
    qty: float,
    leverage: int,
    tp_price: float,
    sl_price: float,
    signal: Dict,
    order_id: str = "",
    is_flip: bool = False,
    # StackMentor fields:
    tp1_price: float = None,
    tp2_price: float = None,
    tp3_price: float = None,
    qty_tp1: float = None,
    qty_tp2: float = None,
    qty_tp3: float = None,
    strategy: str = "stackmentor",
):
    # ... existing code ...
    
    # Add to INSERT:
    s.table("autotrade_trades").insert({
        # ... existing fields ...
        "tp1_price": tp1_price,
        "tp2_price": tp2_price,
        "tp3_price": tp3_price,
        "qty_tp1": qty_tp1,
        "qty_tp2": qty_tp2,
        "qty_tp3": qty_tp3,
        "strategy": strategy,
        # ... rest of fields ...
    }).execute()
```

---

## Summary of Changes

1. ✅ Import StackMentor module
2. ✅ Update ENGINE_CONFIG
3. ✅ Calculate 3-tier TP levels on entry
4. ✅ Split quantity 50/40/10
5. ✅ Register position with StackMentor
6. ✅ Add monitor loop for TP2/TP3
7. ✅ Update database saves
8. ✅ Update trade_history.py

---

## Testing Checklist

- [ ] Database migration applied
- [ ] Code changes integrated
- [ ] Test with small position ($10)
- [ ] Verify TP1 triggers breakeven
- [ ] Verify TP2 closes 40%
- [ ] Verify TP3 closes final 10%
- [ ] Check notifications
- [ ] Monitor logs for errors
- [ ] Deploy to VPS

---

## Rollback Plan

If issues occur:

1. Set `use_stackmentor: False` in ENGINE_CONFIG
2. System will fall back to legacy TP behavior
3. Existing StackMentor positions will still be monitored
4. New positions will use old system

---

**Next Step**: Apply these changes to autotrade_engine.py
