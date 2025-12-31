from typing import Tuple
from app.users_repo import is_premium_active
from app.supabase_repo import ensure_user_exists_no_credit, get_credits, debit_credits_rpc

def require_credits(tg_id: int, cost: int, username: str = None, first: str = None, last: str = None) -> Tuple[bool, int, str]:
    """
    Check and deduct credits for non-premium users.
    - Premium users: bypass debit, unlimited access
    - Non-premium: debit via RPC (atomic)
    Returns: (allowed, remaining, message)
    """
    # Pastikan user exists TANPA mengubah credits
    ensure_user_exists_no_credit(tg_id, username, first, last)

    # Check premium status - jika premium, tidak debit credits
    if is_premium_active(tg_id):
        remaining = get_credits(tg_id)  # hanya untuk display
        print(f"✅ Premium user {tg_id} - access granted (credits not deducted)")
        return True, remaining, "✅ **Premium aktif** - Akses unlimited, kredit tidak terpakai"

    # Non-premium: check credits dan debit atomically
    current = get_credits(tg_id)
    print(f"🔍 Credit check for free user {tg_id}: current={current}, cost={cost}")
    
    if current < cost:
        print(f"❌ Insufficient credits for user {tg_id}: {current} < {cost}")
        return False, current, f"❌ **Kredit tidak cukup**\n💳 Sisa: **{current}** | Biaya: **{cost}**\n\n💡 Gunakan `/credits` atau upgrade premium"

    # Debit credits via RPC (atomic operation)
    remaining = debit_credits_rpc(tg_id, cost)
    
    # CRITICAL: Verify debit actually happened
    # If remaining equals current, debit failed (RPC returned 0 or same value)
    if remaining == current or (remaining == 0 and current >= cost):
        # Double-check by re-fetching credits
        actual_remaining = get_credits(tg_id)
        if actual_remaining == current:
            # Debit did NOT happen - use fallback direct debit
            print(f"⚠️ RPC debit failed for user {tg_id}, using fallback direct debit")
            try:
                from app.users_repo import debit_credits as fallback_debit
                success = fallback_debit(tg_id, cost)
                if success:
                    remaining = get_credits(tg_id)
                    print(f"✅ Fallback debit successful for user {tg_id}: {cost} credits, remaining: {remaining}")
                else:
                    print(f"❌ Fallback debit also failed for user {tg_id}")
                    return False, current, "❌ **Gagal mengurangi kredit**\n\nSilakan coba lagi nanti."
            except Exception as e:
                print(f"❌ Fallback debit error for user {tg_id}: {e}")
                return False, current, "❌ **Sistem kredit bermasalah**\n\nSilakan coba lagi nanti."
        else:
            remaining = actual_remaining
    
    print(f"✅ Credit deducted for user {tg_id}: {cost} credits, remaining: {remaining}")
    return True, remaining, f"💳 **Credit terpakai**: {cost} | **Sisa**: {remaining}"

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
