# Deploy License System to VPS - Step by Step Guide

## Prerequisites

✅ Git changes pushed to GitHub
✅ SSH access to VPS (147.93.156.165)
✅ VPS has Python 3.10+ installed

---

## Option 1: Automatic Deployment (Recommended)

### From Windows (Git Bash):

```bash
bash run_vps_deployment.sh
```

Script akan otomatis:
1. Upload deployment script ke VPS
2. SSH ke VPS dan jalankan deployment
3. Install dependencies
4. Create systemd service
5. Start License API
6. Update Whitelabel #1 .env
7. Restart Whitelabel #1 bot

---

## Option 2: Manual Deployment

### Step 1: SSH to VPS

```bash
ssh root@147.93.156.165
```

### Step 2: Pull Latest Changes

```bash
cd /root/cryptomentor-bot
git pull github main
```

### Step 3: Install Dependencies

```bash
cd /root/cryptomentor-bot/license_server
pip3 install -r requirements.txt
```

### Step 4: Create License API Service

```bash
sudo nano /etc/systemd/system/license-api.service
```

Paste this content:

```ini
[Unit]
Description=License API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cryptomentor-bot/license_server
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 license_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+X, Y, Enter)

### Step 5: Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable license-api
sudo systemctl start license-api
```

### Step 6: Check Service Status

```bash
sudo systemctl status license-api
```

Expected output:
```
● license-api.service - License API Server
   Loaded: loaded (/etc/systemd/system/license-api.service; enabled)
   Active: active (running)
```

### Step 7: Test License API

```bash
curl -X POST http://localhost:8080/api/license/check \
  -H "Content-Type: application/json" \
  -d '{"wl_id":"<REDACTED_UUID>","secret_key":"<REDACTED_WL_SECRET_KEY>"}'
```

Expected response:
```json
{
  "valid": true,
  "expires_in_days": 29,
  "balance": 40.0,
  "warning": false,
  "status": "active"
}
```

### Step 8: Update Whitelabel #1 .env

```bash
cd /root/cryptomentor-bot/whitelabel-1
nano .env
```

Update these lines:
```
WL_ID=<REDACTED_UUID>
WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>
LICENSE_API_URL=http://147.93.156.165:8080
```

Save and exit.

### Step 9: Restart Whitelabel #1 Bot

```bash
sudo systemctl restart whitelabel1
```

### Step 10: Check Bot Status

```bash
sudo systemctl status whitelabel1
```

### Step 11: Check Bot Logs

```bash
sudo journalctl -u whitelabel1 -f
```

Look for:
```
[LicenseGuard] License valid — status: active
```

---

## Verification

### 1. Check License API is Running

```bash
curl http://localhost:8080/api/license/check
```

### 2. Check Bot is Running

```bash
sudo systemctl status whitelabel1
```

### 3. Test Bot in Telegram

1. Open Telegram
2. Find your bot (@YourBotUsername)
3. Send `/start`
4. Bot should respond immediately

---

## Troubleshooting

### License API Not Starting

```bash
# Check logs
sudo journalctl -u license-api -f

# Check if port 8080 is in use
sudo netstat -tulpn | grep 8080

# Restart service
sudo systemctl restart license-api
```

### Bot Shows "License Check Failed"

```bash
# Check if License API is running
curl http://localhost:8080/api/license/check

# Check bot logs
sudo journalctl -u whitelabel1 -f

# Verify .env file
cat /root/cryptomentor-bot/whitelabel-1/.env | grep LICENSE
```

### Import Errors

```bash
# Reinstall dependencies
cd /root/cryptomentor-bot/license_server
pip3 install -r requirements.txt --force-reinstall
```

---

## Optional: Setup Billing Cron & Deposit Monitor

### Billing Cron Service

```bash
sudo nano /etc/systemd/system/license-billing.service
```

Content:
```ini
[Unit]
Description=License Billing Cron
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cryptomentor-bot/license_server
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 billing_cron.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable license-billing
sudo systemctl start license-billing
```

### Deposit Monitor Service

```bash
sudo nano /etc/systemd/system/license-deposit.service
```

Content:
```ini
[Unit]
Description=License Deposit Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cryptomentor-bot/license_server
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 deposit_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable license-deposit
sudo systemctl start license-deposit
```

---

## Services Summary

After deployment, you should have these services running:

1. **license-api** - License validation API (port 8080)
2. **whitelabel1** - Whitelabel #1 bot
3. **license-billing** (optional) - Daily billing cron
4. **license-deposit** (optional) - Deposit monitor

Check all services:
```bash
sudo systemctl status license-api whitelabel1
```

---

## WL#1 Information

```
WL_ID: <REDACTED_UUID>
SECRET_KEY: <REDACTED_UUID>
Deposit Address: 0xadB2a65685e0259BaDa4BAA5A4ed432AF3E82042
Admin1: <REDACTED_ADMIN_ID>
Admin2: <REDACTED_ADMIN_ID>
Monthly Fee: $10 USDT
Current Balance: $40 USDT
Status: active
Expires: 2026-04-25
```

---

## Next Steps

1. ✅ Deploy License API to VPS
2. ✅ Update Whitelabel #1 .env
3. ✅ Restart Whitelabel #1 bot
4. Test bot in Telegram
5. Monitor logs for any issues
6. (Optional) Setup billing cron and deposit monitor

---

## Support

If you encounter any issues:

1. Check service logs: `sudo journalctl -u license-api -f`
2. Check bot logs: `sudo journalctl -u whitelabel1 -f`
3. Verify .env configuration
4. Test License API endpoint manually
5. Restart services if needed
