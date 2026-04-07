#!/bin/bash
# Deploy Dashboard Buttons Fix to VPS
# Restores missing Trading Mode, Community Partners, and Bot Skills buttons

echo "🚀 Deploying Dashboard Buttons Fix..."

# VPS credentials
VPS_HOST="root@147.93.156.165"
VPS_PATH="/root/cryptomentor-bot"

# Upload updated file
echo "📤 Uploading handlers_autotrade.py..."
sshpass -p "<REDACTED_VPS_PASSWORD>" scp -o StrictHostKeyChecking=no \
  Bismillah/app/handlers_autotrade.py \
  ${VPS_HOST}:${VPS_PATH}/app/

if [ $? -ne 0 ]; then
    echo "❌ Upload failed"
    exit 1
fi

echo "✅ File uploaded successfully"

# Restart service
echo "🔄 Restarting cryptomentor service..."
sshpass -p "<REDACTED_VPS_PASSWORD>" ssh -o StrictHostKeyChecking=no ${VPS_HOST} << 'EOF'
cd /root/cryptomentor-bot
systemctl restart cryptomentor
sleep 3
systemctl status cryptomentor --no-pager -l
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ DEPLOYMENT SUCCESSFUL!"
    echo ""
    echo "📋 Changes deployed:"
    echo "   • Trading Mode button restored"
    echo "   • Community Partners button restored (for verified users)"
    echo "   • Bot Skills button restored"
    echo ""
    echo "🧪 Test by running /autotrade command"
else
    echo "❌ Service restart failed"
    exit 1
fi
