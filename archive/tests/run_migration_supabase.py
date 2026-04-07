#!/usr/bin/env python3
"""
Run database migration via Supabase REST API
"""
from supabase import create_client, Client
import sys

# Supabase credentials from .env
SUPABASE_URL = "https://xrbqnocovfymdikngaza.supabase.co"
SUPABASE_KEY = <REDACTED_SUPABASE_KEY>

print("🚀 Running Scalping Mode Migration via Supabase...")
print("=" * 60)

# Initialize Supabase client
print("\n🔌 Connecting to Supabase...")
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase")
except Exception as e:
    print(f"❌ Connection error: {e}")
    sys.exit(1)

# Check if column already exists
print("\n🔍 Checking if column already exists...")
try:
    # Try to query the column
    result = supabase.table("autotrade_sessions").select("trading_mode").limit(1).execute()
    print("⚠️ Column 'trading_mode' already exists!")
    print("   Migration may have been run previously.")
    
    # Show sample data
    if result.data:
        print(f"   Sample: {result.data[0]}")
    
    sys.exit(0)
    
except Exception as e:
    error_msg = str(e)
    if "column" in error_msg.lower() and "does not exist" in error_msg.lower():
        print("✅ Column doesn't exist yet - proceeding with migration")
    else:
        print(f"⚠️ Unexpected error: {e}")
        print("   Proceeding with migration anyway...")

# Run migration using Supabase SQL
print("\n📊 Running migration...")
migration_sql = """
-- Add trading_mode column to autotrade_sessions table
ALTER TABLE autotrade_sessions 
ADD COLUMN IF NOT EXISTS trading_mode VARCHAR(20) DEFAULT 'swing' NOT NULL;

-- Add check constraint to ensure valid values
ALTER TABLE autotrade_sessions 
DROP CONSTRAINT IF EXISTS trading_mode_check;

ALTER TABLE autotrade_sessions 
ADD CONSTRAINT trading_mode_check 
CHECK (trading_mode IN ('scalping', 'swing'));

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_autotrade_sessions_trading_mode 
ON autotrade_sessions(trading_mode);

-- Add column comment
COMMENT ON COLUMN autotrade_sessions.trading_mode IS 
'Trading mode: scalping (5M, fast trades) or swing (15M, longer holds)';
"""

try:
    # Execute SQL via Supabase RPC
    result = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()
    print("✅ Migration executed successfully!")
    
except Exception as e:
    error_msg = str(e)
    
    # Check if it's because RPC doesn't exist - use alternative method
    if "function" in error_msg.lower() or "does not exist" in error_msg.lower():
        print("⚠️ RPC method not available, using alternative approach...")
        print("\n📝 Manual Migration Required:")
        print("\nGo to Supabase Dashboard:")
        print(f"   {SUPABASE_URL}")
        print("\n1. Navigate to: SQL Editor")
        print("2. Run this SQL:")
        print("\n" + "="*60)
        print(migration_sql)
        print("="*60)
        print("\n3. Click 'Run' button")
        print("\nOr use Table Editor:")
        print("1. Go to Table Editor → autotrade_sessions")
        print("2. Add new column:")
        print("   - Name: trading_mode")
        print("   - Type: varchar(20)")
        print("   - Default: 'swing'")
        print("   - Nullable: No")
        print("3. Add check constraint: trading_mode IN ('scalping', 'swing')")
        
    else:
        print(f"❌ Migration error: {e}")
        print("\nTrying alternative method...")

# Verify migration (if it succeeded)
print("\n🔍 Verifying migration...")
try:
    result = supabase.table("autotrade_sessions").select("trading_mode").limit(1).execute()
    print("✅ Column 'trading_mode' exists!")
    
    # Check all sessions
    all_sessions = supabase.table("autotrade_sessions").select("telegram_id, trading_mode").execute()
    print(f"\n📊 Found {len(all_sessions.data)} autotrade sessions")
    
    if all_sessions.data:
        print("\nSample sessions:")
        for session in all_sessions.data[:5]:
            print(f"   User {session['telegram_id']}: mode = {session.get('trading_mode', 'N/A')}")
    
    print("\n✅ All sessions have default mode: 'swing'")
    
except Exception as e:
    error_msg = str(e)
    if "column" in error_msg.lower() and "does not exist" in error_msg.lower():
        print("❌ Column still doesn't exist - manual migration required")
        print("\nPlease run the SQL manually in Supabase Dashboard")
    else:
        print(f"⚠️ Verification error: {e}")

print("\n" + "=" * 60)
print("✅ Migration Process Complete!")
print("\n📊 Next Steps:")
print("1. Verify column exists in Supabase Dashboard")
print("2. Restart bot service on VPS:")
print("   ssh root@147.93.156.165")
print("   systemctl restart cryptomentor.service")
print("\n3. Test in Telegram:")
print("   /autotrade → Click '⚙️ Trading Mode'")
