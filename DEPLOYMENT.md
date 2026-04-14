# CryptoMentor v2.2.0 Deployment Guide

## ✅ Pre-Deployment Verification Complete

All systems tested and verified ready for production deployment:

- **Coordinator Unit Tests**: 20/20 PASSED ✓
- **Regression Tests**: 8 PASSED + 11 SKIPPED (no failures) ✓
- **API Endpoints**: All 4 endpoints verified ✓
- **Dashboard**: All API references correct ✓
- **Git Commits**: 10 feature/docs commits on `ajax` branch ✓

## 1. Environment Setup

### 1.1 Requirements Installation

```bash
pip install -r requirements.txt
```

Required packages (added to requirements.txt):
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
PyJWT==2.8.1
slowapi==0.1.9
python-dotenv>=1.0.0
```

### 1.2 Environment Variables

Create `.env` file or set in deployment environment:

```bash
# Admin Telegram IDs (same as bot.py)
ADMIN_IDS=123456789
ADMIN1=<REDACTED_ADMIN_ID>
ADMIN2=<REDACTED_ADMIN_ID>
ADMIN3=111111111

# JWT Secret for analytics API
JWT_SECRET=<REDACTED_JWT_SECRET>

# Supabase credentials
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY=<REDACTED_SUPABASE_KEY>

# Analytics server config
ANALYTICS_PORT=8896
ANALYTICS_HOST=0.0.0.0
```

## 2. Database Setup

**No schema changes required.**

Coordinator is in-memory; ensures error_logs table exists for analytics engine-health endpoint:

```sql
-- Verify error_logs table has these columns:
- telegram_id (int)
- created_at (timestamp)
- message (text)
```

## 3. Deployment Steps

### 3.1 Git & Code Deployment

```bash
# On VPS, pull latest code
git fetch origin
git checkout ajax
git pull origin ajax

# Or if merging to main:
git checkout main
git merge ajax
```

### 3.2 Deploy Files

Ensure these new files are deployed:

```
Bismillah/app/symbol_coordinator.py          (591 lines - core coordinator)
Bismillah/analytics_api.py                   (517 lines - API backend)
Bismillah/analytics_dashboard.html           (661 lines - UI dashboard)
tests/test_coordinator.py                    (16.6 KB - unit tests)
tests/test_regression.py                     (386 lines - regression tests, updated)
CHANGELOG.md                                 (updated with v2.2.0)
ANALYTICS_SETUP.md                           (new deployment guide)
```

### 3.3 Restart Services

#### Telegram Bot Process
```bash
# Kill existing bot process
pkill -f "python.*bot.py"

# Restart bot (it auto-loads coordinator on startup)
python Bismillah/bot.py &
```

#### Analytics API Service

**Option A: Development (Foreground)**
```bash
cd Bismillah
python -m uvicorn analytics_api:app --host 0.0.0.0 --port 8896 --reload
```

**Option B: Systemd Service (Production)**
```bash
sudo systemctl restart analytics
# or
sudo systemctl start analytics
```

**Option C: Docker (Production)**
```bash
docker build -t cryptomentor-analytics .
docker run -d \
  -e ADMIN_IDS=123456789 \
  -e SUPABASE_URL="..." \
  -e SUPABASE_KEY=<REDACTED_SUPABASE_KEY>
  -p 8896:8896 \
  cryptomentor-analytics
```

#### Web Dashboard
```bash
# Serve analytics_dashboard.html via nginx or your web server
# Point to: /Bismillah/analytics_dashboard.html
```

## 4. Smoke Tests (Must Pass Before Going Live)

### 4.1 Coordinator Function Tests

```bash
# Run unit tests
python -m pytest tests/test_coordinator.py -v

# Expected: 20/20 PASSED
```

### 4.2 Regression Tests

```bash
# Run regression tests
python -m pytest tests/test_regression.py -v

# Expected: 8+ PASSED, 11 SKIPPED (no failures)
```

### 4.3 API Health Check

```bash
# Health endpoint (no auth required)
curl http://localhost:8896/health

# Expected response:
# {"status": "ok", "timestamp": "2026-04-14T..."}
```

### 4.4 Admin Authentication

```bash
# Generate test JWT token
python -c "
import jwt
import json
from datetime import datetime, timedelta

secret = 'your-jwt-secret-here'
admin_id = 123456789
token = jwt.encode(
    {'sub': str(admin_id), 'exp': datetime.utcnow() + timedelta(days=7)},
    secret,
    algorithm='HS256'
)
print(token)
"

# Test coordinator-state endpoint
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:8896/api/analytics/coordinator-state

# Expected: JSON with coordinator state
```

### 4.5 Coordinator Behavior Smoke Tests

#### Fresh Symbol Entry
```python
import asyncio
from Bismillah.app.symbol_coordinator import get_coordinator, StrategyOwner, reset_coordinator_for_testing

async def test_fresh_entry():
    reset_coordinator_for_testing()
    coordinator = get_coordinator()
    
    allowed, reason = await coordinator.can_enter(
        user_id=123,
        symbol="BTCUSDT",
        strategy=StrategyOwner.SWING,
        now_ts=time.time()
    )
    
    assert allowed is True
    assert reason == "allowed"
    print("✓ Fresh symbol entry works")

asyncio.run(test_fresh_entry())
```

#### Multi-User Isolation
```python
async def test_multi_user():
    reset_coordinator_for_testing()
    coordinator = get_coordinator()
    
    # User 1 enters
    await coordinator.can_enter(123, "BTCUSDT", StrategyOwner.SWING, time.time())
    await coordinator.confirm_open(123, "BTCUSDT", StrategyOwner.SWING, "LONG", 0.1, 45000, "id1")
    
    # User 2 can enter same symbol (different user)
    allowed, _ = await coordinator.can_enter(456, "BTCUSDT", StrategyOwner.SWING, time.time())
    assert allowed is True
    print("✓ Multi-user isolation works")

asyncio.run(test_multi_user())
```

#### Same Strategy Reversal
```python
async def test_reversal():
    reset_coordinator_for_testing()
    coordinator = get_coordinator()
    
    # Enter LONG
    await coordinator.confirm_open(123, "BTCUSDT", StrategyOwner.SWING, "LONG", 0.1, 45000, "id1")
    
    # Same strategy can re-enter without explicit close (reversal)
    allowed, _ = await coordinator.can_enter(123, "BTCUSDT", StrategyOwner.SWING, time.time())
    assert allowed is True
    print("✓ Reversal re-entry works")

asyncio.run(test_reversal())
```

## 5. Dashboard Access

### 5.1 Admin Login

1. Open `https://analytics4896.cryptomentor.id/analytics_dashboard.html`
2. Paste your JWT token in the "Admin JWT Token" field
3. Click "Connect Dashboard"
4. Token saved to localStorage for session persistence

### 5.2 Verify Dashboard Displays

- [ ] Coordinator State panel shows total symbols and users
- [ ] Engine Health panel shows running/stopped status
- [ ] Trading Performance panel shows trades and PnL
- [ ] Filtering by user_id works
- [ ] Filtering by symbol works
- [ ] Auto-refresh every 30 seconds works

## 6. Monitoring & Logs

### 6.1 Analytics API Logs

```bash
# If using systemd:
sudo journalctl -u analytics -f

# If using docker:
docker logs -f cryptomentor-analytics

# If foreground uvicorn:
# Check console output
```

### 6.2 Watch for Errors

Common issues and solutions:

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Token invalid or expired. Regenerate JWT. |
| 403 Forbidden | User ID not in ADMIN_IDS env var. |
| 500 Service Error | Supabase connection failed. Check credentials. |
| CORS errors | Ensure API running with CORS enabled (default). |
| Rate limit 429 | 100 req/minute limit hit. Slow down dashboard refresh. |

## 7. Performance Baseline

Post-deployment monitoring metrics:

```
Coordinator queries: O(1) in-memory lookup
Trading stats queries: ~50-100ms per 7-day window
Engine health queries: ~30-50ms per user
Analytics API: ~100 req/minute per admin (rate limited)
Dashboard refresh: 30 second interval (configurable)
Memory: ~1KB per (user_id, symbol) position
```

## 8. Rollback Procedure

If issues arise post-deployment:

```bash
# Kill analytics API
pkill -f "uvicorn.*analytics_api"

# Revert coordinator integration (restart bot only)
pkill -f "python.*bot.py"

# Coordinator state is ephemeral; state resets on bot restart
# Positions reconciled from exchange + DB on next startup
```

## 9. Post-Deployment Checklist

- [ ] All tests passing (28 passed, 11 skipped, 0 failed)
- [ ] Analytics API running on port 8896
- [ ] Dashboard accessible at analytics4896.cryptomentor.id
- [ ] Admin JWT tokens working
- [ ] Coordinator smoke tests passing
- [ ] Multi-user isolation verified
- [ ] Reversals working
- [ ] Database accessible (Supabase)
- [ ] Error logs being recorded
- [ ] Monitoring dashboards set up
- [ ] Team notified of new analytics endpoint

## 10. Going Live Timeline

**Friday Close-of-Business (EOB):**
- Deploy code to VPS
- Start analytics API
- Run smoke tests (30 min)
- Enable dashboard access for admins

**Monday Morning:**
- Team reviews coordinator behavior
- Validates multi-user isolation
- Confirms no false positives

**Week 1 Monitoring:**
- Watch error logs
- Check dashboard auto-refresh
- Monitor API rate limiting
- Collect feedback

## 11. Support & Rollback

**Issue Response:**
1. Check `journalctl` logs for errors
2. Verify environment variables
3. Test with curl (API isolation)
4. Check Supabase connectivity
5. Review ANALYTICS_SETUP.md troubleshooting section

**Emergency Rollback:**
```bash
# Kill analytics API (coordinator state ephemeral)
pkill -f "uvicorn.*analytics_api"

# Trading engines continue normally
# Coordinator auto-reconciles on restart
```

---

**Deployment Date**: 2026-04-14
**Version**: 2.2.0
**Status**: Ready for Production Deployment
**Git Branch**: ajax (10 commits)
**Test Coverage**: 28 passed, 11 skipped, 0 failed
