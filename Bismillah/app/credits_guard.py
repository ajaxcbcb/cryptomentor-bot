from typing import Tuple
from app.users_repo import is_premium_active, get_vuser_by_telegram_id

def require_credits(tg_id: int, cost: int) -> Tuple[bool, int, str]:
    """
    Check and deduct credits for non-premium users
    Returns: (success, remaining_credits, message)
    """
    # Premium aktif: tidak didebit
    if is_premium_active(tg_id):
        row = get_vuser_by_telegram_id(tg_id) or {}
        remain = int(row.get("credits") or 0)
        return True, remain, "✅ Premium aktif — kredit tidak terpakai."

    # Non-premium: ambil saldo & debit sesuai implementasi
    from app.supabase_conn import get_supabase_client
    s = get_supabase_client()
    user = s.table("users").select("credits").eq("telegram_id", int(tg_id)).limit(1).execute().data
    cur = int((user[0] if user else {}).get("credits") or 0)

    if cur < cost:
        return False, cur, f"❌ Kredit tidak cukup. Sisa: {cur}, biaya: {cost}. Upgrade ke premium untuk unlimited access."

    newv = cur - cost
    s.table("users").update({"credits": newv}).eq("telegram_id", int(tg_id)).execute()
    return True, newv, f"✅ {cost} kredit terpakai. Sisa: {newv}."

def check_credits_balance(tg_id: int) -> Tuple[bool, int]:
    """
    Check user's credit balance without deducting
    Returns: (is_premium, credits)
    """
    if is_premium_active(tg_id):
        row = get_vuser_by_telegram_id(tg_id) or {}
        credits = int(row.get("credits") or 0)
        return True, credits

    from app.supabase_conn import get_supabase_client
    s = get_supabase_client()
    user = s.table("users").select("credits").eq("telegram_id", int(tg_id)).limit(1).execute().data
    credits = int((user[0] if user else {}).get("credits") or 0)
    return False, credits
from typing import Tuple
from app.users_repo import is_premium_active
from app.supabase_repo import ensure_user_exists_no_credit, get_credits, debit_credits_rpc

def require_credits(tg_id: int, cost: int, username: str = None, first: str = None, last: str = None) -> Tuple[bool, int, str]:
    """
    - Pastikan row user ada TANPA mengubah credits.
    - Premium aktif: bypass debit.
    - Non-premium: debit via RPC (atomic), tidak pernah reset ke 100.
    Returns: (allowed, remaining, message)
    """
    # Pastikan user exists TANPA mengubah credits
    ensure_user_exists_no_credit(tg_id, username, first, last)

    # Check premium status - jika premium, tidak debit credits
    if is_premium_active(tg_id):
        remaining = get_credits(tg_id)  # hanya untuk display
        return True, remaining, "✅ **Premium aktif** - Akses unlimited, kredit tidak terpakai"

    # Non-premium: check credits dan debit atomically
    current = get_credits(tg_id)
    if current < cost:
        return False, current, f"❌ **Kredit tidak cukup**\n💳 Sisa: **{current}** | Biaya: **{cost}**\n\n💡 Gunakan `/credits` atau upgrade premium"

    # Debit credits via RPC (atomic operation)
    remaining = debit_credits_rpc(tg_id, cost)
    return True, remaining, f"💳 **Credit terpakai**: {cost} | **Sisa**: {remaining}"
