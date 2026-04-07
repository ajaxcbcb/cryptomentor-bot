# Deploy Risk Mode Integration - Quick Guide

**Status:** ✅ READY TO DEPLOY  
**Time Required:** ~10 minutes  
**Risk Level:** LOW (backward compatible)

---

## Quick Deploy (3 Steps)

### Step 1: Database Migration (2 min)
```bash
# Connect to Supabase
psql postgresql://postgres:[YOUR_PASSWORD]@db.xrbqnocovfymdikngaza.supabase.co:5432/postgres

# Run migration
\i db/add_risk_mode.sql

# Verify (should show risk_mode column)
\d autotrade_sessions
```

### Step 2: Deploy Files (3 min)
```bash
# Windows
deploy_risk_mode_integration.bat

# Linux/Mac
bash deploy_risk_mode_integration.sh
```

### Step 3: Verify (5 min)
```bash
# Check logs
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -f"

# Test in Telegram
# 1. Run /autotrade
# 2. Complete API key setup
# 3. Should see "🎯 Choose Risk Mode" screen
```

---

## Manual Deploy (If Scripts Fail)

### Deploy Files
```bash
scp Bismillah/app/handlers_autotrade.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/handlers_risk_mode.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/supabase_repo.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
```

### Restart Service
```bash
ssh root@147.93.156.165 "systemctl restart cryptomentor.service"
```

### Check Status
```bash
ssh root@147.93.156.165 "systemctl status cryptomentor.service"
```

---

## What to Test

### Test 1: New User (Risk-Based)
1. New user runs `/autotrade`
2. Selects exchange (e.g., BingX)
3. Enters API key and secret
4. ✅ Should see "🎯 Choose Risk Mode"
5. Clicks "🌟 Rekomendasi"
6. ✅ Should see risk % options (1%, 2%, 3%, 5%)
7. Selects 2%
8. ✅ Should see confirmation with leverage 10x

### Test 2: New User (Manual)
1. New user runs `/autotrade`
2. Completes API key setup
3. ✅ Should see "🎯 Choose Risk Mode"
4. Clicks "⚙️ Manual"
5. ✅ Should see "Enter margin in USDT"
6. Types "10"
7. ✅ Should see leverage selection
8. Selects 10x
9. ✅ Should see confirmation

### Test 3: Existing User
1. Existing user runs `/autotrade`
2. Clicks "⚙️ Settings"
3. ✅ Should see current mode (defaults to manual)
4. ✅ Should see "🔄 Switch to Rekomendasi Mode"
5. Clicks switch button
6. ✅ Should confirm mode change

---

## Rollback (If Needed)

### Quick Rollback
```bash
# SSH to VPS
ssh root@147.93.156.165

# Restore from git (if you committed before deploy)
cd /root/cryptomentor-bot
git checkout Bismillah/app/handlers_autotrade.py
git checkout Bismillah/app/handlers_risk_mode.py
git checkout Bismillah/app/supabase_repo.py

# Restart
systemctl restart cryptomentor.service
```

### Database Rollback
```sql
-- Only if absolutely necessary
ALTER TABLE autotrade_sessions DROP COLUMN IF EXISTS risk_mode;
```

---

## Monitoring

### Check Logs
```bash
# Real-time logs
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -f"

# Recent errors
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -n 100 | grep -i error"
```

### Check Service
```bash
ssh root@147.93.156.165 "systemctl status cryptomentor.service"
```

---

## Expected Behavior

### After Deployment
- ✅ Bot responds to `/autotrade`
- ✅ New users see risk mode selection
- ✅ Existing users default to manual mode
- ✅ Settings show mode-specific options
- ✅ Mode switching works
- ✅ No errors in logs

### If Issues
1. Check logs for errors
2. Verify database migration ran
3. Verify files deployed correctly
4. Test with test account
5. Rollback if critical issue

---

## Success Criteria

- ✅ Service running without errors
- ✅ New users can complete registration
- ✅ Risk mode selection appears
- ✅ Both modes work correctly
- ✅ Existing users unaffected
- ✅ Settings show correct options

---

## Support

**VPS:** root@147.93.156.165 (password: <REDACTED_VPS_PASSWORD>)  
**Database:** https://xrbqnocovfymdikngaza.supabase.co  
**Service:** cryptomentor.service  
**Path:** /root/cryptomentor-bot  

**Admin:** @BillFarr  
**Documentation:** RISK_MODE_INTEGRATION_COMPLETE.md  

---

## Ready to Deploy?

✅ All tests passed  
✅ Documentation complete  
✅ Deployment scripts ready  
✅ Rollback plan in place  
✅ Backward compatible  

**GO FOR DEPLOYMENT** 🚀

---

**Last Updated:** April 3, 2026 18:45 CEST  
**Status:** READY ✅
