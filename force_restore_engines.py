#!/usr/bin/env python3
"""
Force restore all engines via Supabase - reset engine_active flags
then trigger bot to restart them via health check
"""
import os

with open('/root/cryptomentor-bot/.env') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

from supabase import create_client
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

# Get all active sessions with API keys
sessions = c.table('autotrade_sessions').select(
    'telegram_id, status, engine_active, trading_mode, initial_deposit, leverage'
).not_.in_('status', ['pending_verification', 'uid_rejected', 'pending', 'stopped', 'inactive']).execute()

key_ids = {k['telegram_id'] for k in c.table('user_api_keys').select('telegram_id').execute().data}

print(f"Found {len(sessions.data)} active sessions")
print()

# Reset engine_active=False for all, then set True for those with API keys
# This forces health check to restart them
reset_count = 0
for s in sessions.data:
    uid = s['telegram_id']
    if uid >= 999999990:
        continue
    if uid not in key_ids:
        print(f"  SKIP tg_id={uid} - no API key")
        continue
    
    # Reset engine_active to False to force health check to restart
    c.table('autotrade_sessions').update({
        'engine_active': False
    }).eq('telegram_id', uid).execute()
    reset_count += 1
    print(f"  RESET tg_id={uid} | status={s['status']} | mode={s.get('trading_mode')}")

print(f"\nReset {reset_count} engines to engine_active=False")
print("Health check will restart them within 2 minutes")
print()
print("NOTE: Bot restart is needed to trigger immediate restore.")
print("Run: systemctl restart cryptomentor")
