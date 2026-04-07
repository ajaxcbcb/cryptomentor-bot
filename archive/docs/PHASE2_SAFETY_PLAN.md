# Phase 2: Risk-Based Position Sizing - Safety Plan

**Date:** April 2, 2026  
**Status:** PLANNING  
**Risk Level:** HIGH (Core trading logic changes)

---

## Safety-First Approach

### Critical Rules:
1. ⚠️ **NEVER deploy directly to production**
2. ✅ **Test with demo accounts first**
3. ✅ **Start with minimum position sizes**
4. ✅ **Add extensive logging**
5. ✅ **Keep fallback to old system**
6. ✅ **Monitor every trade**
7. ✅ **Be ready to rollback instantly**

---

## Implementation Strategy

### Phase 2A: Preparation (Today)
- ✅ Create comprehensive test suite
- ✅ Add safety checks and validation
- ✅ Implement fallback mechanism
- ✅ Add detailed logging

### Phase 2B: Integration (Tomorrow)
- ⏳ Update autotrade_engine.py carefully
- ⏳ Update scalping_engine.py carefully
- ⏳ Test with demo accounts
- ⏳ Verify calculations

### Phase 2C: Testing (Day 3-4)
- ⏳ Test all scenarios
- ⏳ Test edge cases
- ⏳ Test with different balances
- ⏳ Test with different risk %

### Phase 2D: Deployment (Day 5)
- ⏳ Deploy during low-traffic hours
- ⏳ Monitor closely for 48 hours
- ⏳ Collect user feedback
- ⏳ Fix any issues immediately

---

## Safety Mechanisms

### 1. Fallback System
If risk-based calculation fails, fall back to fixed margin:
```python
try:
    # Try risk-based position sizing
    sizing = calculate_position_size(...)
    if sizing['valid']:
        qty = sizing['qty']
    else:
        # Fallback to old system
        qty = calc_qty_old(symbol, amount * leverage, entry)
except Exception as e:
    logger.error(f"Risk sizing failed: {e}")
    # Fallback to old system
    qty = calc_qty_old(symbol, amount * leverage, entry)
```

### 2. Validation Checks
Before every trade:
- ✅ Balance > 0
- ✅ Risk % in valid range (0.5-10%)
- ✅ SL distance reasonable (0.1-15%)
- ✅ Position size not too large
- ✅ Margin doesn't exceed balance

### 3. Extensive Logging
Log everything:
```python
logger.info(f"[RiskSizing] User {user_id}: balance=${balance:.2f}, "
            f"risk={risk_pct}%, entry=${entry:.2f}, sl=${sl:.2f}, "
            f"position=${position_size:.2f}, margin=${margin:.2f}, qty={qty}")
```

### 4. Emergency Stop
If anything looks wrong:
```python
if margin_required > balance * 0.95:
    logger.error(f"[EMERGENCY] Margin too high! Stopping trade.")
    await notify_admin(...)
    return  # Don't execute trade
```

---

## Testing Checklist

### Unit Tests:
- [ ] Position sizing with various balances
- [ ] Position sizing with various risk %
- [ ] Position sizing with various SL distances
- [ ] Edge cases (very small balance, very large balance)
- [ ] Invalid inputs (negative values, zero values)

### Integration Tests:
- [ ] Full trade flow with risk-based sizing
- [ ] Balance fetching from exchange
- [ ] Risk % fetching from database
- [ ] Fallback mechanism
- [ ] Error handling

### Live Tests (Demo Account):
- [ ] Execute 1 trade with 1% risk
- [ ] Execute 1 trade with 2% risk
- [ ] Execute 1 trade with 5% risk
- [ ] Verify position sizes correct
- [ ] Verify margin usage correct
- [ ] Verify no account blow-up

---

## Rollback Plan

### If Issues Found:
1. **Immediate:** Stop all engines
2. **Restore:** Upload old engine files
3. **Restart:** Service with old code
4. **Notify:** Users about temporary issue
5. **Fix:** Issues in development
6. **Re-test:** Before deploying again

### Rollback Commands:
```bash
# Stop service
ssh root@147.93.156.165 "systemctl stop cryptomentor.service"

# Restore backup
ssh root@147.93.156.165 "
cd /root/cryptomentor-bot/Bismillah/app
cp autotrade_engine.py.backup autotrade_engine.py
cp scalping_engine.py.backup scalping_engine.py
"

# Restart service
ssh root@147.93.156.165 "systemctl start cryptomentor.service"
```

---

## Monitoring Plan

### First 24 Hours:
- Check logs every 2 hours
- Monitor all trades
- Verify position sizes
- Check for errors
- Collect user feedback

### First Week:
- Daily log review
- Weekly summary report
- User satisfaction survey
- Performance metrics

---

## Success Criteria

### Must Have:
- ✅ No account blow-ups
- ✅ Position sizes calculated correctly
- ✅ Trades execute successfully
- ✅ No errors in logs
- ✅ Users satisfied

### Nice to Have:
- ✅ Better risk management
- ✅ Improved compounding
- ✅ Positive user feedback
- ✅ Increased trading volume

---

## Risk Assessment

### High Risk Areas:
1. **Position size calculation** - Wrong math = blown accounts
2. **Balance fetching** - Stale data = wrong position size
3. **Risk % validation** - Invalid values = errors
4. **Fallback mechanism** - Must work 100%
5. **Edge cases** - Small balances, large balances

### Mitigation:
- Extensive testing
- Multiple validation layers
- Fallback to old system
- Detailed logging
- Close monitoring

---

## Communication Plan

### Before Deployment:
- Notify users about upcoming feature
- Explain benefits
- Set expectations

### During Deployment:
- Announce maintenance window
- Keep users informed
- Provide support

### After Deployment:
- Announce successful deployment
- Provide user guide
- Collect feedback

---

**Next Step:** Create comprehensive test suite before touching engine code.

