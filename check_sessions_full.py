import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

env_path = '/root/cryptomentor-bot/.env'
for line in open(env_path):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

from app.supabase_repo import _client

s = _client()

# ALL sessions including stopped
all_sessions = s.table('autotrade_sessions').select('telegram_id, status, engine_active, updated_at').execute()
sessions = all_sessions.data or []

print(f"\n=== ALL AUTOTRADE SESSIONS ({len(sessions)} total) ===")
for sess in sessions:
    uid = sess.get('telegram_id')
    if uid and int(uid) >= 999999990:
        continue
    print(f"  UID {uid} | status={sess.get('status')} | engine_active={sess.get('engine_active')} | updated={str(sess.get('updated_at',''))[:16]}")

# Check which users with API keys have NO session
keys_res = s.table('user_api_keys').select('telegram_id').execute()
key_uids = {r.get('telegram_id') for r in (keys_res.data or [])}
session_uids = {s.get('telegram_id') for s in sessions if s.get('telegram_id') and int(s.get('telegram_id',0)) < 999999990}

no_session = key_uids - session_uids
print(f"\n=== USERS WITH API KEYS BUT NO SESSION ({len(no_session)}) ===")
for uid in sorted(no_session):
    print(f"  UID {uid} — has API keys but no autotrade_session row")
