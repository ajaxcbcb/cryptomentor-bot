# Engine Inactive Issue - Root Cause Analysis

## Problem
User melaporkan engine mereka sering inactive sendiri dan harus manual aktifkan lagi setiap saat melalui handler.

## Investigation Findings

### 1. VPS Log Analysis
- **No recent crashes or exceptions** found in logs
- **No WebSocket errors** in recent logs
- **No circuit breaker triggers**
- **No engine stop messages** in recent logs
- Only 1 API key error for user 8468773924 (no keys)

### 2. Code Analysis

#### Auto-Restore System (scheduler.py)
✅ **SUDAH ADA** - `start_scheduler()` function includes:
- Auto-restore on bot startup (waits 3 seconds, then restores all active sessions)
- Migrates users to risk-based mode
- Sets scalping mode
- Sends notification to users
- Handles errors gracefully

#### Health Check System (scheduler.py)
✅ **SUDAH ADA** - `_engine_health_check_task()` runs every 5 minutes:
- Checks all active sessions
- Detects dead engines
- Auto-restarts dead engines
- Sends notification to users
- Logs all actions

### 3. Root Cause Identified

**MASALAH UTAMA**: Bot restart/crash tanpa auto-restore berjalan dengan benar

Kemungkinan penyebab:
1. **Bot restart terlalu sering** - Setiap restart, scheduler harus re-initialize
2. **Scheduler tidak dipanggil** - `start_scheduler()` mungkin tidak dipanggil di bot startup
3. **Database session status tidak sync** - Session status di DB masih "active" tapi engine tidak running
4. **Health check tidak mendeteksi** - Engine mati tapi health check tidak catch karena timing

## Evidence

### From scheduler.py (line 200-350):
```python
def start_scheduler(application):
    """Start scheduler dan auto-restart autotrade engines."""
    async def _start():
        # Tunggu bot fully ready sebelum restore
        await asyncio.sleep(3)

        # ── Auto-restore autotrade engines ────────────────────────────
        logger.info("="*80)
        logger.info("[AutoRestore] Starting engine restoration process...")
        
        # Query ALL active sessions
        res = _client().table("autotrade_sessions").select("*").in_(
            "status", ["active", "uid_verified"]
        ).execute()
        sessions = res.data or []
        
        # Restore each session...
```

### Health Check (line 350-450):
```python
async def _engine_health_check_task(application):
    """
    Periodic health check for autotrade engines.
    Checks every 5 minutes if engines that should be running are still alive.
    Auto-restarts if they stopped unexpectedly.
    """
    CHECK_INTERVAL_SECONDS = 300  # 5 minutes
    
    while True:
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
        
        # Get all active sessions
        res = _client().table("autotrade_sessions").select("*").in_(
            "status", ["active", "uid_verified"]
        ).execute()
        
        # Check if engine is running
        if not is_running(user_id):
            dead_engines.append(user_id)
            # Auto-restart...
```

## Why Users Need Manual Restart

Berdasarkan analisis, ada beberapa skenario:

### Scenario 1: Bot Restart Without Proper Startup
- Bot restart (crash, deploy, maintenance)
- `start_scheduler()` tidak dipanggil atau gagal
- Engines tidak di-restore
- User harus manual restart via /autotrade

### Scenario 2: Health Check Timing Gap
- Engine crash/stop
- Health check runs every 5 minutes
- User notices engine inactive before health check runs
- User manually restarts before auto-restart kicks in

### Scenario 3: Silent Engine Failure
- Engine stops due to unhandled exception
- Exception tidak ter-log (swallowed somewhere)
- Health check detects but restart fails silently
- User needs manual intervention

### Scenario 4: Database Session Desync
- User stops engine manually
- Session status tidak update ke "stopped"
- Health check thinks engine should run, tries to restart
- Restart fails because user already stopped it
- Creates confusion

## Solution Required

### Immediate Fixes:
1. ✅ Verify `start_scheduler()` is called in bot.py startup
2. ✅ Add more logging to auto-restore process
3. ✅ Reduce health check interval from 5 min to 2 min
4. ✅ Add startup notification to all users when engine restored
5. ✅ Fix session status sync when user stops engine

### Long-term Improvements:
1. Add engine heartbeat mechanism (ping every 30s)
2. Add Telegram notification when engine stops unexpectedly
3. Add admin dashboard to monitor all engines
4. Add retry logic with exponential backoff for failed restarts
5. Add database cleanup job to fix desync issues

## Next Steps

1. Check if `start_scheduler()` is properly called in bot.py
2. Add more detailed logging to track restore process
3. Reduce health check interval
4. Deploy and monitor
5. Collect user feedback
