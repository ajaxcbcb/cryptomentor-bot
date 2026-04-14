"""Full count of all autotrade users across all tables."""
import os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')

from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
s = create_client(url, key)

DEMO_USER_IDS = {1227424284, 801937545, 5765813002, 1165553495, 6735618958}
SKIP_TEST = {999999999, 999999998, 999999997, 500000025, 500000026}

print("=== USER_API_KEYS TABLE ===")
r = s.table('user_api_keys').select('telegram_id, key_hint, exchange').execute()
api_key_uids = set()
for row in (r.data or []):
    uid = row.get('telegram_id')
    if uid:
        api_key_uids.add(uid)
        demo = "DEMO" if uid in DEMO_USER_IDS else ""
        test = "TEST" if uid in SKIP_TEST else ""
        print(f"  UID {uid} | ...{row.get('key_hint')} | {row.get('exchange')} {demo}{test}")
print(f"Total: {len(api_key_uids)} | Demo: {len(api_key_uids & DEMO_USER_IDS)} | Test: {len(api_key_uids & SKIP_TEST)}")
real_api = api_key_uids - DEMO_USER_IDS - SKIP_TEST
print(f"Real users with API keys: {len(real_api)}")

print("\n=== AUTOTRADE_SESSIONS TABLE (all statuses) ===")
r2 = s.table('autotrade_sessions').select('telegram_id, status, engine_active').execute()
session_uids = set()
for row in (r2.data or []):
    uid = row.get('telegram_id')
    if uid:
        session_uids.add(uid)
        demo = "DEMO" if uid in DEMO_USER_IDS else ""
        test = "TEST" if uid in SKIP_TEST else ""
        print(f"  UID {uid} | status={row.get('status')} | engine_active={row.get('engine_active')} {demo}{test}")
print(f"Total sessions: {len(session_uids)}")
real_sessions = session_uids - DEMO_USER_IDS - SKIP_TEST
print(f"Real user sessions: {len(real_sessions)}")

print("\n=== USER_VERIFICATIONS TABLE (approved) ===")
r3 = s.table('user_verifications').select('telegram_id, status').execute()
verified_uids = set()
for row in (r3.data or []):
    uid = row.get('telegram_id')
    status = row.get('status', '')
    if uid and status in ('approved', 'uid_verified', 'active', 'verified'):
        verified_uids.add(uid)
print(f"Total verified users: {len(verified_uids)}")
real_verified = verified_uids - DEMO_USER_IDS - SKIP_TEST
print(f"Real verified (excl demo/test): {len(real_verified)}")

print("\n=== SUMMARY ===")
print(f"  API keys (real): {len(real_api)}")
print(f"  Sessions (real): {len(real_sessions)}")
print(f"  Verified (real): {len(real_verified)}")
print(f"  Demo users with API keys: {len(api_key_uids & DEMO_USER_IDS)}")

# Users with API keys but no session
no_session = real_api - session_uids
print(f"\n  Real users with API keys but NO session: {len(no_session)}")
for uid in sorted(no_session):
    print(f"    UID {uid}")
