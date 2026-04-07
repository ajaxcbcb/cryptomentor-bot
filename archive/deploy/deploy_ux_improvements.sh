#!/bin/bash
# Deploy UX Improvements to VPS
# Date: April 3, 2026

set -e

VPS_HOST="root@147.93.156.165"
VPS_PATH="/root/cryptomentor-bot"
SERVICE_NAME="cryptomentor.service"

echo "🚀 Deploying UX Improvements to VPS..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Upload new UI components library
echo ""
echo "📦 Step 1/4: Uploading UI components library..."
scp Bismillah/app/ui_components.py ${VPS_HOST}:${VPS_PATH}/Bismillah/app/

# Step 2: Upload updated handlers
echo ""
echo "📦 Step 2/4: Uploading updated handlers..."
scp Bismillah/app/handlers_autotrade.py ${VPS_HOST}:${VPS_PATH}/Bismillah/app/
scp Bismillah/app/handlers_risk_mode.py ${VPS_HOST}:${VPS_PATH}/Bismillah/app/

# Step 3: Restart service
echo ""
echo "🔄 Step 3/4: Restarting service..."
ssh ${VPS_HOST} "systemctl restart ${SERVICE_NAME}"

# Step 4: Check status
echo ""
echo "✅ Step 4/4: Checking service status..."
sleep 3
ssh ${VPS_HOST} "systemctl status ${SERVICE_NAME} --no-pager | head -20"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Deployment complete!"
echo ""
echo "📋 What was deployed:"
echo "  • New UI components library (ui_components.py)"
echo "  • Updated autotrade handlers with progress indicators"
echo "  • Updated risk mode handlers with comparison cards"
echo "  • Improved settings menu with grouped sections"
echo "  • Better loading states with tips"
echo "  • Success messages with structured data"
echo ""
echo "🧪 Test the changes:"
echo "  1. /autotrade - Check welcome message with progress"
echo "  2. Select exchange - Check progress indicator"
echo "  3. Choose risk mode - Check comparison cards"
echo "  4. Complete setup - Check success message"
echo "  5. Open settings - Check grouped sections"
echo ""
echo "📊 Monitor logs:"
echo "  ssh ${VPS_HOST} 'journalctl -u ${SERVICE_NAME} -f'"
echo ""
