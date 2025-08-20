
from typing import Tuple
from .users_repo import is_premium_active, debit_credits, get_credits, check_sufficient_credits, add_credits, set_credits
import os

def check_and_deduct_credits(telegram_id: int, command_cost: int = 1) -> Tuple[bool, str]:
    """
    Check if user has enough credits and deduct if they do
    Returns (success, message)
    """
    try:
        # Premium users don't need credits
        if is_premium_active(telegram_id):
            return True, "✅ Premium user - unlimited access"
        
        # Check if user has sufficient credits
        if not check_sufficient_credits(telegram_id, command_cost):
            current_credits = get_credits(telegram_id)
            return False, f"❌ Insufficient credits! You have {current_credits}, need {command_cost}"
        
        # Deduct credits
        if debit_credits(telegram_id, command_cost):
            remaining = get_credits(telegram_id)
            return True, f"✅ Command executed. Remaining credits: {remaining}"
        else:
            return False, "❌ Failed to deduct credits. Please try again."
            
    except Exception as e:
        print(f"Error in check_and_deduct_credits for user {telegram_id}: {e}")
        return False, "❌ Credit system error. Please contact admin."

def get_credit_status(telegram_id: int) -> str:
    """Get formatted credit status for user"""
    try:
        if is_premium_active(telegram_id):
            return "💎 Premium User - Unlimited Access"
        else:
            credits = get_credits(telegram_id)
            return f"💰 Credits: {credits}"
    except Exception as e:
        print(f"Error getting credit status for user {telegram_id}: {e}")
        return "❌ Error checking credits"

def require_credits(tg_id: int, cost: int) -> Tuple[bool, int, str]:
    """
    Return (allowed, remaining, message)
    - Premium/Admin: always allowed, remaining = current credits (not debited).
    - Non-premium: debit 'cost' atomically; if insufficient, STRICTLY rejected.
    """
    # Check admin status - support multiple admin environment variables
    admin_ids = set()
    # Check ADMIN_IDS first (comma separated)
    if os.getenv("ADMIN_IDS"):
        admin_ids.update({int(x.strip()) for x in os.getenv("ADMIN_IDS").split(",") if x.strip().isdigit()})
    
    # Check individual ADMIN variables (ADMIN, ADMIN1, ADMIN2, etc.)
    for key in ["ADMIN", "ADMIN1", "ADMIN2", "ADMIN3", "ADMIN4", "ADMIN5"]:
        admin_value = os.getenv(key, "").strip()
        if admin_value.isdigit():
            admin_ids.add(int(admin_value))
    
    if tg_id in admin_ids:
        return True, get_credits(tg_id), "👑 Admin: kredit unlimited."
    
    # Check premium status
    if is_premium_active(tg_id):
        return True, get_credits(tg_id), "⭐ Premium: kredit tidak terpakai."
    
    # STRICT credit check BEFORE any operation
    current = get_credits(tg_id)
    print(f"🔍 Credit check for user {tg_id}: has {current}, needs {cost}")
    
    if current < cost:
        print(f"❌ INSUFFICIENT CREDITS: User {tg_id} has {current}, needs {cost}")
        return False, current, f"❌ Kredit tidak cukup. Sisa: {current}, biaya: {cost}. Upgrade ke premium untuk unlimited access."
    
    # Debit credits atomically using Supabase
    print(f"💳 Attempting to debit {cost} credits from user {tg_id}")
    remaining = debit_credits(tg_id, cost)
    
    if remaining < 0:  # Debit failed - this should NOT happen if initial check passed
        print(f"❌ CRITICAL: Debit failed for user {tg_id} despite sufficient credits")
        return False, current, f"❌ Gagal mengurangi kredit. Sistem error - hubungi admin."
    
    print(f"✅ Successfully debited {cost} credits from user {tg_id}, remaining: {remaining}")
    return True, remaining, f"💳 Credit tersisa: {remaining} (biaya: -{cost} credit)"
