#!/usr/bin/env python3
"""
Check Community Partners button visibility issue.
Investigate why button is missing from user's dashboard.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv("Bismillah/.env")

sys.path.insert(0, "Bismillah")

from app.supabase_repo import _client

def check_community_button_visibility():
    """Check all users and their status to understand button visibility."""
    
    print("="*80)
    print("COMMUNITY PARTNERS BUTTON VISIBILITY ANALYSIS")
    print("="*80)
    
    # Get all autotrade sessions
    s = _client()
    res = s.table("autotrade_sessions").select("*").execute()
    sessions = res.data or []
    
    print(f"\nTotal sessions: {len(sessions)}")
    
    # Analyze status distribution
    status_counts = {}
    for session in sessions:
        status = session.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\n" + "="*80)
    print("STATUS DISTRIBUTION:")
    print("="*80)
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"  {status:30s}: {count:3d} users")
    
    # Check button visibility logic
    print("\n" + "="*80)
    print("BUTTON VISIBILITY LOGIC:")
    print("="*80)
    print("Current condition: show_community = (status == 'uid_verified' OR status == 'active')")
    
    # Count how many users would see the button
    visible_count = sum(1 for s in sessions if s.get("status") in ["uid_verified", "active"])
    hidden_count = len(sessions) - visible_count
    
    print(f"\n  ✅ Button VISIBLE for: {visible_count} users")
    print(f"  ❌ Button HIDDEN for:  {hidden_count} users")
    
    # Show users who have engines but can't see button
    print("\n" + "="*80)
    print("USERS WITH ENGINES BUT NO BUTTON:")
    print("="*80)
    
    hidden_users = [s for s in sessions if s.get("status") not in ["uid_verified", "active"]]
    if hidden_users:
        for session in hidden_users[:10]:  # Show first 10
            user_id = session.get("telegram_id")
            status = session.get("status", "unknown")
            deposit = session.get("initial_deposit", 0)
            print(f"  User {user_id}: status={status}, deposit={deposit} USDT")
        if len(hidden_users) > 10:
            print(f"  ... and {len(hidden_users) - 10} more")
    else:
        print("  None - all users with sessions can see the button")
    
    # Check community partners table
    print("\n" + "="*80)
    print("COMMUNITY PARTNERS:")
    print("="*80)
    
    res = s.table("community_partners").select("*").execute()
    communities = res.data or []
    
    print(f"Total communities: {len(communities)}")
    for comm in communities:
        name = comm.get("community_name", "Unknown")
        code = comm.get("community_code", "")
        status = comm.get("status", "")
        members = comm.get("member_count", 0)
        leader_id = comm.get("telegram_id")
        print(f"  {name} ({code}): {status}, {members} members, leader={leader_id}")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS:")
    print("="*80)
    
    if hidden_count > 0:
        print("⚠️  ISSUE FOUND:")
        print(f"   {hidden_count} users have sessions but can't see Community Partners button")
        print(f"   because their status is not 'uid_verified' or 'active'")
        print()
        print("💡 SOLUTION OPTIONS:")
        print("   1. Relax condition to show button for ALL users with sessions")
        print("      (regardless of status)")
        print()
        print("   2. Show button for users with status in:")
        print("      ['uid_verified', 'active', 'pending_verification', 'inactive']")
        print()
        print("   3. Keep current logic but ensure all verified users have")
        print("      status = 'uid_verified' or 'active'")
    else:
        print("✅ No issues found - all users with sessions can see the button")
    
    print("="*80)

if __name__ == "__main__":
    try:
        check_community_button_visibility()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
