
from typing import Tuple
from .users_repo import is_premium_active, debit_credits, get_credits
import os

def require_credits(tg_id: int, cost: int) -> Tuple[bool, int, str]:
    """
    Return (allowed, remaining, message)
    - Premium/Admin: always allowed, remaining = current credits (not debited).
    - Non-premium: debit 'cost' atomically; if insufficient, rejected.
    """
    # Check admin status
    admin_ids = {int(x.strip()) for x in (os.getenv("ADMIN_IDS", "").split(",") if os.getenv("ADMIN_IDS") else [])}
    if tg_id in admin_ids:
        return True, get_credits(tg_id), "✅ Admin: kredit unlimited."
    
    # Check premium status
    if is_premium_active(tg_id):
        return True, get_credits(tg_id), "✅ Premium: kredit tidak terpakai."
    
    # Check current credits BEFORE any operation
    current = get_credits(tg_id)
    if current < cost:
        return False, current, f"❌ Kredit tidak cukup. Sisa: {current}, biaya: {cost}. Upgrade ke premium untuk unlimited access."
    
    # Debit credits atomically
    remaining = debit_credits(tg_id, cost)
    if remaining < 0:  # Double check - debit failed
        return False, current, f"❌ Gagal mengurangi kredit. Sisa: {current}, biaya: {cost}."
    
    return True, remaining, f"✅ {cost} kredit terpakai. Sisa: {remaining}."
