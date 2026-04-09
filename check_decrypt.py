#!/usr/bin/env python3
"""Test decrypt API keys for all users"""
import os, sys
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

with open('/root/cryptomentor-bot/.env') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from supabase import create_client
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# Import decrypt function
from app.handlers_autotrade import get_user_api_keys

# Test all users with API keys
keys_rows = c.table('user_api_keys').select('telegram_id, exchange').execute()

print(f"Testing decrypt for {len(keys_rows.data)} users:\n")
ok = []
fail = []

for row in keys_rows.data:
    uid = row['telegram_id']
    result = get_user_api_keys(uid)
    if result:
        ok.append(uid)
        print(f"  ✅ {uid} | exchange={result['exchange']} | key=...{result['api_key'][-4:]}")
    else:
        fail.append(uid)
        print(f"  ❌ {uid} | DECRYPT FAILED")

print(f"\nSummary: {len(ok)} OK, {len(fail)} FAILED")
if fail:
    print(f"Failed users: {fail}")
