import sys, os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

# Simulate exactly what scheduler does
from app.supabase_repo import _client
from app.lib.crypto import decrypt

def get_user_api_keys_debug(telegram_id):
    s = _client()
    res = s.table("user_api_keys").select("*").eq("telegram_id", int(telegram_id)).limit(1).execute()
    print(f"  DB query result: {len(res.data or [])} rows")
    if not res.data:
        print(f"  -> No data in DB")
        return None
    row = res.data[0]
    print(f"  Row keys: {list(row.keys())}")
    print(f"  api_secret_enc present: {'api_secret_enc' in row}")
    enc = row.get("api_secret_enc", "")
    print(f"  enc length: {len(enc)}")
    try:
        secret = decrypt(enc)
        print(f"  Decrypt: OK (len={len(secret)})")
        return {"api_key": row["api_key"], "api_secret": secret}
    except Exception as e:
        print(f"  Decrypt FAILED: {e}")
        return None

print("Testing UID 1187119989:")
result = get_user_api_keys_debug(1187119989)
print(f"Result: {result is not None}")

# Now test the actual function from handlers_autotrade
print("\nTesting via handlers_autotrade.get_user_api_keys:")
from app.handlers_autotrade import get_user_api_keys
result2 = get_user_api_keys(1187119989)
print(f"Result: {result2 is not None}")
if result2:
    print(f"  key_hint: {result2.get('key_hint')}")
