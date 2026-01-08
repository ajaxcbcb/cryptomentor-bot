from typing import Tuple
from app.users_repo import is_premium_active
from app.supabase_repo import ensure_user_exists_no_credit, get_credits, debit_credits_rpc

def require_credits(tg_id: int, cost: int, username: str = None, first: str = None, last: str = None) -> Tuple[bool, int, str]:
    """
    Check and deduct credits for non-premium users.
    - Premium users: bypass debit, unlimited access
    - Non-premium: debit via direct update (more reliable)
    Returns: (allowed, remaining, message)
    """
    # Pastikan user exists TANPA mengubah credits
    ensure_user_exists_no_credit(tg_id, username, first, last)

    # Check premium status - jika premium, tidak debit credits
    if is_premium_active(tg_id):
        remaining = get_credits(tg_id)  # hanya untuk display
        print(f"✅ Premium user {tg_id} - access granted (credits not deducted)")
        return True, remaining, "✅ **Premium aktif** - Akses unlimited, kredit tidak terpakai"

    # Non-premium: check credits dan debit
    current = get_credits(tg_id)
    print(f"🔍 Credit check for free user {tg_id}: current={current}, cost={cost}")
    
    if current < cost:
        print(f"❌ Insufficient credits for user {tg_id}: {current} < {cost}")
        return False, current, f"❌ **Kredit tidak cukup**\n💳 Sisa: **{current}** | Biaya: **{cost}**\n\n💡 Gunakan `/credits` atau upgrade premium"

    # Use direct debit first (more reliable than RPC)
    try:
        from app.users_repo import debit_credits as direct_debit
        success = direct_debit(tg_id, cost)
        if success:
            remaining = get_credits(tg_id)
            print(f"✅ Direct debit successful for user {tg_id}: {cost} credits, remaining: {remaining}")
            return True, remaining, f"💳 **Credit terpakai**: {cost} | **Sisa**: {remaining}"
        else:
            print(f"⚠️ Direct debit returned False for user {tg_id}, trying RPC fallback")
    except Exception as e:
        print(f"⚠️ Direct debit error for user {tg_id}: {e}, trying RPC fallback")
    
    # Fallback to RPC if direct debit fails
    try:
        remaining = debit_credits_rpc(tg_id, cost)
        
        # Verify debit happened
        actual_remaining = get_credits(tg_id)
        expected_remaining = current - cost
        
        if abs(actual_remaining - expected_remaining) <= 1:  # Allow 1 credit tolerance
            print(f"✅ RPC debit successful for user {tg_id}: {cost} credits, remaining: {actual_remaining}")
            return True, actual_remaining, f"💳 **Credit terpakai**: {cost} | **Sisa**: {actual_remaining}"
        else:
            print(f"❌ RPC debit verification failed for user {tg_id}: expected {expected_remaining}, got {actual_remaining}")
            return False, current, "❌ **Gagal mengurangi kredit**\n\nSilakan coba lagi nanti."
    except Exception as e:
        print(f"❌ RPC debit error for user {tg_id}: {e}")
        return False, current, "❌ **Sistem kredit bermasalah**\n\nSilakan coba lagi nanti."

def check_credits_balance(tg_id: int) -> Tuple[bool, int]:
    """
    Check user's credit balance without deducting
    Returns: (is_premium, credits)
    """
    if is_premium_active(tg_id):
        credits = get_credits(tg_id)
        return True, credits

    credits = get_credits(tg_id)
    return False, credits
