
import os, time, json, requests
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timezone

# ---------- ENV (dengan alias guard) ----------
def _getenv(name: str, *aliases: str) -> str:
    for k in (name, *aliases):
        v = os.getenv(k)
        if v and v.strip():
            return v.strip()
    return ""

def _env() -> Tuple[str, str, str]:
    # dukung alias salah ketik: SUPABASEURL / SUPABASESERVICEKEY
    url = _getenv("SUPABASE_URL", "SUPABASEURL").rstrip("/")
    key = _getenv("SUPABASE_SERVICE_KEY", "SUPABASESERVICEKEY")
    rest = f"{url}/rest/v1" if url else ""
    return url, key, rest

def _headers(key: str, prefer: Optional[str] = None) -> Dict[str, str]:
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h

def _retry(fn, retries=3, base=0.6):
    last = None
    for i in range(retries):
        try:
            return fn()
        except Exception as e:
            last = e
            time.sleep(base * (2 ** i))
    raise last

# ---------- Health ----------
def health(table: str = "users") -> Tuple[bool, str]:
    def _once():
        url, key, rest = _env()
        if not url: raise RuntimeError("ENV SUPABASE_URL missing (atau SUPABASEURL)")
        if not key: raise RuntimeError("ENV SUPABASE_SERVICE_KEY missing (atau SUPABASESERVICEKEY)")
        r0 = requests.get(rest, headers=_headers(key), timeout=8)
        r1 = requests.get(f"{rest}/{table}", headers=_headers(key),
                          params={"select":"telegram_id","limit":"1"}, timeout=12)
        ok = (r0.status_code in (200,401,404)) and (r1.status_code in (200,206))
        return ok, f"root={getattr(r0,'status_code',None)} table={getattr(r1,'status_code',None)} body={r1.text[:160]}"
    try:
        return _retry(_once, retries=2)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

# ---------- CRUD ----------
def get_user_by_tid(telegram_id: int, table: str = "users") -> Optional[Dict[str, Any]]:
    def _once():
        url, key, rest = _env()
        if not url or not key: raise RuntimeError("Supabase env missing")
        r = requests.get(
            f"{rest}/{table}",
            headers=_headers(key),
            params={
                "select":"telegram_id,is_premium,premium_until,credits,banned,updated_at",
                "telegram_id": f"eq.{int(telegram_id)}"
            },
            timeout=15
        )
        if r.status_code not in (200,206):
            raise RuntimeError(f"GET {table} {r.status_code} {r.text}")
        data = r.json()
        return data[0] if isinstance(data, list) and data else None
    return _retry(_once, retries=3)

def upsert_user_tid(telegram_id: int, table: str = "users", **fields) -> Dict[str, Any]:
    def _once():
        url, key, rest = _env()
        if not url or not key: raise RuntimeError("Supabase env missing")
        payload = [ { "telegram_id": int(telegram_id), **fields } ]  # JSON LIST!
        r = requests.post(
            f"{rest}/{table}",
            headers=_headers(key, "resolution=merge-duplicates,return=representation"),
            params={"on_conflict": "telegram_id"},
            json=payload,
            timeout=20
        )
        # log bantu jika gagal
        if r.status_code == 429:
            raise RuntimeError(f"UPSERT 429 (rate-limited): {r.text}")
        if r.status_code not in (200,201):
            raise RuntimeError(f"UPSERT {table} failed: {r.status_code} {r.text}")
        try:
            data = r.json()
        except Exception:
            data = None
        return data[0] if isinstance(data, list) and data else {"telegram_id": telegram_id, **fields}
    return _retry(_once, retries=3)

def update_user_tid(telegram_id: int, table: str = "users", **fields) -> Dict[str, Any]:
    def _once():
        url, key, rest = _env()
        if not url or not key: raise RuntimeError("Supabase env missing")
        r = requests.patch(
            f"{rest}/{table}",
            headers=_headers(key, "return=representation"),
            params={"telegram_id": f"eq.{int(telegram_id)}"},
            json=fields,
            timeout=20
        )
        if r.status_code == 429:
            raise RuntimeError(f"UPDATE 429 (rate-limited): {r.text}")
        if r.status_code not in (200,204):
            raise RuntimeError(f"UPDATE {table} failed: {r.status_code} {r.text}")
        return r.json()[0] if (r.status_code == 200 and r.text) else {"telegram_id": telegram_id, **fields}
    return _retry(_once, retries=3)

def sb_list_users(params: dict, columns: str = "telegram_id,is_premium,premium_until,banned,credits,updated_at",
                  table: str = "users", limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
    def _once():
        url, key, rest = _env()
        if not url or not key: raise RuntimeError("Supabase env missing")
        q = {"select": columns, "limit": str(limit), "offset": str(offset)}
        q.update(params or {})
        r = requests.get(f"{rest}/{table}", headers=_headers(key), params=q, timeout=20)
        if r.status_code not in (200,206):
            raise RuntimeError(f"LIST {table} {r.status_code} {r.text}")
        return r.json()
    return _retry(_once)

# ---------- Write-Probe E2E ----------
def write_probe(table: str = "users") -> Dict[str, Any]:
    """
    Tulis→Baca→Hapus untuk verifikasi jalur tulis. Menggunakan service key.
    """
    url, key, rest = _env()
    if not url or not key: raise RuntimeError("Supabase env missing")
    probe_id = 999999991
    # upsert
    r1 = requests.post(
        f"{rest}/{table}",
        headers=_headers(key, "resolution=merge-duplicates,return=representation"),
        params={"on_conflict": "telegram_id"},
        json=[{"telegram_id": probe_id, "is_premium": True, "premium_until": None, "banned": False}],
        timeout=20
    )
    # read
    r2 = requests.get(
        f"{rest}/{table}",
        headers=_headers(key),
        params={"select":"telegram_id,is_premium,premium_until,banned", "telegram_id": f"eq.{probe_id}"},
        timeout=15
    )
    # delete
    r3 = requests.delete(
        f"{rest}/{table}",
        headers=_headers(key, "return=representation"),
        params={"telegram_id": f"eq.{probe_id}"},
        timeout=20
    )
    return {
        "upsert": {"code": r1.status_code, "body": r1.text[:160]},
        "get": {"code": r2.status_code, "body": r2.text[:160]},
        "delete": {"code": r3.status_code, "body": r3.text[:160]},
    }
