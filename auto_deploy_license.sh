#!/bin/bash

# Auto Deploy License to VPS
# Usage: bash auto_deploy_license.sh

set -e  # Exit on error

VPS_HOST="147.93.156.165"
VPS_USER="root"
WL_ID="64ff0e58-4fd7-4800-b79f-a38915df7480"

echo "======================================================================"
echo "AUTO DEPLOY LICENSE SYSTEM TO VPS"
echo "======================================================================"
echo ""
echo "VPS: ${VPS_HOST}"
echo "WL_ID: ${WL_ID}"
echo ""

# Step 1: Push to GitHub
echo "[1/6] Pushing code to GitHub..."
echo "----------------------------------------------------------------------"
git add .
git commit -m "Deploy test license for UID 7675185179" || echo "No changes to commit"
git push origin main

echo "✅ Code pushed"
echo ""

# Step 2: Pull on VPS
echo "[2/6] Pulling latest code on VPS..."
echo "----------------------------------------------------------------------"
ssh ${VPS_USER}@${VPS_HOST} "cd /root/cryptomentor-bot && git pull origin main"

echo "✅ Code pulled"
echo ""

# Step 3: Check License API
echo "[3/6] Checking License API status..."
echo "----------------------------------------------------------------------"
ssh ${VPS_USER}@${VPS_HOST} "sudo systemctl status license-api --no-pager | head -10" || echo "License API not running, will continue..."

echo ""

# Step 4: Activate License
echo "[4/6] Activating license (deposit + billing)..."
echo "----------------------------------------------------------------------"
ssh ${VPS_USER}@${VPS_HOST} "cd /root/cryptomentor-bot && python3 << 'PYEOF'
import asyncio
from datetime import datetime, timezone, timedelta
import sys
sys.path.insert(0, '/root/cryptomentor-bot')

from license_server.license_manager import LicenseManager

WL_ID = '${WL_ID}'

async def main():
    manager = LicenseManager()
    
    print(f'[Activating] WL_ID: {WL_ID}')
    
    # Deposit \$50
    print('[1/2] Depositing \$50...')
    success = await manager.credit_balance(
        wl_id=WL_ID,
        amount=50.0,
        tx_hash='0xVPS_DEPLOY_FINAL',
        block_number=99999999
    )
    
    if success:
        print('✅ Deposit: \$50')
    else:
        print('⚠️  Deposit skipped (tx_hash exists)')
    
    # Get license info
    license_row = await manager.get_license(wl_id=WL_ID)
    balance = float(license_row['balance_usdt'])
    monthly_fee = float(license_row['monthly_fee'])
    
    print(f'[2/2] Processing billing...')
    print(f'    Balance: \${balance}')
    print(f'    Monthly Fee: \${monthly_fee}')
    
    # Billing
    if balance >= monthly_fee:
        new_balance = balance - monthly_fee
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        new_status = 'active'
    else:
        new_balance = balance
        expires_at = datetime.now(timezone.utc) + timedelta(days=3)
        new_status = 'grace_period'
    
    client = await manager._get_client()
    await client.table('wl_licenses').update({
        'balance_usdt': new_balance,
        'status': new_status,
        'expires_at': expires_at.isoformat()
    }).eq('wl_id', WL_ID).execute()
    
    print(f'✅ Status: {new_status}')
    print(f'   Balance: \${new_balance}')
    print(f'   Expires: {expires_at.strftime(\"%Y-%m-%d %H:%M UTC\")}')

asyncio.run(main())
PYEOF
"

echo ""
echo "✅ License activated"
echo ""

# Step 5: Test License API
echo "[5/6] Testing License API..."
echo "----------------------------------------------------------------------"
ssh ${VPS_USER}@${VPS_HOST} "curl -s -X POST http://localhost:8080/api/license/check \
  -H 'Content-Type: application/json' \
  -d '{\"wl_id\":\"${WL_ID}\",\"secret_key\":\"0cdfc39e-d17c-46c2-a143-27ec4258c5ff\"}' | python3 -m json.tool"

echo ""

# Step 6: Summary
echo "[6/6] Deployment Summary"
echo "----------------------------------------------------------------------"
echo ""
echo "✅ License activated successfully!"
echo ""
echo "Credentials untuk teman kamu (UID: 7675185179):"
echo "================================================================"
echo "WL_ID=64ff0e58-4fd7-4800-b79f-a38915df7480"
echo "WL_SECRET_KEY=0cdfc39e-d17c-46c2-a143-27ec4258c5ff"
echo "LICENSE_API_URL=http://147.93.156.165:8080"
echo "DEPOSIT_ADDRESS=0xff680baa2BaaD50f3756efF778eF673d0fd8cAF9"
echo "================================================================"
echo ""
echo "Next Steps:"
echo "1. Kasih credentials di atas ke teman kamu"
echo "2. Teman kamu isi ke .env bot WL-nya"
echo "3. Restart bot WL"
echo "4. Test /start di Telegram"
echo ""
echo "Manual Commands (if needed):"
echo "  SSH: ssh root@147.93.156.165"
echo "  Check API: sudo systemctl status license-api"
echo "  View Logs: sudo journalctl -u license-api -n 50"
echo ""
