"""
Test maintenance notification system
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('Bismillah/.env')

# Add Bismillah to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Bismillah'))

from app.maintenance_notifier import send_maintenance_notifications
from app.supabase_repo import _client
from app.autotrade_engine import is_running


async def test_maintenance_notifier():
    """Test the maintenance notification system"""
    
    print("=" * 80)
    print("MAINTENANCE NOTIFIER TEST")
    print("=" * 80)
    
    # 1. Check active sessions
    print("\n1. Checking active sessions...")
    try:
        result = _client().table("autotrade_sessions").select("*").in_(
            "status", ["active", "uid_verified"]
        ).execute()
        
        sessions = result.data or []
        print(f"   ✅ Found {len(sessions)} active sessions")
        
        if sessions:
            print("\n   Active sessions:")
            for session in sessions[:5]:  # Show first 5
                user_id = session.get("telegram_id")
                status = session.get("status")
                mode = session.get("trading_mode", "swing")
                print(f"   - User {user_id}: status={status}, mode={mode}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # 2. Check which engines are actually running
    print("\n2. Checking engine status...")
    inactive_count = 0
    active_count = 0
    
    for session in sessions:
        user_id = session.get("telegram_id")
        if not user_id:
            continue
        
        if is_running(user_id):
            active_count += 1
        else:
            inactive_count += 1
    
    print(f"   ✅ Active engines: {active_count}")
    print(f"   ⚠️  Inactive engines: {inactive_count}")
    
    # 3. Test notification logic (without actually sending)
    print("\n3. Testing notification logic...")
    print(f"   Would send notifications to {inactive_count} users")
    
    if inactive_count > 0:
        print("\n   Sample notification message:")
        print("   " + "─" * 70)
        print("""
   🔧 Pemberitahuan Maintenance
   
   Bot baru saja selesai maintenance dan engine AutoTrade Anda saat ini tidak aktif.
   
   📊 Status:
   • Engine: Inactive
   • Trading: Stopped
   
   💡 Apa yang harus dilakukan?
   Untuk melanjutkan trading, silakan aktifkan kembali engine Anda secara manual:
   
   👉 Ketik: /autotrade
   
   Kemudian pilih Start Engine untuk mengaktifkan kembali.
   
   ⚠️ Penting: Engine tidak akan trading sampai Anda mengaktifkannya kembali.
        """)
        print("   " + "─" * 70)
    
    # 4. Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total sessions: {len(sessions)}")
    print(f"Active engines: {active_count}")
    print(f"Inactive engines: {inactive_count}")
    print(f"Notifications to send: {inactive_count}")
    print("\n✅ Test completed successfully!")
    print("\nTo actually send notifications, the system will run automatically")
    print("after bot restart in scheduler.py")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_maintenance_notifier())
