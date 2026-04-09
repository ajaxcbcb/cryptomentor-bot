#!/usr/bin/env python3
"""Check which active users have/don't have API keys"""
import os, sys
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

# Load env manually
with open('/root/cryptomentor-bot/.env') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from supabase import create_client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
c = create_client(url, key)

# Get all active sessions
sessions = c.table('autotrade_sessions').select(
    'telegram_id, status, engine_active, trading_mode'
).not_.in_('status', ['pending_verification', 'uid_rejected', 'pending', 'stopped']).execute()

print(f"Total active sessions: {len(sessions.data)}")
print()

has_keys = []
no_keys = []

for s in sessions.data:
    uid = s['telegram_id']
    if uid >= 999999990:
        continue
    
    # Check API keys
    keys = c.table('user_api_keys').select('telegram_id, exchange, api_key').eq('telegram_id', uid).limit(1).execute()
    
    if keys.data:
        has_keys.append({'uid': uid, 'status': s['status'], 'engine': s['engine_active'], 'exchange': keys.data[0].get('exchange')})
    else:
        no_keys.append({'uid': uid, 'status': s['status'], 'engine': s['engine_active']})

print(f"✅ Users WITH API keys ({len(has_keys)}):")
for u in has_keys:
    print(f"  tg_id={u['uid']} | status={u['status']} | engine_active={u['engine']} | exchange={u['exchange']}")

print()
print(f"❌ Users WITHOUT API keys ({len(no_keys)}):")
for u in no_keys:
    print(f"  tg_id={u['uid']} | status={u['status']} | engine_active={u['engine']}")
