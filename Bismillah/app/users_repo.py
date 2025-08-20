from typing import Optional, Dict, Any, Tuple
import os, time
from datetime import datetime, timezone
from .supabase_conn import get_supabase_client, _san

WELCOME_CREDITS = int(os.getenv("WELCOME_CREDITS", "100"))

def get_user_by_telegram_id(tg_id: int) -> Optional[Dict[str, Any]]:
    """Get user by telegram_id from Supabase"""
    s = get_supabase_client()
    res = s.table("users").select("*").eq("telegram_id", int(tg_id)).limit(1).execute()
    return res.data[0] if res.data else None

def ensure_user_registered(
    tg_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    referred_by: Optional[int] = None,
    welcome_quota: Optional[int] = None
) -> Dict[str, Any]:
    """Register user with welcome credits using RPC"""
    s = get_supabase_client()
    payload = {
        "p_telegram_id": int(tg_id),
        "p_username": _san(username),
        "p_first_name": first_name,
        "p_last_name": last_name,
        "p_welcome_quota": int(welcome_quota if welcome_quota is not None else WELCOME_CREDITS),
        "p_referred_by": int(referred_by) if referred_by else None,
    }
    data = s.rpc("upsert_user_with_welcome", payload).execute().data
    if not data:
        raise RuntimeError("upsert_user_with_welcome returned empty")
    return data

def set_premium(tg_id: int, duration_type: str, duration_value: int = 0) -> None:
    """Set premium status via RPC"""
    s = get_supabase_client()
    s.rpc("set_premium", {
        "p_telegram_id": int(tg_id),
        "p_duration_value": int(duration_value),
        "p_duration_type": duration_type,  # 'days'|'months'|'lifetime'
    }).execute()

def revoke_premium(tg_id: int) -> None:
    """Revoke premium status"""
    s = get_supabase_client()
    s.table("users").update({
        "is_premium": False,
        "is_lifetime": False,
        "premium_until": None
    }).eq("telegram_id", int(tg_id)).execute()

def get_credits(tg_id: int) -> int:
    """Get user credits"""
    row = get_user_by_telegram_id(tg_id)
    if row is None:
        raise RuntimeError("User not found in DB")
    return int(row.get("credits") or 0)

def set_user_credits(tg_id: int, amount: int) -> int:
    """Set user credits directly"""
    s = get_supabase_client()
    data = s.table("users").update({"credits": int(amount)}).eq("telegram_id", int(tg_id)).execute().data
    row = data[0] if data else get_user_by_telegram_id(tg_id)
    return int((row or {}).get("credits") or 0)

def debit_credits(tg_id: int, amount: int) -> int:
    """Debit credits from user, return remaining (negative if insufficient)"""
    s = get_supabase_client()

    # Get current credits with fresh data
    result = s.table("users").select("credits").eq("telegram_id", int(tg_id)).limit(1).execute()
    if not result.data:
        print(f"❌ User {tg_id} not found for credit debit")
        return -1

    current_credits = result.data[0].get('credits', 0)

    # Strict check - insufficient credits
    if current_credits < amount:
        print(f"❌ Insufficient credits: user {tg_id} has {current_credits}, needs {amount}")
        return -1

    new_credits = current_credits - amount

    # Atomic update with safety check
    update_result = s.table("users").update({"credits": new_credits}).eq("telegram_id", int(tg_id)).eq("credits", current_credits).execute()

    if not update_result.data:
        print(f"❌ Failed to debit credits for user {tg_id} - concurrent modification")
        return -1

    print(f"✅ Debited {amount} credits from user {tg_id}, remaining: {new_credits}")
    return new_credits

def is_premium_active(tg_id: int) -> bool:
    """Check if user has active premium"""
    row = get_user_by_telegram_id(tg_id) or {}
    if row.get("is_lifetime"):
        return True
    if not row.get("is_premium"):
        return False

    pu = row.get("premium_until")
    if not pu:
        return False

    try:
        s = str(pu)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        return dt > datetime.now(timezone.utc)
    except Exception:
        return False

def stats_totals() -> Tuple[int, int]:
    """Get total users and premium users count"""
    s = get_supabase_client()
    res = s.rpc("stats_totals").execute()
    row = res.data[0] if isinstance(res.data, list) else res.data
    return int(row.get("total_users", 0)), int(row.get("premium_users", 0))

# Legacy compatibility aliases
get_user = get_user_by_telegram_id
upsert_user = ensure_user_registered
set_credits = set_user_credits

# Legacy functions for backward compatibility
def update_user_premium(tg_id: int, is_premium: bool, premium_until: Optional[str] = None) -> None:
    """Legacy compatibility function"""
    s = get_supabase_client()
    update_data = {
        "is_premium": is_premium,
        "premium_until": premium_until
    }
    s.table("users").update(update_data).eq("telegram_id", int(tg_id)).execute()

def add_user_credits(tg_id: int, amount: int) -> None:
    """Add credits to user"""
    current = get_credits(tg_id)
    set_user_credits(tg_id, current + amount)

def deduct_user_credits(tg_id: int, amount: int) -> bool:
    """Deduct credits from user"""
    try:
        remaining = debit_credits(tg_id, amount)
        return remaining >= 0
    except Exception:
        return False

def touch_user_from_update(update):
    """Auto-upsert user from Telegram update object"""
    try:
        user = update.effective_user
        if not user:
            return

        ensure_user_registered(
            tg_id=user.id,
            username=getattr(user, 'username', None),
            first_name=getattr(user, 'first_name', None),
            last_name=getattr(user, 'last_name', None)
        )
        print(f"✅ User {user.id} upserted")

    except Exception as e:
        print(f"❌ Error in touch_user_from_update: {e}")