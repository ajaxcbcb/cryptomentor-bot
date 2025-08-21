
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

def set_premium(tg_id: int, duration_type: str, duration_value: int = 0) -> Dict[str, Any]:
    """
    duration_type: 'lifetime' | 'days' | 'months'
    duration_value: jumlah hari/bulan untuk 'days'/'months'
    """
    s = _client()
    # panggil RPC resmi jika ada, fallback ke manual update
    try:
        s.rpc("set_premium", {
            "p_telegram_id": int(tg_id),
            "p_duration_value": int(duration_value),
            "p_duration_type": duration_type.lower(),
        }).execute()
    except Exception:
        # Fallback manual update
        from datetime import datetime, timedelta
        
        update_data = {
            "is_premium": True,
            "updated_at": datetime.now().isoformat()
        }
        
        if duration_type.lower() == "lifetime":
            update_data["is_lifetime"] = True
            update_data["premium_until"] = None
        else:
            update_data["is_lifetime"] = False
            if duration_type.lower() == "days":
                premium_until = datetime.now() + timedelta(days=duration_value)
            elif duration_type.lower() == "months":
                premium_until = datetime.now() + timedelta(days=duration_value * 30)
            else:
                premium_until = datetime.now() + timedelta(days=duration_value)
            
            update_data["premium_until"] = premium_until.isoformat()
        
        s.table("users").update(update_data).eq("telegram_id", int(tg_id)).execute()
    
    # verifikasi: baca ulang row
    row = get_user_by_tid(tg_id)
    if not row:
        raise RuntimeError("set_premium ok but row not found after update")
    return row

def revoke_premium(tg_id: int) -> Dict[str, Any]:
    s = _client()
    s.table("users").update({
        "is_premium": False,
        "is_lifetime": False,
        "premium_until": None
    }).eq("telegram_id", int(tg_id)).execute()
    row = get_user_by_tid(tg_id)
    if not row:
        raise RuntimeError("revoke_premium ok but row not found after update")
    return row
