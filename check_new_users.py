import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

env_path = '/root/cryptomentor-bot/.env'
for line in open(env_path):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

from app.supabase_repo import _client
from datetime import datetime, timedelta, timezone

s = _client()
since = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()

print("=== NEW USERS (last 48h) ===")
u = s.table('users').select('telegram_id,first_name,username,created_at').gte('created_at', since).execute()
for row in (u.data or []):
    print(f"  UID={row.get('telegram_id')} name={row.get('first_name')} @{row.get('username')} joined={str(row.get('created_at',''))[:16]}")

print("\n=== PENDING UID VERIFICATIONS ===")
try:
    v = s.table('user_verifications').select('telegram_id,bitunix_uid,status,submitted_at').eq('status','pending').execute()
    for row in (v.data or []):
        print(f"  UID={row.get('telegram_id')} bitunix_uid={row.get('bitunix_uid')} submitted={str(row.get('submitted_at',''))[:16]}")
    if not v.data:
        print("  (none)")
except Exception as e:
    print(f"  Error: {e}")

print("\n=== ALL VERIFICATIONS (last 48h) ===")
try:
    v2 = s.table('user_verifications').select('telegram_id,bitunix_uid,status,submitted_at').gte('submitted_at', since).execute()
    for row in (v2.data or []):
        print(f"  UID={row.get('telegram_id')} bitunix_uid={row.get('bitunix_uid')} status={row.get('status')} submitted={str(row.get('submitted_at',''))[:16]}")
    if not v2.data:
        print("  (none)")
except Exception as e:
    print(f"  Error: {e}")

print("\n=== ADMIN IDS IN ENV ===")
for key in ('ADMIN_IDS','ADMIN1','ADMIN2','ADMIN3'):
    val = os.getenv(key,'')
    if val:
        print(f"  {key}={val}")
