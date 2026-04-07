#!/bin/bash

# Deploy Test License to VPS - Automated Script
# Usage: bash deploy_test_license.sh

VPS_HOST="147.93.156.165"
VPS_USER="root"

echo "======================================================================"
echo "DEPLOY TEST LICENSE TO VPS"
echo "======================================================================"
echo ""

# Step 1: Push to GitHub
echo "Step 1: Pushing code to GitHub..."
echo "----------------------------------------------------------------------"
git add .
git commit -m "Add test license for UID 1234500014 - expires tomorrow"
git push origin main

if [ $? -ne 0 ]; then
    echo "❌ Git push failed. Please check your git configuration."
    exit 1
fi

echo "✅ Code pushed to GitHub"
echo ""

# Step 2: Pull on VPS
echo "Step 2: Pulling latest code on VPS..."
echo "----------------------------------------------------------------------"
ssh ${VPS_USER}@${VPS_HOST} "cd /root/cryptomentor-bot && git pull origin main"

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed on VPS."
    exit 1
fi

echo "✅ Code pulled on VPS"
echo ""

# Step 3: Check License API
echo "Step 3: Checking License API status..."
echo "----------------------------------------------------------------------"
ssh ${VPS_USER}@${VPS_HOST} "sudo systemctl status license-api --no-pager | head -5"

echo ""
echo "Step 4: Testing License API endpoint..."
echo "----------------------------------------------------------------------"
ssh ${VPS_USER}@${VPS_HOST} "curl -s -X POST http://localhost:8080/api/license/check \
  -H 'Content-Type: application/json' \
  -d '{\"wl_id\":\"<REDACTED_UUID>\",\"secret_key\":\"<REDACTED_UUID>\"}' | python3 -m json.tool"

echo ""
echo "======================================================================"
echo "✅ DEPLOYMENT COMPLETED"
echo "======================================================================"
echo ""
echo "Test License Info:"
echo "  WL_ID      : <REDACTED_UUID>"
echo "  SECRET_KEY : <REDACTED_UUID>"
echo "  Admin UID  : 1234500014"
echo "  Monthly Fee: \$10"
echo "  Expires    : 2026-03-27 07:06 UTC (besok)"
echo ""
echo "Next Steps:"
echo "1. Kasih credentials di atas ke teman kamu"
echo "2. Teman kamu isi ke .env bot WL-nya"
echo "3. Restart bot WL"
echo "4. Test /start di Telegram"
echo "5. Besok jam 00:00 UTC, billing cron akan jalan otomatis"
echo ""
echo "Manual Commands:"
echo "  SSH to VPS    : ssh root@147.93.156.165"
echo "  Check API     : sudo systemctl status license-api"
echo "  Check Bot     : sudo systemctl status whitelabel1"
echo "  View Logs     : sudo journalctl -u license-api -f"
echo "  Test Billing  : python3 -c 'import asyncio; from license_server.billing_cron import run_billing_cycle; asyncio.run(run_billing_cycle())'"
echo ""
