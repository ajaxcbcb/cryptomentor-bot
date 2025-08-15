# /home/runner/workspace/Bismillah/supabase_client.py
# Facade yang mengekspor "supabase_service" agar import lama tetap bekerja,
# namun implementasi koneksi memakai REST Supabase yang stabil (requests).
import os, time, requests
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple

REQ_TIMEOUT = 15

def _env() -> Tuple[str, str, str]:
    # dukung alias penulisan env yang sering salah
    url = (os.getenv("SUPABASE_URL") or os.getenv("SUPABASEURL") or "").strip().rstrip("/")
    key = (os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASESERVICEKEY") or "").strip()
    if not url or not key:
        raise RuntimeError("Supabase env missing (SUPABASE_URL / SUPABASE_SERVICE_KEY)")
    return url, key, f"{url}/rest/v1"

def _headers(key: str, prefer: Optional[str] = None) -> Dict[str, str]:
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if prefer: h["Prefer"] = prefer
    return h

def _retry(fn, n=3, base=0.6):
    last = None
    for i in range(n):
        try:
            return fn()
        except Exception as e:
            last = e
            time.sleep(base * (2 ** i))
    raise last

class SupabaseService:
    # ----- Health -----
    def health(self) -> Tuple[bool, str]:
        url, key, rest = _env()
        def _once():
            r0 = requests.get(rest, headers=_headers(key), timeout=REQ_TIMEOUT)
            r1 = requests.get(f"{rest}/users", headers=_headers(key),
                              params={"select":"telegram_id","limit":"1"}, timeout=REQ_TIMEOUT)
            ok = (r0.status_code in (200,401,404)) and (r1.status_code in (200,206))
            return ok, f"root={r0.status_code} users={r1.status_code}"
        return _retry(_once, n=2)

    # ----- Read -----
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        url, key, rest = _env()
        def _once():
            r = requests.get(f"{rest}/users",
                headers=_headers(key),
                params={"select":"telegram_id,is_premium,premium_until,banned,credits,updated_at",
                        "telegram_id": f"eq.{int(telegram_id)}",
                        "limit":"1"},
                timeout=REQ_TIMEOUT)
            if r.status_code not in (200,206):
                raise RuntimeError(f"GET users {r.status_code} {r.text}")
            data = r.json()
            return data[0] if data else None
        return _retry(_once)

    # ----- Upsert (idempoten) -----
    def upsert_user(self, telegram_id: int, **fields) -> Dict[str, Any]:
        url, key, rest = _env()
        def _once():
            payload = [{ "telegram_id": int(telegram_id), **fields }]
            r = requests.post(f"{rest}/users",
                headers=_headers(key, "resolution=merge-duplicates,return=representation"),
                params={"on_conflict":"telegram_id"},
                json=payload, timeout=REQ_TIMEOUT)
            if r.status_code == 429:
                raise RuntimeError(f"UPSERT 429 {r.text}")
            if r.status_code not in (200,201):
                raise RuntimeError(f"UPSERT users {r.status_code} {r.text}")
            return r.json()[0] if r.text else {"telegram_id": telegram_id, **fields}
        return _retry(_once)

    # ----- Premium check (lifetime/aktif & tidak banned) -----
    def is_premium(self, telegram_id: int) -> bool:
        u = self.get_user(telegram_id) or {}
        if u.get("banned"): return False
        if not u.get("is_premium"): return False
        pu = u.get("premium_until")
        if pu is None:  # lifetime
            return True
        try:
            # now() UTC
            return datetime.fromisoformat(pu) >= datetime.now(timezone.utc)
        except Exception:
            return False

    # ----- Daftar premium aktif (untuk broadcast/diagnostik) -----
    def list_premium_active(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        url, key, rest = _env()
        nowiso = datetime.now(timezone.utc).isoformat()
        def _once():
            r = requests.get(f"{rest}/users",
                headers=_headers(key),
                params={
                    "select":"telegram_id,is_premium,premium_until,banned",
                    "is_premium":"eq.true",
                    "banned":"eq.false",
                    "or": f"(premium_until.is.null,premium_until.gte.{nowiso})",
                    "limit": str(limit),
                    "offset": str(offset),
                },
                timeout=REQ_TIMEOUT)
            if r.status_code not in (200,206):
                raise RuntimeError(f"LIST premium {r.status_code} {r.text}")
            return r.json()
        return _retry(_once)

# inilah objek yang diimport oleh kode lama
supabase_service = SupabaseService()

# Legacy compatibility - export the functions that existing code might use
def validate_supabase_connection():
    """Legacy function for backward compatibility"""
    try:
        ok, _ = supabase_service.health()
        return ok
    except:
        return False

def get_live_user_count():
    """Legacy function for backward compatibility"""
    try:
        url, key, rest = _env()
        r = requests.get(f"{rest}/users", headers=_headers(key), 
                        params={"select":"count", "limit":"0"}, timeout=REQ_TIMEOUT)
        if r.status_code in (200, 206):
            return len(r.json()) if r.json() else 0
    except:
        pass
    return 0

# Create supabase object for backward compatibility
class LegacySupabase:
    def __init__(self):
        self.service = supabase_service

    def health(self):
        return self.service.health()

supabase = LegacySupabase()