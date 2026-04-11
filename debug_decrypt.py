"""Debug why get_user_api_keys returns None inside bot process."""
import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

env_path = '/root/cryptomentor-bot/.env'
for line in open(env_path):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

print(f"ENCRYPTION_KEY set: {bool(os.getenv('ENCRYPTION_KEY'))}")
print(f"ENCRYPTION_KEY value: {os.getenv('ENCRYPTION_KEY', '')[:10]}...")

from app.supabase_repo import _client
from app.lib.crypto import decrypt

s = _client()
# Test with one user
test_uid = 1234500009
res = s.table('user_api_keys').select('*').eq('telegram_id', test_uid).limit(1).execute()
if not res.data:
    print(f"UID {test_uid}: NO ROW IN user_api_keys")
else:
    row = res.data[0]
    print(f"UID {test_uid}: Row found, key_hint={row.get('key_hint')}")
    enc = row.get('api_secret_enc', '')
    print(f"  api_secret_enc length: {len(enc)}")
    print(f"  api_secret_enc prefix: {enc[:20]}...")
    try:
        secret = decrypt(enc)
        print(f"  Decrypt: SUCCESS (len={len(secret)})")
    except Exception as e:
        print(f"  Decrypt: FAILED — {e}")
        # Try to understand the encryption format
        import base64
        try:
            decoded = base64.urlsafe_b64decode(enc + '==')
            print(f"  Base64 decoded length: {len(decoded)}")
        except Exception as e2:
            print(f"  Base64 decode failed: {e2}")
