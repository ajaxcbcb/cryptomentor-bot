#!/bin/bash
# Scalping Mode Deployment Script
# VPS: root@147.93.156.165
# Password: <REDACTED_VPS_PASSWORD>

set -e

echo "🚀 Deploying Scalping Mode to VPS..."
echo "=================================="

VPS_HOST="root@147.93.156.165"
VPS_PATH="/root/cryptomentor-bot"

# Step 1: Backup database
echo ""
echo "📦 Step 1: Creating database backup..."
ssh $VPS_HOST << 'EOF'
cd /root/cryptomentor-bot
pg_dump cryptomentor > backup_scalping_$(date +%Y%m%d_%H%M%S).sql
echo "✅ Database backup created"
EOF

# Step 2: Upload database migration
echo ""
echo "📤 Step 2: Uploading database migration..."
scp db/add_trading_mode.sql $VPS_HOST:$VPS_PATH/db/

# Step 3: Run database migration
echo ""
echo "🗄️ Step 3: Running database migration..."
ssh $VPS_HOST << 'EOF'
cd /root/cryptomentor-bot
psql cryptomentor < db/add_trading_mode.sql
echo "✅ Database migration complete"

# Verify migration
echo ""
echo "🔍 Verifying migration..."
psql cryptomentor -c "SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name='autotrade_sessions' AND column_name='trading_mode';"
EOF

# Step 4: Upload new files
echo ""
echo "📤 Step 4: Uploading new files..."
scp Bismillah/app/trading_mode.py $VPS_HOST:$VPS_PATH/Bismillah/app/
scp Bismillah/app/trading_mode_manager.py $VPS_HOST:$VPS_PATH/Bismillah/app/
scp Bismillah/app/scalping_engine.py $VPS_HOST:$VPS_PATH/Bismillah/app/

# Step 5: Upload modified files
echo ""
echo "📤 Step 5: Uploading modified files..."
scp Bismillah/app/autosignal_fast.py $VPS_HOST:$VPS_PATH/Bismillah/app/
scp Bismillah/app/handlers_autotrade.py $VPS_HOST:$VPS_PATH/Bismillah/app/
scp Bismillah/app/autotrade_engine.py $VPS_HOST:$VPS_PATH/Bismillah/app/

# Step 6: Restart service
echo ""
echo "🔄 Step 6: Restarting service..."
ssh $VPS_HOST << 'EOF'
cd /root/cryptomentor-bot
systemctl restart cryptomentor.service
sleep 3
systemctl status cryptomentor.service --no-pager
echo ""
echo "✅ Service restarted"
EOF

# Step 7: Check logs
echo ""
echo "📋 Step 7: Checking logs for errors..."
ssh $VPS_HOST << 'EOF'
echo "Last 30 lines of logs:"
journalctl -u cryptomentor.service -n 30 --no-pager
EOF

echo ""
echo "=================================="
echo "✅ Deployment Complete!"
echo ""
echo "📊 Next Steps:"
echo "1. Test /autotrade command in Telegram"
echo "2. Click '⚙️ Trading Mode' button"
echo "3. Try switching between modes"
echo "4. Monitor logs: ssh $VPS_HOST 'journalctl -u cryptomentor.service -f'"
echo ""
echo "🔍 Verify deployment:"
echo "   ssh $VPS_HOST 'ls -la $VPS_PATH/Bismillah/app/trading_mode*.py'"
echo "   ssh $VPS_HOST 'ls -la $VPS_PATH/Bismillah/app/scalping_engine.py'"
echo ""
