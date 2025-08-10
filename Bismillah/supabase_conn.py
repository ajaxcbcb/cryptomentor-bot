
import os
import requests
from typing import Optional, Dict, Any, Tuple

def _clean_url(u: str) -> str:
    return (u or "").strip().rstrip("/")

SB_URL = _clean_url(os.getenv("SUPABASE_URL"))
SB_KEY = (os.getenv("SUPABASE_SERVICE_KEY") or "").strip()
SB_REST = f"{SB_URL}/rest/v1" if SB_URL else ""

HEADERS = {
    "apikey": SB_KEY,
    "Authorization": f"Bearer {SB_KEY}",
    "Content-Type": "application/json",
}

def env_ok() -> Tuple[bool, str]:
    if not SB_URL:
        return False, "SUPABASE_URL belum diset"
    if "supabase.co" not in SB_URL:
        return False, f"SUPABASE_URL tidak valid: {SB_URL}"
    if not SB_KEY:
        return False, "SUPABASE_SERVICE_KEY belum diset"
    # service key biasanya sangat panjang & berakhiran '...'
    return True, "OK"

def health(table_name: str = "users") -> Tuple[bool, str]:
    ok, info = env_ok()
    if not ok:
        return False, info
    try:
        # Cek root responsif (boleh 401/404 asalkan hidup)
        r = requests.get(SB_REST, headers=HEADERS, timeout=8)
        root_ok = r.status_code in (200, 401, 404)

        # Cek akses tabel spesifik (hindari select=*)
        params = {"select": "telegram_id", "limit": "1"}
        r2 = requests.get(f"{SB_REST}/{table_name}", headers=HEADERS, params=params, timeout=10)
        table_ok = r2.status_code in (200, 206)

        if root_ok and table_ok:
            return True, "CONNECTED"
        # kumpulkan detail error yang membantu debugging
        detail = f"root_ok={root_ok}, table_status={r2.status_code}, body={r2.text[:240]}"
        return False, detail
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def get_user_by_tid(telegram_id: int, table_name: str = "users") -> Optional[Dict[str, Any]]:
    ok, info = env_ok()
    if not ok:
        raise RuntimeError(info)
    params = {
        "select": "id,telegram_id,first_name,last_name,username,is_premium,premium_until,credits,banned,created_at,updated_at",
        "telegram_id": f"eq.{telegram_id}",
    }
    r = requests.get(f"{SB_REST}/{table_name}", headers=HEADERS, params=params, timeout=15)
    if r.status_code not in (200, 206):
        raise RuntimeError(f"GET {table_name} failed: {r.status_code} {r.text}")
    data = r.json()
    return data[0] if data else None

def upsert_user_tid(telegram_id: int, table_name: str = "users", **fields) -> Dict[str, Any]:
    ok, info = env_ok()
    if not ok:
        raise RuntimeError(info)
    payload = [{ "telegram_id": telegram_id, **fields }]
    hdrs = {**HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"}
    r = requests.post(f"{SB_REST}/{table_name}", headers=hdrs, json=payload, timeout=20)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"UPSERT {table_name} failed: {r.status_code} {r.text}")
    data = r.json()
    return data[0] if isinstance(data, list) and data else data

def update_user_tid(telegram_id: int, table_name: str = "users", **fields) -> Dict[str, Any]:
    ok, info = env_ok()
    if not ok:
        raise RuntimeError(info)
    hdrs = {**HEADERS, "Prefer": "return=representation"}
    params = {"telegram_id": f"eq.{telegram_id}"}
    r = requests.patch(f"{SB_REST}/{table_name}", headers=hdrs, params=params, json=fields, timeout=20)
    if r.status_code not in (200, 204):
        raise RuntimeError(f"UPDATE {table_name} failed: {r.status_code} {r.text}")
    return r.json()[0] if r.status_code == 200 and r.text else {"telegram_id": telegram_id, **fields}
