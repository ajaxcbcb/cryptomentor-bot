#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')
os.chdir('/root/cryptomentor-bot/website-backend')
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')

from dotenv import load_dotenv
load_dotenv('.env')

from app.services import bitunix as bsvc

tg_id = 1234500009
keys = bsvc.get_user_api_keys(tg_id)
print(f"API keys found: {keys is not None}")
if keys:
    print(f"Exchange: {keys['exchange']}")
    print(f"Key hint: ...{keys['key_hint']}")
    print("Testing connection...")
    import asyncio
    acc = asyncio.run(bsvc.fetch_account(tg_id))
    print(f"Account success: {acc.get('success')}")
    if acc.get('success'):
        print(f"Balance: {acc.get('available', 0)}")
        print(f"Unrealized PnL: {acc.get('total_unrealized_pnl', 0)}")
    else:
        print(f"Error: {acc.get('error')}")
    
    pos = asyncio.run(bsvc.fetch_positions(tg_id))
    print(f"Positions success: {pos.get('success')}")
    if pos.get('success'):
        print(f"Open positions: {len(pos.get('positions', []))}")
else:
    print("No API keys found for this user")
