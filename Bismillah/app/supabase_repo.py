
import os
import httpx
import time
from typing import Optional, Dict, Any, Tuple
from supabase import create_client, Client

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def _client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Set SUPABASE_URL & SUPABASE_SERVICE_KEY (Service role).")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_user_by_tid(tg_id: int) -> Optional[Dict[str, Any]]:
    s = _client()
    res = s.table("users").select("*").eq("telegram_id", int(tg_id)).limit(1).execute()
    return res.data[0] if res.data else None

def ensure_user_exists(
    tg_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Buat row user jika belum ada. Tidak menyentuh credits.
    Prefer RPC upsert_user_with_welcome(welcome=0) bila tersedia; fallback direct upsert.
    """
    s = _client()
    # 1) Coba RPC (aman walau function tidak ada)
    try:
        payload = {
            "p_telegram_id": int(tg_id),
            "p_username": (username or "").strip().lstrip("@").lower() or None,
            "p_first_name": first_name,
            "p_last_name": last_name,
            "p_welcome_quota": 0,      # tidak mengubah credits
            "p_referred_by": None,
        }
        data = s.rpc("upsert_user_with_welcome", payload).execute().data
        if data:  # RPC mengembalikan row jsonb
            return data
    except Exception:
        pass

    # 2) Fallback upsert langsung ke tabel
    row = {
        "telegram_id": int(tg_id),
        "username": (username or "").strip().lstrip("@").lower() or None,
        "first_name": first_name,
        "last_name": last_name,
        "credits": 100,  # default credits untuk user baru
        "is_premium": False,
        "is_lifetime": False,
    }
    data = s.table("users").upsert(row, on_conflict="telegram_id").execute().data
    if data: 
        return data[0]
    # 3) Ambil ulang
    r2 = s.table("users").select("*").eq("telegram_id", int(tg_id)).limit(1).execute()
    if r2.data: 
        return r2.data[0]
    raise RuntimeError("ensure_user_exists failed to create/find user")

def get_vuser_by_tid(tg_id: int) -> Optional[Dict[str, Any]]:
    """Get user from v_users view (includes premium_active calculation)"""
    s = _client()
    res = s.table("v_users").select("*").eq("telegram_id", int(tg_id)).limit(1).execute()
    return res.data[0] if res.data else None

def _normalize_duration(token: str) -> Tuple[str, int]:
    """
    lifetime         -> ('lifetime', 0)
    30d / 30         -> ('days', 30)
    2m / 2mo / 2mon  -> ('months', 2)
    """
    t = (token or "").strip().lower()
    if t == "lifetime":
        return ("lifetime", 0)
    if t.isdigit():
        return ("days", int(t))
    if t.endswith("d") and t[:-1].isdigit():
        return ("days", int(t[:-1]))
    if t.endswith(("m", "mo", "mon", "month", "months")):
        num = "".join(ch for ch in t if ch.isdigit())
        if num.isdigit():
            return ("months", int(num))
    raise ValueError("Invalid duration. Use lifetime | <days>d | <days> | <months>m")

def set_premium_normalized(tg_id: int, duration_token: str) -> Dict[str, Any]:
    """Accept '30d'/'30'/'2m'/'lifetime', send valid params to RPC, then read from v_users."""
    s = _client()
    dtype, dval = _normalize_duration(duration_token)
    
    try:
        s.rpc("set_premium", {
            "p_telegram_id": int(tg_id),
            "p_duration_value": int(dval),
            "p_duration_type": dtype,
        }).execute()
    except Exception:
        # Fallback manual update
        from datetime import datetime, timedelta
        
        update_data = {
            "is_premium": True,
            "updated_at": datetime.now().isoformat()
        }
        
        if dtype == "lifetime":
            update_data["is_lifetime"] = True
            update_data["premium_until"] = None
        else:
            update_data["is_lifetime"] = False
            if dtype == "days":
                premium_until = datetime.now() + timedelta(days=dval)
            elif dtype == "months":
                premium_until = datetime.now() + timedelta(days=dval * 30)
            else:
                premium_until = datetime.now() + timedelta(days=dval)
            
            update_data["premium_until"] = premium_until.isoformat()
        
        s.table("users").update(update_data).eq("telegram_id", int(tg_id)).execute()
    
    # Verify from view
    v = get_vuser_by_tid(tg_id)
    if not v:
        raise RuntimeError("Premium updated but v_users row not found")
    return v

def set_premium(tg_id: int, duration_type: str, duration_value: int = 0) -> Dict[str, Any]:
    """Legacy function - use set_premium_normalized instead"""
    return set_premium_normalized(tg_id, f"{duration_value}{duration_type[0]}" if duration_value > 0 else "lifetime")

def revoke_premium(tg_id: int) -> Dict[str, Any]:
    s = _client()
    s.table("users").update({
        "is_premium": False,
        "is_lifetime": False,
        "premium_until": None
    }).eq("telegram_id", int(tg_id)).execute()
    v = get_vuser_by_tid(tg_id)
    if not v:
        raise RuntimeError("Revoke ok but v_users row not found")
    return v
