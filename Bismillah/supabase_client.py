
import os
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

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
    print("   - SUPABASE_SERVICE_ROLE_KEY: Your Supabase service role key")
    # Don't raise exception, let bot continue with limited functionality
    supabase = None
    print("⚠️ Bot will continue with limited functionality (no Supabase)")
else:
    # Create Supabase client using service role key only
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    print("✅ Supabase client initialized successfully")
    print(f"🔗 URL: {SUPABASE_URL}")
    print(f"🔑 Service Role Client: ✅ Ready")

# Create alias for backward compatibility
supabase_service = supabase

# CRUD Functions for User Management
def add_user(user_id, username=None, is_premium=False, expired_date=None):
    """Add a new user to Supabase users table - simplified version"""
    if not supabase:
        print("⚠️ Supabase not available")
        return {"success": False, "error": "Supabase not configured"}

    try:
        # Ensure telegram_id is properly typed as int8
        telegram_id = int(user_id) if user_id else None
        if not telegram_id:
            error_msg = f"Invalid telegram_id: {user_id}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

        # Only include columns that exist in the schema (language_code removed)
        user_data = {
            'telegram_id': telegram_id,
            'username': username or 'no_username',
            'is_premium': bool(is_premium)
        }

        if expired_date:
            user_data['premium_until'] = expired_date

        print(f"📝 Inserting user payload: {user_data}")

        result = supabase.table('users').upsert(user_data, on_conflict='telegram_id').execute()

        print(f"📤 Supabase response: {result}")

        if result.data:
            print(f"✅ User {user_id} added/updated successfully")

            # Immediately verify user count
            count_result = supabase.table('users').select('count', count='exact').execute()
            total_users = count_result.count if hasattr(count_result, 'count') else 0
            print(f"📊 Total users after insert: {total_users}")

            return {"success": True, "data": result.data[0]}
        else:
            error_msg = f"No data returned from Supabase for user {user_id}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    except Exception as e:
        error_msg = f"Error adding user {user_id}: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

def get_user(user_id):
    """Get user data from Supabase"""
    if not supabase:
        return {"success": False, "error": "Supabase not configured"}

    try:
        result = supabase.table('users').select('*').eq('telegram_id', int(user_id)).execute()

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
    if not supabase:
        return {"success": False, "error": "Supabase not configured"}

    try:
        # Ensure we don't update telegram_id accidentally
        update_data = {k: v for k, v in data_dict.items() if k != 'telegram_id'}

        print(f"📝 Updating user {user_id} with payload: {update_data}")

        result = supabase.table('users').update(update_data).eq('telegram_id', int(user_id)).execute()

        print(f"📤 Supabase update response: {result}")

        if result.data:
            print(f"✅ User {user_id} updated successfully")
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
    """Delete user from Supabase"""
    if not supabase:
        return {"success": False, "error": "Supabase not configured"}

    try:
        print(f"🗑️ Deleting user {user_id}")

        result = supabase.table('users').delete().eq('telegram_id', int(user_id)).execute()

        print(f"📤 Supabase delete response: {result}")

        if result.data:
            print(f"✅ User {user_id} deleted successfully")
            return {"success": True, "data": result.data[0]}
        else:
            error_msg = f"User {user_id} not found or already deleted"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    except Exception as e:
        error_msg = f"Error deleting user {user_id}: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

def parse_premium_duration(duration_arg):
    """Parse premium duration argument and return expiry date"""
    try:
        current_time = datetime.now(timezone.utc)
        
        if duration_arg.lower() == 'lifetime':
            return "9999-12-31T23:59:59Z", "lifetime"
        
        # Parse format like "30d" or "2m"
        if duration_arg.endswith('d'):
            # Days format
            try:
                days = int(duration_arg[:-1])
                expiry_date = (current_time + timedelta(days=days)).isoformat()
                return expiry_date, f"{days} hari"
            except ValueError:
                return None, None
        
        elif duration_arg.endswith('m'):
            # Months format (approximate as 30 days per month)
            try:
                months = int(duration_arg[:-1])
                days = months * 30
                expiry_date = (current_time + timedelta(days=days)).isoformat()
                return expiry_date, f"{months} bulan"
            except ValueError:
                return None, None
        
        else:
            # Try to parse as plain number (assume days)
            try:
                days = int(duration_arg)
                expiry_date = (current_time + timedelta(days=days)).isoformat()
                return expiry_date, f"{days} hari"
            except ValueError:
                return None, None
    
    except Exception as e:
        print(f"Error parsing duration: {e}")
        return None, None

def set_premium(user_id, duration_type, duration_value=None):
    """
    Set premium status for user with flexible duration - direct insert/update without validation
    
    Args:
        user_id: Telegram user ID
        duration_type: "days", "months", or "lifetime" 
        duration_value: Number of days/months (required for days/months)
    
    Returns:
        dict: Result with success status and expiry date
    """
    if not supabase:
        return {"success": False, "error": "Supabase not configured"}

    try:
        telegram_id = int(user_id)
        current_time = datetime.now(timezone.utc)
        
        # Calculate premium expiry date
        if duration_type == "lifetime":
            # Set to far future date for lifetime premium
            premium_until = "9999-12-31T23:59:59Z"
            expiry_text = "lifetime"
        elif duration_type == "days":
            if not duration_value:
                return {"success": False, "error": "duration_value required for days"}
            premium_until = (current_time + timedelta(days=int(duration_value))).isoformat()
            expiry_text = f"{duration_value} hari"
        elif duration_type == "months":
            if not duration_value:
                return {"success": False, "error": "duration_value required for months"}
            # Calculate months (approximate as 30 days per month)
            days = int(duration_value) * 30
            premium_until = (current_time + timedelta(days=days)).isoformat()
            expiry_text = f"{duration_value} bulan"
        else:
            return {"success": False, "error": "Invalid duration_type. Use 'days', 'months', or 'lifetime'"}

        # Prepare user data for upsert (insert if not exists, update if exists)
        # Only include columns that exist in the schema (language_code removed)
        user_data = {
            "telegram_id": telegram_id,
            "is_premium": True,
            "premium_until": premium_until,
            "username": f"user_{telegram_id}"
        }

        print(f"📝 Setting premium for user {telegram_id}: {expiry_text}")
        print(f"📅 Premium expires at: {premium_until}")

        # Use upsert to insert or update without validation
        result = supabase.table('users').upsert(user_data, on_conflict='telegram_id').execute()

        if result.data:
            print(f"✅ Premium set successfully for user {telegram_id}")
            return {
                "success": True,
                "user_id": telegram_id,
                "duration_type": duration_type,
                "duration_value": duration_value,
                "expiry_date": premium_until,
                "expiry_text": expiry_text,
                "data": result.data[0]
            }
        else:
            error_msg = f"Failed to update premium for user {telegram_id}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    except Exception as e:
        error_msg = f"Error setting premium for user {user_id}: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

def add_premium(user_id, duration_days=None):
    """Add premium status to user (legacy function for compatibility)"""
    if not supabase:
        return {"success": False, "error": "Supabase not configured"}

    try:
        if duration_days == "lifetime":
            return set_premium(user_id, "lifetime")
        elif duration_days:
            try:
                days = int(duration_days)
                return set_premium(user_id, "days", days)
            except ValueError:
                return {"success": False, "error": "Invalid duration format"}
        else:
            # Default 30 days
            return set_premium(user_id, "days", 30)

    except Exception as e:
        return {"success": False, "error": str(e)}

def revoke_premium(user_id):
    """Revoke premium status from user - direct update without validation"""
    if not supabase:
        return {"success": False, "error": "Supabase not configured"}

    try:
        telegram_id = int(user_id)
        
        # Prepare user data for upsert (handles both existing and non-existing users)
        # Only include columns that exist in the schema (language_code removed)
        user_data = {
            "telegram_id": telegram_id,
            "is_premium": False,
            "premium_until": None,
            "username": f"user_{telegram_id}"
        }

        print(f"📝 Revoking premium for user {telegram_id}")

        # Use upsert to update or insert without validation
        result = supabase.table('users').upsert(user_data, on_conflict='telegram_id').execute()

        if result.data:
            print(f"✅ Premium revoked successfully for user {telegram_id}")
            return {
                "success": True,
                "user_id": telegram_id,
                "data": result.data[0]
            }
        else:
            error_msg = f"Failed to revoke premium for user {telegram_id}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    except Exception as e:
        error_msg = f"Error revoking premium for user {user_id}: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

def get_live_user_count():
    """Get live user count directly from Supabase"""
    if not supabase:
        return 0

    try:
        result = supabase.table('users').select('count', count='exact').execute()
        count = result.count if hasattr(result, 'count') else 0
        print(f"📊 Live user count from Supabase: {count}")
        return count
    except Exception as e:
        print(f"❌ Error getting live user count: {e}")
        return 0

# Validate connection on import
if supabase and not validate_supabase_connection():
    print("⚠️ Supabase validation failed - bot will continue with limited functionality")
    print("🔧 To fix: Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to Replit Secrets")
elif supabase:
    print("✅ Supabase fully operational")
    try:
        count = get_live_user_count()
        print(f"📊 Current user count: {count}")
    except:
        print("📊 Current user count: Unable to fetch")
