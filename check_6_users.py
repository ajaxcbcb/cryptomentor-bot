#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')
os.chdir('/root/cryptomentor-bot/Bismillah')

from app.supabase_repo import _client

s = _client()
uids = [6954315669, 1265990951, 1306878013, 7338184122, 8429733088, 1766523174]

print("\n=== STATUS 6 INACTIVE USERS ===\n")
for uid in uids:
    res = s.table("autotrade_sessions").select(
        "telegram_id,status,engine_active,trading_mode,initial_deposit,leverage,updated_at"
    ).eq("telegram_id", uid).execute()
    
    keys = s.table("user_api_keys").select(
        "telegram_id,exchange,api_key"
    ).eq("telegram_id", uid).execute()
    
    session = res.data[0] if res.data else None
    key = keys.data[0] if keys.data else None
    
    if session:
        has_key = bool(key and key.get('api_key'))
        api_key_preview = key['api_key'][:8] + '...' if has_key else 'MISSING'
        print(f"uid={uid}")
        print(f"  status={session.get('status')} | engine_active={session.get('engine_active')}")
        print(f"  mode={session.get('trading_mode')} | deposit=${session.get('initial_deposit')} | leverage={session.get('leverage')}x")
        print(f"  api_key={api_key_preview} | exchange={key.get('exchange') if key else 'N/A'}")
        print(f"  updated_at={session.get('updated_at')}")
        print()
    else:
        print(f"uid={uid} - NO SESSION FOUND\n")
