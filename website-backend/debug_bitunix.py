import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
os.chdir('/root/cryptomentor-bot/website-backend')

from app.services.bitunix import _BITUNIX_AVAILABLE, get_user_api_keys
print('BITUNIX_AVAILABLE:', _BITUNIX_AVAILABLE)

# Test dengan user ID yang ada
from app.db.supabase import _client
s = _client()
res = s.table("user_api_keys").select("telegram_id, exchange, key_hint").limit(5).execute()
print("Users with API keys:", res.data)

if res.data:
    tg_id = res.data[0]['telegram_id']
    keys = get_user_api_keys(tg_id)
    print(f"Keys for {tg_id}:", keys)
