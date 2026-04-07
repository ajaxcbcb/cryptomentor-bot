#!/bin/bash

# Deploy Risk Calculator to VPS
# This script deploys the new risk management module

set -e

VPS_HOST="root@147.93.156.165"
VPS_PATH="/root/cryptomentor-bot"
PASSWORD="<REDACTED_PASSWORD>"

echo "=========================================="
echo "  Deploy Risk Calculator Module"
echo "=========================================="
echo ""

# Step 1: Deploy risk_calculator.py
echo "📦 Step 1: Deploying risk_calculator.py..."
scp Bismillah/app/risk_calculator.py ${VPS_HOST}:${VPS_PATH}/Bismillah/app/
echo "✅ risk_calculator.py deployed"
echo ""

# Step 2: Test module on VPS
echo "🧪 Step 2: Testing module on VPS..."
ssh ${VPS_HOST} << 'EOF'
cd /root/cryptomentor-bot
python3 << 'PYTHON'
from Bismillah.app.risk_calculator import calculate_position_size

# Test 1: Basic calculation
result = calculate_position_size(1000, 2, 66500, 65500)
print(f"Test 1 - Basic: {result}")
assert result['status'] == 'success'
assert result['risk_amount'] == 20.0
assert result['position_size'] == 0.02

# Test 2: Division by zero
result = calculate_position_size(1000, 2, 50000, 50000)
print(f"Test 2 - Division by zero: {result}")
assert result['status'] == 'error'

# Test 3: SHORT position
result = calculate_position_size(500, 2, 3200, 3300)
print(f"Test 3 - SHORT: {result}")
assert result['status'] == 'success'
assert result['risk_amount'] == 10.0

print("\n✅ All tests passed!")
PYTHON
EOF
echo "✅ Module tested successfully"
echo ""

# Step 3: Backup current autotrade_engine.py
echo "💾 Step 3: Backing up autotrade_engine.py..."
ssh ${VPS_HOST} << 'EOF'
cd /root/cryptomentor-bot/Bismillah/app
cp autotrade_engine.py autotrade_engine.py.backup_$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"
EOF
echo ""

echo "=========================================="
echo "  ✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update autotrade_engine.py to use new risk_calculator"
echo "2. Restart service: systemctl restart cryptomentor.service"
echo "3. Monitor logs: journalctl -u cryptomentor.service -f"
echo ""
echo "Module deployed to: ${VPS_PATH}/Bismillah/app/risk_calculator.py"
echo ""
