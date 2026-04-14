"""Check what get_user_api_keys returns inside bot environment."""
import sys, os

# Simulate exact bot startup
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')

sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

from app.supabase_repo import _client

s = _client()

# Check all user_api_keys
res = s.table('user_api_keys').select('telegram_id, key_hint').execute()
print(f"Total rows in user_api_keys: {len(res.data or [])}")
for r in (res.data or []):
    print(f"  UID {r.get('telegram_id')} hint={r.get('key_hint')}")

# Test specific user
test_uid = 1187119989
res2 = s.table('user_api_keys').select('*').eq('telegram_id', test_uid).limit(1).execute()
print(f"\nDirect query UID {test_uid}: {len(res2.data or [])} rows")

# Test get_user_api_keys
from app.handlers_autotrade import get_user_api_keys
result = get_user_api_keys(test_uid)
print(f"get_user_api_keys({test_uid}): {result is not None}")
if result:
    print(f"  key_hint: {result.get('key_hint')}")
