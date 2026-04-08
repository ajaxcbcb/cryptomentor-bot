"""Check balance for ALL 26 users across all statuses."""
import sys, os, asyncio
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
os.chdir('/root/cryptomentor-bot/website-backend')

from app.db.supabase import _client
from app.services.bitunix import get_user_api_keys, fetch_account

async def main():
    s = _client()
    sessions = s.table("autotrade_sessions").select(
        "telegram_id, status, engine_active, exchange"
    ).execute().data or []

    print(f"Total sessions: {len(sessions)}\n")
    print(f"{'TG_ID':<15} {'STATUS':<15} {'ENGINE':<8} {'EXCHANGE':<10} {'BALANCE':>10}")
    print("-" * 65)

    results = []
    for sess in sessions:
        tg_id = sess["telegram_id"]
        status = sess.get("status", "?")
        engine = sess.get("engine_active", False)
        exchange = sess.get("exchange", "?")

        keys = get_user_api_keys(tg_id)
        if not keys:
            results.append((tg_id, status, engine, exchange, None, "NO_KEYS"))
            continue

        try:
            acc = await fetch_account(tg_id)
            bal = float(acc.get("available", 0) or 0)
            results.append((tg_id, status, engine, exchange, bal, "OK"))
        except Exception as e:
            results.append((tg_id, status, engine, exchange, None, f"ERR:{e}"))

    # Sort by balance desc
    results.sort(key=lambda x: (x[4] or -1), reverse=True)

    total_balance = 0
    users_with_balance = 0
    for tg_id, status, engine, exchange, bal, note in results:
        bal_str = f"${bal:.2f}" if bal is not None else note
        flag = " ← HAS BALANCE" if (bal and bal > 0) else ""
        print(f"{tg_id:<15} {status:<15} {str(engine):<8} {exchange:<10} {bal_str:>10}{flag}")
        if bal and bal > 0:
            total_balance += bal
            users_with_balance += 1

    print("-" * 65)
    print(f"Users with balance: {users_with_balance}/{len(results)}")
    print(f"Total balance across all users: ${total_balance:.2f}")

asyncio.run(main())
