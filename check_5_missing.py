import sys, os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

from app.supabase_repo import _client
from app.autotrade_engine import is_running
from datetime import datetime, timezone

s = _client()

# All users with API keys
keys_res = s.table('user_api_keys').select('telegram_id').execute()
key_uids = {r['telegram_id'] for r in (keys_res.data or []) if r.get('telegram_id') and int(r.get('telegram_id',0)) < 999999990}

# All sessions
sess_res = s.table('autotrade_sessions').select('telegram_id, status, engine_active, updated_at').execute()
sessions = {r['telegram_id']: r for r in (sess_res.data or []) if r.get('telegram_id') and int(r.get('telegram_id',0)) < 999999990}

print(f"Users with API keys: {len(key_uids)}")
print(f"Users with sessions: {len(sessions)}")
print(f"Currently running: {sum(1 for uid in key_uids if is_running(uid))}")

print("\n=== 5 USERS NOT RUNNING ===")
not_running = [uid for uid in key_uids if not is_running(uid)]
for uid in sorted(not_running):
    sess = sessions.get(uid)
    if not sess:
        print(f"  UID {uid} — ❌ NO SESSION (needs to be created)")
    else:
        status = sess.get('status', 'unknown')
        updated = str(sess.get('updated_at', ''))[:16]
        if status == 'stopped':
            print(f"  UID {uid} — 🔴 STOPPED manually (last: {updated})")
        else:
            print(f"  UID {uid} — status={status} engine_active={sess.get('engine_active')} (last: {updated})")
