import asyncio
import sys
sys.path.insert(0, 'license_server')
from license_manager import LicenseManager

async def main():
    result = await LicenseManager().register_wl(admin_telegram_id=1234500009, monthly_fee=10.0)
    wl_id = result['wl_id']
    secret = result['secret_key']
    print(f'WL_ID={wl_id}')
    print(f'WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>
    print(f'Lengths: WL_ID={len(wl_id)}, SECRET={len(secret)}')

asyncio.run(main())
