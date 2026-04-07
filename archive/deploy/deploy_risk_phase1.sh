#!/bin/bash

# Deploy Risk Per Trade Phase 1 to VPS
# This script uploads the necessary files and restarts the service

set -e  # Exit on error

# VPS Configuration
VPS_HOST="147.93.156.165"
VPS_USER="root"
VPS_PATH="/root/cryptomentor-bot"
VPS_PASSWORD="<REDACTED_PASSWORD>"

echo "=========================================="
echo "Risk Per Trade Phase 1 Deployment"
echo "=========================================="
echo ""

# Check if files exist
echo "📋 Checking files..."
FILES=(
    "Bismillah/app/supabase_repo.py"
    "Bismillah/app/position_sizing.py"
    "Bismillah/app/handlers_autotrade.py"
)

for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ File not found: $file"
        exit 1
    fi
    echo "✅ Found: $file"
done

echo ""
echo "🔐 VPS: $VPS_USER@$VPS_HOST"
echo "📁 Path: $VPS_PATH"
echo ""

# Confirm deployment
read -p "Deploy to VPS? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "📤 Uploading files..."

# Create backup directory on VPS
echo "Creating backup..."
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_HOST "
    mkdir -p $VPS_PATH/backups/risk_phase1_$(date +%Y%m%d_%H%M%S)
    cd $VPS_PATH/Bismillah/app
    cp supabase_repo.py $VPS_PATH/backups/risk_phase1_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
    cp handlers_autotrade.py $VPS_PATH/backups/risk_phase1_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
"

# Upload files
for file in "${FILES[@]}"; do
    echo "Uploading $file..."
    sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no "$file" "$VPS_USER@$VPS_HOST:$VPS_PATH/$file"
    if [ $? -eq 0 ]; then
        echo "✅ Uploaded: $file"
    else
        echo "❌ Failed to upload: $file"
        exit 1
    fi
done

echo ""
echo "🔄 Restarting service..."

# Restart service
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_HOST "
    systemctl restart cryptomentor.service
    sleep 3
    systemctl status cryptomentor.service --no-pager -l
"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Check logs: ssh $VPS_USER@$VPS_HOST 'journalctl -u cryptomentor.service -n 50'"
    echo "2. Test in Telegram: /autotrade → Settings → Risk Management"
    echo "3. Verify risk settings work correctly"
    echo ""
    echo "🔙 Rollback if needed:"
    echo "   ssh $VPS_USER@$VPS_HOST 'cd $VPS_PATH/backups && ls -lt | head -5'"
else
    echo ""
    echo "❌ Service restart failed!"
    echo "Check logs: ssh $VPS_USER@$VPS_HOST 'journalctl -u cryptomentor.service -n 50'"
    exit 1
fi
