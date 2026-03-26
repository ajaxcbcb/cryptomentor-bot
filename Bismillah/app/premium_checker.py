"""
Premium Checker Module
Utility functions untuk check lifetime premium status dan credit deduction logic.
"""

from typing import Tuple
from app.supabase_conn import get_supabase_client, get_user_by_tid


def is_lifetime_premium(user_id: int) -> bool:
    """
    Check if user is lifetime premium.
    
    Lifetime premium is defined as:
    - is_premium = true
    - premium_until IS NULL (no expiration date)
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if user is lifetime premium, False otherwise
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Query for lifetime premium users
        # Lifetime premium: is_premium=true AND premium_until IS NULL
        result = supabase.table("users").select("telegram_id, is_premium, premium_until").eq(
            "telegram_id", int(user_id)
        ).eq(
            "is_premium", True
        ).is_(
            "premium_until", "null"
        ).limit(1).execute()
        
        # If we found a matching row, user is lifetime premium
        if result.data and len(result.data) > 0:
            print(f"✅ User {user_id} is lifetime premium")
            return True
        
        print(f"ℹ️ User {user_id} is not lifetime premium")
        return False
        
    except Exception as e:
        print(f"❌ Error checking lifetime premium status for user {user_id}: {e}")
        # On error, return False (fail-safe: don't give free access on error)
        return False


def check_and_deduct_credits(user_id: int, cost: int) -> Tuple[bool, str]:
    """
    Check if user has enough credits and deduct if not lifetime premium.
    
    Logic:
    1. Check if user is lifetime premium → bypass credit check, return success
    2. If not lifetime premium → check credit balance
    3. If sufficient credits → deduct and return success
    4. If insufficient credits → return failure with message
    
    Args:
        user_id: Telegram user ID
        cost: Credit cost for the operation
        
    Returns:
        Tuple of (success: bool, message: str)
        - (True, "Lifetime Premium - No credit charge") if lifetime premium
        - (True, "Credits deducted: {cost}") if credits deducted successfully
        - (False, "Insufficient credits. Need {cost}, have {balance}") if insufficient
        - (False, "Error: {error_message}") if error occurred
    """
    try:
        # Step 1: Check if user is lifetime premium
        if is_lifetime_premium(user_id):
            return (True, "Lifetime Premium - No credit charge")
        
        # Step 2: Get user data to check credits
        user = get_user_by_tid(user_id)
        if not user:
            return (False, f"Error: User {user_id} not found")
        
        # Step 3: Check credit balance
        current_credits = user.get("credits", 0)
        if current_credits < cost:
            return (False, f"Insufficient credits. Need {cost}, have {current_credits}")
        
        # Step 4: Deduct credits
        supabase = get_supabase_client()
        new_credits = current_credits - cost
        
        update_result = supabase.table("users").update({
            "credits": new_credits
        }).eq("telegram_id", int(user_id)).execute()
        
        if not update_result.data:
            return (False, f"Error: Failed to deduct credits for user {user_id}")
        
        print(f"✅ Deducted {cost} credits from user {user_id}: {current_credits} → {new_credits}")
        return (True, f"Credits deducted: {cost}")
        
    except Exception as e:
        error_msg = f"Error processing credits: {str(e)[:100]}"
        print(f"❌ {error_msg} for user {user_id}")
        return (False, error_msg)


def get_user_credit_balance(user_id: int) -> int:
    """
    Get user's current credit balance.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Current credit balance (0 if user not found or error)
    """
    try:
        user = get_user_by_tid(user_id)
        if not user:
            return 0
        return user.get("credits", 0)
    except Exception as e:
        print(f"❌ Error getting credit balance for user {user_id}: {e}")
        return 0
