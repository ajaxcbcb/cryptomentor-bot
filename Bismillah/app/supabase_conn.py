
import os, httpx
from functools import lru_cache
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timezone
from supabase import create_client, Client

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SERVICE_KEY = <REDACTED_SUPABASE_KEY>
WELCOME_CREDITS = int(os.getenv("WELCOME_CREDITS", "100"))

# ---------- Core client & health ----------
def _assert_env():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Set SUPABASE_URL & SUPABASE_SERVICE_KEY (Service role).")

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    _assert_env()
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def health() -> Tuple[bool, str]:
    try:
        s = get_supabase_client()
        try:
            s.rpc("hc").execute()
            return True, "rpc(hc): OK"
        except Exception:
            pass
        r = httpx.get(
            f"{SUPABASE_URL}/rest/v1/",
            headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"},
            timeout=6.0,
        )
        if r.status_code in (200, 404): return True, f"rest {r.status_code}"
        if r.status_code in (401, 403): return False, f"{r.status_code} unauthorized (Service role?)"
        return False, f"{r.status_code} {r.text[:120]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

# ---------- Helpers ----------
def _san(u: Optional[str]) -> Optional[str]:
    if not u: return None
    return u.strip().lstrip("@").lower() or None

def _is_premium_active_row(row: Dict[str, Any]) -> bool:
    if not row: return False
    if row.get("is_lifetime"): return True
    if not row.get("is_premium"): return False
    pu = row.get("premium_until")
    if not pu: return False
    # Supabase returns ISO string; compare in UTC
    try:
        # 2025-08-20T10:15:00+00:00 or ...Z
        if isinstance(pu, str):
            # naive parse
            from datetime import datetime
            if pu.endswith("Z"): pu = pu[:-1] + "+00:00"
            dt = datetime.fromisoformat(pu)
        else:
            dt = pu
        return dt > datetime.now(timezone.utc)
    except Exception:
        return False

# ---------- Public API expected by your code ----------
def get_user_by_tid(tg_id: int) -> Optional[Dict[str, Any]]:
    """Legacy compatibility: fetch user row by telegram_id (fresh from DB)."""
    s = get_supabase_client()
    res = s.table("users").select("*").eq("telegram_id", int(tg_id)).limit(1).execute()
    return res.data[0] if res.data else None

def upsert_user_via_rpc(
    tg_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    referred_by: Optional[int] = None,
    welcome_quota: Optional[int] = None,
) -> Dict[str, Any]:
    """Use your RPC upsert_user_with_welcome to ensure welcome credits for new users."""
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
        raise RuntimeError("RPC upsert_user_with_welcome returned empty")
    return data

def set_premium_via_rpc(tg_id: int, duration_type: str, duration_value: int = 0) -> None:
    s = get_supabase_client()
    s.rpc("set_premium", {
        "p_telegram_id": int(tg_id),
        "p_duration_value": int(duration_value),
        "p_duration_type": duration_type,  # 'days'|'months'|'lifetime'
    }).execute()

def revoke_premium(tg_id: int) -> None:
    """Direct table update to revoke premium (since no revoke RPC)."""
    s = get_supabase_client()
    s.table("users").update({
        "is_premium": False,
        "is_lifetime": False,
        "premium_until": None
    }).eq("telegram_id", int(tg_id)).execute()

def set_credits(tg_id: int, amount: int) -> None:
    s = get_supabase_client()
    s.table("users").update({"credits": int(amount)}).eq("telegram_id", int(tg_id)).execute()

def stats_totals() -> Tuple[int, int]:
    s = get_supabase_client()
    res = s.rpc("stats_totals").execute()
    row = res.data[0] if isinstance(res.data, list) else res.data
    return int(row.get("total_users", 0)), int(row.get("premium_users", 0))

def is_premium_active(tg_id: int) -> bool:
    """Legacy compatibility: compute premium-active using current DB row."""
    row = get_user_by_tid(tg_id)
    return _is_premium_active_row(row or {})
