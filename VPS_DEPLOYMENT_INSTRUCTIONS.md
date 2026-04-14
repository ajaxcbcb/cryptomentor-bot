# CryptoMentor v2.2.0 VPS Deployment Instructions

**Status:** Production Ready  
**Date:** 2026-04-14  
**Version:** 2.2.0  
**Branch:** main (12 feature commits)  
**Tests:** 28 PASSED | 11 SKIPPED | 0 FAILED

---

## 📋 Prerequisites

Before deploying, ensure your VPS has:

- ✅ Ubuntu 20.04+ or Debian 10+
- ✅ Python 3.9+
- ✅ Git installed
- ✅ Docker (optional, for container deployment)
- ✅ Supabase credentials (SUPABASE_URL and SUPABASE_KEY)
- ✅ Admin Telegram IDs from bot.py

---

## 🚀 Quick Start (Automated)

### Option 1: Automated Bash Deployment

```bash
# SSH into VPS as cryptomentor user (or with sudo)
ssh user@your-vps-ip

# Navigate to project directory
cd /opt/cryptomentor

# Make deployment script executable
chmod +x deploy.sh

# Run automated deployment
./deploy.sh
```

**What this does:**
1. ✓ Pulls latest code from main branch
2. ✓ Creates/updates Python virtual environment
3. ✓ Installs all dependencies
4. ✓ Runs full test suite
5. ✓ Creates systemd service
6. ✓ Starts analytics API on port 8896
7. ✓ Verifies health check

**Expected output:**
```
✅ DEPLOYMENT COMPLETE
Analytics API: http://localhost:8896
Systemd service: cryptomentor-analytics
```

---

## 🐳 Docker Deployment (Recommended for Production)

### Option 2: Docker Compose

```bash
# Navigate to project directory
cd /opt/cryptomentor

# Create .env file with configuration
cat > .env << EOF
ADMIN_IDS=123456789
ADMIN1=123456789
ADMIN2=987654321
JWT_SECRET="your-secure-secret-here"
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-service-role-key"
EOF

# Build and start
docker-compose up -d

# Verify it's running
docker-compose logs -f analytics
```

**What this does:**
- Builds Docker image with Python 3.11
- Starts analytics API in container on port 8896
- Mounts logs directory for persistence
- Auto-restarts on failure
- Healthcheck every 30 seconds

---

## ⚙️ Manual Deployment (Step-by-Step)

### Step 1: Pull Latest Code

```bash
cd /opt/cryptomentor
git fetch origin
git checkout main
git pull origin main
```

### Step 2: Setup Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Verify key packages
pip list | grep -E "fastapi|uvicorn|PyJWT|slowapi|python-dotenv"
```

Expected output:
```
fastapi              0.104.1
uvicorn              0.24.0
PyJWT                2.8.1
slowapi              0.1.9
python-dotenv        1.0.0
```

### Step 4: Configure Environment

Create `.env` file:

```bash
cat > /opt/cryptomentor/.env << EOF
# Admin Telegram IDs
ADMIN_IDS=123456789
ADMIN1=123456789
ADMIN2=987654321
ADMIN3=111111111

# JWT Secret
JWT_SECRET="your-secure-jwt-secret-here"

# Supabase
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-service-role-key"

# Analytics Server
ANALYTICS_PORT=8896
ANALYTICS_HOST=0.0.0.0
EOF

# Secure the file
chmod 600 /opt/cryptomentor/.env
```

### Step 5: Run Tests

```bash
# Activate venv if not already activated
source venv/bin/activate

# Run coordinator tests
python -m pytest tests/test_coordinator.py -v

# Expected: 20 PASSED

# Run regression tests
python -m pytest tests/test_regression.py -v

# Expected: 8 PASSED, 11 SKIPPED, 0 FAILED
```

### Step 6: Install as Systemd Service

```bash
# Copy service file
sudo cp cryptomentor-analytics.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable cryptomentor-analytics

# Start service
sudo systemctl start cryptomentor-analytics

# Verify it's running
sudo systemctl status cryptomentor-analytics

# Should show: Active: active (running)
```

### Step 7: Verify Deployment

```bash
# Health check
curl http://localhost:8896/health

# Expected response:
# {"status": "ok", "timestamp": "2026-04-14T..."}

# View logs
sudo journalctl -u cryptomentor-analytics -f
```

---

## 🔐 Restart Telegram Bot

The Telegram bot must be restarted to load the coordinator:

```bash
# Kill existing bot process
pkill -f "python.*bot.py"

# Restart bot in background
cd /opt/cryptomentor
source venv/bin/activate
python Bismillah/bot.py &

# Verify it's running
ps aux | grep bot.py
```

---

## ✅ Post-Deployment Verification

### 1. Health Check

```bash
curl -s http://localhost:8896/health | jq .
```

Expected:
```json
{
  "status": "ok",
  "timestamp": "2026-04-14T10:30:00+00:00"
}
```

### 2. Test Coordinator Entry Gating

```bash
# Generate test JWT token
python << 'EOF'
import jwt
from datetime import datetime, timedelta
import os

secret = os.getenv("JWT_SECRET", "analytics-secret-key")
admin_id = int(os.getenv("ADMIN1", "123456789"))
token = jwt.encode(
    {"sub": str(admin_id), "exp": datetime.utcnow() + timedelta(days=7)},
    secret,
    algorithm="HS256"
)
print(f"Token: {token}")
EOF

# Test coordinator-state endpoint
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:8896/api/analytics/coordinator-state | jq .
```

### 3. Run Unit Tests

```bash
python -m pytest tests/test_coordinator.py -v --tb=short
```

Expected: 20 PASSED in 0.15s

### 4. Run Regression Tests

```bash
python -m pytest tests/test_regression.py -v --tb=short
```

Expected: 8 PASSED, 11 SKIPPED, 0 FAILED

### 5. Dashboard Access

Open browser:
```
https://analytics4896.cryptomentor.id/analytics_dashboard.html
```

- Paste JWT token
- Click "Connect Dashboard"
- Should see coordinator state, engine health, trading stats

---

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
sudo journalctl -u cryptomentor-analytics -f

# Last 100 lines
sudo journalctl -u cryptomentor-analytics -n 100

# Error logs only
sudo journalctl -u cryptomentor-analytics --no-pager | grep ERROR
```

### Check Service Status

```bash
sudo systemctl status cryptomentor-analytics
```

### Monitor Resource Usage

```bash
# Memory and CPU
watch -n 1 'ps aux | grep uvicorn'

# Open ports
sudo netstat -tuln | grep 8896
```

### Test Rate Limiting

```bash
# Should accept 100 req/min
for i in {1..100}; do
  curl -H "Authorization: Bearer TOKEN" \
    http://localhost:8896/api/analytics/coordinator-state &
done
wait

# 101st request should get 429 (Too Many Requests)
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8896/api/analytics/coordinator-state
```

---

## 🆘 Troubleshooting

### Issue: 401 Unauthorized

**Cause:** Invalid or expired JWT token

**Solution:**
```bash
# Regenerate JWT token
python << 'EOF'
import jwt
from datetime import datetime, timedelta
import os

secret = os.getenv("JWT_SECRET", "analytics-secret-key")
admin_id = int(os.getenv("ADMIN1", "123456789"))
token = jwt.encode(
    {"sub": str(admin_id), "exp": datetime.utcnow() + timedelta(days=7)},
    secret,
    algorithm="HS256"
)
print(token)
EOF
```

### Issue: 403 Forbidden

**Cause:** User ID not in ADMIN_ALLOWLIST

**Solution:**
1. Check .env file has correct ADMIN_IDS or ADMIN1-5
2. Ensure environment variable matches bot.py's admin IDs
3. Restart analytics service: `sudo systemctl restart cryptomentor-analytics`

### Issue: 500 Service Error

**Cause:** Supabase connection failed

**Solution:**
1. Verify SUPABASE_URL and SUPABASE_KEY in .env
2. Test Supabase connectivity:
   ```bash
   python << 'EOF'
   from Bismillah.app.supabase_repo import _client
   try:
       db = _client()
       print("Supabase connection OK")
   except Exception as e:
       print(f"Connection error: {e}")
   EOF
   ```
3. Check network connectivity to Supabase

### Issue: Service Won't Start

**Solution:**
```bash
# Check systemd logs
sudo journalctl -u cryptomentor-analytics --no-pager

# Manual test
cd /opt/cryptomentor
source venv/bin/activate
python -m uvicorn Bismillah.analytics_api:app --port 8896

# If error shows, fix and restart service
sudo systemctl restart cryptomentor-analytics
```

### Issue: High Memory Usage

**Solution:**
1. Check for memory leaks in logs
2. Restart service:
   ```bash
   sudo systemctl restart cryptomentor-analytics
   ```
3. Reduce uvicorn workers in systemd service:
   ```
   --workers 2  # Instead of 4
   ```

---

## 🔄 Updating to Latest Version

```bash
# Pull latest from main
cd /opt/cryptomentor
git pull origin main

# Activate venv
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/test_coordinator.py tests/test_regression.py -v

# Restart service
sudo systemctl restart cryptomentor-analytics

# Verify
curl http://localhost:8896/health
```

---

## 🛑 Stopping the Service

```bash
# Stop analytics API
sudo systemctl stop cryptomentor-analytics

# Disable (won't start on reboot)
sudo systemctl disable cryptomentor-analytics

# Note: Telegram bot and other services continue running
# Coordinator state is ephemeral and will reconcile on next bot restart
```

---

## 🔙 Rolling Back

If you need to rollback to previous version:

```bash
# Kill analytics service
sudo systemctl stop cryptomentor-analytics

# Coordinator is ephemeral (in-memory only)
# Positions will reconcile from exchange + DB on bot restart

# Revert code if needed
cd /opt/cryptomentor
git revert HEAD  # Or git checkout <previous_tag>

# Restart analytics
sudo systemctl start cryptomentor-analytics
```

---

## 📈 Performance Baselines

After deployment, monitor these metrics:

| Metric | Baseline | Healthy |
|--------|----------|---------|
| Health check response time | <50ms | <100ms |
| Coordinator-state query | <100ms | <500ms |
| Trading-stats query (7 days) | <200ms | <1000ms |
| Engine-health query | <50ms | <200ms |
| CPU usage (idle) | <5% | <20% |
| Memory usage | ~150MB | <500MB |
| Error rate | 0% | <1% |

---

## 🎯 Checklist Before Going Live

- [ ] Code pulled to main branch
- [ ] Virtual environment created and dependencies installed
- [ ] .env file configured with correct credentials
- [ ] Tests passing: 28 PASSED, 11 SKIPPED, 0 FAILED
- [ ] Systemd service created and enabled
- [ ] Analytics API running on port 8896
- [ ] Health check returns 200 OK
- [ ] JWT authentication working
- [ ] Telegram bot restarted
- [ ] Dashboard accessible at analytics4896.cryptomentor.id
- [ ] Multi-user isolation verified
- [ ] Coordinator behavior validated
- [ ] Logs being written and monitoring active
- [ ] Team notified of new analytics endpoint
- [ ] Support procedures documented

---

## 📞 Support

For issues or questions:

1. Check DEPLOYMENT.md for detailed troubleshooting
2. Review ANALYTICS_SETUP.md for configuration options
3. Check systemd logs: `journalctl -u cryptomentor-analytics -f`
4. Review CHANGELOG.md for feature documentation

---

## 🎉 Deployment Complete

After successful deployment, your CryptoMentor v2.2.0 system will have:

✅ Multi-user symbol coordination preventing strategy conflicts  
✅ Real-time analytics dashboard with admin authentication  
✅ Comprehensive position tracking and monitoring  
✅ Automated reconciliation on startup  
✅ Rate-limited API with JWT security  
✅ Full test coverage with passing tests  
✅ Production-ready systemd service  

**Next:** Monitor logs for 1 hour, verify coordinator behavior, and go live!
