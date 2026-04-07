#!/bin/bash
# Deploy SL Price Error Fix to VPS
# Fixes error 30029 in StackMentor breakeven SL update

set -e

VPS_HOST="root@147.93.156.165"
VPS_PATH="/root/cryptomentor-bot"
PASSWORD="<REDACTED_PASSWORD>"

echo "🚀 Deploying SL Price Error Fix..."
echo ""

# Deploy files
echo "📤 Uploading fixed files..."
sshpass -p "$PASSWORD" scp \
  Bismillah/app/stackmentor.py \
  Bismillah/app/bitunix_autotrade_client.py \
  ${VPS_HOST}:${VPS_PATH}/Bismillah/app/

echo ""
echo "🔄 Restarting service..."
sshpass -p "$PASSWORD" ssh ${VPS_HOST} << 'EOF'
cd /root/cryptomentor-bot
sudo systemctl restart cryptomentor.service
sleep 3
sudo systemctl status cryptomentor.service --no-pager -l
EOF

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Monitor logs:"
echo "   ssh root@147.93.156.165"
echo "   sudo journalctl -u cryptomentor.service -f | grep -i 'stackmentor\|invalid sl'"
