#!/bin/bash

# Deploy License System to VPS
# Run this script on VPS after pulling from git

set -e

echo "=========================================="
echo "Deploying License System to VPS"
echo "=========================================="

VPS_IP="147.93.156.165"
VPS_USER="root"
BASE_DIR="/root/cryptomentor-bot"

echo ""
echo "Step 1: Pull latest changes from GitHub"
cd $BASE_DIR
git pull github main

echo ""
echo "Step 2: Install license_server dependencies"
cd $BASE_DIR/license_server
pip3 install -r requirements.txt

echo ""
echo "Step 3: Create systemd service for License API"
cat > /etc/systemd/system/license-api.service << 'EOF'
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
EOF

echo ""
echo "Step 4: Enable and start License API service"
systemctl daemon-reload
systemctl enable license-api
systemctl restart license-api

echo ""
echo "Step 5: Wait for License API to start"
sleep 3

echo ""
echo "Step 6: Check License API status"
systemctl status license-api --no-pager

echo ""
echo "Step 7: Test License API endpoint"
curl -X POST http://localhost:8080/api/license/check \
  -H "Content-Type: application/json" \
  -d '{"wl_id":"<REDACTED_UUID>","secret_key":"<REDACTED_WL_SECRET_KEY>"}' \
  | python3 -m json.tool

echo ""
echo "Step 8: Update Whitelabel #1 .env with License API URL"
cd $BASE_DIR/whitelabel-1
if [ -f .env ]; then
    # Update LICENSE_API_URL
    sed -i 's|LICENSE_API_URL=.*|LICENSE_API_URL=http://147.93.156.165:8080|' .env
    
    # Update WL credentials
    sed -i 's|WL_ID=.*|WL_ID=<REDACTED_UUID>|' .env
    sed -i 's|WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY> .env
    
    echo "✅ .env updated"
else
    echo "❌ .env not found in whitelabel-1 directory"
fi

echo ""
echo "Step 9: Restart Whitelabel #1 bot"
systemctl restart whitelabel1

echo ""
echo "Step 10: Check Whitelabel #1 bot status"
sleep 2
systemctl status whitelabel1 --no-pager

echo ""
echo "=========================================="
echo "✅ License System Deployed Successfully!"
echo "=========================================="
echo ""
echo "Services running:"
echo "  - License API: http://147.93.156.165:8080"
echo "  - Whitelabel #1 Bot: Active"
echo ""
echo "Check logs:"
echo "  sudo journalctl -u license-api -f"
echo "  sudo journalctl -u whitelabel1 -f"
echo ""
echo "WL#1 Credentials:"
echo "  WL_ID: <REDACTED_UUID>"
echo "  SECRET_KEY: <REDACTED_UUID>"
echo "  Deposit Address: 0xadB2a65685e0259BaDa4BAA5A4ed432AF3E82042"
echo ""
