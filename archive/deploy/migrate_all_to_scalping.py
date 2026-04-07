#!/usr/bin/env python3
"""
Migrate all risk-based users to Scalping mode
For better compounding with max 4 concurrent positions
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Determine script location and load .env
script_dir = Path(__file__).parent.resolve()

# Try multiple .env locations
env_locations = [
    script_dir / '.env',                      # Root directory
    script_dir / 'Bismillah' / '.env',        # Bismillah subdirectory
    Path('/root/cryptomentor-bot/.env'),      # VPS root
]

env_loaded = False
for env_path in env_locations:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print(f"⚠️  .env not found in any location, using environment variables")

# Set up path - add both root and Bismillah to path
sys.path.insert(0, str(script_dir))
if (script_dir / 'Bismillah').exists():
    sys.path.insert(0, str(script_dir / 'Bismillah'))
# Also try VPS paths
sys.path.insert(0, '/root/cryptomentor-bot')
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

# Verify environment variables
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = <REDACTED_SUPABASE_KEY>

if not supabase_url or not supabase_key:
    print("\n❌ ERROR: Missing Supabase credentials!")
    print(f"   SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    print(f"   SUPABASE_SERVICE_KEY: {'✅ Set' if supabase_key else '❌ Missing'}")
    print("\nPlease ensure .env file exists with proper credentials.")
    sys.exit(1)

from app.supabase_repo import _client


def migrate_all_to_scalping():
    """Migrate all risk-based users to Scalping mode."""
    print("=" * 60)
    print("MIGRATION: Switch all risk-based users to Scalping mode")
    print("=" * 60)
    
    try:
        s = _client()
        
        # Get all active sessions
        result = s.table("autotrade_sessions").select("telegram_id, risk_mode, trading_mode").eq("status", "active").execute()
        
        if not result.data:
            print("No active sessions found")
            return
        
        sessions = result.data
        print(f"\nFound {len(sessions)} active session(s)")
        
        migrated = 0
        skipped = 0
        
        for session in sessions:
            user_id = session.get("telegram_id")
            current_risk_mode = session.get("risk_mode")
            current_trading_mode = session.get("trading_mode")
            
            # Only migrate risk-based users
            if current_risk_mode != "risk_based":
                print(f"  User {user_id}: SKIP (mode={current_risk_mode or 'manual'})")
                skipped += 1
                continue
            
            # Check if already scalping
            if current_trading_mode == "scalping":
                print(f"  User {user_id}: SKIP (already scalping)")
                skipped += 1
                continue
            
            # Migrate to scalping - update database directly
            try:
                s.table("autotrade_sessions").update({
                    "trading_mode": "scalping"
                }).eq("telegram_id", user_id).execute()
                
                print(f"  User {user_id}: ✅ MIGRATED ({current_trading_mode or 'swing'} → scalping)")
                migrated += 1
            except Exception as e:
                print(f"  User {user_id}: ❌ FAILED ({e})")
        
        print("\n" + "=" * 60)
        print(f"MIGRATION COMPLETE")
        print(f"  ✅ Migrated: {migrated}")
        print(f"  ⏭️  Skipped: {skipped}")
        print(f"  📊 Total: {len(sessions)}")
        print("=" * 60)
        
        if migrated > 0:
            print("\n⚠️  IMPORTANT: Restart bot to apply changes!")
            print("   Run: systemctl restart cryptomentor")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    migrate_all_to_scalping()
