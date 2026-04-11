import sys, os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

from app.supabase_repo import _client
from app.lib.crypto import decrypt

s = _client()
res = s.table('user_api_keys').select('*').eq('telegram_id', 1187119989).limit(1).execute()
row = res.data[0]
enc = row['api_secret_enc']
print(f"enc: {enc[:30]}...")
print(f"ENCRYPTION_KEY: {os.getenv('ENCRYPTION_KEY', '')[:15]}...")

try:
    result = decrypt(enc)
    print(f"Decrypt OK: len={len(result)}")
except Exception as e:
    print(f"Decrypt FAILED: {type(e).__name__}: {e}")
    # Check what crypto module is being used
    import app.lib.crypto as cm
    print(f"Crypto module: {cm.__file__}")
    import inspect
    print(inspect.getsource(cm.decrypt))
