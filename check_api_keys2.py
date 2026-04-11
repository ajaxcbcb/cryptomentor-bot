import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah/venv/lib/python3.12/site-packages')

env_path = '/root/cryptomentor-bot/.env'
for line in open(env_path):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

from app.supabase_repo import _client
from app.lib.crypto import decrypt

s = _client()

keys_res = s.table('user_api_keys').select('telegram_id, api_key, api_secret_enc, key_hint').execute()
keys_data = keys_res.data or []

sessions_res = s.table('autotrade_sessions').select('telegram_id, status, engine_active').not_.in_(
    'status', ['pending_verification', 'uid_rejected', 'pending', 'stopped']
).execute()
sessions = sessions_res.data or []

print(f"\n=== USER API KEYS ({len(keys_data)} total) ===")
keys_by_uid = {}
for k in keys_data:
    uid = k.get('telegram_id')
    try:
        secret = decrypt(k.get('api_secret_enc', ''))
        status = 'OK'
    except Exception as e:
        status = f'DECRYPT_FAIL: {e}'
    keys_by_uid[uid] = status
    print(f"  UID {uid} | hint: ...{k.get('key_hint')} | {status}")

print(f"\n=== ACTIVE SESSIONS ({len(sessions)} total) ===")
for sess in sessions:
    uid = sess.get('telegram_id')
    key_status = keys_by_uid.get(uid, 'NO KEY IN DB')
    print(f"  UID {uid} | status={sess.get('status')} | engine_active={sess.get('engine_active')} | keys={key_status}")
