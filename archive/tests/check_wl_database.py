"""
Script untuk cek status WL di database Supabase.
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
    wl_id = "61796c-bd62-4ccc-5f45-a7731f7f6692"
    
    print(f"Checking WL_ID: {wl_id}")
    print()
    
    manager = LicenseManager()
    
    try:
        license_row = await manager.get_license(wl_id)
        
        if license_row is None:
            print("❌ WL tidak ditemukan di database!")
            print("   Perlu register WL terlebih dahulu.")
        else:
            print("✅ WL ditemukan di database:")
            print(f"   WL ID: {license_row.get('wl_id')}")
            print(f"   Secret Key: {license_row.get('secret_key')}")
            print(f"   Status: {license_row.get('status')}")
            print(f"   Balance: ${license_row.get('balance_usdt', 0):.2f} USDT")
            print(f"   Monthly Fee: ${license_row.get('monthly_fee', 0):.2f}")
            print(f"   Expires At: {license_row.get('expires_at')}")
            print(f"   Deposit Address: {license_row.get('deposit_address')}")
            print(f"   Admin Telegram ID: {license_row.get('admin_telegram_id')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
