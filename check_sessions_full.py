#!/usr/bin/env python3
import os

with open('/root/cryptomentor-bot/.env') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from supabase import create_client
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# Get ALL sessions no filter
all_sessions = c.table('autotrade_sessions').select(
    'telegram_id, status, engine_active, trading_mode'
).execute()

key_ids = {k['telegram_id'] for k in c.table('user_api_keys').select('telegram_id').execute().data}

print(f"ALL sessions: {len(all_sessions.data)}")
print()

# Group by status
from collections import defaultdict
by_status = defaultdict(list)
for s in all_sessions.data:
    by_status[s['status']].append(s)

for status, rows in sorted(by_status.items()):
    print(f"Status '{status}': {len(rows)} users")
    for r in rows:
        uid = r['telegram_id']
        has_key = uid in key_ids
        print(f"  tg_id={uid} | engine={r['engine_active']} | mode={r.get('trading_mode')} | api_key={'✅' if has_key else '❌'}")
    print()

# What the restore query actually returns
print("=== RESTORE QUERY RESULT (not in stopped/pending/rejected) ===")
res = c.table('autotrade_sessions').select('telegram_id, status, engine_active').not_.in_(
    'status', ['pending_verification', 'uid_rejected', 'pending', 'stopped']
).execute()
print(f"Returns: {len(res.data)} sessions")
for r in res.data:
    uid = r['telegram_id']
    has_key = uid in key_ids
    print(f"  tg_id={uid} | status={r['status']} | engine={r['engine_active']} | api_key={'✅' if has_key else '❌'}")
