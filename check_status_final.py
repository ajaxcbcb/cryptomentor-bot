import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

env_path = '/root/cryptomentor-bot/.env'
for line in open(env_path):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

from app.supabase_repo import _client
from app.autotrade_engine import is_running

s = _client()

# Check the 4 newly approved users
pending_uids = [985106924, 5187148337, 1306878013, 1087836223]

print("=== STATUS 4 USER BARU ===")
for uid in pending_uids:
    ver = s.table('user_verifications').select('status, bitunix_uid, reviewed_at').eq('telegram_id', uid).limit(1).execute()
    ver_row = (ver.data or [{}])[0]
    
    sess = s.table('autotrade_sessions').select('status, engine_active').eq('telegram_id', uid).limit(1).execute()
    sess_row = (sess.data or [{}])[0]
    
    keys = s.table('user_api_keys').select('key_hint').eq('telegram_id', uid).limit(1).execute()
    has_keys = bool(keys.data)
    
    engine_running = is_running(uid)
    
    print(f"\n  UID {uid}:")
    print(f"    Verification: {ver_row.get('status','none')} | reviewed: {str(ver_row.get('reviewed_at',''))[:16]}")
    print(f"    Session: {sess_row.get('status','no session')} | engine_active: {sess_row.get('engine_active')}")
    print(f"    API Keys: {'✅ yes' if has_keys else '❌ no'}")
    print(f"    Engine running: {'✅ YES' if engine_running else '❌ NO'}")

# Overall count
print("\n=== TOTAL AUTOTRADE USERS ===")
all_ver = s.table('user_verifications').select('telegram_id, status').execute()
approved = [r for r in (all_ver.data or []) if r.get('status') in ('approved','uid_verified','active','verified')]
print(f"  Verified users: {len(approved)}")

all_keys = s.table('user_api_keys').select('telegram_id').execute()
key_uids = {r['telegram_id'] for r in (all_keys.data or []) if r.get('telegram_id') and int(r.get('telegram_id',0)) < 999999990}
print(f"  Users with API keys: {len(key_uids)}")

running_count = sum(1 for uid in key_uids if is_running(uid))
print(f"  Engines currently running: {running_count}")
print(f"\n  TOTAL AUTOTRADE USERS (verified + API keys): {len(approved)}")
