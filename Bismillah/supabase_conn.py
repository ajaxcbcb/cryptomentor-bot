
import os
import requests
from typing import Optional, Dict, Any

SB_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SB_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
SB_REST = f"{SB_URL}/rest/v1" if SB_URL else ""

HEADERS = {
    "apikey": SB_KEY,
    "Authorization": f"Bearer {SB_KEY}",
    "Content-Type": "application/json",
}

def health() -> tuple[bool, str]:
    """Check Supabase connection health"""
    if not SB_URL: 
        return False, "SUPABASE_URL belum diset"
    if not SB_KEY: 
        return False, "SUPABASE_SERVICE_KEY belum diset"
    
    try:
        # Root responsiveness check
        r = requests.get(SB_REST, headers=HEADERS, timeout=8)
        root_ok = r.status_code in (200, 401, 404)
        
        # Table check (users)
        r2 = requests.get(f"{SB_REST}/users",
                          headers=HEADERS,
                          params={"select": "telegram_id", "limit": "1"},
                          timeout=8)
        table_ok = r2.status_code in (200, 206)
        
        if root_ok and table_ok:
            return True, "CONNECTED"
        
        return False, f"root_ok={root_ok}, table_status={r2.status_code}, body={r2.text[:200]}"
    
    except Exception as e:
        return False, str(e)

def get_user_by_tid(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get user by telegram ID"""
    r = requests.get(f"{SB_REST}/users",
                     headers=HEADERS,
                     params={"select": "telegram_id,is_premium,premium_until,credits,banned,updated_at",
                             "telegram_id": f"eq.{telegram_id}"},
                     timeout=15)
    
    if r.status_code not in (200, 206):
        raise RuntimeError(f"GET users failed: {r.status_code} {r.text}")
    
    arr = r.json()
    return arr[0] if arr else None

def upsert_user_tid(telegram_id: int, **fields) -> Dict[str, Any]:
    """Upsert user by telegram ID"""
    payload = [{"telegram_id": telegram_id, **fields}]
    hdrs = {**HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"}
    
    r = requests.post(f"{SB_REST}/users", headers=hdrs, json=payload, timeout=20)
    
    if r.status_code not in (200, 201):
        raise RuntimeError(f"UPSERT users failed: {r.status_code} {r.text}")
    
    data = r.json()
    return data[0] if isinstance(data, list) and data else data

def update_user_tid(telegram_id: int, **fields) -> Dict[str, Any]:
    """Update user by telegram ID"""
    hdrs = {**HEADERS, "Prefer": "return=representation"}
    
    r = requests.patch(f"{SB_REST}/users",
                       headers=hdrs,
                       params={"telegram_id": f"eq.{telegram_id}"},
                       json=fields, timeout=20)
    
    if r.status_code not in (200, 204):
        raise RuntimeError(f"UPDATE users failed: {r.status_code} {r.text}")
    
    return r.json()[0] if r.status_code == 200 and r.text else {"telegram_id": telegram_id, **fields}
