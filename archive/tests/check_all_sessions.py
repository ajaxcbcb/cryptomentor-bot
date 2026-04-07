#!/usr/bin/env python3
"""Check all autotrade sessions - active and inactive"""

import sys
import os
from pathlib import Path

# Load environment variables
env_path = Path('/root/cryptomentor-bot/Bismillah/.env')
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

from app.supabase_repo import _client

try:
    s = _client()
    
    # Get ALL sessions (active and inactive)
    all_sessions = s.table("autotrade_sessions").select(
        "telegram_id, status, trading_mode, risk_mode, initial_deposit, leverage, created_at"
    ).execute()
    
    print("\n" + "="*80)
    print("AUTOTRADE SESSIONS ANALYSIS")
    print("="*80)
    
    active_sessions = [sess for sess in all_sessions.data if sess.get('status') == 'active']
    inactive_sessions = [sess for sess in all_sessions.data if sess.get('status') != 'active']
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total registered users: {len(all_sessions.data)}")
    print(f"   Active sessions: {len(active_sessions)}")
    print(f"   Inactive sessions: {len(inactive_sessions)}")
    
    print(f"\n✅ ACTIVE SESSIONS ({len(active_sessions)}):")
    print("-" * 80)
    print(f"{'User ID':<15} {'Trading Mode':<15} {'Risk Mode':<15} {'Capital':<10} {'Leverage':<10}")
    print("-" * 80)
    
    for sess in active_sessions:
        user_id = sess.get('telegram_id')
        trading_mode = sess.get('trading_mode') or 'swing'
        risk_mode = sess.get('risk_mode') or 'fixed'
        capital = sess.get('initial_deposit') or 0
        leverage = sess.get('leverage') or 10
        
        print(f"{user_id:<15} {trading_mode:<15} {risk_mode:<15} ${capital:<9.1f} {leverage}x")
    
    print(f"\n❌ INACTIVE SESSIONS ({len(inactive_sessions)}):")
    print("-" * 80)
    print(f"{'User ID':<15} {'Status':<15} {'Last Capital':<12} {'Created At':<20}")
    print("-" * 80)
    
    for sess in inactive_sessions:
        user_id = sess.get('telegram_id')
        status = sess.get('status') or 'unknown'
        capital = sess.get('initial_deposit') or 0
        created = sess.get('created_at', '')[:10] if sess.get('created_at') else 'N/A'
        
        print(f"{user_id:<15} {status:<15} ${capital:<11.1f} {created:<20}")
    
    print("\n" + "="*80)
    
    # Check if there are users with API keys but no active session
    all_api_keys = s.table("user_api_keys").select("telegram_id, exchange").execute()
    
    users_with_keys = set(k.get('telegram_id') for k in all_api_keys.data)
    users_with_active_session = set(sess.get('telegram_id') for sess in active_sessions)
    
    users_with_keys_but_inactive = users_with_keys - users_with_active_session
    
    if users_with_keys_but_inactive:
        print(f"\n⚠️  USERS WITH API KEYS BUT NO ACTIVE SESSION ({len(users_with_keys_but_inactive)}):")
        print("-" * 80)
        for user_id in users_with_keys_but_inactive:
            # Check if they have inactive session
            user_sessions = [s for s in all_sessions.data if s.get('telegram_id') == user_id]
            if user_sessions:
                status = user_sessions[0].get('status', 'unknown')
                print(f"   User {user_id}: Has API keys, session status = {status}")
            else:
                print(f"   User {user_id}: Has API keys, but NO session record")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80 + "\n")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
