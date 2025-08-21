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
    ATOMIC CREDIT CHECK & DEBIT using Supabase with proper remaining display
    Returns: (allowed, remaining_after, message)
    """
    from app.users_repo import is_premium_active, get_vuser_by_telegram_id
    from app.lib.auth import is_admin

    # Premium active: no debit
    if is_premium_active(tg_id):
        row = get_vuser_by_telegram_id(tg_id) or {}
        remain = int(row.get("credits") or 0)
        return True, remain, "✅ Premium aktif — kredit tidak terpakai."

    # Admin bypass
    if is_admin(tg_id):
        row = get_vuser_by_telegram_id(tg_id) or {}
        remain = int(row.get("credits") or 0)
        return True, remain, "👑 Admin - Unlimited access"

    # Non-premium: check balance & debit
    try:
        s = get_supabase_client()

        # Try atomic RPC debit first
        try:
            result = s.rpc('debit_credits', {
                'p_telegram_id': tg_id,
                'p_cost': cost
            }).execute()

            if result.data is not None:
                new_balance = int(result.data)
                return True, new_balance, f"✅ {cost} credit terpakai. Sisa: {new_balance}."
        except Exception:
            pass  # Fallback to manual method

        # Manual check & debit
        user = s.table("users").select("credits").eq("telegram_id", int(tg_id)).limit(1).execute().data
        cur = int((user[0] if user else {}).get("credits") or 0)

        if cur < cost:
            return False, cur, f"❌ Credit tidak cukup. Sisa: {cur}, biaya: {cost}. Upgrade ke premium untuk unlimited access."

        newv = cur - cost
        s.table("users").update({"credits": newv}).eq("telegram_id", int(tg_id)).execute()
        return True, newv, f"✅ {cost} credit terpakai. Sisa: {newv}."

    except Exception as e:
        print(f"❌ Credit guard error: {e}")
        # Final fallback
        from app.users_repo import get_credits
        current = get_credits(tg_id)
        return False, current, f"❌ Sistem error. Sisa credit: {current}. Coba lagi nanti."