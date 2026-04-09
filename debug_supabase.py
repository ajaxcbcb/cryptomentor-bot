#!/usr/bin/env python3
"""Debug Supabase query directly"""
import os

with open('/root/cryptomentor-bot/.env') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from supabase import create_client
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

print("=== TEST 1: Select ALL from autotrade_sessions ===")
r1 = c.table('autotrade_sessions').select('telegram_id, status, engine_active').execute()
print(f"Rows returned: {len(r1.data)}")
for r in r1.data:
    print(f"  {r['telegram_id']} | {r['status']} | engine={r['engine_active']}")

print()
print("=== TEST 2: not_.in_ filter ===")
r2 = c.table('autotrade_sessions').select('telegram_id, status').not_.in_(
    'status', ['pending_verification', 'uid_rejected', 'pending', 'stopped', 'inactive']
).execute()
print(f"Rows returned: {len(r2.data)}")
for r in r2.data:
    print(f"  {r['telegram_id']} | {r['status']}")

print()
print("=== TEST 3: status=active only ===")
r3 = c.table('autotrade_sessions').select('telegram_id, status').eq('status', 'active').execute()
print(f"Rows returned: {len(r3.data)}")
for r in r3.data:
    print(f"  {r['telegram_id']} | {r['status']}")

print()
print("=== TEST 4: status=uid_verified only ===")
r4 = c.table('autotrade_sessions').select('telegram_id, status').eq('status', 'uid_verified').execute()
print(f"Rows returned: {len(r4.data)}")
for r in r4.data:
    print(f"  {r['telegram_id']} | {r['status']}")
