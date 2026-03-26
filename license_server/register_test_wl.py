"""
Script TEST — Register WL dengan expires besok (1 hari).
Khusus untuk testing sistem billing B2B.
Jalankan: python -m license_server.register_test_wl
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from license_server.license_manager import LicenseManager


async def main():
    # UID teman untuk tes
    ADMIN_TELEGRAM_ID = 7675185179
    MONTHLY_FEE = 10.0  # $10 untuk tes

    # Expires besok (24 jam dari sekarang)
    expires_at = datetime.now(timezone.utc) + timedelta(days=1)

    print(f"[TEST] Registering WL:")
    print(f"  Admin Telegram ID : {ADMIN_TELEGRAM_ID}")
    print(f"  Monthly Fee       : ${MONTHLY_FEE}")
    print(f"  Expires At        : {expires_at.isoformat()} (besok)")
    print()

    manager = LicenseManager()
    client = await manager._get_client()

    # Fetch used indices
    res = await client.table("wl_licenses").select("deposit_index").execute()
    used_indices = [row["deposit_index"] for row in (res.data or [])]

    import uuid
    deposit_index = manager._wallet.get_next_index(used_indices)
    deposit_address = manager._wallet.derive_address(deposit_index)
    secret_key = str(uuid.uuid4())

    row = {
        "admin_telegram_id": ADMIN_TELEGRAM_ID,
        "monthly_fee": MONTHLY_FEE,
        "deposit_index": deposit_index,
        "deposit_address": deposit_address,
        "secret_key": secret_key,
        "expires_at": expires_at.isoformat(),
        "status": "active",  # langsung active untuk tes
    }

    insert_res = await client.table("wl_licenses").insert(row).execute()
    inserted = insert_res.data[0]

    print("=" * 60)
    print("✅ TEST WL REGISTERED")
    print("=" * 60)
    print(f"WL_ID           : {inserted['wl_id']}")
    print(f"SECRET_KEY      : {inserted['secret_key']}")
    print(f"DEPOSIT_ADDRESS : {inserted['deposit_address']}")
    print(f"EXPIRES_AT      : {expires_at.isoformat()}")
    print(f"STATUS          : active")
    print(f"MONTHLY_FEE     : ${MONTHLY_FEE}")
    print()
    print("⚠️  Lisensi ini akan expired besok.")
    print("   Jika tidak ada deposit, billing cron akan set status → grace_period → suspended.")
    print()
    print("Isi ke .env WL:")
    print(f"  WL_ID={inserted['wl_id']}")
    print(f"  WL_SECRET_KEY={inserted['secret_key']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
