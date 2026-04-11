import os, sys
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')
from supabase import create_client

s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
uids = [1234500006, 1234500013, 1234500016, 1087836223]

print("=== 4 NEWLY APPROVED USERS ===")
for uid in uids:
    k = s.table('user_api_keys').select('key_hint, exchange').eq('telegram_id', uid).limit(1).execute()
    sess = s.table('autotrade_sessions').select('status, engine_active').eq('telegram_id', uid).limit(1).execute()
    has_key = bool(k.data)
    key_hint = k.data[0].get('key_hint') if k.data else 'none'
    status = sess.data[0].get('status') if sess.data else 'no session'
    engine_active = sess.data[0].get('engine_active') if sess.data else False
    
    if has_key:
        key_status = f"✅ has key (...{key_hint})"
    else:
        key_status = "❌ NO API KEY"
    
    print(f"  UID {uid} | {key_status} | session={status} | engine_active={engine_active}")
