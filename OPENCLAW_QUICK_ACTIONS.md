# 🚀 OpenClaw - Quick Action Guide

## ⏳ CURRENT STATUS: Waiting for Railway Redeploy

Bot sedang restart di Railway dengan fix yang sudah di-push.  
**Estimated time:** 1-2 minutes

---

## 📋 3 Steps to Activate OpenClaw

### Step 1: Add API Key to Railway ⚠️ REQUIRED
```
1. Go to: https://railway.app/project/[your-project-id]
2. Click: web service
3. Click: Variables tab
4. Click: + New Variable
5. Add:
   Name: OPENCLAW_API_KEY
   Value: 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
6. Click: Add
7. Bot will auto-restart
```

### Step 2: Run Database Migration ⚠️ REQUIRED
```bash
# Option A: Railway CLI (recommended)
railway run python3 run_openclaw_migration.py

# Option B: Railway Shell
railway shell
python3 run_openclaw_migration.py
exit
```

**Expected output:**
```
✅ Creating OpenClaw tables...
✅ Creating OpenClaw functions...
✅ Testing OpenClaw Manager...
✅ Migration complete!
```

### Step 3: Test in Telegram ✅
```
/openclaw_create Alex friendly
/openclaw_start
Hello, can you explain AI?
```

---

## 🧪 Quick Test Commands

### Test Bot is Online:
```
/start
/menu
/help
```

### Test OpenClaw:
```
# Create assistant
/openclaw_create Alex friendly

# Check balance (will be 0 initially)
/openclaw_balance

# Activate chat mode
/openclaw_start

# Chat freely (no command prefix!)
Hello, can you help me?

# Exit chat mode
/openclaw_exit

# View help
/openclaw_help
```

---

## 💰 Simulate Credit Purchase (For Testing)

Since payment integration isn't live yet, you can manually add credits for testing:

```python
# In Railway shell or local:
from services import get_database
from app.openclaw_manager import get_openclaw_manager

db = get_database()
manager = get_openclaw_manager(db)

# Add 1000 credits to your Telegram user ID
user_id = YOUR_TELEGRAM_ID  # Replace with your ID
result = manager.purchase_credits(user_id, 10.0)  # 10 USDC = 800 credits
print(f"✅ Added {result['credits']} credits")
```

Or directly in database:
```sql
INSERT INTO openclaw_credit_transactions (
    transaction_id, user_id, transaction_type,
    gross_amount_usdc, platform_fee_usdc, net_amount_usdc,
    net_credits, created_at
) VALUES (
    'TEST-' || hex(randomblob(8)),
    YOUR_TELEGRAM_ID,
    'purchase',
    10.0,
    2.0,
    8.0,
    800,
    datetime('now')
);
```

---

## 🔍 Verify Everything Works

### 1. Check Railway Logs:
```bash
railway logs --service web
```

**Look for:**
```
✅ "🚀 Starting CryptoMentor AI Bot..."
✅ "✅ OpenClaw AI Assistant handlers registered"
✅ "✅ Bot initialized"
```

### 2. Check Database Tables:
```bash
railway shell
python3 -c "
from services import get_database
db = get_database()
tables = db.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'openclaw%'\").fetchall()
print('OpenClaw tables:', [t[0] for t in tables])
"
```

**Expected output:**
```
OpenClaw tables: ['openclaw_assistants', 'openclaw_conversations', 'openclaw_messages', 'openclaw_credit_transactions', 'openclaw_user_credits']
```

### 3. Test API Connection:
```bash
railway run python3 test_openclaw_api.py
```

**Expected output:**
```
✅ OpenRouter API connection successful!
✅ GPT-4.1 model available
✅ Response received
```

---

## 🐛 Common Issues & Fixes

### Issue: "python: command not found"
**Status:** ✅ FIXED (commit e16f1c6)  
**Action:** Wait for Railway redeploy

### Issue: "OPENCLAW_API_KEY not found"
**Fix:** Add API key to Railway variables (Step 1 above)

### Issue: "Table openclaw_assistants doesn't exist"
**Fix:** Run database migration (Step 2 above)

### Issue: "Insufficient credits"
**Fix:** Add test credits (see "Simulate Credit Purchase" above)

### Issue: OpenClaw commands not responding
**Check:**
1. API key added to Railway? ✓
2. Migration run? ✓
3. Bot restarted after adding API key? ✓
4. Check logs for handler registration ✓

---

## 📊 Monitor Usage

### Check Platform Revenue:
```sql
SELECT 
    SUM(platform_fee_usdc) as revenue,
    COUNT(*) as transactions
FROM openclaw_credit_transactions
WHERE transaction_type = 'purchase';
```

### Check Active Users:
```sql
SELECT 
    COUNT(DISTINCT user_id) as users,
    SUM(total_credits_spent) as credits_used
FROM openclaw_assistants;
```

### Check Recent Conversations:
```sql
SELECT 
    a.name as assistant,
    c.message_count,
    c.total_credits_spent,
    c.updated_at
FROM openclaw_conversations c
JOIN openclaw_assistants a ON c.assistant_id = a.assistant_id
ORDER BY c.updated_at DESC
LIMIT 10;
```

---

## 🎯 Success Criteria

✅ Bot online in Railway  
✅ `/start` command works  
✅ `/openclaw_help` shows help  
✅ `/openclaw_create` creates assistant  
✅ `/openclaw_start` activates chat mode  
✅ Can chat without command prefix  
✅ AI responds with GPT-4.1  
✅ Credits deducted correctly  
✅ `/openclaw_balance` shows balance  

---

## 📱 User Flow Example

```
User: /openclaw_create Sarah professional
Bot: ✅ AI Assistant Created!
     🤖 Name: Sarah
     🎭 Personality: professional

User: /openclaw_balance
Bot: 💰 Credit Balance: 800 credits

User: /openclaw_start
Bot: ✅ OpenClaw Mode Activated
     💬 You can now chat freely!

User: What is blockchain?
AI: Blockchain is a distributed ledger technology...
    💬 1,234 tokens • 💰 12 credits • Balance: 788

User: How does it ensure security?
AI: Blockchain ensures security through several mechanisms...
    💬 987 tokens • 💰 10 credits • Balance: 778

User: /openclaw_exit
Bot: 👋 OpenClaw Mode Deactivated
```

---

## 🚀 Ready to Launch!

**Current Status:**
- ✅ Code deployed to Railway
- ✅ Python error fixed
- ⏳ Bot restarting (1-2 minutes)

**Your Actions:**
1. ⚠️ Add `OPENCLAW_API_KEY` to Railway
2. ⚠️ Run migration
3. ✅ Test in Telegram

**After completing these 3 steps, OpenClaw will be 100% operational!**

---

## 💡 Pro Tips

1. **Test with your own Telegram account first**
2. **Add test credits before testing chat**
3. **Monitor OpenRouter usage dashboard**
4. **Check Railway logs regularly**
5. **Keep track of platform revenue**

---

## 📞 Support

**Documentation:**
- `OPENCLAW_RAILWAY_DEPLOYMENT_FINAL.md` - Complete guide
- `RAILWAY_PYTHON_FIX.md` - Fix details
- `OPENCLAW_READY_TO_USE.md` - Setup guide

**Logs:**
```bash
railway logs --service web
```

**Database:**
```bash
railway shell
python3
>>> from services import get_database
>>> db = get_database()
>>> # Run queries here
```

---

🎉 **OpenClaw is ready! Just 3 steps to activate!** 🚀
