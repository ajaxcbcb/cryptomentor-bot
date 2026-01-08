from typing import Tuple
import sys
from app.supabase_repo import ensure_user_exists_no_credit, get_credits, debit_credits_rpc

def _check_premium(tg_id: int) -> bool:
    """Check premium status using Supabase"""
    try:
        from app.supabase_repo import get_user_by_tid
        user = get_user_by_tid(tg_id)
        if not user:
            return False
        
        if user.get("is_lifetime"):
            return True
        if not user.get("is_premium"):
            return False
        
        # Check expiry
        premium_until = user.get("premium_until")
        if not premium_until:
            return user.get("is_premium", False)
        
        from datetime import datetime
        try:
            if isinstance(premium_until, str):
                expiry = datetime.fromisoformat(premium_until.replace('Z', '+00:00').replace('+00:00', ''))
            else:
                expiry = premium_until
            return expiry > datetime.utcnow()
        except:
            return user.get("is_premium", False)
    except Exception as e:
        print(f"[_check_premium] Error: {e}", flush=True)
        return False

def require_credits(tg_id: int, cost: int, username: str = None, first: str = None, last: str = None) -> Tuple[bool, int, str]:
    """
    Check and deduct credits for non-premium users.
    - Premium users: bypass debit, unlimited access
    - Non-premium: debit via direct update (more reliable)
    Returns: (allowed, remaining, message)
    """
    print(f"[require_credits] START for user {tg_id}, cost={cost}", flush=True)
    
    # Pastikan user exists TANPA mengubah credits
    try:
        ensure_user_exists_no_credit(tg_id, username, first, last)
    except Exception as e:
        print(f"[require_credits] ensure_user error: {e}", flush=True)

    # Check premium status - jika premium, tidak debit credits
    is_premium = _check_premium(tg_id)
    print(f"[require_credits] Premium check result: {is_premium}", flush=True)
    
    if is_premium:
        remaining = get_credits(tg_id)
        print(f"✅ Premium user {tg_id} - access granted (credits not deducted)", flush=True)
        return True, remaining, "✅ **Premium aktif** - Akses unlimited, kredit tidak terpakai"

    # Non-premium: check credits dan debit
    try:
        current = get_credits(tg_id)
        print(f"🔍 Credit check for free user {tg_id}: current={current}, cost={cost}", flush=True)
    except Exception as e:
        print(f"[require_credits] get_credits error: {e}", flush=True)
        return False, 0, "❌ **Gagal mengecek kredit**\n\nSilakan coba lagi nanti."
    
    if current < cost:
        print(f"❌ Insufficient credits for user {tg_id}: {current} < {cost}", flush=True)
        return False, current, f"❌ **Kredit tidak cukup**\n💳 Sisa: **{current}** | Biaya: **{cost}**\n\n💡 Gunakan `/credits` atau upgrade premium"

    # Use direct debit first (more reliable than RPC)
    try:
        from app.users_repo import debit_credits as direct_debit
        print(f"[require_credits] Attempting direct debit for user {tg_id}", flush=True)
        success = direct_debit(tg_id, cost)
        if success:
            remaining = get_credits(tg_id)
            print(f"✅ Direct debit successful for user {tg_id}: {cost} credits, remaining: {remaining}", flush=True)
            return True, remaining, f"💳 **Credit terpakai**: {cost} | **Sisa**: {remaining}"
        else:
            print(f"⚠️ Direct debit returned False for user {tg_id}, trying RPC fallback", flush=True)
    except Exception as e:
        print(f"⚠️ Direct debit error for user {tg_id}: {e}, trying RPC fallback", flush=True)
    
    # Fallback to RPC if direct debit fails
    try:
        print(f"[require_credits] Attempting RPC debit for user {tg_id}", flush=True)
        remaining = debit_credits_rpc(tg_id, cost)
        
        # Verify debit happened
        actual_remaining = get_credits(tg_id)
        expected_remaining = current - cost
        
        if abs(actual_remaining - expected_remaining) <= 1:  # Allow 1 credit tolerance
            print(f"✅ RPC debit successful for user {tg_id}: {cost} credits, remaining: {actual_remaining}", flush=True)
            return True, actual_remaining, f"💳 **Credit terpakai**: {cost} | **Sisa**: {actual_remaining}"
        else:
            print(f"❌ RPC debit verification failed for user {tg_id}: expected {expected_remaining}, got {actual_remaining}", flush=True)
            return False, current, "❌ **Gagal mengurangi kredit**\n\nSilakan coba lagi nanti."
    except Exception as e:
        print(f"❌ RPC debit error for user {tg_id}: {e}", flush=True)
        return False, current, "❌ **Sistem kredit bermasalah**\n\nSilakan coba lagi nanti."

def check_credits_balance(tg_id: int) -> Tuple[bool, int]:
    """
    Check user's credit balance without deducting
    Returns: (is_premium, credits)
    """
    if _check_premium(tg_id):
        credits = get_credits(tg_id)
        return True, credits

    credits = get_credits(tg_id)
    return False, credits
