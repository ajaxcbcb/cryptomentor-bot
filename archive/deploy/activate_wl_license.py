"""
Activate WL License - Simulate deposit + billing
"""
import asyncio
import sys
from datetime import datetime, timezone, timedelta
sys.path.insert(0, 'license_server')

from license_manager import LicenseManager
from dotenv import load_dotenv
import os

load_dotenv('Whitelabel #1/.env')

WL_ID = os.getenv('WL_ID')

async def main():
    manager = LicenseManager()
    
    print("=" * 70)
    print("ACTIVATING WL LICENSE")
    print("=" * 70)
    print(f"WL_ID: {WL_ID}")
    print()
    
    # Step 1: Simulate deposit
    print("Step 1: Simulating $50 USDT deposit...")
    await manager.credit_balance(
        wl_id=WL_ID,
        amount=50.0,
        tx_hash="0xTEST_LOCAL_DEPOSIT_123",
        block_number=12345678
    )
    print("✅ Deposit credited")
    print()
    
    # Step 2: Manual billing - deduct monthly fee and activate
    print("Step 2: Running billing (deduct $10, activate for 30 days)...")
    client = await manager._get_client()
    
    # Get current license
    license_row = await manager.get_license(wl_id=WL_ID)
    balance = float(license_row.get('balance_usdt', 0))
    monthly_fee = float(license_row.get('monthly_fee', 10))
    
    if balance >= monthly_fee:
        new_balance = balance - monthly_fee
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        # Update license
        await client.table('wl_licenses').update({
            'balance_usdt': new_balance,
            'status': 'active',
            'expires_at': expires_at.isoformat()
        }).eq('wl_id', WL_ID).execute()
        
        print(f"✅ Billing successful - deducted ${monthly_fee}")
        print(f"   New balance: ${new_balance}")
        print(f"   Expires: {expires_at}")
    else:
        print(f"❌ Insufficient balance: ${balance} < ${monthly_fee}")
    
    print()
    
    # Step 3: Check license status
    print("Step 3: Checking final license status...")
    license_row = await manager.get_license(wl_id=WL_ID)
    print(f"Status: {license_row.get('status')}")
    print(f"Balance: ${license_row.get('balance_usdt')}")
    print(f"Expires: {license_row.get('expires_at')}")
    print()
    
    if license_row.get('status') == 'active':
        print("✅ License ACTIVATED successfully!")
    else:
        print(f"❌ License activation failed - status: {license_row.get('status')}")
    
    print("=" * 70)

asyncio.run(main())
