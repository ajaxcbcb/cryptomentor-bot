# Deploy StackMentor NOW - Step by Step Guide

## ✅ Pre-Deployment Checklist

- [x] Code integration complete
- [x] All tests passed
- [x] No syntax errors
- [x] Database migration ready
- [x] Deployment script ready
- [x] Rollback plan documented

---

## 🚀 Deployment Steps (Copy-Paste Ready)

### Step 1: Apply Database Migration

1. Open Supabase Dashboard: https://supabase.com/dashboard
2. Go to SQL Editor
3. Copy and paste this SQL:

```sql
-- StackMentor System Migration
-- Add 3-tier TP tracking and breakeven mode support

-- Add TP price columns
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp1_price NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp2_price NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp3_price NUMERIC(18,8);

-- Add TP hit tracking
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp1_hit BOOLEAN DEFAULT FALSE;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp2_hit BOOLEAN DEFAULT FALSE;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp3_hit BOOLEAN DEFAULT FALSE;

-- Add TP hit timestamps
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp1_hit_at TIMESTAMPTZ;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp2_hit_at TIMESTAMPTZ;
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS tp3_hit_at TIMESTAMPTZ;

-- Add breakeven mode flag
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS breakeven_mode BOOLEAN DEFAULT FALSE;

-- Add quantity splits for each TP
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS qty_tp1 NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS qty_tp2 NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS qty_tp3 NUMERIC(18,8);

-- Add TP profit tracking
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS profit_tp1 NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS profit_tp2 NUMERIC(18,8);
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS profit_tp3 NUMERIC(18,8);

-- Add strategy identifier
ALTER TABLE autotrade_trades ADD COLUMN IF NOT EXISTS strategy TEXT DEFAULT 'stackmentor';

-- Create index for active StackMentor positions
CREATE INDEX IF NOT EXISTS idx_stackmentor_active 
ON autotrade_trades(telegram_id, status, breakeven_mode) 
WHERE status = 'open' AND strategy = 'stackmentor';

-- Create index for TP monitoring
CREATE INDEX IF NOT EXISTS idx_stackmentor_tp_monitor 
ON autotrade_trades(telegram_id, symbol, tp1_hit, tp2_hit, tp3_hit) 
WHERE status = 'open';

COMMENT ON COLUMN autotrade_trades.tp1_price IS 'StackMentor TP1: 50% at R:R 1:2';
COMMENT ON COLUMN autotrade_trades.tp2_price IS 'StackMentor TP2: 40% at R:R 1:3';
COMMENT ON COLUMN autotrade_trades.tp3_price IS 'StackMentor TP3: 10% at R:R 1:10';
COMMENT ON COLUMN autotrade_trades.breakeven_mode IS 'TRUE after TP1 hit, SL moved to entry';
COMMENT ON COLUMN autotrade_trades.strategy IS 'Trading strategy: stackmentor, premium, etc';
```

4. Click "Run" and verify success

---

### Step 2: Deploy Files to VPS

**Option A - Automated (Recommended):**

```bash
# Make script executable
chmod +x deploy_stackmentor.sh

# Run deployment
./deploy_stackmentor.sh
```

**Option B - Manual Commands:**

```bash
# 1. Upload stackmentor.py
scp Bismillah/app/stackmentor.py root@147.93.156.165:/root/cryptomentor-bot/app/

# 2. Upload autotrade_engine.py
scp Bismillah/app/autotrade_engine.py root@147.93.156.165:/root/cryptomentor-bot/app/

# 3. Upload trade_history.py
scp Bismillah/app/trade_history.py root@147.93.156.165:/root/cryptomentor-bot/app/

# 4. SSH to VPS
ssh root@147.93.156.165

# 5. Restart service
cd /root/cryptomentor-bot
sudo systemctl restart cryptomentor.service

# 6. Check status
sudo systemctl status cryptomentor.service

# 7. Watch logs
sudo journalctl -u cryptomentor.service -f
```

---

### Step 3: Verify Deployment

**Check logs for StackMentor initialization:**

```bash
ssh root@147.93.156.165
sudo journalctl -u cryptomentor.service -n 50 | grep -i "stackmentor\|engine.*started"
```

**Expected output:**
```
AutoTrade PRO started for user 123456, exchange=bitunix, amount=10, leverage=10x, premium=False
[StackMentor:123456] Registered BTCUSDT LONG — TP1=45000 TP2=46000 TP3=53000
```

---

### Step 4: Test with Real Trade

1. **Start autotrade** with small position ($10)
2. **Wait for entry** (bot will scan for signals)
3. **Monitor logs** for StackMentor registration
4. **Watch for TP1 hit** → should close 50% and move SL to breakeven
5. **Verify notifications** in Telegram

**Monitor command:**
```bash
ssh root@147.93.156.165 'sudo journalctl -u cryptomentor.service -f | grep -i "stackmentor\|tp1\|tp2\|tp3"'
```

---

### Step 5: Verify Database

**Check StackMentor positions in Supabase:**

```sql
SELECT 
    telegram_id,
    symbol,
    side,
    entry_price,
    tp1_price,
    tp2_price,
    tp3_price,
    qty_tp1,
    qty_tp2,
    qty_tp3,
    tp1_hit,
    tp2_hit,
    tp3_hit,
    breakeven_mode,
    strategy,
    opened_at
FROM autotrade_trades
WHERE status = 'open' AND strategy = 'stackmentor'
ORDER BY opened_at DESC
LIMIT 10;
```

---

## 🎯 Success Criteria

- [ ] Database migration applied successfully
- [ ] Files uploaded to VPS
- [ ] Bot service restarted without errors
- [ ] Logs show "StackMentor" initialization
- [ ] Test trade opens with 3 TP levels
- [ ] TP1 hit triggers breakeven SL update
- [ ] Telegram notifications show StackMentor messages
- [ ] Database shows StackMentor fields populated

---

## 🛡️ Rollback (If Needed)

If something goes wrong:

1. **SSH to VPS:**
   ```bash
   ssh root@147.93.156.165
   ```

2. **Edit config to disable StackMentor:**
   ```bash
   cd /root/cryptomentor-bot
   nano app/autotrade_engine.py
   
   # Change line 30:
   "use_stackmentor": False,  # Disable StackMentor
   ```

3. **Restart service:**
   ```bash
   sudo systemctl restart cryptomentor.service
   ```

4. System will fall back to legacy TP behavior

---

## 📊 Expected Behavior

### When Trade Opens:
```
✅ ORDER EXECUTED  [#1 today]

📊 BTCUSDT | LONG | 10x
💵 Entry: 43000.0000
🎯 TP1: 45000.0000 (+4.7%) — 50% position
🎯 TP2: 46000.0000 (+7.0%) — 40% position
🎯 TP3: 53000.0000 (+23.3%) — 10% position
🛑 SL: 42000.0000 (-2.3%)
📦 Qty: 0.123 (TP1: 0.062 | TP2: 0.049 | TP3: 0.012)

⚖️ R:R: 1:2 → 1:3 → 1:10 (StackMentor)
🔒 After TP1 hit → SL moves to entry (breakeven)
```

### When TP1 Hits:
```
🎯 TP1 HIT — BTCUSDT

✅ Closed 50% @ 45000.0000
💰 Profit: +$23.25 USDT (+4.7%)

🔒 SL MOVED TO BREAKEVEN
📍 Breakeven: 43000.0000

⏳ Remaining 50% running to TP2/TP3...
✅ SL updated

🎯 StackMentor: Risk-free from here!
```

### When TP2 Hits:
```
🎯 TP2 HIT — BTCUSDT

✅ Closed 40% @ 46000.0000
💰 Profit: +$34.23 USDT (+7.0%)

🔒 SL still at breakeven
⏳ Final 10% running to TP3 (R:R 1:10)...

🎯 StackMentor: 90% secured, 10% for jackpot!
```

### When TP3 Hits:
```
🎉 TP3 HIT — JACKPOT! BTCUSDT

✅ Closed final 10% @ 53000.0000
💰 TP3 Profit: +$28.65 USDT (+23.3%)

📊 TOTAL TRADE PROFIT:
💵 +$86.13 USDT

🎯 StackMentor Breakdown:
• TP1 (50%): +$23.25 ✅
• TP2 (40%): +$34.23 ✅
• TP3 (10%): +$28.65 ✅

🔥 Perfect execution! All targets hit!
```

---

## 🎉 Ready to Deploy!

**All systems are GO. StackMentor is ready for production.**

**Estimated deployment time:** 10-15 minutes

**Risk level:** Low (backward compatible, easy rollback)

**Impact:** High (better risk management, increased volume, happier users)

---

**Next Action:** Run `./deploy_stackmentor.sh` or follow manual steps above.

**Questions?** Check logs, verify database, test with small position first.

**Good luck! 🚀**
