"""
Activate Test License - Deposit $50 dan jalankan billing
WL_ID: <REDACTED_UUID>
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), 'license_server', '.env'))

from license_server.license_manager import LicenseManager

WL_ID = "<REDACTED_UUID>"


async def main():
    manager = LicenseManager()
    
    print(f"Activating license: {WL_ID}")
    print("=" * 60)
    
    # Step 1: Deposit $50
    print("\n[1/3] Depositing $50...")
    success = await manager.credit_balance(
        wl_id=WL_ID,
        amount=50.0,
        tx_hash="0xVPS_DEPLOY_FINAL",
        block_number=99999999
    )
    
    if not success:
        print("❌ Deposit failed (tx_hash might already exist)")
        print("   Continuing with billing anyway...")
    else:
        print("✅ Deposit: $50")
    
    # Step 2: Get current license info
    print("\n[2/3] Getting license info...")
    license_row = await manager.get_license(wl_id=WL_ID)
    
    if not license_row:
        print(f"❌ License not found: {WL_ID}")
        return
    
    balance = float(license_row['balance_usdt'])
    monthly_fee = float(license_row['monthly_fee'])
    current_status = license_row['status']
    
    print(f"   Current Balance: ${balance}")
    print(f"   Monthly Fee: ${monthly_fee}")
    print(f"   Current Status: {current_status}")
    
    # Step 3: Manual billing (deduct fee and extend expiry)
    print("\n[3/3] Processing billing...")
    
    if balance < monthly_fee:
        print(f"⚠️  Insufficient balance (${balance} < ${monthly_fee})")
        print("   Setting status to grace_period...")
        new_status = "grace_period"
        new_balance = balance
        expires_at = datetime.now(timezone.utc) + timedelta(days=3)  # 3 days grace
    else:
        new_balance = balance - monthly_fee
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        new_status = "active"
    
    client = await manager._get_client()
    await client.table('wl_licenses').update({
        'balance_usdt': new_balance,
        'status': new_status,
        'expires_at': expires_at.isoformat()
    }).eq('wl_id', WL_ID).execute()
    
    print(f"✅ Billing processed")
    print(f"   Deducted: ${monthly_fee if balance >= monthly_fee else 0}")
    print(f"   New Balance: ${new_balance}")
    print(f"   Status: {new_status}")
    print(f"   Expires: {expires_at.isoformat()}")
    
    print("\n" + "=" * 60)
    print("✅ LICENSE ACTIVATED")
    print("=" * 60)
    print(f"\nWL_ID: {WL_ID}")
    print(f"SECRET_KEY: {license_row['secret_key']}")
    print(f"Status: {new_status}")
    print(f"Balance: ${new_balance}")
    print(f"Expires: {expires_at.strftime('%Y-%m-%d %H:%M UTC')}")


if __name__ == "__main__":
    asyncio.run(main())
