
import os
from typing import Optional, Dict, Any, Tuple
from supabase import create_client, Client

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SERVICE_KEY = <REDACTED_SUPABASE_KEY>

def _client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Set SUPABASE_URL & SUPABASE_SERVICE_KEY (Service role).")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# --- READERS ---
def get_user_by_tid(tg_id: int) -> Optional[Dict[str, Any]]:
    """Get user by telegram ID"""
    s = _client()
    res = s.table("users").select("*").eq("telegram_id", int(tg_id)).limit(1).execute()
    return res.data[0] if res.data else None

def get_vuser_by_tid(tg_id: int) -> Optional[Dict[str, Any]]:
    """Get user from v_users view"""
    s = _client()
    res = s.table("v_users").select("*").eq("telegram_id", int(tg_id)).limit(1).execute()
    return res.data[0] if res.data else None

# --- REGISTER (NO CREDIT CHANGE) untuk command biasa ---
def ensure_user_exists_no_credit(
    tg_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Upsert TANPA mengubah credits. Pakai di /market, /analyze, /futures_signals, dst.
    """
    s = _client()
    
    # Check if user exists first
    existing = get_user_by_tid(tg_id)
    if existing:
        # User exists, just update profile info if provided
        update_data = {}
        if username is not None:
            update_data["username"] = (username or "").strip().lstrip("@").lower() or None
        if first_name is not None:
            update_data["first_name"] = first_name
        if last_name is not None:
            update_data["last_name"] = last_name
        
        if update_data:
            update_data["updated_at"] = "now()"
            s.table("users").update(update_data).eq("telegram_id", int(tg_id)).execute()
        
        return existing
    
    # User doesn't exist, create with minimal data (no credits set - will use default)
    row = {
        "telegram_id": int(tg_id),
        "username": (username or "").strip().lstrip("@").lower() or None,
        "first_name": first_name or "User",
        "last_name": last_name,
        "credits": 0,  # New users get 0 credits by default (welcome credits only from /start)
    }
    
    s.table("users").insert(row).execute()
    return get_user_by_tid(tg_id) or row

# --- REGISTER WELCOME (HANYA untuk /start) ---
def upsert_user_with_welcome(
    tg_id: int, 
    username: Optional[str], 
    first: Optional[str], 
    last: Optional[str], 
    welcome: int = 100
) -> Dict[str, Any]:
    """
    Khusus /start: kalau user baru, set credits=welcome; kalau sudah ada, JANGAN ubah credits.
    """
    s = _client()
    try:
        data = s.rpc("upsert_user_with_welcome", {
            "p_telegram_id": int(tg_id),
            "p_username": (username or "").strip().lstrip("@").lower() or None,
            "p_first_name": first,
            "p_last_name": last,
            "p_welcome_quota": int(welcome),
            "p_referred_by": None
        }).execute().data
        
        if data and len(data) > 0:
            row_data = data[0]
            return {
                "telegram_id": row_data.get("telegram_id"),
                "credits": row_data.get("credits"),
                "is_new": row_data.get("is_new", False)
            }
    except Exception as e:
        print(f"RPC upsert_user_with_welcome failed: {e}")
    
    # Fallback: manual upsert behavior
    existing = get_user_by_tid(tg_id)
    if not existing:
        s.table("users").insert({
            "telegram_id": int(tg_id),
            "username": (username or "").strip().lstrip("@").lower() or None,
            "first_name": first,
            "last_name": last,
            "credits": int(welcome),
        }).execute()
    
    return get_user_by_tid(tg_id) or {}

# --- CREDITS: baca & debit ATOMIK via RPC ---
def get_credits(tg_id: int) -> int:
    """Get current credits for user"""
    row = get_user_by_tid(tg_id)
    return int(row.get("credits", 0)) if row else 0

def debit_credits_rpc(tg_id: int, amount: int) -> int:
    """Atomically debit credits and return remaining"""
    s = _client()
    try:
        res = s.rpc("debit_credits", {"p_telegram_id": int(tg_id), "p_amount": int(amount)}).execute()
        # res.data bisa integer atau array tergantung driver
        if isinstance(res.data, list) and res.data:
            return int(res.data[0])
        return int(res.data or 0)
    except Exception as e:
        print(f"debit_credits_rpc failed: {e}")
        return 0

# --- PREMIUM FUNCTIONS ---
def set_premium_normalized(tg_id: int, duration_str: str) -> Dict[str, Any]:
    """Set premium status using normalized duration"""
    from datetime import datetime, timedelta
    
    ensure_user_exists_no_credit(tg_id)
    s = _client()
    
    if duration_str.lower() == 'lifetime':
        update_data = {
            "is_premium": True,
            "is_lifetime": True,
            "premium_until": None,
            "updated_at": datetime.now().isoformat()
        }
    else:
        # Parse duration (30d, 2m, etc.)
        if duration_str.endswith('d'):
            days = int(duration_str[:-1])
        elif duration_str.endswith('m'):
            days = int(duration_str[:-1]) * 30
        elif duration_str.isdigit():
            days = int(duration_str)
        else:
            days = 30  # default
        
        premium_until = datetime.now() + timedelta(days=days)
        update_data = {
            "is_premium": True,
            "is_lifetime": False,
            "premium_until": premium_until.isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    s.table("users").update(update_data).eq("telegram_id", int(tg_id)).execute()
    
    # Return verification from v_users view
    return get_vuser_by_tid(tg_id) or {}

def revoke_premium(tg_id: int) -> Dict[str, Any]:
    """Revoke premium status"""
    ensure_user_exists_no_credit(tg_id)
    s = _client()
    
    update_data = {
        "is_premium": False,
        "is_lifetime": False,
        "premium_until": None,
        "updated_at": datetime.now().isoformat()
    }
    
    s.table("users").update(update_data).eq("telegram_id", int(tg_id)).execute()
    
    # Return verification from v_users view
    return get_vuser_by_tid(tg_id) or {}

def ensure_user_exists(tg_id: int, username: str = None, first_name: str = None):
    """Legacy compatibility function"""
    return ensure_user_exists_no_credit(tg_id, username, first_name)
