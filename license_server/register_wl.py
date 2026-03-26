"""
Script untuk register Whitelabel baru.
Jalankan sekali untuk setiap WL owner baru.
Output: wl_id, secret_key, deposit_address → isi ke .env WL
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from license_server.license_manager import LicenseManager


async def main():
    # Isi sesuai WL yang mau didaftarkan
    ADMIN_TELEGRAM_ID = int(input("Masukkan Telegram ID admin WL#1: ").strip())
    MONTHLY_FEE = 10.0  # USD per bulan (TEST MODE)

    print(f"\nRegistering WL dengan:")
    print(f"  Admin Telegram ID: {ADMIN_TELEGRAM_ID}")
    print(f"  Monthly Fee: ${MONTHLY_FEE}")
    print()

    manager = LicenseManager()
    result = await manager.register_wl(
        admin_telegram_id=ADMIN_TELEGRAM_ID,
        monthly_fee=MONTHLY_FEE,
    )

    print("=" * 60)
    print("✅ WL REGISTERED SUCCESSFULLY")
    print("=" * 60)
    print(f"WL_ID:           {result['wl_id']}")
    print(f"SECRET_KEY:      {result['secret_key']}")
    print(f"DEPOSIT_ADDRESS: {result['deposit_address']}")
    print()
    print("Isi ke Whitelabel #1/.env:")
    print(f"  WL_ID={result['wl_id']}")
    print(f"  WL_SECRET_KEY={result['secret_key']}")
    print(f"  LICENSE_API_URL=http://YOUR_VPS_IP:8080")
    print()
    print(f"Berikan deposit address ini ke WL owner untuk top-up:")
    print(f"  BSC USDT Address: {result['deposit_address']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
