# Phase 2: Quick Deployment Guide

**Status:** ✅ Ready to Deploy  
**Date:** April 2, 2026

---

## Pre-Flight Checklist

- [x] All tests passed (5/5)
- [x] No syntax errors
- [x] Fallback mechanism implemented
- [x] Extensive logging added
- [x] Deployment scripts ready
- [x] Rollback plan ready

---

## Deploy Now (Choose One)

### Option 1: Automated Script (Recommended)

**Linux/Mac:**
```bash
bash deploy_phase2_risk_sizing.sh
```

**Windows:**
```cmd
deploy_phase2_risk_sizing.bat
```

### Option 2: Manual Deployment

```bash
# 1. Backup
ssh root@147.93.156.165 "
cd /root/cryptomentor-bot/Bismillah/app
cp autotrade_engine.py autotrade_engine.py.phase2_backup
cp scalping_engine.py scalping_engine.py.phase2_backup
"

# 2. Upload
scp Bismillah/app/autotrade_engine.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/scalping_engine.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# 3. Restart
ssh root@147.93.156.165 "systemctl restart cryptomentor.service"

# 4. Monitor
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -f"
```

---

## Monitor (First 24 Hours)

### Watch Live Logs:
```bash
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -f | grep -i 'risksizing\|fallback\|error'"
```

### Check Risk Sizing Working:
```bash
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -n 100 | grep RiskSizing"
```

**Good:** See messages like:
```
[RiskSizing:123456] BTCUSDT - Balance=$100.00, Risk=2%, Entry=$50000.00, SL=$49000.00, Position=$100.00, Margin=$10.00, Qty=0.002
```

**Bad:** See messages like:
```
[RiskSizing:123456] FAILED: ... - Falling back to fixed margin system
```

---

## Rollback (If Needed)

```bash
ssh root@147.93.156.165 "
systemctl stop cryptomentor.service
cd /root/cryptomentor-bot/Bismillah/app
cp autotrade_engine.py.phase2_backup autotrade_engine.py
cp scalping_engine.py.phase2_backup scalping_engine.py
systemctl start cryptomentor.service
"
```

---

## What Changed

### Before (Fixed Margin):
- User sets $10 capital
- Every trade uses $10 * leverage
- No compounding

### After (Risk-Based):
- User sets 2% risk
- Position size varies by SL distance
- Automatic compounding as balance grows

### Example:
```
Balance: $100, Risk: 2%
Entry: $50,000, SL: $49,000 (2% away)
Leverage: 10x

Position: $100 (risk $2 / 0.02 SL distance)
Margin: $10 ($100 / 10x)
Qty: 0.002 BTC

If SL hits: Lose exactly $2 (2% of balance) ✅
```

---

## Success Indicators

✅ Logs show `[RiskSizing:xxx]` messages  
✅ Position sizes vary based on balance  
✅ No "FALLBACK" messages  
✅ Trades execute successfully  
✅ No account blow-ups  

---

## Support

**Issues?** Check:
1. Service status: `ssh root@147.93.156.165 "systemctl status cryptomentor.service"`
2. Recent logs: `ssh root@147.93.156.165 "journalctl -u cryptomentor.service -n 100"`
3. Errors: `ssh root@147.93.156.165 "journalctl -u cryptomentor.service -n 100 | grep -i error"`

**Still issues?** Rollback and investigate.

---

**Ready to deploy? Run the script and monitor closely!** 🚀
