#!/bin/bash
# StackMentor Deployment Script
# Deploy StackMentor system to VPS with $60 deposit requirement

set -e

VPS_HOST="147.93.156.165"
VPS_USER="root"
VPS_PATH="/root/cryptomentor-bot"
SERVICE_NAME="cryptomentor.service"

echo "🚀 StackMentor Deployment Starting..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  StackMentor requires deposit ≥ \$60 USDT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Upload stackmentor.py module
echo ""
echo "📦 Step 1: Uploading stackmentor.py module..."
scp -o StrictHostKeyChecking=no \
    Bismillah/app/stackmentor.py \
    ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/app/

if [ $? -eq 0 ]; then
    echo "✅ stackmentor.py uploaded successfully"
else
    echo "❌ Failed to upload stackmentor.py"
    exit 1
fi

# Step 2: Upload updated autotrade_engine.py
echo ""
echo "📦 Step 2: Uploading updated autotrade_engine.py..."
scp -o StrictHostKeyChecking=no \
    Bismillah/app/autotrade_engine.py \
    ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/app/

if [ $? -eq 0 ]; then
    echo "✅ autotrade_engine.py uploaded successfully"
else
    echo "❌ Failed to upload autotrade_engine.py"
    exit 1
fi

# Step 3: Upload updated trade_history.py
echo ""
echo "📦 Step 3: Uploading updated trade_history.py..."
scp -o StrictHostKeyChecking=no \
    Bismillah/app/trade_history.py \
    ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/app/

if [ $? -eq 0 ]; then
    echo "✅ trade_history.py uploaded successfully"
else
    echo "❌ Failed to upload trade_history.py"
    exit 1
fi

# Step 4: Upload updated supabase_repo.py
echo ""
echo "📦 Step 4: Uploading updated supabase_repo.py..."
scp -o StrictHostKeyChecking=no \
    Bismillah/app/supabase_repo.py \
    ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/app/

if [ $? -eq 0 ]; then
    echo "✅ supabase_repo.py uploaded successfully"
else
    echo "❌ Failed to upload supabase_repo.py"
    exit 1
fi

# Step 5: Apply database migrations
echo ""
echo "📊 Step 5: Applying database migrations..."
echo "⚠️  You need to run these SQL scripts manually in Supabase:"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "MIGRATION 1: Deposit Tracking"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat db/add_deposit_tracking.sql
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "MIGRATION 2: StackMentor Fields"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat db/stackmentor_migration.sql
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Press ENTER after you've applied BOTH migrations in Supabase..."

# Step 6: Restart bot service
echo ""
echo "🔄 Step 6: Restarting bot service..."
ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
cd /root/cryptomentor-bot
sudo systemctl restart cryptomentor.service
sleep 3
sudo systemctl status cryptomentor.service --no-pager
ENDSSH

if [ $? -eq 0 ]; then
    echo "✅ Bot service restarted successfully"
else
    echo "⚠️  Service restart may have failed - check manually"
fi

# Step 7: Check logs
echo ""
echo "📋 Step 7: Checking recent logs..."
ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
sudo journalctl -u cryptomentor.service -n 30 --no-pager | grep -i "stackmentor\|engine\|started"
ENDSSH

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ StackMentor Deployment Complete!"
echo ""
echo "📝 Next Steps:"
echo "1. Add deposits for existing users who should have access:"
echo "   SELECT add_user_deposit(telegram_id, amount);"
echo ""
echo "2. Test with eligible user (deposit ≥ \$60):"
echo "   - Start autotrade"
echo "   - Verify StackMentor notification"
echo "   - Check 3-tier TP levels"
echo ""
echo "3. Test with non-eligible user (deposit < \$60):"
echo "   - Start autotrade"
echo "   - Verify legacy TP notification"
echo "   - Check upgrade message"
echo ""
echo "4. Monitor logs:"
echo "   ssh root@${VPS_HOST} 'sudo journalctl -u ${SERVICE_NAME} -f'"
echo ""
echo "🎯 StackMentor is now active for users with deposit ≥ \$60!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
