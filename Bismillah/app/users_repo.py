
"""
Shim/adapter untuk kompatibilitas kode lama.
Mengekspor nama-nama fungsi yang biasa diimport modul lain:
- get_user_by_telegram_id
- get_user
- ensure_user_registered (alias upsert untuk /start)
- upsert_user
- set_premium
- revoke_premium
- set_credits / set_user_credits
- stats_totals
- is_premium_active
Semuanya diarahkan ke implementasi Supabase di app.supabase_conn
"""

from typing import Optional, Dict, Any, Tuple
from .supabase_conn import (
    get_user_by_tid as _get_user_by_tid,
    upsert_user_via_rpc as _upsert_user_via_rpc,
    set_premium_via_rpc as _set_premium_via_rpc,
    revoke_premium as _revoke_premium,
    set_credits as _set_credits,
    stats_totals as _stats_totals,
    is_premium_active as _is_premium_active,
)

# --- Readers ---
def get_user_by_telegram_id(tg_id: int) -> Optional[Dict[str, Any]]:
    """Nama yang dicari kode lama. Ambil row user langsung dari Supabase."""
    return _get_user_by_tid(tg_id)

def get_user(tg_id: int) -> Optional[Dict[str, Any]]:
    """Alias yang kadang dipakai kode lama."""
    return _get_user_by_tid(tg_id)

# --- Writers / Mutators ---
def ensure_user_registered(
    tg_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    referred_by: Optional[int] = None,
    welcome_quota: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Dipanggil dari /start untuk memastikan user terdaftar dan (jika baru) dapat welcome credits.
    """
    return _upsert_user_via_rpc(
        tg_id=tg_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        referred_by=referred_by,
        welcome_quota=welcome_quota,
    )

def upsert_user(
    tg_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    referred_by: Optional[int] = None,
    welcome_quota: Optional[int] = None,
) -> Dict[str, Any]:
    """Alias nama fungsi lain di kode lama."""
    return ensure_user_registered(tg_id, username, first_name, last_name, referred_by, welcome_quota)

def set_premium(tg_id: int, duration_type: str, duration_value: int = 0) -> None:
    """
    Set premium user: duration_type = 'lifetime' | 'days' | 'months'
    Untuk days/months, duration_value wajib > 0.
    """
    _set_premium_via_rpc(tg_id, duration_type, duration_value)

def revoke_premium(tg_id: int) -> None:
    """Cabut premium user (is_premium=false, is_lifetime=false, premium_until=null)."""
    _revoke_premium(tg_id)

def set_credits(tg_id: int, amount: int) -> None:
    """Set credits user langsung di Supabase."""
    _set_credits(tg_id, amount)

def set_user_credits(tg_id: int, amount: int) -> None:
    """Alias tambahan yang kadang dipakai kode lama."""
    _set_credits(tg_id, amount)

# --- Stats / Flags ---
def stats_totals() -> Tuple[int, int]:
    return _stats_totals()

def is_premium_active(tg_id: int) -> bool:
    return _is_premium_active(tg_id)

def touch_user_from_update(update):
    """Auto-upsert user to Supabase from Telegram update object"""
    try:
        user = update.effective_user
        if not user:
            return

        # Try new sb_client first
        try:
            from .supabase_conn import upsert_user_via_rpc
            upsert_user_via_rpc(
                tg_id=user.id,
                username=getattr(user, 'username', None),
                first_name=getattr(user, 'first_name', None),
                last_name=getattr(user, 'last_name', None)
            )
            print(f"✅ User {user.id} upserted via RPC")
            return
        except ImportError:
            print("ℹ️ supabase_conn not found, falling back.")
            pass
        except Exception as e:
            print(f"⚠️ Error calling upsert_user_via_rpc for user {user.id}: {e}")

    except Exception as e:
        print(f"❌ Error in touch_user_from_update: {e}")
