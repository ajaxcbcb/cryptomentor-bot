# Scalping Engine Not Generating Signals - Investigation

## Problem Discovered

After deploying the ranging market fix to `autosignal_async.py`, the scalping engines are initialized but NOT generating any signals.

## Evidence from VPS Logs

### ✅ What's Working:
```
Apr 03 16:02:40 - [Scalping:1234500018] Engine initialized with config: ScalpingConfig(...)
Apr 03 16:02:41 - [Scalping:1234500011] Engine initialized with config: ScalpingConfig(...)
Apr 03 16:02:41 - [Scalping:1234500007] Engine initialized with config: ScalpingConfig(...)
... (10 engines total initialized)
```

### ❌ What's NOT Working:
- **NO scalping signal generation logs** (should see "[Scalping:XXX] Signal generated")
- **NO scalping scan logs** (should see "[Scalping:XXX] Scanning...")
- **NO errors from scalping engines** (silent failure)

### What IS Working (OLD Swing Engine):
```
Apr 03 16:06:29 - [Engine:1234500019] Max concurrent positions (4) reached
Apr 03 16:02:49 - [Signal] BTCUSDT SHORT conf=73% entry=66644.5000 ...
```

## Possible Root Causes

### 1. Scan Loop Not Executing
- Scalping engine `run()` method may not be starting
- Async loop may be blocked or not scheduled
- Check: Is `await engine.run()` being called?

### 2. Silent Exception in Signal Generation
- `compute_signal_scalping_async()` may be throwing exception
- Exception caught but not logged
- Check: Add try/except logging in `generate_scalping_signal()`

### 3. Trading Mode Mismatch
- Database may not have `trading_mode="scalping"` set
- Engine checks trading mode before scanning
- Check: Query `autotrade_sessions` table for `trading_mode` column

### 4. Validation Failing Silently
- Signals generated but rejected by `validate_scalping_entry()`
- No logs for rejected signals
- Check: Add logging for validation failures

## Investigation Steps

### Step 1: Check Database Trading Mode
```sql
SELECT telegram_id, trading_mode, risk_mode 
FROM autotrade_sessions 
WHERE is_active = true;
```

Expected: `trading_mode = "scalping"` for 10 users

### Step 2: Add Debug Logging to Scalping Engine
Add to `scalping_engine.py` in `run()` method:
```python
async def run(self):
    self.running = True
    logger.info(f"[Scalping:{self.user_id}] Engine started - SCAN LOOP BEGINNING")
    
    try:
        while self.running:
            logger.debug(f"[Scalping:{self.user_id}] Scan iteration starting...")
            # ... rest of code
```

### Step 3: Add Debug Logging to Signal Generation
Add to `generate_scalping_signal()`:
```python
async def generate_scalping_signal(self, symbol: str):
    logger.debug(f"[Scalping:{self.user_id}] Generating signal for {symbol}...")
    try:
        signal_dict = await compute_signal_scalping_async(...)
        logger.debug(f"[Scalping:{self.user_id}] Signal dict: {signal_dict}")
        # ... rest of code
```

### Step 4: Check if Engines Are Actually Running
Add to `scheduler.py` or wherever engines are started:
```python
logger.info(f"[Scheduler] Starting scalping engine for user {user_id}")
asyncio.create_task(engine.run())
logger.info(f"[Scheduler] Scalping engine task created for user {user_id}")
```

## Quick Fix Options

### Option 1: Restart with Debug Logging
1. Add debug logging to scalping engine
2. Deploy to VPS
3. Restart bot
4. Monitor logs for 1 minute

### Option 2: Check Database First
1. SSH to VPS
2. Query database for trading_mode
3. If not "scalping", run migration again
4. Restart bot

### Option 3: Force Manual Test
1. Create test script that calls `compute_signal_scalping_async()` directly
2. Run on VPS to verify signal generation works
3. If works, issue is in engine initialization/scheduling

## Expected Behavior

### What SHOULD Happen:
```
16:02:40 - [Scalping:1234500018] Engine initialized
16:02:40 - [Scalping:1234500018] Engine started - SCAN LOOP BEGINNING
16:02:40 - [Scalping:1234500018] Scanning BTCUSDT...
16:02:41 - [Scalping:1234500018] Signal generated: BTCUSDT LONG @ 66500 (confidence: 82%)
16:02:41 - [Scalping:1234500018] Validation passed
16:02:41 - [Scalping:1234500018] Order placed: BTCUSDT LONG
... (every 15 seconds)
```

### What IS Happening:
```
16:02:40 - [Scalping:1234500018] Engine initialized
... (silence - no scan logs, no signal logs, no errors)
```

## Next Actions

1. **IMMEDIATE**: Check database trading_mode values
2. **IF trading_mode correct**: Add debug logging and redeploy
3. **IF trading_mode wrong**: Run migration script again
4. **VERIFY**: Monitor logs for 2-3 minutes after restart

## Files to Check/Modify

- `Bismillah/app/scalping_engine.py` - Add debug logging
- `Bismillah/app/scheduler.py` - Check engine startup
- `Bismillah/app/autosignal_async.py` - Already updated (working)
- `migrate_all_to_scalping.py` - May need to run again

## Status

- **Code**: ✅ Deployed (ranging market logic)
- **Engines**: ✅ Initialized (10 engines)
- **Scanning**: ❌ NOT WORKING (no logs)
- **Signals**: ❌ NOT WORKING (no logs)
- **Root Cause**: 🔍 INVESTIGATING

---

**Created**: 2026-04-03 16:08 CEST
**Status**: BLOCKED - Need to investigate why engines are silent
