"""Minimal test - check all 22 API keys one by one."""
import os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')

import sys, asyncio
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

from supabase import create_client
from app.lib.crypto import decrypt

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
s = create_client(url, key)

keys_res = s.table('user_api_keys').select('*').execute()
all_rows = [r for r in (keys_res.data or []) if r.get('telegram_id') and int(r.get('telegram_id',0)) < 999999990]
print(f"Total rows: {len(all_rows)}")

# First just test decrypt for all
print("\n=== DECRYPT TEST ===")
decrypt_ok = []
decrypt_fail = []
for row in all_rows:
    uid = int(row['telegram_id'])
    hint = row.get('key_hint', '???')
    enc = row.get('api_secret_enc', '')
    try:
        secret = decrypt(enc)
        print(f"  UID {uid} | ...{hint} | decrypt OK (len={len(secret)})")
        decrypt_ok.append({'uid': uid, 'api_key': row['api_key'], 'api_secret': secret, 'hint': hint})
    except Exception as e:
        print(f"  UID {uid} | ...{hint} | DECRYPT FAILED: {e}")
        decrypt_fail.append({'uid': uid, 'hint': hint})

print(f"\nDecrypt OK: {len(decrypt_ok)} | Decrypt FAIL: {len(decrypt_fail)}")

# Now test connection for decrypt_ok users
print("\n=== CONNECTION TEST ===")
from app.bitunix_autotrade_client import BitunixAutoTradeClient

invalid_users = list(decrypt_fail)  # decrypt failures are already invalid
valid_users = []

for u in decrypt_ok:
    uid = u['uid']
    hint = u['hint']
    try:
        client = BitunixAutoTradeClient(api_key=u['api_key'], api_secret=u['api_secret'])
        result = client.check_connection()
        if result.get('online'):
            print(f"  UID {uid} | ...{hint} | ✅ VALID")
            valid_users.append(uid)
        else:
            error = result.get('error', 'Connection failed')
            print(f"  UID {uid} | ...{hint} | ❌ INVALID: {error}")
            invalid_users.append({'uid': uid, 'reason': error, 'hint': hint})
    except Exception as e:
        print(f"  UID {uid} | ...{hint} | ❌ ERROR: {str(e)[:80]}")
        invalid_users.append({'uid': uid, 'reason': str(e)[:80], 'hint': hint})

print(f"\n=== FINAL SUMMARY ===")
print(f"✅ Valid: {len(valid_users)}")
print(f"❌ Invalid/Failed: {len(invalid_users)}")
if invalid_users:
    print("\nInvalid users:")
    for u in invalid_users:
        print(f"  UID {u['uid']} | ...{u.get('hint','?')} | {u.get('reason','?')}")

# Save invalid UIDs to file for notification
if invalid_users:
    with open('/tmp/invalid_uids.txt', 'w') as f:
        for u in invalid_users:
            f.write(f"{u['uid']}\n")
    print(f"\nSaved {len(invalid_users)} invalid UIDs to /tmp/invalid_uids.txt")
