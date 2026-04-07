#!/bin/bash

# Deploy Partial TP Notification Fix to VPS
# This improves notification clarity about when partial closes happen

set -e

VPS_HOST="root@147.93.156.165"
VPS_PATH="/root/cryptomentor-bot"
PASSWORD="<REDACTED_PASSWORD>"

echo "=========================================="
echo "Deploying Partial TP Notification Fix"
echo "=========================================="
echo ""

echo "📦 Transferring autotrade_engine.py to VPS..."
sshpass -p "$PASSWORD" scp Bismillah/app/autotrade_engine.py $VPS_HOST:$VPS_PATH/Bismillah/app/

echo ""
echo "🔄 Restarting cryptomentor service..."
sshpass -p "$PASSWORD" ssh $VPS_HOST << 'EOF'
cd /root/cryptomentor-bot
systemctl restart cryptomentor
sleep 3
systemctl status cryptomentor --no-pager
EOF

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 What changed:"
echo "  • Added '🤖 Partial close otomatis saat harga hit TP' to notification"
echo "  • Simplified qty display (removed breakdown)"
echo "  • Improved profit display (shows total potential)"
echo ""
echo "🧪 Testing:"
echo "  1. Wait for next trade signal"
echo "  2. Check notification shows clarification about automatic partial close"
echo "  3. Verify exchange shows 1 order with TP1 (expected behavior)"
echo "  4. Wait for TP1 hit and verify bot closes 50% automatically"
echo ""
echo "📊 Monitor logs:"
echo "  ssh root@147.93.156.165"
echo "  tail -f /var/log/cryptomentor.log"
echo ""
