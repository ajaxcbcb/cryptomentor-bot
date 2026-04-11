import os
from typing import Optional, Dict, Any, Tuple
from supabase import create_client, Client
from datetime import datetime, timezone

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def _client() -> Client:
    # Re-read env vars at call time to handle cases where dotenv loads after module import
    url = (os.getenv("SUPABASE_URL") or SUPABASE_URL or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_KEY") or SUPABASE_SERVICE_KEY
    if not url or not key:
        raise RuntimeError("Set SUPABASE_URL & SUPABASE_SERVICE_KEY (Service role).")
    return create_client(url, key)

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

    # Check if user already exists
    existing = get_user_by_tid(tg_id)
    if existing:
        # User exists, update profile info only, DON'T touch credits
        update_data = {}
        if username is not None:
            update_data["username"] = (username or "").strip().lstrip("@").lower() or None
        if first is not None:
            update_data["first_name"] = first
        if last is not None:
            update_data["last_name"] = last

        if update_data:
            update_data["updated_at"] = "now()"
            s.table("users").update(update_data).eq("telegram_id", int(tg_id)).execute()

        return {
            "telegram_id": existing.get("telegram_id"),
            "credits": existing.get("credits", 0),
            "is_new": False
        }

    # User doesn't exist, create with welcome credits
    user_data = {
        "telegram_id": int(tg_id),
        "username": (username or "").strip().lstrip("@").lower() or None,
        "first_name": first or "User",
        "last_name": last,
        "credits": int(welcome),
    }

    s.table("users").insert(user_data).execute()

    return {
        "telegram_id": int(tg_id),
        "credits": int(welcome),
        "is_new": True
    }

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

# This function is a placeholder for get_supabase_client, assuming it's defined elsewhere
# If not, you'd need to implement it or use _client() directly.
# For now, we'll assume _client() can be used as a substitute.
def get_supabase_client():
    return _client()

def revoke_premium(tg_id: int):
    """Revoke premium status from user with comprehensive verification"""
    s = get_supabase_client()

    try:
        # First check if user exists
        existing_user = s.table("users").select("telegram_id, is_premium, is_lifetime").eq("telegram_id", tg_id).execute()
        if not existing_user.data:
            raise Exception(f"User {tg_id} not found")

        current_user = existing_user.data[0]
        print(f"🔄 Revoking premium for user {tg_id}: current_premium={current_user.get('is_premium')}, current_lifetime={current_user.get('is_lifetime')}")

        # Set premium status to False with complete reset
        update_data = {
            "is_premium": False,
            "is_lifetime": False,
            "premium_until": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        # Update the user
        result = s.table("users").update(update_data).eq("telegram_id", tg_id).execute()

        if not result.data:
            raise Exception(f"Failed to update user {tg_id} premium status")

        print(f"✅ Premium revoked for user {tg_id}")

        # Verify the update using v_users view for accurate status
        v_result = s.table("v_users").select("*").eq("telegram_id", tg_id).execute()
        if v_result.data:
            verified_data = v_result.data[0]
            print(f"🔍 Verification: is_premium={verified_data.get('is_premium')}, premium_active={verified_data.get('premium_active')}")
            return verified_data
        else:
            # Fallback: return the updated data from users table
            return result.data[0]

    except Exception as e:
        print(f"❌ Error in revoke_premium for user {tg_id}: {e}")
        raise e

def ensure_user_exists(tg_id: int, username: str = None, first_name: str = None):
    """Legacy compatibility function"""
    return ensure_user_exists_no_credit(tg_id, username, first_name)

# ------------------------------------------------------------------ #
#  User API Key management (Bitunix, enkripsi AES-256-GCM di sisi app)#
# ------------------------------------------------------------------ #


def save_user_api_key(telegram_id: int, exchange: str,
                      api_key: str, api_secret: str) -> bool:
    """
    Upsert encrypted API key ke Supabase (direct table, enkripsi di sisi app).
    Pastikan user ada dulu untuk memenuhi FK constraint user_api_keys -> users.
    """
    from app.lib.crypto import encrypt
    try:
        # Pastikan user ada di tabel users (FK constraint)
        ensure_user_exists_no_credit(int(telegram_id))

        s = _client()
        row = {
            "telegram_id": int(telegram_id),
            "exchange": exchange,
            "api_key": api_key,
            "api_secret_enc": encrypt(api_secret),
            "key_hint": api_key[-4:] if len(api_key) >= 4 else api_key,
        }
        s.table("user_api_keys").upsert(row, on_conflict="telegram_id").execute()
        return True
    except Exception as e:
        print(f"save_user_api_key error: {e}")
        return False


def get_user_api_key(telegram_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch dan decrypt API key user dari Supabase.
    Returns dict dengan keys: exchange, api_key, api_secret, key_hint, created_at
    """
    from app.lib.crypto import decrypt
    try:
        s = _client()
        res = s.table("user_api_keys").select("*").eq("telegram_id", int(telegram_id)).limit(1).execute()
        if not res.data:
            return None
        row = res.data[0]
        row["api_secret"] = decrypt(row["api_secret_enc"])
        return row
    except Exception as e:
        print(f"get_user_api_key error: {e}")
        return None


def delete_user_api_key(telegram_id: int) -> bool:
    """Hapus API key user dari Supabase."""
    try:
        s = _client()
        s.table("user_api_keys").delete().eq("telegram_id", int(telegram_id)).execute()
        return True
    except Exception as e:
        print(f"delete_user_api_key error: {e}")
        return False


# ------------------------------------------------------------------ #
#  StackMentor Eligibility (Balance-Based, No Manual Tracking)       #
# ------------------------------------------------------------------ #

def is_stackmentor_eligible_by_balance(balance: float) -> bool:
    """
    Check if user is eligible for StackMentor based on exchange balance.
    ALL balances are eligible - no minimum requirement.
    
    This is called by autotrade engine after fetching user's balance from exchange.
    No database tracking needed - pure balance check.
    """
    return True  # All users can use StackMentor regardless of balance


# ------------------------------------------------------------------ #
#  Risk Per Trade Management (Professional Money Management)         #
# ------------------------------------------------------------------ #

def get_risk_per_trade(telegram_id: int) -> float:
    """
    Get user's risk percentage per trade from database.

    Returns:
        Risk percentage as float in range 0.25 - 5.0.
        Default: 1.0 if not set
    """
    try:
        s = _client()
        res = s.table("autotrade_sessions").select("risk_per_trade").eq(
            "telegram_id", int(telegram_id)
        ).limit(1).execute()

        if res.data and len(res.data) > 0:
            stored_value = res.data[0].get("risk_per_trade")
            if stored_value is not None:
                risk_value = float(stored_value)
                # Safety clamp: enforce dashboard/autotrade supported range.
                risk_value = max(0.25, min(5.0, risk_value))
                # Log to help debug
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"[RiskFetch:{telegram_id}] Retrieved risk_per_trade: {risk_value}")
                return risk_value

        # Default: 1.0 if not set
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[RiskFetch:{telegram_id}] No risk_per_trade found, using default 1.0")
        return 1.0
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[RiskFetch:{telegram_id}] Error fetching risk_per_trade: {e}")
        return 1.0  # Safe default


def get_risk_mode(telegram_id: int) -> str:
    """
    Get user's risk management mode.
    
    Args:
        telegram_id: User's Telegram ID
    
    Returns:
        'risk_based' or 'manual'
    """
    try:
        s = _client()
        res = s.table("autotrade_sessions").select("risk_mode").eq(
            "telegram_id", int(telegram_id)
        ).limit(1).execute()
        
        if res.data and len(res.data) > 0:
            mode = res.data[0].get("risk_mode", "risk_based")
            return mode if mode in ["risk_based", "manual"] else "risk_based"
        
        return "risk_based"  # Default for new users
    except Exception as e:
        print(f"get_risk_mode error: {e}")
        return "risk_based"  # Safe default


def set_risk_mode(telegram_id: int, mode: str) -> Dict[str, Any]:
    """
    Update user's risk management mode.
    
    Args:
        telegram_id: User's Telegram ID
        mode: 'risk_based' or 'manual'
    
    Returns:
        {
            'success': bool,
            'risk_mode': str,
            'error': str (if failed)
        }
    """
    try:
        # Validate mode
        if mode not in ["risk_based", "manual"]:
            return {
                'success': False,
                'error': 'Mode must be risk_based or manual',
                'risk_mode': ''
            }
        
        # Ensure user exists
        ensure_user_exists_no_credit(int(telegram_id))
        
        # Update risk mode
        s = _client()
        s.table("autotrade_sessions").upsert({
            "telegram_id": int(telegram_id),
            "risk_mode": mode,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }, on_conflict="telegram_id").execute()
        
        return {
            'success': True,
            'risk_mode': mode,
            'error': None
        }
    except Exception as e:
        print(f"set_risk_mode error: {e}")
        return {
            'success': False,
            'error': str(e),
            'risk_mode': ''
        }


def set_risk_per_trade(telegram_id: int, risk_pct: float) -> Dict[str, Any]:
    """
    Update user's risk percentage per trade.
    
    Args:
        telegram_id: User's Telegram ID
        risk_pct: Risk percentage (0.25 - 5.0)
    
    Returns:
        {
            'success': bool,
            'risk_per_trade': float,
            'error': str (if failed)
        }
    """
    try:
        # Validate risk percentage
        if risk_pct < 0.25 or risk_pct > 5.0:
            return {
                'success': False,
                'error': 'Risk must be between 0.25% and 5%',
                'risk_per_trade': 0
            }
        
        # Ensure user exists
        ensure_user_exists_no_credit(int(telegram_id))
        
        # Update risk percentage
        s = _client()
        s.table("autotrade_sessions").upsert({
            "telegram_id": int(telegram_id),
            "risk_per_trade": float(risk_pct),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }, on_conflict="telegram_id").execute()
        
        return {
            'success': True,
            'risk_per_trade': float(risk_pct),
            'error': None
        }
    except Exception as e:
        print(f"set_risk_per_trade error: {e}")
        return {
            'success': False,
            'error': str(e),
            'risk_per_trade': 0
        }


def get_user_balance_from_exchange(telegram_id: int, exchange_id: str) -> float:
    """
    Get user's current balance from exchange API.
    
    This is a helper function that fetches balance using stored API keys.
    Used for position sizing calculations.
    
    Args:
        telegram_id: User's Telegram ID
        exchange_id: Exchange identifier (bitunix, binance, bybit, bingx)
    
    Returns:
        Available balance in USDT (0.0 if error)
    """
    try:
        # Get user's API keys
        from app.supabase_repo import get_user_api_key
        keys = get_user_api_key(telegram_id)
        
        if not keys:
            print(f"get_user_balance_from_exchange: No API keys for user {telegram_id}")
            return 0.0
        
        # Get exchange client
        from app.exchange_registry import get_client
        client = get_client(exchange_id, keys["api_key"], keys["api_secret"])
        
        # Fetch balance
        balance_result = client.get_balance()
        
        if balance_result.get('success'):
            return float(balance_result.get('balance', 0))
        else:
            print(f"get_user_balance_from_exchange: API error - {balance_result.get('error')}")
            return 0.0
            
    except Exception as e:
        print(f"get_user_balance_from_exchange error: {e}")
        return 0.0
def get_autotrade_session(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get user's autotrade session status from Supabase."""
    s = _client()
    res = s.table("autotrade_sessions").select("*").eq("telegram_id", int(telegram_id)).limit(1).execute()
    return res.data[0] if res.data else None

def save_autotrade_session(telegram_id: int, status: str = "none", uid: str = None, exchange: str = "bitunix"):
    """Upsert autotrade session for the user."""
    s = _client()
    row = {
        "telegram_id": int(telegram_id),
        "status": status,
        "bitunix_uid": uid,
        "exchange": exchange,
        "updated_at": datetime.utcnow().isoformat()
    }
    s.table("autotrade_sessions").upsert(row, on_conflict="telegram_id").execute()
