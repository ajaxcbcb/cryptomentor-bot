#!/usr/bin/env python3
"""Check trading_mode in Supabase database"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

from app.supabase_repo import _client

try:
    s = _client()
    
    # Query active sessions
    result = s.table("autotrade_sessions").select(
        "telegram_id, trading_mode, risk_mode, is_active"
    ).eq("is_active", True).execute()
    
    print("\n=== ACTIVE AUTOTRADE SESSIONS ===\n")
    print(f"{'User ID':<15} {'Trading Mode':<15} {'Risk Mode':<15}")
    print("-" * 50)
    
    scalping_count = 0
    swing_count = 0
    manual_count = 0
    
    for row in result.data:
        user_id = row.get('telegram_id')
        trading_mode = row.get('trading_mode') or 'NULL'
        risk_mode = row.get('risk_mode') or 'NULL'
        
        print(f"{user_id:<15} {trading_mode:<15} {risk_mode:<15}")
        
        if trading_mode == "scalping":
            scalping_count += 1
        elif trading_mode == "swing":
            swing_count += 1
        elif trading_mode == "manual":
            manual_count += 1
    
    print("-" * 50)
    print(f"\nTotal active sessions: {len(result.data)}")
    print(f"Scalping mode: {scalping_count}")
    print(f"Swing mode: {swing_count}")
    print(f"Manual mode: {manual_count}")
    
    if scalping_count == 0:
        print("\n⚠️  WARNING: No scalping sessions found!")
        print("This explains why scalping engines are not generating signals.")
        print("Run migrate_all_to_scalping.py to fix this.")
    elif scalping_count > 0:
        print(f"\n✅ Found {scalping_count} scalping sessions")
        print("Scalping engines should be running...")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
