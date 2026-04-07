#!/usr/bin/env python3
"""
Check specific user's community button access
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv("Bismillah/.env")
sys.path.insert(0, "Bismillah")

from app.supabase_repo import _client

def check_user_access(telegram_id=None):
    """Check if user should see Community Partners button."""
    
    s = _client()
    
    if telegram_id:
        # Check specific user
        res = s.table("autotrade_sessions").select("*").eq("telegram_id", telegram_id).execute()
        sessions = res.data or []
    else:
        # Check all users
        res = s.table("autotrade_sessions").select("*").execute()
        sessions = res.data or []
    
    print("="*80)
    print("COMMUNITY BUTTON ACCESS CHECK")
    print("="*80)
    
    for session in sessions:
        user_id = session.get("telegram_id")
        status = session.get("status", "unknown")
        deposit = session.get("initial_deposit", 0)
        
        # Check button visibility logic
        show_button = status in ["uid_verified", "active", "stopped"]
        
        print(f"\nUser ID: {user_id}")
        print(f"  Status: {status}")
        print(f"  Deposit: {deposit} USDT")
        print(f"  Button visible: {'✅ YES' if show_button else '❌ NO'}")
        
        if not show_button:
            print(f"  Reason: Status '{status}' not in ['uid_verified', 'active', 'stopped']")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    # Check all users
    check_user_access()
