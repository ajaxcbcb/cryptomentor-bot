#!/bin/bash

# Deploy License System to VPS - Final Version
# This script will setup everything needed for license system on VPS

VPS_HOST="147.93.156.165"
VPS_USER="root"

# Credentials from local test (working)
WL_ID="<REDACTED_UUID>"
WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>
ADMIN_TELEGRAM_ID="1234500009"

echo "======================================================================"
echo "DEPLOYING LICENSE SYSTEM TO VPS"
echo "======================================================================"
echo ""
echo "VPS: ${VPS_HOST}"
echo "WL_ID: ${WL_ID}"
echo "Admin: ${ADMIN_TELEGRAM_ID}"
echo ""

# Step 1: Register WL on VPS
echo "Step 1: Registering WL on VPS..."
echo "----------------------------------------------------------------------"

ssh ${VPS_USER}@${VPS_HOST} "cd /root/cryptomentor-bot/license_server && source venv/bin/activate && python -c \"
import asyncio
from license_manager import LicenseManager

async def main():
    manager = LicenseManager()
    result = await manager.register_wl(admin_telegram_id=${ADMIN_TELEGRAM_ID}, monthly_fee=10.0)
    print(f'WL_ID={result[\\\"wl_id\\\"]}')
    print(f'SECRET_KEY={result[\\\"secret_key\\\"]}')
    print(f'DEPOSIT_ADDRESS={result[\\\"deposit_address\\\"]}')

asyncio.run(main())
\""

echo ""
echo "Step 2: Activating license (deposit + billing)..."
echo "----------------------------------------------------------------------"

ssh ${VPS_USER}@${VPS_HOST} "cd /root/cryptomentor-bot/license_server && source venv/bin/activate && python -c \"
import asyncio
from datetime import datetime, timezone, timedelta
from license_manager import LicenseManager

async def main():
    manager = LicenseManager()
    
    # Get the latest WL (just registered)
    client = await manager._get_client()
    result = await client.table('wl_licenses').select('*').order('created_at', desc=True).limit(1).execute()
    wl_id = result.data[0]['wl_id']
    
    print(f'Activating WL: {wl_id}')
    
    # Deposit
    await manager.credit_balance(
        wl_id=wl_id,
        amount=50.0,
        tx_hash='0xVPS_TEST_DEPOSIT_123',
        block_number=12345678
    )
    print('✅ Deposit credited: \$50')
    
    # Billing
    license_row = await manager.get_license(wl_id=wl_id)
    balance = float(license_row.get('balance_usdt', 0))
    monthly_fee = float(license_row.get('monthly_fee', 10))
    
    if balance >= monthly_fee:
        new_balance = balance - monthly_fee
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        await client.table('wl_licenses').update({
            'balance_usdt': new_balance,
            'status': 'active',
            'expires_at': expires_at.isoformat()
        }).eq('wl_id', wl_id).execute()
        
        print(f'✅ Billing successful - deducted \${monthly_fee}')
        print(f'   New balance: \${new_balance}')
        print(f'   Status: active')
        print(f'   Expires: {expires_at}')
    
    # Print credentials for .env
    print('')
    print('=== CREDENTIALS FOR .ENV ===')
    print(f'WL_ID={wl_id}')
    license_row = await manager.get_license(wl_id=wl_id)
    print(f'WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>

asyncio.run(main())
\""

echo ""
echo "Step 3: Updating whitelabel-1 .env..."
echo "----------------------------------------------------------------------"

# Note: We'll use the credentials from the registration output
# For now, let's get the latest WL credentials

LATEST_CREDS=$(ssh ${VPS_USER}@${VPS_HOST} "cd /root/cryptomentor-bot/license_server && source venv/bin/activate && python -c \"
import asyncio
from license_manager import LicenseManager

async def main():
    manager = LicenseManager()
    client = await manager._get_client()
    result = await client.table('wl_licenses').select('*').order('created_at', desc=True).limit(1).execute()
    wl = result.data[0]
    print(f'{wl[\\\"wl_id\\\"]}|{wl[\\\"secret_key\\\"]}')

asyncio.run(main())
\"")

NEW_WL_ID=$(echo $LATEST_CREDS | cut -d'|' -f1)
NEW_SECRET=$(echo $LATEST_CREDS | cut -d'|' -f2)

echo "New credentials:"
echo "  WL_ID: ${NEW_WL_ID}"
echo "  SECRET_KEY: ${NEW_SECRET}"

ssh ${VPS_USER}@${VPS_HOST} "cd /root/cryptomentor-bot/whitelabel-1 && \
  sed -i 's/^WL_ID=.*/WL_ID=${NEW_WL_ID}/' .env && \
  sed -i 's/^WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY> .env && \
  sed -i 's|^LICENSE_API_URL=.*|LICENSE_API_URL=http://147.93.156.165:8080|' .env"

echo "✅ .env updated"

echo ""
echo "Step 4: Restarting whitelabel1 service..."
echo "----------------------------------------------------------------------"

ssh ${VPS_USER}@${VPS_HOST} "sudo systemctl restart whitelabel1"
sleep 5

echo ""
echo "Step 5: Checking service status..."
echo "----------------------------------------------------------------------"

ssh ${VPS_USER}@${VPS_HOST} "sudo systemctl status whitelabel1 --no-pager -l | head -20"

echo ""
echo "Step 6: Checking bot logs..."
echo "----------------------------------------------------------------------"

ssh ${VPS_USER}@${VPS_HOST} "sudo journalctl -u whitelabel1 -n 30 --no-pager | grep -E '(License|Started|ERROR)'"

echo ""
echo "======================================================================"
echo "✅ DEPLOYMENT COMPLETED"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "1. Check logs: ssh root@147.93.156.165 'sudo journalctl -u whitelabel1 -f'"
echo "2. Look for: [LicenseGuard] License valid — status: active"
echo "3. Test bot in Telegram with /start command"
echo ""
