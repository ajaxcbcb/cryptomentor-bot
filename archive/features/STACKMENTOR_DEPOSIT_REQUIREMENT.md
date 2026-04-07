# StackMentor Deposit Requirement

## 🎯 Eligibility Requirement

**StackMentor is now a PREMIUM feature for users with deposit ≥ $60 USDT**

### Why $60 Minimum?

1. **Serious Traders**: Filters out casual users, focuses on committed traders
2. **Volume Incentive**: Encourages larger deposits = more trading volume for owner
3. **Premium Value**: Makes StackMentor a valuable upgrade incentive
4. **Risk Management**: Users with larger capital benefit more from 3-tier TP

---

## 📊 Feature Comparison

| Feature | Free User | Deposit < $60 | Deposit ≥ $60 |
|---------|-----------|---------------|---------------|
| AutoTrade | ✅ | ✅ | ✅ |
| Single TP | ✅ | ✅ | ✅ |
| Dual TP (Premium) | ❌ | ✅ | ✅ |
| **StackMentor 3-Tier TP** | ❌ | ❌ | ✅ |
| Breakeven SL | ❌ | ✅ | ✅ |
| R:R 1:10 Target | ❌ | ❌ | ✅ |

---

## 🔧 Implementation Changes

### 1. Database Migration

New SQL file: `db/add_deposit_tracking.sql`

```sql
-- Add total_deposit column
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_deposit NUMERIC(18,2) DEFAULT 0.00;

-- Function to check eligibility
CREATE OR REPLACE FUNCTION public.is_stackmentor_eligible(p_telegram_id BIGINT)
RETURNS BOOLEAN LANGUAGE SQL STABLE AS $$
  SELECT COALESCE(total_deposit, 0) >= 60
  FROM public.users
  WHERE telegram_id = p_telegram_id;
$$;

-- Function to add deposit
CREATE OR REPLACE FUNCTION public.add_user_deposit(
  p_telegram_id BIGINT,
  p_amount NUMERIC
) RETURNS NUMERIC ...
```

### 2. Supabase Repo Functions

Added to `Bismillah/app/supabase_repo.py`:

```python
def get_user_total_deposit(telegram_id: int) -> float:
    """Get user's total lifetime deposits"""

def is_stackmentor_eligible(telegram_id: int) -> bool:
    """Check if user is eligible for StackMentor (deposit >= $60)"""

def add_user_deposit(telegram_id: int, amount: float) -> float:
    """Add deposit to user's total and return new total"""
```

### 3. AutoTrade Engine Check

Modified `Bismillah/app/autotrade_engine.py`:

```python
# Check eligibility before enabling StackMentor
from app.supabase_repo import is_stackmentor_eligible

stackmentor_enabled = False
try:
    stackmentor_enabled = cfg.get("use_stackmentor", True) and is_stackmentor_eligible(user_id)
    if cfg.get("use_stackmentor", True) and not stackmentor_enabled:
        logger.info(f"[StackMentor:{user_id}] Not eligible - deposit < $60 (using legacy TP)")
except Exception as _sm_check_err:
    logger.warning(f"[StackMentor:{user_id}] Eligibility check failed: {_sm_check_err}")
    stackmentor_enabled = False
```

### 4. User Notifications

Updated order execution notification to show:

**For eligible users (deposit ≥ $60):**
```
🎯 TP1: 45000.0000 (+4.7%) — 50% posisi
🎯 TP2: 46000.0000 (+7.0%) — 40% posisi
🎯 TP3: 53000.0000 (+23.3%) — 10% posisi
⚖️ R:R: 1:2 → 1:3 → 1:10 (StackMentor 🎯)
🎯 StackMentor Active (Deposit ≥ $60)
```

**For non-eligible users (deposit < $60):**
```
🎯 TP: 45000.0000 (+4.7%)
⚖️ R:R Ratio: 1:2
💡 Deposit $60+ untuk unlock StackMentor (3-tier TP)
```

---

## 🚀 Deployment Steps

### Step 1: Apply Database Migration

Run in Supabase SQL Editor:

```bash
# Copy content from db/add_deposit_tracking.sql
```

### Step 2: Deploy Updated Files

```bash
# Upload updated files
scp Bismillah/app/supabase_repo.py root@147.93.156.165:/root/cryptomentor-bot/app/
scp Bismillah/app/autotrade_engine.py root@147.93.156.165:/root/cryptomentor-bot/app/
scp Bismillah/app/stackmentor.py root@147.93.156.165:/root/cryptomentor-bot/app/
scp Bismillah/app/trade_history.py root@147.93.156.165:/root/cryptomentor-bot/app/

# Restart service
ssh root@147.93.156.165
sudo systemctl restart cryptomentor.service
```

### Step 3: Add Deposits for Existing Users

For users who should have StackMentor access, manually add their deposits:

```sql
-- Add deposit for specific user
SELECT add_user_deposit(123456789, 100.00);  -- telegram_id, amount

-- Or update directly
UPDATE users SET total_deposit = 100.00 WHERE telegram_id = 123456789;

-- Check eligibility
SELECT telegram_id, total_deposit, is_stackmentor_eligible(telegram_id) as eligible
FROM users
WHERE total_deposit > 0;
```

---

## 📈 How to Track Deposits

### Manual Tracking (Current)

Admin manually adds deposits when user sends proof:

```sql
-- User deposits $100
SELECT add_user_deposit(123456789, 100.00);

-- Check user's total
SELECT telegram_id, first_name, total_deposit 
FROM users 
WHERE telegram_id = 123456789;
```

### Automated Tracking (Future)

Integrate with payment gateway to auto-update deposits:

```python
# When payment confirmed
from app.supabase_repo import add_user_deposit

new_total = add_user_deposit(telegram_id, payment_amount)
print(f"User {telegram_id} new total: ${new_total}")

# Check if now eligible
if new_total >= 60:
    await bot.send_message(
        chat_id=telegram_id,
        text="🎉 Congratulations! You've unlocked StackMentor 3-tier TP system!"
    )
```

---

## 🎯 Marketing Message

### For Non-Eligible Users

When they start autotrade or see notification:

```
💡 Want better risk management?

Deposit $60+ to unlock StackMentor:
• 3-tier Take Profit (50%/40%/10%)
• Risk-free trading after TP1
• Capture big moves with R:R 1:10
• Professional profit management

Current deposit: $0
Required: $60

Contact @yongdnf3 to deposit
```

### For Newly Eligible Users

When deposit reaches $60:

```
🎉 StackMentor Unlocked!

You now have access to:
✅ 3-tier Take Profit system
✅ Automatic breakeven SL
✅ R:R 1:2 → 1:3 → 1:10
✅ Professional risk management

Your next autotrade will use StackMentor automatically!
```

---

## 📊 Expected Impact

### User Behavior

1. **Deposit Incentive**: Users will deposit more to reach $60 threshold
2. **Retention**: Premium feature keeps users engaged
3. **Volume**: Larger deposits = larger positions = more volume

### Revenue Impact

- **Before**: Users deposit $10-30 on average
- **After**: Users deposit $60+ to unlock StackMentor
- **Increase**: 2-3x average deposit size

### Trading Volume

- **StackMentor users**: 3 partial closes per trade
- **Regular users**: 1 close per trade
- **Volume increase**: 200% for eligible users

---

## 🛡️ Rollback Plan

If deposit requirement causes issues:

### Option 1: Lower Threshold

```sql
-- Change to $30 minimum
CREATE OR REPLACE FUNCTION public.is_stackmentor_eligible(p_telegram_id BIGINT)
RETURNS BOOLEAN LANGUAGE SQL STABLE AS $$
  SELECT COALESCE(total_deposit, 0) >= 30  -- Changed from 60
  FROM public.users
  WHERE telegram_id = p_telegram_id;
$$;
```

### Option 2: Disable Requirement

```python
# In autotrade_engine.py
stackmentor_enabled = cfg.get("use_stackmentor", True)  # Remove eligibility check
```

### Option 3: Make Free for All

```sql
-- Everyone eligible
CREATE OR REPLACE FUNCTION public.is_stackmentor_eligible(p_telegram_id BIGINT)
RETURNS BOOLEAN LANGUAGE SQL STABLE AS $$
  SELECT TRUE;  -- Always eligible
$$;
```

---

## 📝 Admin Commands (Future)

Add bot commands for deposit management:

```python
# /add_deposit <user_id> <amount>
@admin_only
async def cmd_add_deposit(update, context):
    user_id = int(context.args[0])
    amount = float(context.args[1])
    
    new_total = add_user_deposit(user_id, amount)
    
    await update.message.reply_text(
        f"✅ Added ${amount} to user {user_id}\n"
        f"New total: ${new_total}\n"
        f"StackMentor: {'✅ Eligible' if new_total >= 60 else '❌ Not eligible'}"
    )

# /check_deposit <user_id>
@admin_only
async def cmd_check_deposit(update, context):
    user_id = int(context.args[0])
    
    total = get_user_total_deposit(user_id)
    eligible = is_stackmentor_eligible(user_id)
    
    await update.message.reply_text(
        f"User {user_id}:\n"
        f"Total deposit: ${total}\n"
        f"StackMentor: {'✅ Eligible' if eligible else '❌ Not eligible'}\n"
        f"{'✅' if eligible else f'Need ${60 - total:.2f} more'}"
    )
```

---

## ✅ Summary

**Changes Made:**

1. ✅ Added `total_deposit` column to users table
2. ✅ Created `is_stackmentor_eligible()` function
3. ✅ Created `add_user_deposit()` function
4. ✅ Added eligibility check in autotrade engine
5. ✅ Updated notifications to show eligibility status
6. ✅ Added helper functions in supabase_repo.py

**Deployment Required:**

1. Apply `db/add_deposit_tracking.sql` migration
2. Apply `db/stackmentor_migration.sql` migration (from before)
3. Upload updated Python files
4. Restart bot service
5. Manually add deposits for existing users who should have access

**Result:**

- StackMentor is now a premium feature
- Only users with deposit ≥ $60 can use it
- Non-eligible users see upgrade message
- Incentivizes larger deposits
- Easy to adjust threshold or disable requirement

---

**Created**: 2026-04-01  
**Status**: Ready for Deployment  
**Minimum Deposit**: $60 USDT  
**Adjustable**: Yes (can change threshold easily)
