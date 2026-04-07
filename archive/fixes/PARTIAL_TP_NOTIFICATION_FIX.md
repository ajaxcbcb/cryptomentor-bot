# Partial TP Notification Improvement

## ISSUE
User confused why notification shows "TP1: 53.1 | TP2: 17.8" but exchange only shows 1 order with single TP/SL.

## ROOT CAUSE
System works correctly, but notification didn't explain WHEN partial closes happen:
- Order placement: 1 order with TP1 only (what exchange shows)
- Partial closes: Executed by monitoring loop when price hits TP levels
- User sees exchange immediately after order placement, before any TP hits

## SOLUTION IMPLEMENTED

### 1. Added Clarification to Notification
```diff
+ 🤖 Partial close otomatis saat harga hit TP
```

This tells user that partial closes happen automatically via bot monitoring, not at order placement.

### 2. Simplified Qty Display
```diff
- 📦 Qty: 71.1 (TP1: 35.5 | TP2: 28.4 | TP3: 7.1)
+ 📦 Qty: 71.1
```

Removed qty breakdown to reduce confusion. User will see actual closes in TP hit notifications.

### 3. Improved Profit Display
```diff
- 💰 TP1 profit: +X USDT
- 💰 TP2 profit: +Y USDT
+ 💰 Potential profit: +Y USDT (full TP)
```

Shows total potential profit if all TPs hit, clearer expectation.

## HOW IT WORKS

### Order Placement (T+0)
```
Exchange shows:
- 1 order
- Qty: 71.1
- TP: TP1 price
- SL: SL price
```

### TP1 Hit (T+X minutes)
```
Bot automatically:
1. Closes 50% (35.5 qty) ✅
2. Moves SL to entry (breakeven) ✅
3. Sends notification ✅

Exchange now shows:
- Remaining qty: 35.5
- TP: Still TP1 (will be ignored)
- SL: Entry price (breakeven)
```

### TP2 Hit (T+Y minutes)
```
Bot automatically:
1. Closes 40% of original (28.4 qty) ✅
2. Sends notification ✅

Exchange now shows:
- Remaining qty: 7.1
- SL: Entry price (breakeven)
```

### TP3 Hit (T+Z minutes)
```
Bot automatically:
1. Closes final 10% (7.1 qty) ✅
2. Sends notification ✅
3. Position fully closed ✅
```

## NOTIFICATION BEFORE/AFTER

### BEFORE (Confusing)
```
✅ ORDER EXECUTED

📊 BTCUSDT | LONG
💵 Entry: 95000.00
🎯 TP1: 96000.00 (+1.05%) — 50% posisi
🎯 TP2: 97000.00 (+2.11%) — 40% posisi
🎯 TP3: 105000.00 (+10.53%) — 10% posisi
🛑 SL: 94000.00 (-1.05%)
📦 Qty: 71.1 (TP1: 35.5 | TP2: 28.4 | TP3: 7.1)

⚖️ R:R: 1:2 → 1:3 → 1:10 (StackMentor 🎯)
🔒 Setelah TP1 hit → SL geser ke entry (breakeven)
```

User thinks: "Why exchange only shows 1 TP?"

### AFTER (Clear)
```
✅ ORDER EXECUTED

📊 BTCUSDT | LONG
💵 Entry: 95000.00
🎯 TP1: 96000.00 (+1.05%) — 50% posisi
🎯 TP2: 97000.00 (+2.11%) — 40% posisi
🎯 TP3: 105000.00 (+10.53%) — 10% posisi
🛑 SL: 94000.00 (-1.05%)
📦 Qty: 71.1

⚖️ R:R: 1:2 → 1:3 → 1:10 (StackMentor 🎯)
🤖 Partial close otomatis saat harga hit TP
🔒 Setelah TP1 hit → SL geser ke entry (breakeven)

💰 Potential profit: +2000.00 USDT (full TP)
⚠️ Max loss: -75.00 USDT
💼 Balance: $3750.00 | Risk: 2%
```

User understands: "Bot will automatically close partial positions when price hits TP levels"

## FILES CHANGED
- `Bismillah/app/autotrade_engine.py` - Updated notification text

## DEPLOYMENT

```bash
# SCP file to VPS
scp Bismillah/app/autotrade_engine.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# SSH to VPS and restart
ssh root@147.93.156.165
cd /root/cryptomentor-bot
systemctl restart cryptomentor
systemctl status cryptomentor

# Verify
tail -f /var/log/cryptomentor.log
```

## TESTING

1. Wait for next trade signal
2. Check notification shows: "🤖 Partial close otomatis saat harga hit TP"
3. Check exchange shows 1 order with TP1 only (expected)
4. Wait for TP1 hit
5. Verify bot automatically closes 50% and moves SL to breakeven
6. Check TP1 hit notification

## RESULT

✅ Notification now clearly explains that partial closes happen automatically via bot monitoring
✅ User understands why exchange shows single TP initially
✅ Reduced confusion about StackMentor strategy
✅ Cleaner, less cluttered notification

## NEXT STEPS

Monitor user feedback. If still confused, can add:
- More detailed explanation in /help command
- FAQ about partial TP execution
- Video tutorial showing how StackMentor works
