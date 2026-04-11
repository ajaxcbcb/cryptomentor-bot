import sys, os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

from app.supabase_repo import _client

s = _client()

# All sessions
all_sess = s.table('autotrade_sessions').select('telegram_id, status, engine_active, updated_at').execute()

print("=== ALL SESSIONS STATUS ===")
stopped = []
no_session_uids = []

for r in (all_sess.data or []):
    uid = r.get('telegram_id')
    if not uid or int(uid) >= 999999990:
        continue
    status = r.get('status', '')
    updated = str(r.get('updated_at', ''))[:16]
    print(f"  UID {uid} | status={status} | engine_active={r.get('engine_active')} | updated={updated}")
    if status == 'stopped':
        stopped.append(uid)

print(f"\n=== STOPPED (manual): {len(stopped)} ===")
for uid in stopped:
    print(f"  UID {uid}")

# Check users with API keys but no session
keys_res = s.table('user_api_keys').select('telegram_id').execute()
key_uids = {r['telegram_id'] for r in (keys_res.data or []) if r.get('telegram_id') and int(r.get('telegram_id',0)) < 999999990}
session_uids = {r['telegram_id'] for r in (all_sess.data or []) if r.get('telegram_id') and int(r.get('telegram_id',0)) < 999999990}

no_session = key_uids - session_uids
print(f"\n=== USERS WITH API KEYS BUT NO SESSION: {len(no_session)} ===")
for uid in sorted(no_session):
    print(f"  UID {uid} — needs session created")
