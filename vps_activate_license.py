#!/usr/bin/env python3
"""
Activate license on VPS - deposit $50 and process billing
"""
import asyncio
from datetime import datetime, timezone, timedelta
import sys
sys.path.insert(0, '/root/cryptomentor-bot')

from license_server.license_manager import LicenseManager

WL_ID = '64ff0e58-4fd7-4800-b79f-a38915df7480'

async def main():
    manager = LicenseManager()
    
    print(f'[Activating] WL_ID: {WL_ID}')
    print('=' * 60)
    
    # Deposit $50
    print('\n[1/2] Depositing $50...')
    success = await manager.credit_balance(
        wl_id=WL_ID,
        amount=50.0,
        tx_hash='0xVPS_DEPLOY_FINAL',
        block_number=99999999
    )
    
    if success:
        print('OK Deposit: $50')
    else:
        print('WARN Deposit skipped (tx_hash exists)')
    
    # Get license info
    license_row = await manager.get_license(wl_id=WL_ID)
    balance = float(license_row['balance_usdt'])
    monthly_fee = float(license_row['monthly_fee'])
    
    print(f'\n[2/2] Processing billing...')
    print(f'    Balance: ${balance}')
    print(f'    Monthly Fee: ${monthly_fee}')
    
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
    
    print(f'\nOK Status: {new_status}')
    print(f'   Balance: ${new_balance}')
    print(f'   Expires: {expires_at.strftime("%Y-%m-%d %H:%M UTC")}')
    print('\n' + '=' * 60)
    print('OK LICENSE ACTIVATED')

if __name__ == '__main__':
    asyncio.run(main())
