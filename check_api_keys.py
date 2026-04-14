import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

# Load env
env_path = '/root/cryptomentor-bot/.env'
for line in open(env_path):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

from app.supabase_repo import _client
from app.lib.crypto import decrypt

s = _client()

# Get all user_api_keys
keys_res = s.table('user_api_keys').select('telegram_id, api_key, api_secret_enc, key_hint').execute()
keys_data = keys_res.data or []

# Get all autotrade_sessions that should be active
sessions_res = s.table('autotrade_sessions').select('telegram_id, status, engine_active').not_.in_(
    'status', ['pending_verification', 'uid_rejected', 'pending', 'stopped']
).execute()
sessions = sessions_res.data or []

print(f"\n=== USER API KEYS IN DATABASE ({len(keys_data)} total) ===")
keys_by_uid = {}
for k in keys_data:
    uid = k.get('telegram_id')
    try:
        secret = decrypt(k.get('api_secret_enc', ''))
        status = 'OK'
    except Exception as e:
        secret = None
        status = f'DECRYPT_FAIL: {e}'
    keys_by_uid[uid] = status
    print(f"  UID {uid} | hint: {k.get('key_hint')} | decrypt: {status}")

print(f"\n=== ACTIVE SESSIONS WITHOUT VALID API KEYS ===")
for sess in sessions:
    uid = sess.get('telegram_id')
    if uid not in keys_by_uid:
        print(f"  UID {uid} | status={sess.get('status')} | NO API KEY IN DB")
    elif 'FAIL' in keys_by_uid.get(uid, ''):
        print(f"  UID {uid} | status={sess.get('status')} | {keys_by_uid[uid]}")
    else:
        print(f"  UID {uid} | status={sess.get('status')} | API key OK")
