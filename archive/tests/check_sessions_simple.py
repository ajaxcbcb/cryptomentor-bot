#!/usr/bin/env python3
"""Simple check using bot's existing connection"""

import asyncio
import sys

async def check_sessions():
    # Import after adding to path
    sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')
    
    # Import the running bot's modules
    from app.autotrade_engine import _running_tasks
    from app.supabase_repo import _client
    
    try:
        s = _client()
        
        # Get all sessions
        all_result = s.table("autotrade_sessions").select("telegram_id, status").execute()
        
        active = [r for r in all_result.data if r.get('status') == 'active']
        inactive = [r for r in all_result.data if r.get('status') != 'active']
        
        print(f"\n{'='*60}")
        print(f"AUTOTRADE SESSIONS SUMMARY")
        print(f"{'='*60}")
        print(f"Total registered users: {len(all_result.data)}")
        print(f"Active sessions (DB): {len(active)}")
        print(f"Inactive sessions (DB): {len(inactive)}")
        print(f"Running engines (memory): {len(_running_tasks)}")
        print(f"{'='*60}\n")
        
        if len(active) > 0:
            print("Active session user IDs:")
            for sess in active:
                print(f"  - {sess.get('telegram_id')}")
        
        if len(inactive) > 0:
            print(f"\nInactive session user IDs ({len(inactive)}):")
            for sess in inactive[:10]:  # Show first 10
                print(f"  - {sess.get('telegram_id')} (status: {sess.get('status')})")
            if len(inactive) > 10:
                print(f"  ... and {len(inactive) - 10} more")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_sessions())
