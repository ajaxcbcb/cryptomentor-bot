
# -*- coding: utf-8 -*-
"""
Supabase Client Integration for CryptoMentor AI Bot
Uses SUPABASE_URL and SUPABASE_SERVICE_KEY from environment
"""

import os
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    print(f"⚠️ Supabase not available: {e}")

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

# Global client
supabase_client: Optional[Client] = None

def init_supabase_client() -> Optional[Client]:
    """Initialize Supabase client with environment variables"""
    global supabase_client
    
    if not SUPABASE_AVAILABLE:
        print("❌ Supabase library not installed")
        return None
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return None
    
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print("✅ Supabase client initialized successfully")
        return supabase_client
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        return None

# Initialize client on import
supabase = init_supabase_client()

def supabase_service() -> Optional[Client]:
    """Get Supabase service client - for backward compatibility"""
    return supabase

def validate_supabase_connection() -> bool:
    """Validate Supabase connection"""
    if not supabase:
        return False
    
    try:
        # Test connection with a simple query
        result = supabase.table('users').select('count', count='exact').limit(1).execute()
        return True
    except Exception as e:
        print(f"❌ Supabase connection validation failed: {e}")
        return False

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by telegram_id"""
    if not supabase:
        return None
    
    try:
        result = supabase.table('users').select('*').eq('telegram_id', user_id).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"❌ Error getting user {user_id}: {e}")
        return None

def add_user(user_id: int, username: str = None, first_name: str = None, 
             last_name: str = None, is_premium: bool = False, 
             credits: int = 100) -> Dict[str, Any]:
    """Add new user to Supabase"""
    if not supabase:
        return {"success": False, "error": "Supabase not configured"}
    
    try:
        user_data = {
            "telegram_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "is_premium": is_premium,
            "credits": credits,
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table('users').insert(user_data).execute()
        return {"success": True, "data": result.data[0] if result.data else user_data}
    except Exception as e:
        print(f"❌ Error adding user {user_id}: {e}")
        return {"success": False, "error": str(e)}

def update_user(user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update user in Supabase"""
    if not supabase:
        return {"success": False, "error": "Supabase not configured"}
    
    try:
        updates["updated_at"] = datetime.now().isoformat()
        result = supabase.table('users').update(updates).eq('telegram_id', user_id).execute()
        return {"success": True, "data": result.data[0] if result.data else updates}
    except Exception as e:
        print(f"❌ Error updating user {user_id}: {e}")
        return {"success": False, "error": str(e)}

def delete_user(user_id: int) -> Dict[str, Any]:
    """Delete user from Supabase"""
    if not supabase:
        return {"success": False, "error": "Supabase not configured"}
    
    try:
        result = supabase.table('users').delete().eq('telegram_id', user_id).execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        print(f"❌ Error deleting user {user_id}: {e}")
        return {"success": False, "error": str(e)}

def set_premium(user_id: int, duration_days: int = 30) -> Dict[str, Any]:
    """Set user premium status"""
    if not supabase:
        return {"success": False, "error": "Supabase not configured"}
    
    try:
        premium_until = (datetime.now() + timedelta(days=duration_days)).isoformat()
        updates = {
            "is_premium": True,
            "subscription_end": premium_until,
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table('users').update(updates).eq('telegram_id', user_id).execute()
        return {"success": True, "data": result.data[0] if result.data else updates}
    except Exception as e:
        print(f"❌ Error setting premium for user {user_id}: {e}")
        return {"success": False, "error": str(e)}

def revoke_premium(user_id: int) -> Dict[str, Any]:
    """Revoke user premium status"""
    if not supabase:
        return {"success": False, "error": "Supabase not configured"}
    
    try:
        updates = {
            "is_premium": False,
            "subscription_end": None,
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table('users').update(updates).eq('telegram_id', user_id).execute()
        return {"success": True, "data": result.data[0] if result.data else updates}
    except Exception as e:
        print(f"❌ Error revoking premium for user {user_id}: {e}")
        return {"success": False, "error": str(e)}

def add_premium(user_id: int, duration_days: int = 30) -> Dict[str, Any]:
    """Add premium to user - alias for set_premium"""
    return set_premium(user_id, duration_days)

def admin_set_premium(user_id: int, duration_days: int = 30) -> Dict[str, Any]:
    """Admin function to set premium"""
    return set_premium(user_id, duration_days)

def admin_revoke_premium(user_id: int) -> Dict[str, Any]:
    """Admin function to revoke premium"""
    return revoke_premium(user_id)

def admin_grant_credits(user_id: int, credits: int) -> Dict[str, Any]:
    """Admin function to grant credits"""
    if not supabase:
        return {"success": False, "error": "Supabase not configured"}
    
    try:
        # Get current credits
        user = get_user(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        current_credits = user.get('credits', 0)
        new_credits = current_credits + credits
        
        result = update_user(user_id, {"credits": new_credits})
        return result
    except Exception as e:
        print(f"❌ Error granting credits to user {user_id}: {e}")
        return {"success": False, "error": str(e)}

def parse_premium_duration(duration_str: str) -> Optional[int]:
    """Parse premium duration string to days"""
    try:
        if 'd' in duration_str.lower():
            return int(duration_str.lower().replace('d', '').strip())
        elif 'w' in duration_str.lower():
            return int(duration_str.lower().replace('w', '').strip()) * 7
        elif 'm' in duration_str.lower():
            return int(duration_str.lower().replace('m', '').strip()) * 30
        else:
            return int(duration_str)
    except:
        return None

def get_live_user_count() -> int:
    """Get total user count from Supabase"""
    if not supabase:
        return 0
    
    try:
        result = supabase.table('users').select('count', count='exact').execute()
        return result.count or 0
    except Exception as e:
        print(f"❌ Error getting user count: {e}")
        return 0

def verify_database_integrity() -> Dict[str, Any]:
    """Verify database integrity and connection"""
    if not supabase:
        return {
            "success": False,
            "error": "Supabase client not initialized",
            "tables_accessible": False,
            "total_users": 0
        }
    
    try:
        # Test basic connection and count users
        result = supabase.table('users').select('count', count='exact').limit(1).execute()
        total_users = result.count or 0
        
        # Test basic read operation
        test_result = supabase.table('users').select('telegram_id').limit(1).execute()
        tables_accessible = test_result is not None
        
        return {
            "success": True,
            "tables_accessible": tables_accessible,
            "total_users": total_users,
            "connection_healthy": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tables_accessible": False,
            "total_users": 0,
            "connection_healthy": False
        }

# Health check function
def health_check() -> Tuple[bool, str]:
    """Check Supabase health"""
    if not supabase:
        return False, "Supabase client not initialized"
    
    try:
        result = supabase.table('users').select('count', count='exact').limit(1).execute()
        return True, "Supabase connection healthy"
    except Exception as e:
        return False, f"Supabase connection failed: {e}"

# Legacy compatibility exports
__all__ = [
    'supabase', 'supabase_service', 'validate_supabase_connection',
    'get_user', 'add_user', 'update_user', 'delete_user',
    'set_premium', 'revoke_premium', 'add_premium',
    'admin_set_premium', 'admin_revoke_premium', 'admin_grant_credits',
    'parse_premium_duration', 'get_live_user_count', 'health_check',
    'verify_database_integrity'
]
