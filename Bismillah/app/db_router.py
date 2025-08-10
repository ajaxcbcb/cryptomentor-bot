
# app/db_router.py
import os
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

# backends
try:
    from app.supabase_conn import health as sb_health, upsert_user_tid as sb_upsert, update_user_tid as sb_update, get_user_by_tid as sb_get
except Exception:
    sb_health = None; sb_upsert = None; sb_update = None; sb_get = None

try:
    from app.storage_local import load_users, save_users, get_user, update_user
except Exception:
    load_users = save_users = get_user = update_user = None

DB_MODE = "unknown"
DB_READY = False
DB_NOTE = ""

def _supabase_env_ok() -> bool:
    return bool(os.getenv("SUPABASE_URL")) and bool(os.getenv("SUPABASE_SERVICE_KEY"))

def init_db() -> Tuple[str, bool, str]:
    global DB_MODE, DB_READY, DB_NOTE
    # 1) coba supabase
    if _supabase_env_ok() and sb_health is not None:
        ok, info = sb_health()
        if ok:
            DB_MODE, DB_READY, DB_NOTE = "supabase", True, "Supabase CONNECTED"
            return DB_MODE, DB_READY, DB_NOTE
        else:
            DB_MODE, DB_READY, DB_NOTE = "supabase", False, f"Supabase NOT READY: {info}"
    # 2) fallback lokal
    if load_users and save_users:
        DB_MODE, DB_READY, DB_NOTE = "local", True, "Local JSON storage"
        return DB_MODE, DB_READY, DB_NOTE
    # 3) gagal total
    DB_MODE, DB_READY, DB_NOTE = "none", False, "No database backend available"
    return DB_MODE, DB_READY, DB_NOTE

def db_status() -> Dict[str, Any]:
    return {"mode": DB_MODE, "ready": DB_READY, "note": DB_NOTE}

def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get user data konsisten dari router"""
    if DB_MODE == "supabase" and DB_READY:
        return sb_get(telegram_id)
    # local
    users = load_users()
    return users.get(str(telegram_id))

def _verify_set(fields: Dict[str, Any], fetched: Dict[str, Any]) -> Tuple[bool, str]:
    """Verifikasi write berhasil dengan membandingkan field yang di-set"""
    # cek boolean premium & (opsional) premium_until match
    want_prem = fields.get("is_premium")
    got_prem = fetched.get("is_premium")
    if want_prem is not None and (bool(want_prem) != bool(got_prem)):
        return False, f"is_premium mismatch (want={want_prem}, got={got_prem})"
    
    if "premium_until" in fields:
        want_until = fields.get("premium_until")
        got_until = fetched.get("premium_until")
        # string compare cukup (ISO); toleransi None vs null
        if (want_until or "") != (got_until or ""):
            return False, f"premium_until mismatch (want={want_until}, got={got_until})"
    
    if "credits" in fields:
        want_credits = fields.get("credits")
        got_credits = fetched.get("credits")
        if int(want_credits or 0) != int(got_credits or 0):
            return False, f"credits mismatch (want={want_credits}, got={got_credits})"
    
    return True, "ok"

# ======= Helpers bisnis =======

def _iso_in_days(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=int(days))).isoformat()

def add_premium(telegram_id: int, duration: str) -> Tuple[Dict[str, Any], str]:
    """Tambah premium dengan verifikasi write"""
    duration = str(duration).strip().lower()
    
    if duration == "lifetime":
        fields = {"banned": False, "is_premium": True, "premium_until": None}
        msg = f"✅ Premium lifetime diaktifkan untuk {telegram_id}."
    else:
        if not duration.isdigit() or int(duration) < 1:
            raise ValueError("days harus angka >= 1 atau 'lifetime'")
        iso = _iso_in_days(int(duration))
        fields = {"banned": False, "is_premium": True, "premium_until": iso}
        msg = f"✅ Premium {duration} hari diaktifkan untuk {telegram_id} sampai {fields['premium_until']}."

    if DB_MODE == "supabase" and DB_READY:
        rec = sb_upsert(telegram_id, **fields)
        # verify
        ref = sb_get(telegram_id) or {}
        ok, why = _verify_set(fields, ref)
        if not ok:
            raise RuntimeError(f"Verify failed: {why}")
        return ref, msg

    # local
    users = load_users()
    rec = update_user(users, telegram_id, fields)
    save_users(users)
    return rec, msg

def remove_premium(telegram_id: int) -> Dict[str, Any]:
    """Remove premium dengan verifikasi"""
    fields = {"is_premium": False, "premium_until": None}
    
    if DB_MODE == "supabase" and DB_READY:
        sb_update(telegram_id, **fields)
        ref = sb_get(telegram_id) or {}
        ok, why = _verify_set(fields, ref)
        if not ok:
            raise RuntimeError(f"Verify failed: {why}")
        return ref
    
    users = load_users()
    rec = update_user(users, telegram_id, fields)
    save_users(users)
    return rec

def grant_credits(telegram_id: int, amount: int) -> Tuple[Dict[str, Any], int]:
    """Grant credits dengan verifikasi"""
    amt = int(amount)
    if amt < 0:
        raise ValueError("credits harus >= 0")
    
    if DB_MODE == "supabase" and DB_READY:
        cur = sb_get(telegram_id) or {"credits": 0}
        total = int(cur.get("credits", 0)) + amt
        sb_upsert(telegram_id, credits=total)
        ref = sb_get(telegram_id) or {}
        if int(ref.get("credits", 0)) != total:
            raise RuntimeError(f"Verify failed: credits mismatch (want={total}, got={ref.get('credits')})")
        return ref, total
    
    # local
    users = load_users()
    rec = get_user_dict(users, telegram_id)
    total = int(rec.get("credits", 0) if rec else 0) + amt
    rec = update_user(users, telegram_id, {"credits": total})
    save_users(users)
    return rec, total

def ban_user(telegram_id: int) -> Dict[str, Any]:
    if DB_MODE == "supabase" and DB_READY:
        return sb_upsert(telegram_id, banned=True, is_premium=False, premium_until=None)
    # local
    users = load_users()
    rec = update_user(users, telegram_id, {"banned": True, "is_premium": False, "premium_until": None})
    save_users(users)
    return rec

def unban_user(telegram_id: int) -> Dict[str, Any]:
    if DB_MODE == "supabase" and DB_READY:
        return sb_upsert(telegram_id, banned=False)
    # local
    users = load_users()
    rec = update_user(users, telegram_id, {"banned": False})
    save_users(users)
    return rec

def add_premium(telegram_id: int, duration: str) -> Tuple[Dict[str, Any], str]:
    duration = str(duration).strip().lower()
    if duration == "lifetime":
        fields = {"banned": False, "is_premium": True, "premium_until": None}
        msg = f"✅ Premium lifetime diaktifkan untuk {telegram_id}."
    else:
        if not duration.isdigit() or int(duration) < 1:
            raise ValueError("days harus angka >= 1 atau 'lifetime'")
        iso = _iso_in_days(int(duration))
        fields = {"banned": False, "is_premium": True, "premium_until": iso}
        msg = f"✅ Premium {duration} hari diaktifkan untuk {telegram_id} sampai {iso}."
    
    if DB_MODE == "supabase" and DB_READY:
        rec = sb_upsert(telegram_id, **fields)
        return rec, msg
    # local
    users = load_users()
    rec = update_user(users, telegram_id, fields)
    save_users(users)
    return rec, msg

def remove_premium(telegram_id: int) -> Dict[str, Any]:
    if DB_MODE == "supabase" and DB_READY:
        return sb_update(telegram_id, is_premium=False, premium_until=None)
    users = load_users()
    rec = update_user(users, telegram_id, {"is_premium": False, "premium_until": None})
    save_users(users)
    return rec

def grant_credits(telegram_id: int, amount: int) -> Tuple[Dict[str, Any], int]:
    amt = int(amount)
    if amt < 0:
        raise ValueError("credits harus >= 0")
    
    if DB_MODE == "supabase" and DB_READY:
        rec = sb_get(telegram_id) or {}
        current = int(rec.get("credits", 0))
        total = current + amt
        out = sb_upsert(telegram_id, credits=total)
        return out, total
    # local
    users = load_users()
    rec = get_user(users, telegram_id)
    total = int(rec.get("credits", 0)) + amt
    rec = update_user(users, telegram_id, {"credits": total})
    save_users(users)
    return rec, total

def get_user_info(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get user information"""
    if DB_MODE == "supabase" and DB_READY:
        return sb_get(telegram_id)
    # local
    users = load_users()
    return get_user(users, telegram_id)

def check_user_banned(telegram_id: int) -> bool:
    """Check if user is banned"""
    user = get_user_info(telegram_id)
    return user.get("banned", False) if user else False

def check_user_premium(telegram_id: int) -> bool:
    """Check if user has premium access"""
    user = get_user_info(telegram_id)
    if not user:
        return False
    
    is_premium = user.get("is_premium", False)
    premium_until = user.get("premium_until")
    
    if not is_premium:
        return False
    
    # Check if premium is expired
    if premium_until is None:  # Lifetime
        return True
    
    try:
        expiry = datetime.fromisoformat(premium_until.replace('Z', '+00:00'))
        return datetime.now(timezone.utc) < expiry
    except:
        return False
