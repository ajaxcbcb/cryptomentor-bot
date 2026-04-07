# 🎯 StackMentor System - Advanced 3-Tier TP Strategy

**System Name**: StackMentor  
**Target**: All users (default strategy)  
**Goal**: Maximize trading volume + Secure profits with breakeven protection

---

## 📊 Strategy Overview

### 3-Tier Take Profit System:

| Tier | Position % | R:R Ratio | Action |
|------|-----------|-----------|--------|
| TP1 | 50% | 1:2 | Close 50%, Move SL to Breakeven |
| TP2 | 40% | 1:3 | Close 40%, Keep SL at Breakeven |
| TP3 | 10% | 1:10 | Close 10%, Ride the trend |

### Key Features:

1. **Breakeven Protection**: SL moves to entry after TP1 hit
2. **Profit Stacking**: Secure profits incrementally
3. **Trend Riding**: Keep 10% for massive gains
4. **Volume Boost**: More trades = more volume for owner

---

## 🔧 Technical Implementation

### Entry Calculation:

```python
# Example: Entry at $100, SL at $98 (2% risk)
entry_price = 100.0
sl_distance = 2.0  # $2 risk

# Calculate TP levels
tp1 = entry_price + (sl_distance * 2)   # $104 (R:R 1:2)
tp2 = entry_price + (sl_distance * 3)   # $106 (R:R 1:3)
tp3 = entry_price + (sl_distance * 10)  # $120 (R:R 1:10)
```

### Position Sizing:

```python
total_qty = 1.0  # Example: 1 BTC

# Split into 3 tiers
qty_tp1 = total_qty * 0.50  # 0.5 BTC (50%)
qty_tp2 = total_qty * 0.40  # 0.4 BTC (40%)
qty_tp3 = total_qty * 0.10  # 0.1 BTC (10%)
```

### Breakeven Logic:

```python
# When TP1 is hit:
if mark_price >= tp1:
    # 1. Close 50% position
    close_partial(qty_tp1)
    
    # 2. Move SL to breakeven (entry price)
    update_sl(entry_price)
    
    # 3. Mark position as "breakeven mode"
    position_status = "breakeven"
```

---

## 🎯 Exchange API Requirements

### Check: Can Bot Control SL After Entry?

**Bitunix API Capabilities**:

1. ✅ **Place order with TP/SL**: `place_order_with_tpsl()`
2. ✅ **Update SL**: `set_position_sl(symbol, new_sl_price)`
3. ✅ **Partial close**: `close_partial(symbol, side, qty)`
4. ✅ **Get position info**: `get_positions()`

**Answer**: ✅ **YES, bot can control SL dynamically**

---

## 📋 Implementation Steps

### Step 1: Update Engine Config

```python
STACKMENTOR_CONFIG = {
    "enabled": True,  # Enable for all users
    "tp1_pct": 0.50,  # 50% at TP1
    "tp2_pct": 0.40,  # 40% at TP2
    "tp3_pct": 0.10,  # 10% at TP3
    "tp1_rr": 2.0,    # R:R 1:2
    "tp2_rr": 3.0,    # R:R 1:3
    "tp3_rr": 10.0,   # R:R 1:10
    "breakeven_after_tp1": True,
}
```

### Step 2: Order Placement

```python
# Calculate all TP levels
tp1 = entry + (sl_dist * 2)
tp2 = entry + (sl_dist * 3)
tp3 = entry + (sl_dist * 10)

# Place order with TP1 as primary TP
# (TP2 and TP3 will be monitored by bot)
result = client.place_order_with_tpsl(
    symbol=symbol,
    side="BUY",
    qty=total_qty,
    tp_price=tp1,  # Exchange handles TP1
    sl_price=sl_price
)
```

### Step 3: TP Monitor Loop

```python
async def monitor_stackmentor_positions(bot, user_id, client):
    """Monitor positions for TP2/TP3 hits and breakeven"""
    
    positions = await client.get_positions()
    
    for pos in positions:
        symbol = pos['symbol']
        mark_price = pos['mark_price']
        
        # Get position data from DB
        db_pos = get_position_from_db(user_id, symbol)
        
        # Check TP1 hit (breakeven trigger)
        if not db_pos['tp1_hit'] and mark_price >= db_pos['tp1']:
            await handle_tp1_hit(bot, user_id, client, pos, db_pos)
        
        # Check TP2 hit
        elif db_pos['tp1_hit'] and not db_pos['tp2_hit'] and mark_price >= db_pos['tp2']:
            await handle_tp2_hit(bot, user_id, client, pos, db_pos)
        
        # Check TP3 hit
        elif db_pos['tp2_hit'] and not db_pos['tp3_hit'] and mark_price >= db_pos['tp3']:
            await handle_tp3_hit(bot, user_id, client, pos, db_pos)
```

### Step 4: TP1 Handler (Breakeven)

```python
async def handle_tp1_hit(bot, user_id, client, pos, db_pos):
    """
    TP1 Hit: Close 50%, Move SL to Breakeven
    """
    symbol = db_pos['symbol']
    entry = db_pos['entry_price']
    qty_total = db_pos['qty']
    qty_tp1 = qty_total * 0.50
    
    # 1. Close 50% position
    close_result = await client.close_partial(
        symbol=symbol,
        side="SELL" if db_pos['side'] == "LONG" else "BUY",
        qty=qty_tp1
    )
    
    if not close_result['success']:
        logger.error(f"TP1 partial close failed: {close_result['error']}")
        return
    
    # 2. Move SL to breakeven
    sl_result = await client.set_position_sl(symbol, entry)
    
    # 3. Update DB
    update_position_db(user_id, symbol, {
        'tp1_hit': True,
        'tp1_hit_at': datetime.utcnow(),
        'qty_remaining': qty_total * 0.50,
        'sl_price': entry,  # Now at breakeven
        'status': 'breakeven'
    })
    
    # 4. Notify user
    profit_tp1 = (db_pos['tp1'] - entry) * qty_tp1
    await bot.send_message(
        chat_id=user_id,
        text=(
            f"🎯 <b>TP1 HIT — {symbol}</b>\n\n"
            f"✅ Closed 50% @ <code>{db_pos['tp1']:.4f}</code>\n"
            f"💰 Profit: +${profit_tp1:.2f} USDT\n\n"
            f"🔒 <b>SL moved to BREAKEVEN</b>\n"
            f"📍 Breakeven: <code>{entry:.4f}</code>\n\n"
            f"⏳ Remaining 50% running to TP2/TP3...\n"
            f"{'✅ SL updated' if sl_result['success'] else '⚠️ SL update failed'}"
        ),
        parse_mode='HTML'
    )
```

### Step 5: TP2 Handler

```python
async def handle_tp2_hit(bot, user_id, client, pos, db_pos):
    """
    TP2 Hit: Close 40% of ORIGINAL position (80% of remaining)
    """
    symbol = db_pos['symbol']
    qty_total = db_pos['qty']
    qty_tp2 = qty_total * 0.40  # 40% of original
    
    # Close 40%
    close_result = await client.close_partial(
        symbol=symbol,
        side="SELL" if db_pos['side'] == "LONG" else "BUY",
        qty=qty_tp2
    )
    
    # Update DB
    update_position_db(user_id, symbol, {
        'tp2_hit': True,
        'tp2_hit_at': datetime.utcnow(),
        'qty_remaining': qty_total * 0.10,  # Only 10% left
    })
    
    # Notify
    profit_tp2 = (db_pos['tp2'] - db_pos['entry_price']) * qty_tp2
    await bot.send_message(
        chat_id=user_id,
        text=(
            f"🎯 <b>TP2 HIT — {symbol}</b>\n\n"
            f"✅ Closed 40% @ <code>{db_pos['tp2']:.4f}</code>\n"
            f"💰 Profit: +${profit_tp2:.2f} USDT\n\n"
            f"🔒 SL still at breakeven\n"
            f"⏳ Final 10% running to TP3 (R:R 1:10)..."
        ),
        parse_mode='HTML'
    )
```

### Step 6: TP3 Handler

```python
async def handle_tp3_hit(bot, user_id, client, pos, db_pos):
    """
    TP3 Hit: Close final 10% - JACKPOT!
    """
    symbol = db_pos['symbol']
    qty_total = db_pos['qty']
    qty_tp3 = qty_total * 0.10
    
    # Close final 10%
    close_result = await client.close_partial(
        symbol=symbol,
        side="SELL" if db_pos['side'] == "LONG" else "BUY",
        qty=qty_tp3
    )
    
    # Calculate total profit
    entry = db_pos['entry_price']
    total_profit = (
        (db_pos['tp1'] - entry) * (qty_total * 0.50) +
        (db_pos['tp2'] - entry) * (qty_total * 0.40) +
        (db_pos['tp3'] - entry) * (qty_total * 0.10)
    )
    
    # Update DB - position fully closed
    update_position_db(user_id, symbol, {
        'tp3_hit': True,
        'tp3_hit_at': datetime.utcnow(),
        'qty_remaining': 0,
        'status': 'closed_tp3',
        'total_profit': total_profit
    })
    
    # Notify - CELEBRATION!
    await bot.send_message(
        chat_id=user_id,
        text=(
            f"🎉 <b>TP3 HIT — JACKPOT! {symbol}</b>\n\n"
            f"✅ Closed final 10% @ <code>{db_pos['tp3']:.4f}</code>\n"
            f"💰 TP3 Profit: +${(db_pos['tp3'] - entry) * qty_tp3:.2f} USDT\n\n"
            f"📊 <b>Total Trade Profit:</b>\n"
            f"💵 <b>+${total_profit:.2f} USDT</b>\n\n"
            f"🎯 StackMentor Strategy:\n"
            f"• TP1 (50%): R:R 1:2 ✅\n"
            f"• TP2 (40%): R:R 1:3 ✅\n"
            f"• TP3 (10%): R:R 1:10 ✅\n\n"
            f"🔥 Perfect execution!"
        ),
        parse_mode='HTML'
    )
```

---

## 📊 Database Schema Updates

### Add StackMentor Fields:

```sql
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp1_price NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp2_price NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp3_price NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp1_hit BOOLEAN DEFAULT FALSE;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp2_hit BOOLEAN DEFAULT FALSE;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp3_hit BOOLEAN DEFAULT FALSE;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp1_hit_at TIMESTAMPTZ;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp2_hit_at TIMESTAMPTZ;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp3_hit_at TIMESTAMPTZ;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS breakeven_mode BOOLEAN DEFAULT FALSE;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS qty_tp1 NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS qty_tp2 NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS qty_tp3 NUMERIC(18,8);
```

---

## 🎯 Benefits

### For Users:

1. ✅ **Secured Profits**: 50% locked at TP1
2. ✅ **Risk-Free Trading**: Breakeven after TP1
3. ✅ **Trend Riding**: 10% for massive gains
4. ✅ **Better Win Rate**: Incremental exits

### For Owner:

1. 📈 **Higher Trading Volume**: More partial closes = more trades
2. 💰 **More Commissions**: Each TP generates commission
3. 🎯 **Better User Retention**: Users see consistent profits
4. 🔥 **Competitive Edge**: Advanced strategy vs competitors

---

## 📋 Implementation Checklist

- [ ] Update `autotrade_engine.py` with StackMentor config
- [ ] Add TP calculation logic (3-tier)
- [ ] Implement TP monitor loop
- [ ] Add TP1/TP2/TP3 handlers
- [ ] Update database schema
- [ ] Add breakeven SL update logic
- [ ] Create notification messages
- [ ] Test with small position
- [ ] Deploy to VPS
- [ ] Monitor first trades

---

## 🚀 Rollout Plan

1. **Phase 1**: Implement code (1-2 hours)
2. **Phase 2**: Test locally (30 min)
3. **Phase 3**: Deploy to VPS (15 min)
4. **Phase 4**: Monitor first 5 trades (24 hours)
5. **Phase 5**: Full rollout to all users

---

**Status**: Ready for implementation  
**Priority**: High (volume booster)  
**Risk**: Low (breakeven protection)
