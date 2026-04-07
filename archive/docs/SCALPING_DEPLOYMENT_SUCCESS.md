# ✅ Scalping Mode - Deployment Success

## Files Uploaded to VPS

### Database Migration
- ✅ `db/add_trading_mode.sql` → `/root/cryptomentor-bot/db/`

### New Files (3)
- ✅ `Bismillah/app/trading_mode.py` → `/root/cryptomentor-bot/Bismillah/app/`
- ✅ `Bismillah/app/trading_mode_manager.py` → `/root/cryptomentor-bot/Bismillah/app/`
- ✅ `Bismillah/app/scalping_engine.py` → `/root/cryptomentor-bot/Bismillah/app/`

### Modified Files (3)
- ✅ `Bismillah/app/autosignal_fast.py` → `/root/cryptomentor-bot/Bismillah/app/`
- ✅ `Bismillah/app/handlers_autotrade.py` → `/root/cryptomentor-bot/Bismillah/app/`
- ✅ `Bismillah/app/autotrade_engine.py` → `/root/cryptomentor-bot/Bismillah/app/`

## Next Steps (Run on VPS)

### SSH to VPS
```bash
ssh root@147.93.156.165
# Password: <REDACTED_VPS_PASSWORD>
```

### Run These Commands
```bash
# 1. Backup database
cd /root/cryptomentor-bot
pg_dump cryptomentor > backup_scalping_$(date +%Y%m%d_%H%M%S).sql

# 2. Run database migration
psql cryptomentor < db/add_trading_mode.sql

# 3. Verify migration
psql cryptomentor -c "SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name='autotrade_sessions' AND column_name='trading_mode';"

# Expected output:
# column_name  | data_type         | column_default
# trading_mode | character varying | 'swing'::character varying

# 4. Restart service
systemctl restart cryptomentor.service

# 5. Check status
systemctl status cryptomentor.service

# 6. Monitor logs
journalctl -u cryptomentor.service -f
```

## Verification Checklist

### On VPS
- [ ] Database backup created
- [ ] Migration runs without errors
- [ ] Column `trading_mode` exists in `autotrade_sessions` table
- [ ] Service restarts successfully
- [ ] No errors in logs
- [ ] Bot responds to commands

### In Telegram
- [ ] Run `/autotrade` command
- [ ] Dashboard displays correctly
- [ ] "⚙️ Trading Mode" button appears
- [ ] Click button → Mode selection menu appears
- [ ] Both modes listed (Scalping & Swing)
- [ ] Current mode marked with ✅
- [ ] Select Scalping mode → Confirmation message
- [ ] Dashboard updates to show "⚡ Mode: Scalping (5M)"
- [ ] Logs show: `[AutoTrade:user_id] Started SCALPING engine`

## Expected Behavior

### Default State
- All users start with Swing Mode (15M)
- Dashboard shows: "📊 Mode: Swing (15M)"

### After Switching to Scalping
- Dashboard shows: "⚡ Mode: Scalping (5M)"
- Engine restarts automatically
- Logs show: `[AutoTrade:user_id] Started SCALPING engine`
- Scan interval: 15 seconds (vs 45s for swing)
- Min confidence: 80% (vs 68% for swing)

### Mode Selection Menu
```
⚙️ Select Trading Mode

⚡ Scalping Mode (5M):
• Fast trades on 5-minute chart
• 10-20 trades per day
• Single TP at 1.5R
• 30-minute max hold time
• Pairs: BTC, ETH

📊 Swing Mode (15M):
• Swing trades on 15-minute chart
• 2-3 trades per day
• 3-tier TP (StackMentor)
• No max hold time
• Pairs: BTC, ETH, SOL, BNB

Current mode: SWING

[⚡ Scalping Mode (5M)]
[✅ 📊 Swing Mode (15M)]
[🔙 Back to Dashboard]
```

## Monitoring

### Key Log Patterns to Watch
```bash
# Mode switches
journalctl -u cryptomentor.service -f | grep "Trading mode"

# Engine starts
journalctl -u cryptomentor.service -f | grep "Started SCALPING\|Started SWING"

# Signal generation
journalctl -u cryptomentor.service -f | grep "\[Signal\]"

# Position management
journalctl -u cryptomentor.service -f | grep "\[Scalping:"
```

### Expected Logs
```
[TradingModeManager] User 123456 switched from SWING to SCALPING
[AutoTrade:123456] Engine stopped for mode switch
[AutoTrade:123456] Started SCALPING engine (exchange=bitunix)
[Scalping:123456] Engine started — scan_interval=15s, min_conf=80%
[Signal] BTCUSDT LONG conf=82% entry=43250.00 sl=43100.00 tp=43475.00
[Scalping:123456] Position opened: BTCUSDT LONG @ 43250.00
[Scalping:123456] Position closed: max_hold_time_exceeded (30m)
```

## Troubleshooting

### If Service Fails to Start
```bash
# Check logs for errors
journalctl -u cryptomentor.service -n 100 --no-pager

# Common issues:
# - Import error → Check file permissions
# - Database error → Verify migration ran successfully
# - Syntax error → Check file upload completed
```

### If Mode Switching Doesn't Work
```bash
# Verify database column exists
psql cryptomentor -c "SELECT * FROM autotrade_sessions LIMIT 1;"

# Check if trading_mode column is present
# Should show: trading_mode | swing
```

### Rollback Plan
```bash
# If issues occur, restore from backup
cd /root/cryptomentor-bot
psql cryptomentor < backup_scalping_YYYYMMDD_HHMMSS.sql

# Remove new files
rm Bismillah/app/trading_mode.py
rm Bismillah/app/trading_mode_manager.py
rm Bismillah/app/scalping_engine.py

# Restore old files from git
git checkout HEAD~1 Bismillah/app/handlers_autotrade.py
git checkout HEAD~1 Bismillah/app/autotrade_engine.py
git checkout HEAD~1 Bismillah/app/autosignal_fast.py

# Restart service
systemctl restart cryptomentor.service
```

## Success Criteria

- ✅ All files uploaded successfully
- ✅ Database migration ready to run
- ✅ Service ready to restart
- ⏳ Database migration executed (run on VPS)
- ⏳ Service restarted (run on VPS)
- ⏳ Bot tested in Telegram (after restart)

## Performance Metrics to Track

### Week 1 (Beta Testing)
- Number of users switching to scalping mode
- Average trades per day per user (scalping)
- Win rate (target: 60%+)
- Average hold time (should be < 30 minutes)
- Max hold time violations (should trigger at 30 min)

### Week 2-4 (Full Rollout)
- Total trading volume increase (target: +50-80%)
- User engagement increase (target: +30-50%)
- Signal quality (confidence >= 80%)
- System stability (no crashes)

## Support

### Documentation
- `SCALPING_MODE_DEPLOYMENT_READY.md` - Full deployment guide
- `SCALPING_MODE_COMPLETE.md` - Implementation summary
- `VPS_COMMANDS_SCALPING.txt` - Quick command reference

### Contact
- VPS: root@147.93.156.165
- Service: cryptomentor.service
- Logs: `journalctl -u cryptomentor.service -f`

---

**Deployment Date:** April 2, 2026
**Status:** ✅ Files Uploaded - Ready for Database Migration
**Next Action:** SSH to VPS and run database migration + restart service
