"""
Force start engines for stopped users with balance.
Checks live Bitunix balance before starting.
"""
import sys, os, asyncio
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
os.chdir('/root/cryptomentor-bot/website-backend')

from app.db.supabase import _client
from app.services.bitunix import get_user_api_keys, fetch_account

# Users yang stopped dari debug sebelumnya
STOPPED_USERS = [
    1234500006,   # stopped
    1234500007,  # stopped
    1234500008,  # stopped
    1234500009,  # stopped
    1234500010,   # stopped
    1234500011,  # stopped
    1234500002,   # stopped
    1234500012,  # stopped
    1234500013,  # stopped
    1234500014,  # stopped
    1234500015,  # stopped
]

async def check_and_start():
    s = _client()
    to_start = []

    print("Checking balances for stopped users...\n")
    for tg_id in STOPPED_USERS:
        keys = get_user_api_keys(tg_id)
        if not keys:
            print(f"  TG:{tg_id} | NO API KEYS - skip")
            continue
        try:
            acc = await fetch_account(tg_id)
            balance = float(acc.get("available", 0) or 0)
            print(f"  TG:{tg_id} | balance=${balance:.2f} | success={acc.get('success')}")
            if balance > 0:
                to_start.append((tg_id, balance))
        except Exception as e:
            print(f"  TG:{tg_id} | ERROR: {e}")

    print(f"\n{'='*50}")
    print(f"Users with balance to start: {len(to_start)}")
    for tg_id, bal in sorted(to_start, key=lambda x: -x[1]):
        print(f"  TG:{tg_id} | balance=${bal:.2f}")

    if not to_start:
        print("No users to start.")
        return

    print(f"\nForce starting {len(to_start)} engines...")
    for tg_id, bal in to_start:
        try:
            # Update status to active di Supabase
            s.table("autotrade_sessions").update({
                "status": "active",
                "engine_active": True,
            }).eq("telegram_id", tg_id).execute()
            print(f"  ✓ TG:{tg_id} | Started (balance=${bal:.2f})")
        except Exception as e:
            print(f"  ✗ TG:{tg_id} | DB update failed: {e}")

    print("\nDone. Bot engine_restore will pick these up on next cycle.")

asyncio.run(check_and_start())
