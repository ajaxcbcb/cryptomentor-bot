
import os
from supabase import create_client, Client

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

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

# CRUD Functions for User Management
def add_user(user_id, username=None, is_premium=False, expired_date=None, first_name=None, last_name=None):
    """Add a new user to Supabase users table"""
    try:
        user_data = {
            'telegram_id': user_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'is_premium': is_premium,
            'credits': 100,  # Default credits
            'language_code': 'id'  # Default Indonesian
        }
        
        if expired_date:
            user_data['subscription_end'] = expired_date
        
        # Use upsert to handle conflicts
        result = supabase.table('users').upsert(user_data, on_conflict='telegram_id').execute()
        
        if result.data:
            print(f"✅ User {user_id} added/updated successfully")
            return {"success": True, "data": result.data[0]}
        else:
            print(f"❌ Failed to add user {user_id}")
            return {"success": False, "error": "No data returned"}
            
    except Exception as e:
        print(f"❌ Error adding user {user_id}: {e}")
        return {"success": False, "error": str(e)}

def get_user(user_id):
    """Get user data from Supabase"""
    try:
        result = supabase.table('users').select('*').eq('telegram_id', user_id).execute()
        
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
    """Update user data in Supabase"""
    try:
        # Ensure we don't update telegram_id accidentally
        update_data = {k: v for k, v in data_dict.items() if k != 'telegram_id'}
        
        result = supabase.table('users').update(update_data).eq('telegram_id', user_id).execute()
        
        if result.data:
            print(f"✅ User {user_id} updated successfully")
            return {"success": True, "data": result.data[0]}
        else:
            print(f"❌ Failed to update user {user_id}")
            return {"success": False, "error": "No data updated"}
            
    except Exception as e:
        print(f"❌ Error updating user {user_id}: {e}")
        return {"success": False, "error": str(e)}

def delete_user(user_id):
    """Delete user from Supabase"""
    try:
        result = supabase.table('users').delete().eq('telegram_id', user_id).execute()
        
        if result.data:
            print(f"✅ User {user_id} deleted successfully")
            return {"success": True, "data": result.data[0]}
        else:
            print(f"❌ Failed to delete user {user_id}")
            return {"success": False, "error": "User not found or already deleted"}
            
    except Exception as e:
        print(f"❌ Error deleting user {user_id}: {e}")
        return {"success": False, "error": str(e)}

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
        return update_user(user_id, {"credits": credits})
    except Exception as e:
        print(f"❌ Error updating credits for user {user_id}: {e}")
        return {"success": False, "error": str(e)}

def grant_premium(user_id, expiry_date=None):
    """Grant premium access to user"""
    try:
        update_data = {"is_premium": True}
        if expiry_date:
            update_data["subscription_end"] = expiry_date
        
        return update_user(user_id, update_data)
    except Exception as e:
        print(f"❌ Error granting premium to user {user_id}: {e}")
        return {"success": False, "error": str(e)}

# Validate connection on import
if not validate_supabase_connection():
    print("⚠️ Supabase validation failed - bot will continue with limited functionality")
    print("🔧 To fix: Run 'python setup_supabase_tables.py' to create required tables")
else:
    print("✅ Supabase fully operational")
