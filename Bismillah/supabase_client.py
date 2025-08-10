
import os
from supabase import create_client, Client

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = <REDACTED_SUPABASE_KEY>
SUPABASE_SERVICE_ROLE_KEY = <REDACTED_SUPABASE_KEY>

def validate_supabase_connection():
    """Validate Supabase connection and tables"""
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment variables")
            print("💡 Please add them to Replit Secrets")
            return False
        
        # Test connection with service role key
        test_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
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
            print("❌ Authentication failed - check SUPABASE_SERVICE_ROLE_KEY")
        elif "PGRST000" in error_msg:
            print("❌ Connection failed - check SUPABASE_URL")
        else:
            print(f"❌ Supabase validation failed: {error_msg}")
        
        return False

# Validate that required environment variables are present
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment variables")
    print("💡 Please add them to Replit Secrets:")
    print("   - SUPABASE_URL: Your Supabase project URL")
    print("   - SUPABASE_SERVICE_ROLE_KEY: Your Supabase service role key (for write operations)")
    raise Exception("Missing required Supabase environment variables")

# Create global supabase client instances
# Service role client for write operations (bypasses RLS)
supabase_service: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Anon client for read operations (respects RLS if enabled)
supabase_anon: Client = None
if SUPABASE_ANON_KEY:
    supabase_anon = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Primary client for backward compatibility (uses service role)
supabase: Client = supabase_service

print("✅ Supabase clients initialized successfully")
print(f"🔗 URL: {SUPABASE_URL}")
print(f"🔑 Service Role Client: {'✅ Ready' if supabase_service else '❌ Failed'}")
print(f"🔑 Anon Client: {'✅ Ready' if supabase_anon else '⚠️ Not configured'}")

# CRUD Functions for User Management
def add_user(user_id, username=None, is_premium=False, expired_date=None, first_name=None, last_name=None):
    """Add a new user to Supabase users table using service role client"""
    try:
        # Ensure telegram_id is properly typed as int8
        telegram_id = int(user_id) if user_id else None
        if not telegram_id:
            error_msg = f"Invalid telegram_id: {user_id}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
            
        user_data = {
            'telegram_id': telegram_id,
            'username': username or 'no_username',
            'first_name': first_name or 'Unknown',
            'last_name': last_name,
            'is_premium': bool(is_premium),
            'credits': 100,  # Default credits
            'language_code': 'id'  # Default Indonesian
        }
        
        if expired_date:
            user_data['subscription_end'] = expired_date
        
        print(f"📝 Inserting user payload: {user_data}")
        
        # Use service role client for write operations (bypasses RLS)
        result = supabase_service.table('users').upsert(user_data, on_conflict='telegram_id').execute()
        
        print(f"📤 Supabase response: {result}")
        
        if result.data:
            print(f"✅ User {user_id} added/updated successfully")
            
            # Immediately verify user count
            count_result = supabase_service.table('users').select('count', count='exact').execute()
            total_users = count_result.count if hasattr(count_result, 'count') else 0
            print(f"📊 Total users after insert: {total_users}")
            
            return {"success": True, "data": result.data[0]}
        else:
            error_msg = f"No data returned from Supabase for user {user_id}"
            print(f"❌ {error_msg}")
            print(f"🔍 Full response: {result}")
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        error_msg = f"Error adding user {user_id}: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"🚨 CRITICAL: Database insert failed - stopping execution")
        raise Exception(f"Supabase insert failed: {error_msg}")

def get_user(user_id):
    """Get user data from Supabase using read client"""
    try:
        # Use anon client for reads if available, otherwise service client
        read_client = supabase_anon if supabase_anon else supabase_service
        result = read_client.table('users').select('*').eq('telegram_id', int(user_id)).execute()
        
        if result.data:
            print(f"✅ User {user_id} found")
            return {"success": True, "data": result.data[0]}
        else:
            print(f"⚠️ User {user_id} not found")
            return {"success": False, "error": "User not found"}
            
    except Exception as e:
        print(f"❌ Error getting user {user_id}: {e}")
        return {"success": False, "error": str(e)}

def update_user(user_id, data_dict):
    """Update user data in Supabase using service role client"""
    try:
        # Ensure we don't update telegram_id accidentally
        update_data = {k: v for k, v in data_dict.items() if k != 'telegram_id'}
        
        print(f"📝 Updating user {user_id} with payload: {update_data}")
        
        # Use service role client for write operations
        result = supabase_service.table('users').update(update_data).eq('telegram_id', int(user_id)).execute()
        
        print(f"📤 Supabase update response: {result}")
        
        if result.data:
            print(f"✅ User {user_id} updated successfully")
            
            # Immediately verify user count after update
            count_result = supabase_service.table('users').select('count', count='exact').execute()
            total_users = count_result.count if hasattr(count_result, 'count') else 0
            print(f"📊 Total users after update: {total_users}")
            
            return {"success": True, "data": result.data[0]}
        else:
            error_msg = f"No data updated for user {user_id}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        error_msg = f"Error updating user {user_id}: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

def delete_user(user_id):
    """Delete user from Supabase using service role client"""
    try:
        print(f"🗑️ Deleting user {user_id}")
        
        # Use service role client for write operations
        result = supabase_service.table('users').delete().eq('telegram_id', int(user_id)).execute()
        
        print(f"📤 Supabase delete response: {result}")
        
        if result.data:
            print(f"✅ User {user_id} deleted successfully")
            
            # Immediately verify user count after delete
            count_result = supabase_service.table('users').select('count', count='exact').execute()
            total_users = count_result.count if hasattr(count_result, 'count') else 0
            print(f"📊 Total users after delete: {total_users}")
            
            return {"success": True, "data": result.data[0]}
        else:
            error_msg = f"User {user_id} not found or already deleted"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        error_msg = f"Error deleting user {user_id}: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

def get_user_credits(user_id):
    """Get user's current credits"""
    try:
        result = get_user(user_id)
        if result["success"]:
            return result["data"].get("credits", 0)
        return 0
    except Exception as e:
        print(f"❌ Error getting credits for user {user_id}: {e}")
        return 0

def update_user_credits(user_id, credits):
    """Update user's credits"""
    try:
        print(f"💳 Updating credits for user {user_id} to {credits}")
        return update_user(user_id, {"credits": int(credits)})
    except Exception as e:
        error_msg = f"Error updating credits for user {user_id}: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

def grant_premium(user_id, expiry_date=None):
    """Grant premium access to user"""
    try:
        update_data = {"is_premium": True}
        if expiry_date:
            update_data["subscription_end"] = expiry_date
        
        print(f"⭐ Granting premium to user {user_id}")
        result = update_user(user_id, update_data)
        
        if result["success"]:
            print(f"✅ Premium granted successfully to user {user_id}")
        
        return result
    except Exception as e:
        error_msg = f"Error granting premium to user {user_id}: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

def get_live_user_count():
    """Get live user count directly from Supabase (no caching)"""
    try:
        result = supabase_service.table('users').select('count', count='exact').execute()
        count = result.count if hasattr(result, 'count') else 0
        print(f"📊 Live user count from Supabase: {count}")
        return count
    except Exception as e:
        print(f"❌ Error getting live user count: {e}")
        return 0

def verify_database_integrity():
    """Verify database integrity after operations"""
    try:
        print("🔍 Verifying database integrity...")
        
        # Get user count
        user_count = get_live_user_count()
        
        # Get premium user count
        premium_result = supabase_service.table('users').select('count', count='exact').eq('is_premium', True).execute()
        premium_count = premium_result.count if hasattr(premium_result, 'count') else 0
        
        print(f"📊 Database Status:")
        print(f"   Total Users: {user_count}")
        print(f"   Premium Users: {premium_count}")
        print(f"   Free Users: {user_count - premium_count}")
        
        return {
            "total_users": user_count,
            "premium_users": premium_count,
            "free_users": user_count - premium_count
        }
        
    except Exception as e:
        print(f"❌ Error verifying database integrity: {e}")
        return None

# Validate connection on import
if not validate_supabase_connection():
    print("⚠️ Supabase validation failed - bot will continue with limited functionality")
    print("🔧 To fix: Run 'python setup_supabase_tables.py' to create required tables")
else:
    print("✅ Supabase fully operational")
    # Show initial database status
    verify_database_integrity()
