# Deploy Scalping + StackMentor Integration

**Date:** April 7, 2026
**Priority:** HIGH
**Impact:** Scalping mode sekarang menggunakan StackMentor 3-tier TP system

---

## 🎯 What Changed?

Scalping mode sekarang menggunakan **StackMentor 3-tier TP system** untuk memastikan TP/SL selalu ter-set dengan sistem yang proven.

### Before:
- Single TP at 1.5R
- Manual TP/SL setup via exchange API
- Risk: TP/SL bisa gagal

### After:
- **3-tier TP:** 60% @ 2R, 30% @ 3R, 10% @ 10R
- **StackMentor system:** Proven dan aman
- **Auto-breakeven:** SL moves to entry when TP1 hit
- **Guaranteed:** TP/SL ter-set via StackMentor database

---

## 📦 Files Changed

1. **`Bismillah/app/scalping_engine.py`**
   - Modified `place_scalping_order()` - Use StackMentor
   - Added `_notify_stackmentor_opened()` - New notification
   - Modified `monitor_positions()` - Use StackMentor monitoring
   - Modified `_close_position_max_hold()` - Update StackMentor

---

## 🚀 Deployment Commands

```bash
# 1. Backup current version
ssh root@147.93.156.165 "cp /root/cryptomentor-bot/Bismillah/app/scalping_engine.py /root/cryptomentor-bot/Bismillah/app/scalping_engine.py.backup.$(date +%Y%m%d_%H%M%S)"

# 2. Deploy new version
scp Bismillah/app/scalping_engine.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# 3. Restart service
ssh root@147.93.156.165 "systemctl restart cryptomentor"

# 4. Check status
ssh root@147.93.156.165 "systemctl status cryptomentor"

# 5. Monitor logs for StackMentor
ssh root@147.93.156.165 "journalctl -u cryptomentor -f | grep -E 'StackMentor|Scalping'"
```

---

## ✅ Verification

### Check Logs:
```bash
# Should see StackMentor position creation
ssh root@147.93.156.165 "journalctl -u cryptomentor | grep 'StackMentor position opened' | tail -5"

# Should see SL setup success
ssh root@147.93.156.165 "journalctl -u cryptomentor | grep 'SL set @' | tail -5"

# Should see 3-tier TP in notifications
ssh root@147.93.156.165 "journalctl -u cryptomentor | grep '3-Tier Take Profit' | tail -5"
```

### Expected Log Output:
```
[Scalping:123456] StackMentor position opened: ETHUSDT BUY @ 2450.50, Qty: 0.05, TP1=2465.75 TP2=2475.50 TP3=2550.00
[Scalping:123456] SL set @ 2440.25 ✅
```

### User Notification Should Show:
```
⚡ SCALP Trade Opened (StackMentor)

Symbol: ETHUSDT
Side: LONG
Entry: 2,450.50
Quantity: 0.05

🎯 3-Tier Take Profit:
TP1: 2,465.75 (2.0R) - 0.03 (60%)
TP2: 2,475.50 (3.0R) - 0.015 (30%)
TP3: 2,550.00 (10.0R) - 0.005 (10%)

🛡️ Stop Loss: 2,440.25
💡 Auto-Breakeven: SL moves to entry when TP1 hit

✅ TP/SL ter-set dengan StackMentor system!
```

---

## 📊 Benefits

1. **Lebih Aman:** TP/SL guaranteed via StackMentor system
2. **Lebih Profit:** 3-tier TP captures more profit (2-3R vs 1.5R)
3. **Auto-Breakeven:** Risk-free after TP1 hit
4. **User Confidence:** Clear indication TP/SL ter-set
5. **Proven System:** Already used in Swing mode

---

## ⚠️ Important Notes

- StackMentor system already exists and proven
- No database changes needed (uses existing `tp_partial_tracking` table)
- Risk management unchanged (5% max, 10x leverage cap)
- Max hold time still 30 minutes
- Emergency close still active if SL setup fails

---

## 🔍 Monitoring

### Key Metrics to Watch:
- StackMentor position creation rate (should be 100%)
- SL setup success rate (should be 100%)
- TP1/TP2/TP3 hit rates
- Average profit per trade (should increase)
- User feedback on TP/SL confidence

### Alert If:
- StackMentor position creation fails
- SL setup fails (should trigger emergency close)
- No TP hit notifications
- User complaints about TP/SL

---

## 🆘 Rollback Plan

If issues occur:

```bash
# 1. Restore backup
ssh root@147.93.156.165 "cp /root/cryptomentor-bot/Bismillah/app/scalping_engine.py.backup.* /root/cryptomentor-bot/Bismillah/app/scalping_engine.py"

# 2. Restart service
ssh root@147.93.156.165 "systemctl restart cryptomentor"

# 3. Verify rollback
ssh root@147.93.156.165 "journalctl -u cryptomentor -n 50"
```

---

## 📞 Support

### Common Issues:

**Q: StackMentor position not created?**
A: Check logs for error messages. Verify StackMentor module is working.

**Q: SL setup failed?**
A: Emergency close should trigger automatically. Check logs for "EMERGENCY CLOSE".

**Q: User not seeing 3 TP levels?**
A: Check notification function. Verify StackMentor levels calculation.

**Q: TP not hitting?**
A: StackMentor monitoring should handle this. Check `monitor_stackmentor_positions()` logs.

---

**Status:** ✅ READY TO DEPLOY
**Risk Level:** LOW (StackMentor already proven in Swing mode)
**Expected Downtime:** ~30 seconds (service restart)
**Rollback Time:** <2 minutes if needed
