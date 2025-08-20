
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Get authenticated Supabase client"""
    try:
        from app.supabase_conn import get_supabase_client as get_client
        return get_client()
    except:
        # Fallback direct connection
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise Exception("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return create_client(url, key)

def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get user by telegram ID from Supabase"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error getting user {telegram_id}: {e}")
        return None

def get_user_by_tid(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Alias for get_user_by_telegram_id"""
    return get_user_by_telegram_id(telegram_id)

def create_user_if_not_exists(telegram_id: int, username: str = None, first_name: str = None) -> bool:
    """Create user in Supabase if not exists"""
    try:
        supabase = get_supabase_client()
        
        # Check if user exists
        existing = get_user_by_telegram_id(telegram_id)
        if existing:
            print(f"User {telegram_id} already exists")
            return True
            
        # Create new user
        user_data = {
            "telegram_id": telegram_id,
            "username": username or "no_username",
            "first_name": first_name or "Unknown",
            "is_premium": False,
            "is_lifetime": False,
            "credits": 100,  # Default credits for new users
            "premium_until": None
        }
        
        result = supabase.table("users").insert(user_data).execute()
        print(f"Created user {telegram_id} in Supabase")
        return bool(result.data)
        
    except Exception as e:
        print(f"Error creating user {telegram_id}: {e}")
        return False

def set_premium(telegram_id: int, lifetime: bool = False, days: int = None) -> bool:
    """Set premium status for user in Supabase (auto-creates user if not exists)"""
    try:
        supabase = get_supabase_client()
        
        # Check if user exists, if not create them first
        existing_user = get_user_by_telegram_id(telegram_id)
        if not existing_user:
            print(f"User {telegram_id} not found. Creating new user...")
            # Create user with minimal data since admin is adding premium
            user_data = {
                "telegram_id": telegram_id,
                "username": f"user_{telegram_id}",  # Placeholder username
                "first_name": "Premium User",  # Placeholder name
                "is_premium": False,  # Will be updated below
                "is_lifetime": False,
                "credits": 100,  # Default credits
                "premium_until": None
            }
            
            # Insert new user
            create_result = supabase.table("users").insert(user_data).execute()
            if not create_result.data:
                print(f"Failed to create user {telegram_id}")
                return False
            print(f"Successfully created user {telegram_id}")
        
        # Prepare premium update data
        update_data = {
            "is_premium": True,
            "is_lifetime": lifetime,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if lifetime:
            update_data["premium_until"] = None
        elif days:
            premium_until = datetime.utcnow() + timedelta(days=days)
            update_data["premium_until"] = premium_until.isoformat()
        else:
            # Default 30 days if no days specified
            premium_until = datetime.utcnow() + timedelta(days=30)
            update_data["premium_until"] = premium_until.isoformat()
        
        # Update user with premium status
        result = supabase.table("users").update(update_data).eq("telegram_id", telegram_id).execute()
        
        if result.data:
            premium_type = "LIFETIME" if lifetime else f"{days or 30} days"
            print(f"Set premium {premium_type} for user {telegram_id}")
            return True
        else:
            print(f"Failed to update premium for user {telegram_id}")
            return False
            
    except Exception as e:
        print(f"Error setting premium for user {telegram_id}: {e}")
        return False

def revoke_premium(telegram_id: int) -> bool:
    """Revoke premium status from user in Supabase"""
    try:
        supabase = get_supabase_client()
        
        # Reset premium status
        update_data = {
            "is_premium": False,
            "is_lifetime": False,
            "premium_until": None,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("users").update(update_data).eq("telegram_id", telegram_id).execute()
        
        if result.data:
            print(f"Revoked premium for user {telegram_id}")
            return True
        else:
            print(f"Failed to revoke premium for user {telegram_id}")
            return False
            
    except Exception as e:
        print(f"Error revoking premium for user {telegram_id}: {e}")
        return False

def touch_user_from_update(update):
    """Create/update user from Telegram update"""
    if not update or not update.effective_user:
        return
        
    user = update.effective_user
    create_user_if_not_exists(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

def get_credits(telegram_id: int) -> int:
    """Get user credits from Supabase"""
    try:
        user = get_user_by_telegram_id(telegram_id)
        return user.get("credits", 0) if user else 0
    except Exception as e:
        print(f"Error getting credits for user {telegram_id}: {e}")
        return 0

def is_premium_active(telegram_id: int) -> bool:
    """Check if user has active premium"""
    try:
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            return False
            
        if not user.get("is_premium", False):
            return False
            
        if user.get("is_lifetime", False):
            return True
            
        premium_until = user.get("premium_until")
        if not premium_until:
            return False
            
        # Parse premium_until and check if still valid
        if isinstance(premium_until, str):
            premium_dt = datetime.fromisoformat(premium_until.replace('Z', '+00:00'))
        else:
            premium_dt = premium_until
            
        return premium_dt > datetime.utcnow()
        
    except Exception as e:
        print(f"Error checking premium for user {telegram_id}: {e}")
        return False

def debit_credits(telegram_id: int, amount: int) -> bool:
    """Deduct credits from user account"""
    try:
        supabase = get_supabase_client()
        
        # Get current credits
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            print(f"User {telegram_id} not found for credit debit")
            return False
            
        current_credits = user.get("credits", 0)
        if current_credits < amount:
            print(f"Insufficient credits for user {telegram_id}: {current_credits} < {amount}")
            return False
            
        # Deduct credits
        new_credits = current_credits - amount
        update_data = {
            "credits": new_credits,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("users").update(update_data).eq("telegram_id", telegram_id).execute()
        
        if result.data:
            print(f"Debited {amount} credits from user {telegram_id}: {current_credits} → {new_credits}")
            return True
        else:
            print(f"Failed to debit credits for user {telegram_id}")
            return False
            
    except Exception as e:
        print(f"Error debiting credits for user {telegram_id}: {e}")
        return False

def add_credits(telegram_id: int, amount: int) -> bool:
    """Add credits to user account"""
    try:
        supabase = get_supabase_client()
        
        # Get current credits
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            print(f"User {telegram_id} not found for credit addition")
            return False
            
        current_credits = user.get("credits", 0)
        new_credits = current_credits + amount
        
        update_data = {
            "credits": new_credits,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("users").update(update_data).eq("telegram_id", telegram_id).execute()
        
        if result.data:
            print(f"Added {amount} credits to user {telegram_id}: {current_credits} → {new_credits}")
            return True
        else:
            print(f"Failed to add credits for user {telegram_id}")
            return False
            
    except Exception as e:
        print(f"Error adding credits for user {telegram_id}: {e}")
        return False

def set_credits(telegram_id: int, amount: int) -> bool:
    """Set exact credit amount for user"""
    try:
        supabase = get_supabase_client()
        
        update_data = {
            "credits": amount,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("users").update(update_data).eq("telegram_id", telegram_id).execute()
        
        if result.data:
            print(f"Set {amount} credits for user {telegram_id}")
            return True
        else:
            print(f"Failed to set credits for user {telegram_id}")
            return False
            
    except Exception as e:
        print(f"Error setting credits for user {telegram_id}: {e}")
        return False

def check_sufficient_credits(telegram_id: int, required_amount: int) -> bool:
    """Check if user has sufficient credits"""
    try:
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            return False
            
        current_credits = user.get("credits", 0)
        return current_credits >= required_amount
        
    except Exception as e:
        print(f"Error checking credits for user {telegram_id}: {e}")
        return False
