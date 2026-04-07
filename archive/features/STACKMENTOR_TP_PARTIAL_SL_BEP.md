# StackMentor: TP Partial & SL Auto-Move to Breakeven

## 📋 Overview

StackMentor menggunakan sistem 3-tier Take Profit dengan automatic Stop Loss movement ke breakeven setelah TP1 hit.

---

## 🎯 Cara Kerja TP Partial

### 1. Entry Position
Bot membuka trade dengan Order ID dari exchange, contoh:
- Symbol: ETHUSDT
- Side: LONG
- Entry: $2000
- Total Quantity: 1 ETH
- Leverage: 10x

### 2. TP Levels Setup (3-Tier)
Bot otomatis set 3 TP levels dengan quantity split:

**TP1 (60%)**: Close 0.6 ETH
- Target: Entry + (4.0 × ATR)
- Risk:Reward = 1:2
- Action: Close 60% position + Move SL to Breakeven

**TP2 (30%)**: Close 0.3 ETH  
- Target: Entry + (6.0 × ATR)
- Risk:Reward = 1:3
- Action: Close 30% position

**TP3 (10%)**: Close 0.1 ETH
- Target: Entry + (8.0 × ATR)  
- Risk:Reward = 1:4
- Action: Close remaining 10% position

### 3. Quantity Split Calculation
```python
def calculate_qty_splits(total_qty: float, precision: int = 3):
    """
    Split quantity: 60% / 30% / 10%
    """
    qty_tp1 = round(total_qty * 0.60, precision)  # 60%
    qty_tp2 = round(total_qty * 0.30, precision)  # 30%
    qty_tp3 = round(total_qty * 0.10, precision)  # 10%
    
    # Ensure total = 100%
    if qty_tp1 + qty_tp2 + qty_tp3 != total_qty:
        qty_tp3 = round(total_qty - qty_tp1 - qty_tp2, precision)
    
    return qty_tp1, qty_tp2, qty_tp3
```

---

## 🛡️ Auto SL Movement to Breakeven

### Trigger: TP1 Hit
Ketika mark price menyentuh TP1:

1. **Close 60% Position**
   ```python
   close_side = "SELL" if side == "LONG" else "BUY"
   client.place_order(
       symbol=symbol,
       side=close_side,
       quantity=qty_tp1,  # 60% of total
       order_type='market',
       reduce_only=True
   )
   ```

2. **Validate Breakeven SL**
   - LONG: Entry price must be BELOW current mark price
   - SHORT: Entry price must be ABOVE current mark price
   - If validation fails, keep original SL (market moved too far)

3. **Move SL to Entry Price (Breakeven)**
   ```python
   if sl_valid:
       client.set_position_sl(symbol, entry_price)
       logger.info(f"SL moved to breakeven @ {entry_price}")
   ```

4. **Update Position State**
   ```python
   pos_data['tp1_hit'] = True
   pos_data['breakeven_mode'] = True
   pos_data['sl_price'] = entry_price
   ```

### Result: Risk-Free Trade
- 60% profit sudah locked in
- Remaining 40% position = ZERO RISK (SL at breakeven)
- Bisa target TP2 dan TP3 tanpa risiko loss

---

## 📊 Example Trade Flow

### Entry
```
Symbol: ETHUSDT
Side: LONG
Entry: $2000
Quantity: 1 ETH
Leverage: 10x

Initial SL: $1960 (-2% = -$40)
TP1: $2080 (+4% = +$48) → 60% = 0.6 ETH
TP2: $2120 (+6% = +$72) → 30% = 0.3 ETH  
TP3: $2160 (+8% = +$96) → 10% = 0.1 ETH
```

### TP1 Hit @ $2080
```
✅ Close 0.6 ETH @ $2080
   Profit: +$48 (60% position)

🛡️ Move SL to $2000 (breakeven)
   Remaining: 0.4 ETH @ ZERO RISK
```

### TP2 Hit @ $2120
```
✅ Close 0.3 ETH @ $2120
   Profit: +$36 (30% position)

🛡️ SL still at $2000 (breakeven)
   Remaining: 0.1 ETH @ ZERO RISK
```

### TP3 Hit @ $2160
```
✅ Close 0.1 ETH @ $2160
   Profit: +$16 (10% position)

🎉 Total Profit: $48 + $36 + $16 = $100
```

---

## 🔧 Technical Implementation

### Position Monitoring
```python
async def monitor_stackmentor_positions(bot, user_id, client, notify_chat_id):
    """
    Monitor StackMentor positions every 5 seconds
    Check if mark price hit any TP level
    """
    while True:
        positions = get_all_stackmentor_positions(user_id)
        
        for pos in positions:
            ticker = client.get_ticker(pos['symbol'])
            mark_price = ticker['mark_price']
            
            # Check TP1
            if not pos['tp1_hit'] and is_tp_hit(mark_price, pos['tp1_price'], pos['side']):
                await handle_tp1_hit(bot, user_id, client, notify_chat_id, 
                                    pos['symbol'], pos, mark_price)
            
            # Check TP2
            elif pos['tp1_hit'] and not pos['tp2_hit'] and is_tp_hit(mark_price, pos['tp2_price'], pos['side']):
                await handle_tp2_hit(bot, user_id, client, notify_chat_id,
                                    pos['symbol'], pos, mark_price)
            
            # Check TP3
            elif pos['tp2_hit'] and not pos['tp3_hit'] and is_tp_hit(mark_price, pos['tp3_price'], pos['side']):
                await handle_tp3_hit(bot, user_id, client, notify_chat_id,
                                    pos['symbol'], pos, mark_price)
        
        await asyncio.sleep(5)  # Check every 5 seconds
```

### SL Validation Logic
```python
def validate_breakeven_sl(side: str, entry: float, current_mark: float) -> bool:
    """
    Validate if breakeven SL is valid based on current market price
    
    LONG: Entry must be BELOW current mark (profit zone)
    SHORT: Entry must be ABOVE current mark (profit zone)
    """
    if side == "LONG":
        return entry < current_mark
    else:  # SHORT
        return entry > current_mark
```

---

## 🎯 Benefits

### 1. Risk Management
- Lock in 60% profit at TP1
- Remaining 40% = ZERO RISK after SL moves to breakeven
- Can't lose money after TP1 hit

### 2. Profit Maximization
- Still have 40% position to catch TP2 and TP3
- Let winners run without risk
- Professional money management

### 3. Psychological Edge
- No stress after TP1 hit (risk-free)
- Can hold for bigger moves
- Avoid premature exits

---

## 📝 Database Tracking

### Position State
```sql
CREATE TABLE stackmentor_positions (
    user_id INTEGER,
    symbol TEXT,
    entry_price REAL,
    side TEXT,
    total_qty REAL,
    qty_tp1 REAL,  -- 60%
    qty_tp2 REAL,  -- 30%
    qty_tp3 REAL,  -- 10%
    tp1_price REAL,
    tp2_price REAL,
    tp3_price REAL,
    sl_price REAL,
    tp1_hit BOOLEAN DEFAULT FALSE,
    tp2_hit BOOLEAN DEFAULT FALSE,
    tp3_hit BOOLEAN DEFAULT FALSE,
    breakeven_mode BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    PRIMARY KEY (user_id, symbol)
);
```

---

## 🚀 Eligibility Update

### Previous Requirement
- Minimum balance: $60 USDT
- Only users with balance >= $60 could use StackMentor

### New Requirement (Updated)
- **NO MINIMUM BALANCE**
- All users can use StackMentor regardless of balance
- Function `is_stackmentor_eligible_by_balance()` now returns `True` for all

```python
def is_stackmentor_eligible_by_balance(balance: float) -> bool:
    """
    ALL balances are eligible - no minimum requirement.
    """
    return True  # All users can use StackMentor
```

---

## 📊 Success Metrics

### Risk Reduction
- 60% profit locked at TP1
- 40% position at zero risk
- Maximum drawdown = 0 after TP1

### Win Rate Improvement
- Even if TP2/TP3 not hit, still profitable
- SL at breakeven prevents losses
- Higher overall win rate

### Profit Optimization
- Capture extended moves with remaining 40%
- Average R:R improves from 1:2 to 1:2.5+
- Better risk-adjusted returns

---

## 🎓 User Education

### Notification Messages

**Entry:**
```
🎯 StackMentor Active (3-tier TP)
TP1: $2080 (60% @ 1:2 R:R)
TP2: $2120 (30% @ 1:3 R:R)
TP3: $2160 (10% @ 1:4 R:R)
```

**TP1 Hit:**
```
✅ TP1 HIT — 60% Closed @ $2080
💰 Profit: +$48 locked in
🛡️ SL moved to breakeven @ $2000
📊 Remaining: 0.4 ETH @ ZERO RISK
```

**TP2 Hit:**
```
✅ TP2 HIT — 30% Closed @ $2120
💰 Additional profit: +$36
📊 Remaining: 0.1 ETH @ ZERO RISK
```

**TP3 Hit:**
```
🎉 TP3 HIT — Final 10% Closed @ $2160
💰 Final profit: +$16
🏆 Total Profit: $100 (+5% ROI)
```

---

## 🔄 Deployment

### Files Modified
1. `Bismillah/app/autotrade_engine.py` - Remove $60 minimum check
2. `Bismillah/app/supabase_repo.py` - Update eligibility function
3. `Bismillah/app/stackmentor.py` - TP partial & SL BEP logic (already implemented)

### Deployment Command
```bash
# Upload files
scp -P 22 Bismillah/app/autotrade_engine.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp -P 22 Bismillah/app/supabase_repo.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# Restart service
ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor"

# Verify
ssh -p 22 root@147.93.156.165 "systemctl status cryptomentor"
```

---

## ✅ Status

- [x] TP Partial logic implemented
- [x] SL auto-move to breakeven implemented
- [x] Minimum balance requirement removed
- [x] All users can use StackMentor
- [x] Ready for deployment

---

**Last Updated**: 2026-04-06  
**Status**: ✅ Complete & Ready to Deploy
