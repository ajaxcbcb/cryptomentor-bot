#!/usr/bin/env python3
"""
Deep investigation: Check ALL users in database and their engine status
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv('Bismillah/.env')
sys.path.insert(0, 'Bismillah')

from app.supabase_repo import _client
from app.autotrade_engine import is_running

async def check_all_users():
    """Check ALL users in database and their actual status"""
    
    print("=" * 80)
    print("DEEP INVESTIGATION: ALL USERS IN DATABASE")
    print("=" * 80)
    
    try:
        # 1. Check autotrade_sessions table
        print("\n[1] Checking autotrade_sessions table...")
        sessions_result = _client().table("autotrade_sessions").select("*").execute()
        all_sessions = sessions_result.data or []
        
        print(f"Total sessions in DB: {len(all_sessions)}")
        
        # Group by status
        by_status = {}
        for s in all_sessions:
            status = s.get("status", "unknown")
            by_status.setdefault(status, []).append(s)
        
        print("\nSessions by status:")
        for status, sessions in by_status.items():
            print(f"  {status}: {len(sessions)} sessions")
        
        # 2. Check which engines are actually running
        print("\n[2] Checking actual engine status...")
        
        active_sessions = []
        for status in ["active", "uid_verified"]:
            if status in by_status:
                active_sessions.extend(by_status[status])
        
        print(f"\nActive/uid_verified sessions: {len(active_sessions)}")
        
        running_count = 0
        not_running_count = 0
        
        for session in active_sessions:
            user_id = session.get("telegram_id")
            if not user_id:
                continue
            
            is_engine_running = is_running(user_id)
            status_emoji = "✅" if is_engine_running else "❌"
            
            print(f"{status_emoji} User {user_id}: Engine {'RUNNING' if is_engine_running else 'NOT RUNNING'} (status: {session.get('status')})")
            
            if is_engine_running:
                running_count += 1
            else:
                not_running_count += 1
        
        # 3. Check users table for total registered users
        print("\n[3] Checking users table...")
        users_result = _client().table("users").select("telegram_id").execute()
        all_users = users_result.data or []
        
        print(f"Total registered users: {len(all_users)}")
        
        # 4. Check if there are users with sessions but not in active status
        print("\n[4] Checking other session statuses...")
        
        other_statuses = [s for s in ["inactive", "stopped", "paused", "error"] if s in by_status]
        if other_statuses:
            for status in other_statuses:
                sessions = by_status[status]
                print(f"\n{status.upper()} sessions: {len(sessions)}")
                for s in sessions[:5]:  # Show first 5
                    user_id = s.get("telegram_id")
                    print(f"  - User {user_id}")
        
        # 5. Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total registered users: {len(all_users)}")
        print(f"Total sessions: {len(all_sessions)}")
        print(f"Active/uid_verified sessions: {len(active_sessions)}")
        print(f"  ✅ Engines actually running: {running_count}")
        print(f"  ❌ Engines NOT running: {not_running_count}")
        print("=" * 80)
        
        # 6. Check if there are users who should receive notifications but didn't
        print("\n[6] Checking notification targets...")
        
        # Users who should receive notifications:
        # - Have active/uid_verified session
        # - Regardless of engine status (they should know if engine is active or not)
        
        notification_targets = len(active_sessions)
        print(f"\nUsers who SHOULD receive maintenance notifications: {notification_targets}")
        
        if notification_targets != 13:
            print(f"\n⚠️ WARNING: Expected 13 users but found {notification_targets} users!")
            print("This might explain why some users didn't receive notifications.")
        else:
            print(f"\n✅ Notification target count matches (13 users)")
        
        # 7. Check for users with multiple sessions
        print("\n[7] Checking for duplicate sessions...")
        user_session_count = {}
        for s in all_sessions:
            uid = s.get("telegram_id")
            if uid:
                user_session_count[uid] = user_session_count.get(uid, 0) + 1
        
        duplicates = {uid: count for uid, count in user_session_count.items() if count > 1}
        if duplicates:
            print(f"Found {len(duplicates)} users with multiple sessions:")
            for uid, count in duplicates.items():
                print(f"  User {uid}: {count} sessions")
        else:
            print("No duplicate sessions found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_all_users())
