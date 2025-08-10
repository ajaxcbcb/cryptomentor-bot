
import os
from supabase import create_client, Client

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = <REDACTED_SUPABASE_KEY>

def validate_supabase_connection():
    """Validate Supabase connection and tables"""
    try:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY in environment variables")
            print("💡 Please add them to Replit Secrets")
            return False
        
        # Test connection
        test_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # Try to access users table
        result = test_client.table('users').select('count', count='exact').limit(1).execute()
        
        print("✅ Supabase connection validated successfully")
        print(f"📊 Users table accessible with {result.count or 0} records")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "PGRST205" in error_msg:
            print("❌ Table 'users' not found in Supabase database")
            print("💡 Run: python setup_supabase_tables.py to create tables")
        elif "PGRST301" in error_msg:
            print("❌ Authentication failed - check SUPABASE_ANON_KEY")
        elif "PGRST000" in error_msg:
            print("❌ Connection failed - check SUPABASE_URL")
        else:
            print(f"❌ Supabase validation failed: {error_msg}")
        
        return False

# Validate that required environment variables are present
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY in environment variables")
    print("💡 Please add them to Replit Secrets:")
    print("   - SUPABASE_URL: Your Supabase project URL")
    print("   - SUPABASE_ANON_KEY: Your Supabase anon/public key")
    raise Exception("Missing required Supabase environment variables")

# Create global supabase client instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

print("✅ Supabase client initialized successfully")
print(f"🔗 URL: {SUPABASE_URL}")

# Validate connection on import
if not validate_supabase_connection():
    print("⚠️ Supabase validation failed - bot will continue with limited functionality")
    print("🔧 To fix: Run 'python setup_supabase_tables.py' to create required tables")
else:
    print("✅ Supabase fully operational")
