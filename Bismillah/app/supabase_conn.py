# app/supabase_conn.py
import os
import requests
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

# Alias for SUPABASE_URL and SUPABASE_SERVICE_KEY for easier use in functions
SB_URL = SUPABASE_URL
SB_KEY = SUPABASE_SERVICE_KEY
SB_REST = f"{SB_URL}/rest/v1"  # Base URL for REST API

HEADERS = {
    "apikey": SB_KEY,
    "Authorization": f"Bearer {SB_KEY}",
    "Content-Type": "application/json"
}

def health() -> Tuple[bool, str]:
    """Check Supabase connection health"""
    try:
        if not SB_URL or not SB_KEY:
            return False, "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY"

        # Test connection dengan timeout singkat
        response = requests.get(f"{SB_REST}/users?limit=1", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return True, f"Connected to {SB_URL[:30]}..."
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def get_user_by_tid(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get user by telegram ID from Supabase"""
    try:
        url = f"{SB_REST}/users?telegram_id=eq.{telegram_id}&select=*"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data[0] if data else None
        return None
    except Exception as e:
        print(f"Error getting user from Supabase: {e}")
        return None

def upsert_user_tid(telegram_id: int, table_name: str = "users", **fields) -> Dict[str, Any]:
    """UPSERT user berdasarkan telegram_id dengan on_conflict"""
    if not SB_URL or not SB_KEY:
        raise RuntimeError("Supabase env missing")

    payload = [{"telegram_id": telegram_id, **fields}]
    hdrs = {**HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"}
    params = {"on_conflict": "telegram_id"}  # PENTING: UPSERT berdasarkan telegram_id

    response = requests.post(f"{SB_REST}/{table_name}", headers=hdrs, params=params, json=payload, timeout=20)

    if response.status_code not in (200, 201):
        raise RuntimeError(f"UPSERT {table_name} failed: {response.status_code} {response.text}")

    try:
        data = response.json()
    except Exception:
        data = None

    if isinstance(data, list) and data:
        return data[0]
    return data or {"telegram_id": telegram_id, **fields}

def update_user_tid(telegram_id: int, table_name: str = "users", **fields) -> Dict[str, Any]:
    """UPDATE user berdasarkan telegram_id"""
    if not SB_URL or not SB_KEY:
        raise RuntimeError("Supabase env missing")

    hdrs = {**HEADERS, "Prefer": "return=representation"}
    params = {"telegram_id": f"eq.{telegram_id}"}

    response = requests.patch(f"{SB_REST}/{table_name}", headers=hdrs, params=params, json=fields, timeout=20)

    if response.status_code not in (200, 204):
        raise RuntimeError(f"UPDATE {table_name} failed: {response.status_code} {response.text}")

    return response.json()[0] if response.status_code == 200 and response.text else {"telegram_id": telegram_id, **fields}