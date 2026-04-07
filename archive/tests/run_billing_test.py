"""
Script untuk test billing WL#1 (untuk testing).
Dalam production, ini dilakukan otomatis oleh billing_cron.py setiap hari.
"""
import asyncio
import os
import sys

# Add license_server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'license_server'))

from dotenv import load_dotenv
load_dotenv('license_server/.env')

from license_manager import LicenseManager


async def main():
    wl_id = "<REDACTED_UUID>"
    
    print(f"Running billing for WL#1:")
    print(f"  WL_ID: {wl_id}")
    print()
    
    manager = LicenseManager()
    
    try:
        # Get current status
        license_before = await manager.get_license(wl_id)
        print("Before billing:")
        print(f"  Balance: ${license_before.get('balance_usdt', 0):.2f} USDT")
        print(f"  Status: {license_before.get('status')}")
        print(f"  Expires At: {license_before.get('expires_at')}")
        print()
        
        # Run billing
        result = await manager.debit_billing(wl_id)
        
        print("Billing result:")
        print(f"  Success: {result.get('success')}")
        print(f"  Balance Before: ${result.get('balance_before', 0):.2f}")
        print(f"  Balance After: ${result.get('balance_after', 0):.2f}")
        print(f"  New Status: {result.get('new_status')}")
        print(f"  New Expires At: {result.get('expires_at')}")
        print()
        
        if result.get('success'):
            print("✅ Billing successful! License is now active.")
        else:
            print("❌ Billing failed (insufficient balance)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
