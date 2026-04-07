#!/bin/bash
# Manual SCP Deployment for Phase 2
# Date: April 2, 2026

VPS_HOST="root@147.93.156.165"
VPS_PATH="/root/cryptomentor-bot"

echo "============================================"
echo "Phase 2: Manual SCP Deployment"
echo "============================================"
echo ""

# Step 1: Create backups on VPS
echo "Step 1: Creating backups on VPS..."
ssh $VPS_HOST "
cd $VPS_PATH/Bismillah/app
cp autotrade_engine.py autotrade_engine.py.phase2_backup_\$(date +%Y%m%d_%H%M%S)
cp scalping_engine.py scalping_engine.py.phase2_backup_\$(date +%Y%m%d_%H%M%S)
ls -lh *.phase2_backup* | tail -2
"
echo ""

# Step 2: Upload files
echo "Step 2: Uploading modified files..."
echo "Uploading autotrade_engine.py..."
scp Bismillah/app/autotrade_engine.py $VPS_HOST:$VPS_PATH/Bismillah/app/
echo ""
echo "Uploading scalping_engine.py..."
scp Bismillah/app/scalping_engine.py $VPS_HOST:$VPS_PATH/Bismillah/app/
echo ""

# Step 3: Verify files
echo "Step 3: Verifying uploaded files..."
ssh $VPS_HOST "
cd $VPS_PATH/Bismillah/app
echo 'Checking autotrade_engine.py...'
grep -q 'calc_qty_with_risk' autotrade_engine.py && echo '✅ autotrade_engine.py contains calc_qty_with_risk' || echo '❌ FAILED'
echo 'Checking scalping_engine.py...'
grep -q 'used_risk_sizing' scalping_engine.py && echo '✅ scalping_engine.py contains used_risk_sizing' || echo '❌ FAILED'
"
echo ""

# Step 4: Restart service
echo "Step 4: Restarting service..."
ssh $VPS_HOST "systemctl restart cryptomentor.service"
sleep 3
echo ""

# Step 5: Check status
echo "Step 5: Checking service status..."
ssh $VPS_HOST "systemctl status cryptomentor.service --no-pager | head -20"
echo ""

# Step 6: Check logs
echo "Step 6: Checking recent logs..."
ssh $VPS_HOST "journalctl -u cryptomentor.service -n 30 --no-pager"
echo ""

echo "============================================"
echo "✅ Deployment Complete!"
echo "============================================"
echo ""
echo "📊 Monitor with:"
echo "   ssh $VPS_HOST 'journalctl -u cryptomentor.service -f | grep -i risksizing'"
echo ""
