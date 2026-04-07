#!/usr/bin/env python3
"""
Run database migration directly from local machine to Neon database
"""
import psycopg2
import sys

# Database connection from .env
DB_CONFIG = {
    "host": "ep-divine-wind-aes4g3k8.c-2.us-east-2.aws.neon.tech",
    "port": 5432,
    "user": "neondb_owner",
    "password": "npg_PXo7pTdgJ4ny",
    "database": "neondb",
    "sslmode": "require"
}

print("🚀 Running Scalping Mode Migration...")
print("=" * 50)

# Read migration SQL
print("\n📄 Reading migration file...")
try:
    with open("db/add_trading_mode.sql", "r") as f:
        migration_sql = f.read()
    print("✅ Migration file loaded")
except Exception as e:
    print(f"❌ Error reading migration file: {e}")
    sys.exit(1)

# Connect to database
print("\n🔌 Connecting to database...")
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("✅ Connected to Neon database")
except Exception as e:
    print(f"❌ Connection error: {e}")
    sys.exit(1)

# Run migration
print("\n📊 Running migration...")
try:
    cursor.execute(migration_sql)
    conn.commit()
    print("✅ Migration executed successfully!")
except Exception as e:
    print(f"❌ Migration error: {e}")
    conn.rollback()
    cursor.close()
    conn.close()
    sys.exit(1)

# Verify migration
print("\n🔍 Verifying migration...")
try:
    cursor.execute("""
        SELECT column_name, data_type, column_default 
        FROM information_schema.columns 
        WHERE table_name='autotrade_sessions' AND column_name='trading_mode';
    """)
    result = cursor.fetchone()
    
    if result:
        print("✅ Column 'trading_mode' exists!")
        print(f"   Column: {result[0]}")
        print(f"   Type: {result[1]}")
        print(f"   Default: {result[2]}")
    else:
        print("⚠️ Column not found - migration may have failed")
        
except Exception as e:
    print(f"⚠️ Verification error: {e}")

# Check existing data
print("\n📋 Checking existing sessions...")
try:
    cursor.execute("SELECT COUNT(*) FROM autotrade_sessions;")
    count = cursor.fetchone()[0]
    print(f"✅ Found {count} existing autotrade sessions")
    
    if count > 0:
        cursor.execute("SELECT telegram_id, trading_mode FROM autotrade_sessions LIMIT 5;")
        sessions = cursor.fetchall()
        print("\nSample sessions:")
        for session in sessions:
            print(f"   User {session[0]}: mode = {session[1]}")
            
except Exception as e:
    print(f"⚠️ Data check error: {e}")

# Close connection
cursor.close()
conn.close()

print("\n" + "=" * 50)
print("✅ Database Migration Complete!")
print("\n📊 Next Steps:")
print("1. Restart service on VPS:")
print("   ssh root@147.93.156.165")
print("   systemctl restart cryptomentor.service")
print("   journalctl -u cryptomentor.service -f")
print("\n2. Test in Telegram:")
print("   /autotrade → Click '⚙️ Trading Mode'")
