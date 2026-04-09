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

# No filter at all
r = c.table('autotrade_sessions').select('telegram_id, status, initial_deposit').execute()
print(f'Raw count: {len(r.data)}')
for s in r.data:
    print(f"  {s['telegram_id']} | {s['status']} | {s.get('initial_deposit')}")
