#!/usr/bin/env python3
"""
Test Community Partners button visibility logic
Simulates the exact logic from handlers_autotrade.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv("Bismillah/.env")
sys.path.insert(0, "Bismillah")

from app.supabase_repo import _client
from app.demo_users import is_demo_user

def test_button_visibility(telegram_id):
    """Test if button should be visible for a specific user."""
    
    print("="*80)
    print(f"TESTING COMMUNITY BUTTON VISIBILITY FOR USER {telegram_id}")
    print("="*80)
    
    # Step 1: Check if demo user
    is_demo = is_demo_user(telegram_id)
    print(f"\n1. Demo User Check: {'❌ YES (BLOCKED)' if is_demo else '✅ NO'}")
    
    if is_demo:
        print("   → Demo users are blocked from Community Partners")
        print("   → Button will NOT appear")
        return False
    
    # Step 2: Get session
    s = _client()
    res = s.table("autotrade_sessions").select("*").eq("telegram_id", telegram_id).execute()
    session = res.data[0] if res.data else None
    
    print(f"\n2. Session Check: {'✅ FOUND' if session else '❌ NOT FOUND'}")
    
    if not session:
        print("   → No session found")
        print("   → Button will NOT appear")
        return False
    
    # Step 3: Check status
    uid_status = session.get("status", "")
    print(f"\n3. Status Check: {uid_status}")
    
    # Step 4: Button visibility logic
    show_community = uid_status in ["uid_verified", "active", "stopped"]
    
    print(f"\n4. Button Visibility Logic:")
    print(f"   uid_status in ['uid_verified', 'active', 'stopped']")
    print(f"   '{uid_status}' in ['uid_verified', 'active', 'stopped']")
    print(f"   Result: {show_community}")
    
    print(f"\n{'='*80}")
    print(f"FINAL RESULT: Button {'✅ WILL APPEAR' if show_community else '❌ WILL NOT APPEAR'}")
    print(f"{'='*80}")
    
    if not show_community:
        print(f"\nREASON: Status '{uid_status}' is not in the allowed list")
        print("Allowed statuses: uid_verified, active, stopped")
    
    return show_community

if __name__ == "__main__":
    # Test for common user IDs
    test_users = [
        1234500002,  # Demo user with stopped status
        1234500008, # Regular user with stopped status
        1234500018, # Regular user with active status
    ]
    
    for user_id in test_users:
        test_button_visibility(user_id)
        print("\n" + "="*80 + "\n")
