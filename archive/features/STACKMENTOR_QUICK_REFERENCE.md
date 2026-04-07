# StackMentor Quick Reference

## 🎯 Quick Commands

### Add Deposit for User

```sql
-- Add $100 deposit
SELECT add_user_deposit(TELEGRAM_ID, 100.00);

-- Example
SELECT add_user_deposit(123456789, 100.00);
```

### Check User Eligibility

```sql
-- Check single user
SELECT 
    telegram_id,
    first_name,
    total_deposit,
    is_stackmentor_eligible(telegram_id) as eligible
FROM users
WHERE telegram_id = TELEGRAM_ID;
```

### List All Eligible Users

```sql
SELECT 
    telegram_id,
    first_name,
    username,
    total_deposit
FROM users
WHERE total_deposit >= 60
ORDER BY total_deposit DESC;
```

### Check Active StackMentor Trades

```sql
SELECT 
    telegram_id,
    symbol,
    side,
    entry_price,
    tp1_price,
    tp2_price,
    tp3_price,
    tp1_hit,
    tp2_hit,
    breakeven_mode
FROM autotrade_trades
WHERE status = 'open' AND strategy = 'stackmentor';
```

---

## 🔧 VPS Commands

### Check Service

```bash
ssh root@147.93.156.165
sudo systemctl status cryptomentor.service
```

### Restart Service

```bash
sudo systemctl restart cryptomentor.service
```

### Watch Logs

```bash
# All logs
sudo journalctl -u cryptomentor.service -f

# StackMentor only
sudo journalctl -u cryptomentor.service -f | grep -i stackmentor
```

### Test StackMentor

```bash
cd /root/cryptomentor-bot
source venv/bin/activate
python3 test_vps_stackmentor.py
```

---

## 📊 How It Works

### Eligible User (Deposit ≥ $60)
1. User starts autotrade
2. Engine checks: `is_stackmentor_eligible(user_id)` → TRUE
3. StackMentor enabled
4. 3-tier TP: 50%/40%/10% at R:R 1:2/1:3/1:10
5. After TP1 → SL moves to breakeven (risk-free)

### Non-Eligible User (Deposit < $60)
1. User starts autotrade
2. Engine checks: `is_stackmentor_eligible(user_id)` → FALSE
3. Legacy TP used (single TP at R:R 1:2)
4. Notification shows upgrade message

---

## 💡 Common Tasks

### Give User StackMentor Access

```sql
-- Add $60+ deposit
SELECT add_user_deposit(TELEGRAM_ID, 60.00);

-- Verify
SELECT is_stackmentor_eligible(TELEGRAM_ID);
```

### Remove StackMentor Access

```sql
-- Reset deposit to 0
UPDATE users SET total_deposit = 0 WHERE telegram_id = TELEGRAM_ID;
```

### Change Threshold

```sql
-- Lower to $30
CREATE OR REPLACE FUNCTION public.is_stackmentor_eligible(p_telegram_id BIGINT)
RETURNS BOOLEAN LANGUAGE SQL STABLE AS $$
  SELECT COALESCE(total_deposit, 0) >= 30
  FROM public.users
  WHERE telegram_id = p_telegram_id;
$$;
```

### Make Free for All

```sql
-- Everyone eligible
CREATE OR REPLACE FUNCTION public.is_stackmentor_eligible(p_telegram_id BIGINT)
RETURNS BOOLEAN LANGUAGE SQL STABLE AS $$
  SELECT TRUE;
$$;
```

---

## 🎯 Testing Checklist

- [ ] Add deposit for test user
- [ ] Start autotrade
- [ ] Verify StackMentor notification
- [ ] Wait for entry
- [ ] Monitor TP1 hit → breakeven SL
- [ ] Monitor TP2 hit
- [ ] Monitor TP3 hit (if lucky!)
- [ ] Check database records

---

## 📞 Quick Access

**VPS:** `ssh root@147.93.156.165`  
**Password:** `<REDACTED_VPS_PASSWORD>`  
**Path:** `/root/cryptomentor-bot`  
**Service:** `cryptomentor.service`

**Supabase:** Dashboard → SQL Editor  
**Minimum Deposit:** $60 USDT  
**Strategy:** 50%/40%/10% at R:R 1:2/1:3/1:10
