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
key_ids = {k['telegram_id'] for k in c.table('user_api_keys').select('telegram_id').execute().data}
sessions = c.table('autotrade_sessions').select('telegram_id, status, initial_deposit').execute()
print(f'Total sessions: {len(sessions.data)}, Users with keys: {len(key_ids)}')
for s in sessions.data:
    uid = s['telegram_id']
    if uid >= 999999990:
        continue
    dep = float(s.get('initial_deposit') or 0)
    has_key = uid in key_ids
    status = s['status']
    print(f'  {uid} | {status} | deposit={dep} | key={has_key}')
