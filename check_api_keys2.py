#!/usr/bin/env python3
"""Check user_api_keys table directly"""
import os

with open('/root/cryptomentor-bot/.env') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from supabase import create_client
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

print("=== ALL ROWS IN user_api_keys ===")
keys = c.table('user_api_keys').select('telegram_id, exchange, api_key, created_at').execute()
print(f"Total rows: {len(keys.data)}")
for k in keys.data:
    hint = k['api_key'][-6:] if k.get('api_key') else 'N/A'
    print(f"  tg_id={k['telegram_id']} | exchange={k.get('exchange')} | key=...{hint} | created={k.get('created_at','?')[:10]}")

print()
print("=== ACTIVE SESSIONS vs API KEYS ===")
sessions = c.table('autotrade_sessions').select(
    'telegram_id, status, engine_active'
).not_.in_('status', ['pending_verification', 'uid_rejected', 'pending', 'stopped']).execute()

key_ids = {k['telegram_id'] for k in keys.data}

for s in sessions.data:
    uid = s['telegram_id']
    if uid >= 999999990:
        continue
    has_key = uid in key_ids
    print(f"  tg_id={uid} | status={s['status']} | engine={s['engine_active']} | has_api_key={'✅' if has_key else '❌'}")
