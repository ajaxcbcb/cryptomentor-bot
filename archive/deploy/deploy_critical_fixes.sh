#!/bin/bash
# Deploy critical fixes to VPS

VPS_HOST="root@147.93.156.165"
VPS_PATH="/root/cryptomentor-bot"

echo "========================================="
echo "DEPLOYING CRITICAL FIXES"
echo "========================================="
echo ""

# Fix 1: Add get_balance() to BitunixAutoTradeClient
echo "📦 Uploading bitunix_autotrade_client.py..."
scp Bismillah/app/bitunix_autotrade_client.py $VPS_HOST:$VPS_PATH/Bismillah/app/
echo "✅ Done"
echo ""

# Fix 2: Add verbose logging to scalping_engine
echo "📦 Uploading scalping_engine.py..."
scp Bismillah/app/scalping_engine.py $VPS_HOST:$VPS_PATH/Bismillah/app/
echo "✅ Done"
echo ""

# Fix 3: Upload restart script
echo "📦 Uploading restart_all_engines.py..."
scp restart_all_engines.py $VPS_HOST:$VPS_PATH/
echo "✅ Done"
echo ""

# Restart service
echo "🔄 Restarting cryptomentor service..."
ssh $VPS_HOST "systemctl restart cryptomentor"
echo "✅ Service restarted"
echo ""

# Wait for bot to start
echo "⏳ Waiting 5 seconds for bot to initialize..."
sleep 5
echo ""

# Run restart script
echo "🚀 Restarting all engines..."
ssh $VPS_HOST "cd $VPS_PATH && python3 restart_all_engines.py"
echo ""

echo "========================================="
echo "DEPLOYMENT COMPLETE"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Monitor logs: ssh $VPS_HOST 'journalctl -u cryptomentor.service -f'"
echo "2. Check engines: python check_engine_status.py"
echo "3. Watch for signals in next 30 minutes"
echo ""
