#!/bin/bash
# Fix /autotrade error - Deploy corrected scalping_engine.py
# Date: April 7, 2026

echo "🔧 Fixing /autotrade error..."
echo ""

# 1. Stop the service first
echo "1️⃣ Stopping cryptomentor service..."
ssh root@147.93.156.165 "systemctl stop cryptomentor"
sleep 2

# 2. Backup current version
echo "2️⃣ Backing up current version..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ssh root@147.93.156.165 "cp /root/cryptomentor-bot/Bismillah/app/scalping_engine.py /root/cryptomentor-bot/Bismillah/app/scalping_engine.py.backup.$TIMESTAMP"

# 3. Deploy corrected version
echo "3️⃣ Deploying corrected scalping_engine.py..."
scp Bismillah/app/scalping_engine.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# 4. Verify syntax on VPS
echo "4️⃣ Verifying syntax on VPS..."
ssh root@147.93.156.165 "cd /root/cryptomentor-bot && python3 -m py_compile Bismillah/app/scalping_engine.py"

if [ $? -eq 0 ]; then
    echo "✅ Syntax check passed!"
else
    echo "❌ Syntax check failed! Restoring backup..."
    ssh root@147.93.156.165 "cp /root/cryptomentor-bot/Bismillah/app/scalping_engine.py.backup.$TIMESTAMP /root/cryptomentor-bot/Bismillah/app/scalping_engine.py"
    ssh root@147.93.156.165 "systemctl start cryptomentor"
    echo "⚠️ Rollback completed. Please check the error."
    exit 1
fi

# 5. Start the service
echo "5️⃣ Starting cryptomentor service..."
ssh root@147.93.156.165 "systemctl start cryptomentor"
sleep 3

# 6. Check service status
echo "6️⃣ Checking service status..."
ssh root@147.93.156.165 "systemctl status cryptomentor --no-pager -l"

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📊 Monitor logs with:"
echo "ssh root@147.93.156.165 'journalctl -u cryptomentor -f'"
echo ""
echo "🧪 Test /autotrade command in Telegram bot"
