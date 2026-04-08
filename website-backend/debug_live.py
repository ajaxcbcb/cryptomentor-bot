import asyncio, sys, os
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
os.chdir('/root/cryptomentor-bot/website-backend')

from app.services.bitunix import fetch_account, fetch_positions

async def main():
    tg_id = 1234500009
    print("Fetching account...")
    acc = await fetch_account(tg_id)
    print("Account:", acc)
    print()
    print("Fetching positions...")
    pos = await fetch_positions(tg_id)
    print("Positions:", pos)

asyncio.run(main())
