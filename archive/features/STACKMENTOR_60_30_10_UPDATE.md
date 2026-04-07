# StackMentor Configuration Update: 60/30/10 Split

## Summary
Updated StackMentor system configuration from 50%/40%/10% to 60%/30%/10% split with adjusted R:R ratios as requested.

## Changes Made

### 1. Configuration Update (`Bismillah/app/stackmentor.py`)

**Previous Configuration:**
- TP1: 50% @ R:R 1:2
- TP2: 40% @ R:R 1:3
- TP3: 10% @ R:R 1:10

**New Configuration:**
- TP1: 60% @ R:R 1:2
- TP2: 30% @ R:R 1:3
- TP3: 10% @ R:R 1:5

### 2. Code Changes

```python
# Updated STACKMENTOR_CONFIG
STACKMENTOR_CONFIG = {
    "enabled": True,
    "tp1_pct": 0.60,          # Changed from 0.50
    "tp2_pct": 0.30,          # Changed from 0.40
    "tp3_pct": 0.10,          # Unchanged
    "tp1_rr": 2.0,            # Unchanged
    "tp2_rr": 3.0,            # Unchanged
    "tp3_rr": 5.0,            # Changed from 10.0
    "breakeven_after_tp1": True,
}
```

### 3. Updated Functions

1. **Documentation strings** - Updated to reflect 60%/30%/10% split
2. **Notification messages** - Updated percentages in user notifications
3. **Comments** - Updated inline comments for clarity

### 4. Behavior

**TP1 Hit (60% close):**
- Close 60% of position at 1:2 R:R
- Move SL to breakeven (entry price)
- Position becomes risk-free
- Remaining 40% runs to TP2/TP3

**TP2 Hit (30% close):**
- Close 30% of original position at 1:3 R:R
- SL remains at breakeven
- Final 10% runs to TP3

**TP3 Hit (10% close):**
- Close final 10% at 1:5 R:R
- Position fully closed
- Maximum profit achieved

## Benefits of 60/30/10 Split

### Compared to 50/40/10:

1. **Faster Profit Locking**
   - 60% secured at TP1 vs 50% (20% more capital secured early)
   - Reduces exposure to reversals after TP1

2. **Better Risk Management**
   - More capital protected at breakeven after TP1
   - Only 40% exposed to market after TP1 (vs 50%)

3. **Balanced Approach**
   - Still maintains 30% runner for TP2 (good profit potential)
   - 10% lottery ticket for TP3 (1:5 R:R is more realistic than 1:10)

4. **Psychological Benefits**
   - Traders feel more secure with 60% locked
   - Less stress watching remaining position
   - Higher satisfaction rate

## Example Trade

**Entry:** $50,000 BTC LONG
**Position Size:** 0.1 BTC ($5,000)
**SL:** $49,000 (1% risk = $100)
**Leverage:** 10x

**TP Levels:**
- TP1: $51,000 (1:2 R:R) → Close 0.06 BTC → Profit: $60
- TP2: $51,500 (1:3 R:R) → Close 0.03 BTC → Profit: $45
- TP3: $52,500 (1:5 R:R) → Close 0.01 BTC → Profit: $25

**Total Potential Profit:** $130 (1.3:1 average R:R if all TPs hit)

**Scenarios:**
1. All TPs hit: +$130 (best case)
2. TP1 + TP2 hit, TP3 stopped at BE: +$105 (good case)
3. TP1 hit, TP2/TP3 stopped at BE: +$60 (acceptable case)
4. SL hit before TP1: -$100 (worst case)

## Database Schema

No changes needed - existing `autotrade_trades` table already has:
- `tp1_hit`, `tp2_hit`, `tp3_hit` (BOOLEAN)
- `tp1_hit_at`, `tp2_hit_at`, `tp3_hit_at` (TIMESTAMPTZ)
- `profit_tp1`, `profit_tp2`, `profit_tp3` (NUMERIC)
- `breakeven_mode` (BOOLEAN)

## Testing Checklist

- [ ] Test TP1 hit → 60% closes correctly
- [ ] Test SL moves to breakeven after TP1
- [ ] Test TP2 hit → 30% closes correctly
- [ ] Test TP3 hit → 10% closes correctly
- [ ] Test notifications show correct percentages
- [ ] Test quantity splits round correctly
- [ ] Test with small positions (minimum qty)
- [ ] Test with large positions
- [ ] Test SL validation (prevent error 30029)

## Deployment

### Files Changed:
1. `Bismillah/app/stackmentor.py` - Configuration and logic updated

### Deployment Steps:
1. Upload updated `stackmentor.py` to VPS
2. Restart bot service
3. Monitor first few trades for correct behavior
4. Verify notifications show 60%/30%/10%

### Deployment Commands:
```bash
# Upload file
pscp -pw <REDACTED_VPS_PASSWORD> Bismillah/app/stackmentor.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# Restart service
plink -pw <REDACTED_VPS_PASSWORD> root@147.93.156.165 "systemctl restart cryptomentor"

# Check logs
plink -pw <REDACTED_VPS_PASSWORD> root@147.93.156.165 "journalctl -u cryptomentor -f --lines=50"
```

## Rollback Plan

If issues occur, revert to previous configuration:
```python
STACKMENTOR_CONFIG = {
    "tp1_pct": 0.50,
    "tp2_pct": 0.40,
    "tp3_pct": 0.10,
    "tp1_rr": 2.0,
    "tp2_rr": 3.0,
    "tp3_rr": 10.0,
}
```

## Notes

- StackMentor is enabled for ALL users (not just premium)
- Eligibility based on balance ≥ $60
- Percentages are based on quantity of pairs ordered (not dollar amount)
- SL validation prevents error 30029 (invalid SL price)
- System automatically handles rounding for exchange precision

## Status

✅ Configuration updated
✅ Code updated
✅ Documentation updated
⏳ Ready for deployment
⏳ Awaiting testing

---

**Updated:** 2026-01-04
**By:** Kiro AI Assistant
**Requested by:** User (60%/30%/10% split with 1:2/1:3/1:5 R:R)
