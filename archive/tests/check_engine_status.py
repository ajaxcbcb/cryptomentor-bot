#!/usr/bin/env python3
"""Check current engine status and why they're stopping"""

import os
import sys
sys.path.insert(0, 'Bismillah')

from dotenv import load_dotenv
load_dotenv('Bismillah/.env')

from app.supabase_repo import _client
from app.autotrade_engine import is_running

def main():
    s = _client()
    
    # Get all active sessions
    result = s.table("autotrade_sessions").select("*").eq("status", "active").execute()
    sessions = result.data or []
    
    print(f"\n{'='*80}")
    print(f"ACTIVE SESSIONS IN DATABASE: {len(sessions)}")
    print(f"{'='*80}\n")
    
    for session in sessions:
        user_id = session['telegram_id']
        capital = session.get('initial_deposit', 0)
        leverage = session.get('leverage', 10)
        trading_mode = session.get('trading_mode', 'swing')
        
        # Check if engine actually running
        running = is_running(user_id)
        
        print(f"User: {user_id}")
        print(f"  Capital: {capital} USDT")
        print(f"  Leverage: {leverage}x")
        print(f"  Mode: {trading_mode}")
        print(f"  Engine Running: {'✅ YES' if running else '❌ NO'}")
        print()
    
    # Check for recently stopped sessions
    result2 = s.table("autotrade_sessions").select("*").eq("status", "stopped").order("updated_at", desc=True).limit(10).execute()
    stopped = result2.data or []
    
    if stopped:
        print(f"\n{'='*80}")
        print(f"RECENTLY STOPPED SESSIONS: {len(stopped)}")
        print(f"{'='*80}\n")
        
        for session in stopped:
            user_id = session['telegram_id']
            updated = session.get('updated_at', 'unknown')
            print(f"User: {user_id} - Stopped at: {updated}")

if __name__ == "__main__":
    main()
