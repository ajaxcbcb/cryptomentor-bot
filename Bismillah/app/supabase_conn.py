
# app/supabase_conn.py
import os
import requests
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_KEY = <REDACTED_SUPABASE_KEY>

def _headers():
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }

def health() -> Tuple[bool, str]:
    """Check Supabase connection health"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return False, "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY"
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?select=count&limit=1"
        response = requests.get(url, headers=_headers(), timeout=10)
        if response.status_code == 200:
            return True, "Connected"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def get_user_by_tid(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get user by telegram ID from Supabase"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?telegram_id=eq.{telegram_id}&select=*"
        response = requests.get(url, headers=_headers(), timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data[0] if data else None
        return None
    except Exception as e:
        print(f"Error getting user from Supabase: {e}")
        return None

def upsert_user_tid(telegram_id: int, **fields) -> Dict[str, Any]:
    """Upsert user in Supabase"""
    try:
        # Prepare data
        data = {
            "telegram_id": telegram_id,
            "updated_at": datetime.now().isoformat(),
            **fields
        }
        
        url = f"{SUPABASE_URL}/rest/v1/users"
        headers = {**_headers(), "Prefer": "resolution=merge-duplicates"}
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            return {"success": True, "data": data}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_user_tid(telegram_id: int, **fields) -> Dict[str, Any]:
    """Update user in Supabase"""
    try:
        data = {
            "updated_at": datetime.now().isoformat(),
            **fields
        }
        
        url = f"{SUPABASE_URL}/rest/v1/users?telegram_id=eq.{telegram_id}"
        response = requests.patch(url, json=data, headers=_headers(), timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "data": data}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
