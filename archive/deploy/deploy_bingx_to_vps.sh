#!/bin/bash

# ============================================================
# Deploy BingX Updates to VPS
# ============================================================

set -e  # Exit on error

VPS_HOST="147.93.156.165"
VPS_USER="root"
VPS_PORT="22"
VPS_PATH="/root/CryptoMentor"

echo "============================================================"
echo "🚀 Deploying BingX Updates to VPS"
echo "============================================================"
echo ""
echo "VPS: $VPS_USER@$VPS_HOST:$VPS_PORT"
echo "Path: $VPS_PATH"
echo ""

# Files yang akan di-upload
FILES_TO_UPLOAD=(
    "Bismillah/app/exchange_registry.py"
    "Bismillah/app/handlers_autotrade.py"
    "Bismillah/app/bingx_autotrade_client.py"
    "Bismillah/app/autotrade_engine.py"
    "Bismillah/app/scheduler.py"
)

echo "📦 Files to upload:"
for file in "${FILES_TO_UPLOAD[@]}"; do
    echo "  - $file"
done
echo ""

# Backup di VPS
echo "📋 Step 1: Creating backup on VPS..."
ssh -p $VPS_PORT $VPS_USER@$VPS_HOST << 'ENDSSH'
cd /root/CryptoMentor
BACKUP_DIR="backups/bingx_update_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating backup in $BACKUP_DIR..."
cp -r Bismillah/app/exchange_registry.py "$BACKUP_DIR/" 2>/dev/null || true
cp -r Bismillah/app/handlers_autotrade.py "$BACKUP_DIR/" 2>/dev/null || true
cp -r Bismillah/app/bingx_autotrade_client.py "$BACKUP_DIR/" 2>/dev/null || true
cp -r Bismillah/app/autotrade_engine.py "$BACKUP_DIR/" 2>/dev/null || true
cp -r Bismillah/app/scheduler.py "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ Backup created: $BACKUP_DIR"
ENDSSH

echo ""

# Upload files
echo "📤 Step 2: Uploading updated files..."
for file in "${FILES_TO_UPLOAD[@]}"; do
    echo "  Uploading $file..."
    scp -P $VPS_PORT "$file" "$VPS_USER@$VPS_HOST:$VPS_PATH/$file"
done

echo ""
echo "✅ All files uploaded successfully!"
echo ""

# Restart bot service
echo "🔄 Step 3: Restarting bot service..."
ssh -p $VPS_PORT $VPS_USER@$VPS_HOST << 'ENDSSH'
cd /root/CryptoMentor

# Check if bot is running
if systemctl is-active --quiet cryptomentor-bot; then
    echo "Stopping bot service..."
    systemctl stop cryptomentor-bot
    sleep 2
fi

# Start bot service
echo "Starting bot service..."
systemctl start cryptomentor-bot
sleep 3

# Check status
if systemctl is-active --quiet cryptomentor-bot; then
    echo "✅ Bot service started successfully!"
    systemctl status cryptomentor-bot --no-pager | head -20
else
    echo "❌ Bot service failed to start!"
    echo "Checking logs..."
    journalctl -u cryptomentor-bot -n 50 --no-pager
    exit 1
fi
ENDSSH

echo ""
echo "============================================================"
echo "✅ Deployment Complete!"
echo "============================================================"
echo ""
echo "📊 Next steps:"
echo "  1. Monitor logs: ssh -p $VPS_PORT $VPS_USER@$VPS_HOST 'journalctl -u cryptomentor-bot -f'"
echo "  2. Test BingX registration flow"
echo "  3. Test BingX autotrade"
echo ""
echo "🔙 Rollback if needed:"
echo "  ssh -p $VPS_PORT $VPS_USER@$VPS_HOST"
echo "  cd /root/CryptoMentor/backups"
echo "  ls -la  # Find backup directory"
echo "  # Copy files back from backup"
echo ""
