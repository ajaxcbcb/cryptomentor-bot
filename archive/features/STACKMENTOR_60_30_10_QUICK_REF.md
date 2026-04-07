# StackMentor 60/30/10 - Quick Reference

## Configuration

```
TP1: 60% @ R:R 1:2 → Move SL to Breakeven
TP2: 30% @ R:R 1:3 → Keep SL at Breakeven
TP3: 10% @ R:R 1:5 → Full Close
```

## Example Trade

**Position:** 0.1 BTC @ $50,000 (10x leverage)
**SL:** $49,000 (risk $100)

### TP Levels
- **TP1:** $52,000 → Close 0.06 BTC → Profit +$120
- **TP2:** $53,000 → Close 0.03 BTC → Profit +$90
- **TP3:** $55,000 → Close 0.01 BTC → Profit +$50

### Total Profit: +$260 (R:R 1:2.6)

## Scenarios

### Best Case (All TPs Hit)
- TP1: +$120 ✅
- TP2: +$90 ✅
- TP3: +$50 ✅
- **Total: +$260**

### Good Case (TP1 + TP2, TP3 at BE)
- TP1: +$120 ✅
- TP2: +$90 ✅
- TP3: $0 (stopped at breakeven)
- **Total: +$210**

### Acceptable Case (TP1 only, rest at BE)
- TP1: +$120 ✅
- TP2: $0 (stopped at breakeven)
- TP3: $0 (stopped at breakeven)
- **Total: +$120**

### Worst Case (SL before TP1)
- **Total: -$100**

## Deployment

```bash
# Run deployment script
deploy_stackmentor_60_30_10.bat

# Or manually
pscp -pw <REDACTED_VPS_PASSWORD> Bismillah/app/stackmentor.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
plink -pw <REDACTED_VPS_PASSWORD> root@147.93.156.165 "systemctl restart cryptomentor"
```

## Verification

```bash
# Check logs
plink -pw <REDACTED_VPS_PASSWORD> root@147.93.156.165 "journalctl -u cryptomentor -f --lines=50"

# Look for:
# - "TP1 HIT" → Should close 60%
# - "SL moved to breakeven"
# - "TP2 HIT" → Should close 30%
# - "TP3 HIT" → Should close 10%
```

## Files Changed

- `Bismillah/app/stackmentor.py` - Configuration updated

## Status

✅ Tested and ready for deployment
