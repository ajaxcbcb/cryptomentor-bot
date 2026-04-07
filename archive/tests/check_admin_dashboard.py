#!/usr/bin/env python3
"""
Check admin dashboard status
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv("Bismillah/.env")
sys.path.insert(0, "Bismillah")

from app.supabase_repo import _client
from app.demo_users import is_demo_user

# Get admin IDs from env
ADMIN_IDS = set()
for key in ["ADMIN1", "ADMIN2", "ADMIN3"]:
    val = os.getenv(key, "").strip()
    if val and val.isdigit():
        ADMIN_IDS.add(int(val))

admin_ids_str = os.getenv("ADMIN_IDS", "")
if admin_ids_str:
    for val in admin_ids_str.split(","):
        val = val.strip()
        if val.isdigit():
            ADMIN_IDS.add(int(val))

print("="*80)
print("ADMIN DASHBOARD ANALYSIS")
print("="*80)

print(f"\nAdmin IDs from .env: {sorted(ADMIN_IDS)}")

# Check each admin's session
s = _client()

for admin_id in sorted(ADMIN_IDS):
    print(f"\n{'='*80}")
    print(f"ADMIN ID: {admin_id}")
    print(f"{'='*80}")
    
    # Check if demo user
    is_demo = is_demo_user(admin_id)
    print(f"Demo User: {'YES ❌' if is_demo else 'NO ✅'}")
    
    # Get session
    res = s.table("autotrade_sessions").select("*").eq("telegram_id", admin_id).execute()
    session = res.data[0] if res.data else None
    
    if not session:
        print("Session: NOT FOUND ❌")
        print("→ Admin has no autotrade session")
        print("→ Community Partners button will NOT appear")
        continue
    
    # Check session details
    status = session.get("status", "unknown")
    deposit = session.get("initial_deposit", 0)
    
    print(f"Session: FOUND ✅")
    print(f"  Status: {status}")
    print(f"  Deposit: {deposit} USDT")
    
    # Check button visibility
    show_community = status in ["uid_verified", "active", "stopped"]
    
    print(f"\nButton Visibility Logic:")
    print(f"  status in ['uid_verified', 'active', 'stopped']")
    print(f"  '{status}' in ['uid_verified', 'active', 'stopped']")
    print(f"  Result: {show_community}")
    
    print(f"\nCommunity Partners Button: {'✅ WILL APPEAR' if show_community else '❌ WILL NOT APPEAR'}")
    
    if not show_community:
        print(f"\nREASON: Status '{status}' is not in allowed list")
        print("To fix: Change status to 'uid_verified', 'active', or 'stopped'")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

# Get all sessions
res = s.table("autotrade_sessions").select("*").execute()
all_sessions = res.data or []

admin_sessions = [s for s in all_sessions if s.get("telegram_id") in ADMIN_IDS]
user_sessions = [s for s in all_sessions if s.get("telegram_id") not in ADMIN_IDS]

print(f"\nTotal sessions: {len(all_sessions)}")
print(f"  Admin sessions: {len(admin_sessions)}")
print(f"  User sessions: {len(user_sessions)}")

# Count button visibility
admin_with_button = sum(1 for s in admin_sessions if s.get("status") in ["uid_verified", "active", "stopped"])
user_with_button = sum(1 for s in user_sessions if s.get("status") in ["uid_verified", "active", "stopped"])

print(f"\nButton visibility:")
print(f"  Admins with button: {admin_with_button}/{len(admin_sessions)}")
print(f"  Users with button: {user_with_button}/{len(user_sessions)}")

print("\n" + "="*80)
