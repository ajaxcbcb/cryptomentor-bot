#!/bin/bash

echo "=========================================="
echo "Debug License System on VPS"
echo "=========================================="
echo ""

VPS_HOST="147.93.156.165"
VPS_USER="root"

echo "Step 1: Check License API service status..."
ssh ${VPS_USER}@${VPS_HOST} "sudo systemctl status license-api --no-pager -l"

echo ""
echo "Step 2: Test License API from VPS (localhost)..."
ssh ${VPS_USER}@${VPS_HOST} "curl -X POST http://localhost:8080/api/license/check -H 'Content-Type: application/json' -d '{\"wl_id\":\"<REDACTED_UUID>\",\"secret_key\":\"<REDACTED_UUID>\"}'"

echo ""
echo ""
echo "Step 3: Test License API from VPS (IP address)..."
ssh ${VPS_USER}@${VPS_HOST} "curl -X POST http://147.93.156.165:8080/api/license/check -H 'Content-Type: application/json' -d '{\"wl_id\":\"<REDACTED_UUID>\",\"secret_key\":\"<REDACTED_UUID>\"}'"

echo ""
echo ""
echo "Step 4: Check WL1 .env LICENSE settings..."
ssh ${VPS_USER}@${VPS_HOST} "cd /root/cryptomentor-bot/whitelabel-1 && grep -E '(WL_ID|WL_SECRET_KEY|LICENSE_API_URL)' .env"

echo ""
echo "Step 5: Check if port 8080 is listening..."
ssh ${VPS_USER}@${VPS_HOST} "sudo netstat -tulpn | grep 8080"

echo ""
echo "Step 6: Check License API logs..."
ssh ${VPS_USER}@${VPS_HOST} "sudo journalctl -u license-api -n 20 --no-pager"

echo ""
echo "=========================================="
echo "Debug completed"
echo "=========================================="
