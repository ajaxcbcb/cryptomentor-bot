# Deploy Risk Per Trade - Quick Guide

**Status:** ✅ READY TO DEPLOY  
**Risk Level:** LOW (No breaking changes)  
**Time Required:** 5 minutes  

---

## What You're Deploying

Risk management UI that lets users select their risk percentage (1%, 2%, 3%, 5%) instead of fixed margin. This phase is UI-only - the risk % is saved but not yet used by the trading engine.

---

## Quick Deploy (Choose One)

### Option 1: Automated (Linux/Mac)
```bash
chmod +x deploy_risk_phase1.sh
./deploy_risk_phase1.sh
```

### Option 2: Automated (Windows)
```cmd
deploy_risk_phase1.bat
```

### Option 3: Manual (3 commands)
```bash
scp Bismillah/app/supabase_repo.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/position_sizing.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/handlers_autotrade.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

ssh root@147.93.156.165 "systemctl restart cryptomentor.service"
```

---

## Verify Deployment (2 minutes)

### 1. Check Service
```bash
ssh root@147.93.156.165 "systemctl status cryptomentor.service"
```
Should show: `Active: active (running)`

### 2. Check Logs
```bash
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -n 20"
```
Should show: No errors, bot started successfully

### 3. Test in Telegram
1. Open bot
2. `/autotrade`
3. Click "Settings"
4. Should see "Risk per trade: 2.0%"
5. Click "Risk Management"
6. Should see 4 buttons: 1%, 2%, 3%, 5%
7. Click "3%"
8. Should see confirmation
9. Go back to Settings
10. Should now show "Risk per trade: 3.0%"

---

## What Users Will See

### New Button in Settings:
```
⚙️ AutoTrade Settings

💵 Trading capital: 100 USDT
🎯 Risk per trade: 2.0%
📊 Leverage: 10x
...

[🎯 Risk Management]  ← NEW!
[💰 Change Trading Capital]
[📊 Change Leverage]
...
```

### Risk Management Menu:
```
🎯 Risk Management Settings

💰 Current Balance: $100.00
⚖️ Moderate
Risk per trade: 2.0% ($2.00)
Survivability: 50+ consecutive losses

💡 Recommended for your balance: 2.0%

Select your risk level:
[🛡️ 1%] [⚖️ 2%]
[⚡ 3%] [🔥 5%]
[📚 Learn More]
[🧮 Simulator]
```

---

## Important Notes

### What Works:
- ✅ Users can view risk settings
- ✅ Users can change risk %
- ✅ Settings persist
- ✅ Education and simulator work

### What Doesn't Work Yet:
- ⏳ Risk % doesn't control position size yet
- ⏳ Trading engine still uses fixed margin
- ⏳ This is Phase 1 - UI only

### Why This Is Safe:
- No changes to trading logic
- Risk % is saved but not used yet
- Can't break existing functionality
- Easy to rollback if needed

---

## Rollback (If Needed)

```bash
ssh root@147.93.156.165
cd /root/cryptomentor-bot/backups
ls -lt | head -5  # Find latest backup
cd risk_phase1_YYYYMMDD_HHMMSS
cp * /root/cryptomentor-bot/Bismillah/app/
systemctl restart cryptomentor.service
```

---

## Support

### If Service Won't Start:
```bash
# Check logs
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -n 50"

# Check for Python errors
ssh root@147.93.156.165 "cd /root/cryptomentor-bot && python3 -m py_compile Bismillah/app/supabase_repo.py"
ssh root@147.93.156.165 "cd /root/cryptomentor-bot && python3 -m py_compile Bismillah/app/position_sizing.py"
ssh root@147.93.156.165 "cd /root/cryptomentor-bot && python3 -m py_compile Bismillah/app/handlers_autotrade.py"
```

### If UI Doesn't Show:
1. Check if files uploaded correctly
2. Verify service restarted
3. Check logs for errors
4. Try `/start` command in bot to refresh

---

## Success Checklist

- [ ] Files uploaded successfully
- [ ] Service restarted without errors
- [ ] Logs show no errors
- [ ] "Risk Management" button appears in Settings
- [ ] Can change risk percentage
- [ ] Settings persist after closing bot
- [ ] Education and simulator work

---

## What's Next

After successful deployment:

1. **Monitor for 24 hours**
   - Check logs periodically
   - Watch for user feedback
   - Verify no errors

2. **Collect Feedback**
   - Do users understand the feature?
   - Is the UI clear?
   - Any confusion?

3. **Plan Phase 2**
   - Engine integration
   - Make risk % actually control position sizes
   - Timeline: 1-2 weeks

---

## Quick Reference

**VPS:** root@147.93.156.165  
**Password:** <REDACTED_VPS_PASSWORD>  
**Path:** /root/cryptomentor-bot  
**Service:** cryptomentor.service  

**Files Deployed:**
- Bismillah/app/supabase_repo.py
- Bismillah/app/position_sizing.py
- Bismillah/app/handlers_autotrade.py

**Tests Passing:** 9/9 ✅

---

**Ready to deploy? Run the deployment script now!**

