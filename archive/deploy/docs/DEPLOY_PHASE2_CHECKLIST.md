# Phase 2 Deployment Checklist

**Date:** April 2, 2026  
**Status:** Ready for Deployment

---

## Pre-Deployment Checklist

### Code Quality:
- [x] Implementation complete
- [x] All tests passed (5/5)
- [x] Verification passed (4/4)
- [x] No syntax errors
- [x] Code reviewed

### Safety:
- [x] Fallback mechanism implemented
- [x] Extensive logging added
- [x] Validation checks in place
- [x] Error handling complete
- [x] Rollback plan ready

### Documentation:
- [x] Technical documentation complete
- [x] Deployment guide ready
- [x] Monitoring guide ready
- [x] User guide available (Phase 1)

### Scripts:
- [x] Deployment script ready (Linux/Mac)
- [x] Deployment script ready (Windows)
- [x] Verification script ready
- [x] Test suite ready

---

## Deployment Steps

### Step 1: Final Review
- [ ] Read `PHASE2_COMPLETE_SUMMARY.md`
- [ ] Read `PHASE2_DEPLOYMENT_READY.md`
- [ ] Understand what will change
- [ ] Understand rollback procedure

### Step 2: Backup Verification
- [ ] Confirm VPS credentials work
- [ ] Confirm SSH access to VPS
- [ ] Confirm service is running

### Step 3: Deploy
- [ ] Run deployment script:
  - Windows: `deploy_phase2_risk_sizing.bat`
  - Linux/Mac: `bash deploy_phase2_risk_sizing.sh`
- [ ] Verify files uploaded successfully
- [ ] Verify service restarted successfully
- [ ] Check for immediate errors

### Step 4: Initial Monitoring (First Hour)
- [ ] Watch live logs for 10 minutes
- [ ] Check for any errors
- [ ] Verify service is stable
- [ ] Check first trade uses risk-based sizing

### Step 5: Extended Monitoring (First 24 Hours)
- [ ] Check logs every 2 hours
- [ ] Verify position sizes calculated correctly
- [ ] Verify no fallback messages
- [ ] Verify trades execute successfully
- [ ] Verify no account blow-ups

### Step 6: Week 1 Monitoring
- [ ] Daily log review
- [ ] Check user feedback
- [ ] Monitor performance metrics
- [ ] Verify compounding working
- [ ] Collect success stories

---

## Monitoring Commands

### Live Logs:
```bash
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -f | grep -i 'risksizing\|fallback\|error'"
```

### Check Risk Sizing:
```bash
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -n 100 | grep RiskSizing"
```

### Check Fallback Usage:
```bash
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -n 100 | grep FALLBACK"
```

### Check Errors:
```bash
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -n 100 | grep -i error"
```

### Service Status:
```bash
ssh root@147.93.156.165 "systemctl status cryptomentor.service"
```

---

## What to Look For

### ✅ Good Signs:
- Logs show `[RiskSizing:xxx] BTCUSDT - Balance=$...`
- Position sizes vary based on balance
- No "FALLBACK" messages
- Trades execute successfully
- No errors in logs
- Users report better risk management

### ⚠️ Warning Signs:
- Frequent "FALLBACK" messages
- Position sizes not varying
- Calculation errors in logs
- Trades failing occasionally

### 🚨 Critical Issues:
- Service crashes
- Multiple trade failures
- Account balance dropping rapidly
- Position sizes exceeding balance
- Users reporting account blow-ups

---

## Rollback Procedure

### If Critical Issues Found:

**1. Stop Service:**
```bash
ssh root@147.93.156.165 "systemctl stop cryptomentor.service"
```

**2. Restore Backups:**
```bash
ssh root@147.93.156.165 "
cd /root/cryptomentor-bot/Bismillah/app
cp autotrade_engine.py.phase2_backup autotrade_engine.py
cp scalping_engine.py.phase2_backup scalping_engine.py
"
```

**3. Restart Service:**
```bash
ssh root@147.93.156.165 "systemctl start cryptomentor.service"
```

**4. Verify:**
```bash
ssh root@147.93.156.165 "systemctl status cryptomentor.service"
```

**5. Notify Users:**
- Explain temporary issue
- Provide timeline for fix
- Offer support

---

## Success Criteria

### Must Have (First 24 Hours):
- [ ] No service crashes
- [ ] No account blow-ups
- [ ] Position sizes calculated correctly
- [ ] Trades execute successfully
- [ ] No critical errors in logs

### Nice to Have (First Week):
- [ ] Users report better risk management
- [ ] Improved compounding visible
- [ ] Positive feedback
- [ ] No fallback usage
- [ ] Increased confidence

---

## Communication Plan

### Before Deployment:
- [ ] Notify about upcoming feature (optional)
- [ ] Set expectations
- [ ] Explain benefits

### During Deployment:
- [ ] Announce maintenance window (if needed)
- [ ] Keep users informed
- [ ] Provide support

### After Deployment:
- [ ] Announce successful deployment
- [ ] Explain new feature:
  - "Position sizes now adjust automatically based on your risk %"
  - "As your balance grows, positions grow too (safe compounding)"
  - "Change risk % anytime in Settings → Risk Management"
- [ ] Provide user guide
- [ ] Collect feedback

---

## Post-Deployment Tasks

### First 24 Hours:
- [ ] Monitor logs every 2 hours
- [ ] Check first 5-10 trades
- [ ] Verify risk sizing working
- [ ] Respond to user questions
- [ ] Document any issues

### First Week:
- [ ] Daily log review
- [ ] Weekly summary report
- [ ] User satisfaction survey
- [ ] Performance metrics
- [ ] Adjust if needed

### First Month:
- [ ] Monthly performance report
- [ ] User feedback analysis
- [ ] Optimization opportunities
- [ ] Celebrate success! 🎉

---

## Emergency Contacts

**VPS Access:**
- Host: root@147.93.156.165
- Password: <REDACTED_VPS_PASSWORD>
- Path: /root/cryptomentor-bot

**Service:**
- Name: cryptomentor.service
- Logs: `journalctl -u cryptomentor.service`

**Database:**
- Supabase: https://xrbqnocovfymdikngaza.supabase.co

---

## Final Checks Before Deploy

- [ ] All tests passed ✅
- [ ] Verification passed ✅
- [ ] Documentation reviewed ✅
- [ ] Deployment script ready ✅
- [ ] Monitoring plan ready ✅
- [ ] Rollback plan ready ✅
- [ ] VPS access confirmed ✅
- [ ] Backups will be created ✅

---

## Deploy Now?

**If all checks above are complete, you're ready to deploy!**

**Run:**
```bash
# Windows
deploy_phase2_risk_sizing.bat

# Linux/Mac
bash deploy_phase2_risk_sizing.sh
```

**Then monitor closely for 24-48 hours.**

---

**Good luck with the deployment! 🚀**

---

## Notes

Use this space to track deployment progress:

**Deployment Date/Time:** _________________

**Deployed By:** _________________

**Initial Status:** _________________

**First Trade:** _________________

**Issues Found:** _________________

**Resolution:** _________________

**Final Status:** _________________

---

**Remember: Monitor closely, rollback if needed, and celebrate success!** 🎯
