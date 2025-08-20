"""
Users Repository - Supabase Integration
Handles all user operations with proper Supabase integration
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client

# Supabase client initialization
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_KEY = <REDACTED_SUPABASE_KEY>

def get_supabase_client() -> Client:
    """Get Supabase client with service role key"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise Exception("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in Replit Secrets")

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get user by telegram ID from Supabase"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("users").select("*").eq("telegram_id", telegram_id).limit(1).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None

    except Exception as e:
        print(f"Error getting user {telegram_id}: {e}")
        return None

def get_user_by_tid(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Alias for get_user_by_telegram_id for compatibility"""
    return get_user_by_telegram_id(telegram_id)

def create_user_if_not_exists(telegram_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> Dict[str, Any]:
    """Create user if not exists in Supabase, return user data"""
    try:
        supabase = get_supabase_client()

        # Check if user exists
        existing_user = get_user_by_telegram_id(telegram_id)
        if existing_user:
            return existing_user

        # Create new user
        user_data = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name or f"User{telegram_id}",
            "credits": 100,
            "is_premium": False,
            "is_lifetime": False,
            "premium_until": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        result = supabase.table("users").insert(user_data).execute()

        if result.data and len(result.data) > 0:
            print(f"✅ Created new user {telegram_id}")
            return result.data[0]
        else:
            raise Exception("Failed to create user - no data returned")

    except Exception as e:
        print(f"Error creating user {telegram_id}: {e}")
        raise e

def set_premium(telegram_id: int, lifetime: bool = False, days: Optional[int] = None) -> Dict[str, Any]:
    """Set premium status for user in Supabase"""
    try:
        supabase = get_supabase_client()

        # Ensure user exists
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            user = create_user_if_not_exists(telegram_id)

        # Calculate premium_until
        premium_until = None
        if not lifetime and days:
            premium_until = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()

        # Update user premium status
        update_data = {
            "is_premium": True,
            "is_lifetime": lifetime,
            "premium_until": premium_until,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        result = supabase.table("users").update(update_data).eq("telegram_id", telegram_id).execute()

        if result.data and len(result.data) > 0:
            print(f"✅ Set premium for user {telegram_id}: lifetime={lifetime}, days={days}")
            return result.data[0]
        else:
            raise Exception("Failed to update premium status - no data returned")

    except Exception as e:
        print(f"Error setting premium for user {telegram_id}: {e}")
        raise e

def revoke_premium(telegram_id: int) -> Dict[str, Any]:
    """Revoke premium status for user in Supabase"""
    try:
        supabase = get_supabase_client()

        # Check if user exists
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            raise Exception(f"User {telegram_id} not found")

        # Update user to remove premium
        update_data = {
            "is_premium": False,
            "is_lifetime": False,
            "premium_until": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        result = supabase.table("users").update(update_data).eq("telegram_id", telegram_id).execute()

        if result.data and len(result.data) > 0:
            print(f"✅ Revoked premium for user {telegram_id}")
            return result.data[0]
        else:
            raise Exception("Failed to revoke premium - no data returned")

    except Exception as e:
        print(f"Error revoking premium for user {telegram_id}: {e}")
        raise e

def touch_user_from_update(update) -> Optional[Dict[str, Any]]:
    """Auto-upsert user from Telegram update"""
    if not update.effective_user:
        return None

    user = update.effective_user
    try:
        return create_user_if_not_exists(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
    except Exception as e:
        print(f"Error in touch_user_from_update: {e}")
        return None

def get_credits(telegram_id: int) -> int:
    """Get user credits from Supabase"""
    user = get_user_by_telegram_id(telegram_id)
    return user.get('credits', 0) if user else 0

def is_premium_active(telegram_id: int) -> bool:
    """Check if user has active premium in Supabase"""
    user = get_user_by_telegram_id(telegram_id)
    if not user or not user.get('is_premium'):
        return False

    # Lifetime premium
    if user.get('is_lifetime'):
        return True

    # Timed premium
    premium_until = user.get('premium_until')
    if not premium_until:
        return False

    try:
        expiry_date = datetime.fromisoformat(premium_until.replace('Z', '+00:00'))
        return datetime.now(timezone.utc) < expiry_date
    except:
        return False