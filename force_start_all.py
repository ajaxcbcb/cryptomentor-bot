#!/usr/bin/env python3
"""Force start all eligible users"""
import os

with open('/root/cryptomentor-bot/.env') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from supabase import create_client
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

key_ids = {k['telegram_id'] for k in c.table('user_api_keys').select('telegram_id').execute().data}
sessions = c.table('autotrade_sessions').select('telegram_id, status, initial_deposit').execute()

updated = []
skipped = []

for s in sessions.data:
    uid = s['telegram_id']
    if uid in (999999999, 999999998, 999999997, 500000025, 500000026):
        continue
    if s['status'] in ('uid_rejected', 'inactive', 'pending_verification', 'pending'):
        skipped.append(f"  SKIP {uid} - status={s['status']}")
        continue
    if uid not in key_ids:
        skipped.append(f"  SKIP {uid} - no API key")
        continue
    dep = float(s.get('initial_deposit') or 0)
    if dep <= 0:
        skipped.append(f"  SKIP {uid} - deposit=0")
        continue

    c.table('autotrade_sessions').update({
        'status': 'active',
        'engine_active': False
    }).eq('telegram_id', uid).execute()
    updated.append(uid)
    print(f"  ✅ {uid} | was={s['status']} | deposit={dep}")

print()
for s in skipped:
    print(s)

print(f"\nForce-activated: {len(updated)} users")
