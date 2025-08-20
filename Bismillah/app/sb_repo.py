
import os
from typing import Optional, Dict, Any, Tuple
from .supabase_conn import get_supabase_client

WELCOME_CREDITS = int(os.getenv("WELCOME_CREDITS", "100"))

def _san(u: Optional[str]) -> Optional[str]:
    if not u: return None
    return u.strip().lstrip("@").lower() or None

def get_user_row(tg_id: int) -> Optional[Dict[str, Any]]:
    s = get_supabase_client()
    res = s.table("users").select("*").eq("telegram_id", int(tg_id)).limit(1).execute()
    return res.data[0] if res.data else None

def upsert_user_strict(
    tg_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    referred_by: Optional[int],
) -> Dict[str, Any]:
    s = get_supabase_client()
    payload = {
        "p_telegram_id": int(tg_id),
        "p_username": _san(username),
        "p_first_name": first_name,
        "p_last_name": last_name,
        "p_welcome_quota": WELCOME_CREDITS,
        "p_referred_by": int(referred_by) if referred_by else None,
    }
    # STRICT: kalau RPC gagal, raise (biar ketahuan & ga "seolah sukses")
    data = s.rpc("upsert_user_with_welcome", payload).execute().data
    if not data:
        raise RuntimeError("RPC upsert_user_with_welcome returned empty")
    return data

def set_premium_rpc(tg_id: int, duration_type: str, duration_value: int = 0) -> None:
    s = get_supabase_client()
    s.rpc("set_premium", {
        "p_telegram_id": int(tg_id),
        "p_duration_value": int(duration_value),
        "p_duration_type": duration_type,  # 'days'|'months'|'lifetime'
    }).execute()

def revoke_premium_db(tg_id: int) -> None:
    # SQL tidak menyediakan revoke RPC → update langsung ke Supabase table
    s = get_supabase_client()
    s.table("users").update({
        "is_premium": False,
        "is_lifetime": False,
        "premium_until": None
    }).eq("telegram_id", int(tg_id)).execute()

def set_credits_db(tg_id: int, amount: int) -> None:
    s = get_supabase_client()
    s.table("users").update({"credits": int(amount)}).eq("telegram_id", int(tg_id)).execute()

def stats_totals() -> Tuple[int,int]:
    s = get_supabase_client()
    res = s.rpc("stats_totals").execute()
    row = res.data[0] if isinstance(res.data, list) else res.data
    return int(row.get("total_users",0)), int(row.get("premium_users",0))

# Legacy compatibility functions
def user_exists(tg_id: int) -> bool:
    return get_user_row(tg_id) is not None

def upsert_user_with_ref_optional(
    tg_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    referred_by: Optional[int],
) -> Dict[str, Any]:
    return upsert_user_strict(tg_id, username, first_name, last_name, referred_by)

def upsert_user_ref_required(
    tg_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    referred_by: Optional[int],
) -> Dict[str, Any]:
    if not referred_by:
        raise ValueError("Referral required: missing referred_by")
    return upsert_user_strict(tg_id, username, first_name, last_name, referred_by)
