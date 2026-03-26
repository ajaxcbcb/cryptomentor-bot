#!/bin/bash

# Script untuk update .env Whitelabel #1 di VPS dengan license credentials

echo "=========================================="
echo "Update Whitelabel #1 .env with License Credentials"
echo "=========================================="
echo ""

# VPS connection
VPS_HOST="147.93.156.165"
VPS_USER="root"
WL1_DIR="/root/cryptomentor-bot/whitelabel-1"

echo "Step 1: Backup current .env file..."
ssh ${VPS_USER}@${VPS_HOST} "cd ${WL1_DIR} && cp .env .env.backup.$(date +%Y%m%d_%H%M%S)"

echo ""
echo "Step 2: Update LICENSE_API_URL to use VPS IP..."
ssh ${VPS_USER}@${VPS_HOST} "cd ${WL1_DIR} && sed -i 's|LICENSE_API_URL=http://localhost:8080|LICENSE_API_URL=http://147.93.156.165:8080|g' .env"

echo ""
echo "Step 3: Verify .env changes..."
echo "--- Current LICENSE settings in .env ---"
ssh ${VPS_USER}@${VPS_HOST} "cd ${WL1_DIR} && grep -E '(WL_ID|WL_SECRET_KEY|LICENSE_API_URL)' .env"

echo ""
echo "Step 4: Restart whitelabel1 service..."
ssh ${VPS_USER}@${VPS_HOST} "sudo systemctl restart whitelabel1"

echo ""
echo "Step 5: Wait 5 seconds for service to start..."
sleep 5

echo ""
echo "Step 6: Check service status..."
ssh ${VPS_USER}@${VPS_HOST} "sudo systemctl status whitelabel1 --no-pager -l"

echo ""
echo "=========================================="
echo "✅ Update completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Check bot logs: ssh root@147.93.156.165 'sudo journalctl -u whitelabel1 -f'"
echo "2. Look for: [LicenseGuard] License valid — status: active"
echo "3. Test bot in Telegram with /start command"
echo ""
