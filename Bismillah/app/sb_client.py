
# Bismillah/app/sb_client.py
# Supabase REST minimal client + adapter instance `supabase_client`
# agar import `from app.sb_client import supabase_client` tidak error.

import os, time, requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

REQ_TIMEOUT = 15

# ---------- core helpers ----------
def _env() -> Tuple[str, str, str]:
    url = (os.getenv("SUPABASE_URL") or os.getenv("SUPABASEURL") or "").strip().rstrip("/")
    key = (os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASESERVICEKEY") or "").strip()
    if not url or not key:
        raise RuntimeError("Supabase env missing (SUPABASE_URL / SUPABASE_SERVICE_KEY)")
    rest = f"{url}/rest/v1"
    return url, key, rest

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
            last = e; time.sleep(base*(2**i))
    raise last

# ---------- raw ops (fungsi level modul, dipakai juga oleh adapter) ----------
def health() -> Tuple[bool, str]:
    url, key, rest = _env()
    def _once():
        # root + table ping
        r0 = requests.get(rest, headers=_headers(key), timeout=REQ_TIMEOUT)
        r1 = requests.get(f"{rest}/users", headers=_headers(key),
                          params={"select":"telegram_id","limit":"1"}, timeout=REQ_TIMEOUT)
        ok = (r0.status_code in (200,401,404)) and (r1.status_code in (200,206))
        return ok, f"root={r0.status_code} users={r1.status_code}"
    return _retry(_once, n=2)

def project_url() -> str:
    url, _, _ = _env()
    return url

def get_table(table: str, params: Dict[str, Any] | None = None, prefer: str | None = None):
    url, key, rest = _env()
    def _once():
        r = requests.get(f"{rest}/{table}", headers=_headers(key, prefer),
                         params=params or {}, timeout=REQ_TIMEOUT)
        if r.status_code not in (200,206):
            raise RuntimeError(f"GET {table} {r.status_code} {r.text}")
        return r.json()
    return _retry(_once)

def get_view(view: str):
    return get_table(view, params={"select":"*"})

def upsert_users(rows: List[Dict[str, Any]]):
    url, key, rest = _env()
    def _once():
        r = requests.post(f"{rest}/users",
            headers=_headers(key, "resolution=merge-duplicates,return=representation"),
            params={"on_conflict":"telegram_id"},
            json=rows, timeout=REQ_TIMEOUT)
        if r.status_code not in (200,201):
            raise RuntimeError(f"UPSERT users {r.status_code} {r.text}")
        return r.json() if r.text else []
    return _retry(_once)

def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    url, key, rest = _env()
    def _once():
        r = requests.get(f"{rest}/users",
            headers=_headers(key),
            params={
                "select":"telegram_id,is_premium,premium_until,banned,credits,updated_at",
                "telegram_id": f"eq.{int(telegram_id)}",
                "limit":"1"
            }, timeout=REQ_TIMEOUT)
        if r.status_code not in (200,206):
            raise RuntimeError(f"GET users {r.status_code} {r.text}")
        data = r.json()
        return data[0] if data else None
    return _retry(_once)

def upsert_user(telegram_id: int, **fields) -> Dict[str, Any]:
    return upsert_users([{ "telegram_id": int(telegram_id), **fields }])[0]

def list_premium_active(limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
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

def write_probe():
    """Upsert → Get → Delete (opsional delete) untuk uji jalur tulis."""
    url, key, rest = _env()
    pid = 999999221
    r1 = requests.post(f"{rest}/users",
        headers=_headers(key, "resolution=merge-duplicates,return=representation"),
        params={"on_conflict":"telegram_id"},
        json=[{"telegram_id": pid, "is_premium": True, "premium_until": None, "banned": False}],
        timeout=REQ_TIMEOUT)
    r2 = requests.get(f"{rest}/users",
        headers=_headers(key),
        params={"select":"telegram_id,is_premium,premium_until,banned","telegram_id":f"eq.{pid}","limit":"1"},
        timeout=REQ_TIMEOUT)
    # hapus jika allowed (kalau gagal, biarkan saja; ini debug)
    try:
        r3 = requests.delete(f"{rest}/users",
            headers=_headers(key, "return=representation"),
            params={"telegram_id":f"eq.{pid}"},
            timeout=REQ_TIMEOUT)
        del_res = {"code": r3.status_code, "body": r3.text[:140]}
    except Exception as e:
        del_res = {"error": str(e)}
    return {
        "upsert": {"code": r1.status_code, "body": r1.text[:140]},
        "get":    {"code": r2.status_code, "body": r2.text[:140]},
        "delete": del_res
    }

def is_premium(telegram_id: int) -> bool:
    u = get_user(telegram_id) or {}
    if u.get("banned"): return False
    if not u.get("is_premium"): return False
    pu = u.get("premium_until")
    if pu is None:  # lifetime
        return True
    try:
        return datetime.fromisoformat(pu) >= datetime.now(timezone.utc)
    except Exception:
        return False

# ---------- adapter class & INSTANCE ----------
class _SupabaseClientAdapter:
    """Adapter dengan nama & method yang umum dipakai oleh kode lain."""
    # health & whereami
    def health(self) -> Tuple[bool, str]:
        return health()
    def project_url(self) -> str:
        return project_url()

    # read
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        return get_user(telegram_id)
    def get_view(self, name: str):
        return get_view(name)
    def get_table(self, table: str, params: Dict[str, Any] | None = None):
        return get_table(table, params=params)

    # write
    def upsert_user(self, telegram_id: int, **fields) -> Dict[str, Any]:
        return upsert_user(telegram_id, **fields)
    def upsert_users(self, rows: List[Dict[str, Any]]):
        return upsert_users(rows)

    # premium helpers
    def is_premium(self, telegram_id: int) -> bool:
        return is_premium(telegram_id)
    def list_premium_active(self, limit: int = 1000, offset: int = 0):
        return list_premium_active(limit=limit, offset=offset)

    # debug
    def write_probe(self):
        return write_probe()

# Inilah objek yang dicari oleh import lama:
supabase_client = _SupabaseClientAdapter()
