
import os
import time
import requests
from typing import Optional, Dict, Any, List, Tuple

def _env():
    """Get Supabase environment variables"""
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    key = (os.getenv("SUPABASE_SERVICE_KEY") or "").strip()
    rest = f"{url}/rest/v1" if url else ""
    return url, key, rest

def _headers(key: str, prefer: str | None = None):
    """Generate headers for Supabase requests"""
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h

def health() -> Tuple[bool, str]:
    """Check Supabase connection health"""
    try:
        url, key, rest = _env()
        if not url or not key:
            return False, "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY"
        
        r = requests.get(f"{rest}/users", headers=_headers(key), params={"limit": "1"}, timeout=10)
        
        if r.status_code == 200:
            return True, f"Connected to {url} (service_role)"
        else:
            return False, f"HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def sb_list_users(filters: Dict[str, str] = None, table: str = "users") -> List[Dict[str, Any]]:
    """List users with optional filters"""
    try:
        url, key, rest = _env()
        if not url or not key:
            raise RuntimeError("Supabase env missing")
        
        params = filters or {}
        r = requests.get(f"{rest}/{table}", headers=_headers(key), params=params, timeout=15)
        
        if r.status_code == 200:
            return r.json()
        else:
            raise RuntimeError(f"List users failed: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Error listing users: {e}")
        return []

def get_user_by_tid(telegram_id: int, table: str = "users") -> Optional[Dict[str, Any]]:
    """Get user by telegram_id"""
    try:
        url, key, rest = _env()
        if not url or not key:
            return None
        
        r = requests.get(
            f"{rest}/{table}",
            headers=_headers(key),
            params={"telegram_id": f"eq.{int(telegram_id)}", "limit": "1"},
            timeout=10
        )
        
        if r.status_code == 200:
            data = r.json()
            return data[0] if data else None
        else:
            return None
    except Exception as e:
        print(f"Error getting user {telegram_id}: {e}")
        return None

def upsert_user_tid(telegram_id: int, table: str = "users", **fields) -> Dict[str, Any]:
    """Upsert user by telegram_id with conflict resolution"""
    url, key, rest = _env()
    if not url or not key:
        raise RuntimeError("Supabase env missing")
    
    payload = {"telegram_id": int(telegram_id), **fields}
    
    print(f"🔄 Upserting user {telegram_id} with data: {payload}")
    
    # Try UPDATE first
    update_r = requests.patch(
        f"{rest}/{table}",
        headers=_headers(key, "return=representation"),
        params={"telegram_id": f"eq.{int(telegram_id)}"},
        json=fields,
        timeout=20
    )
    
    print(f"📝 UPDATE response: {update_r.status_code} - {update_r.text[:200]}")
    
    if update_r.status_code == 200 and update_r.text.strip() != "[]":
        # User exists and was updated
        try:
            data = update_r.json()
            return data[0] if isinstance(data, list) and data else payload
        except:
            return payload
    
    # User doesn't exist, try INSERT
    print(f"🔄 User not found, inserting new user {telegram_id}")
    insert_r = requests.post(
        f"{rest}/{table}",
        headers=_headers(key, "return=representation"),
        json=payload,
        timeout=20
    )
    
    print(f"📝 INSERT response: {insert_r.status_code} - {insert_r.text[:200]}")
    
    if insert_r.status_code not in (200, 201):
        # Final fallback: try upsert with conflict resolution
        print(f"🔄 Trying upsert with conflict resolution for user {telegram_id}")
        upsert_r = requests.post(
            f"{rest}/{table}",
            headers=_headers(key, "resolution=merge-duplicates,return=representation"),
            params={"on_conflict": "telegram_id"},
            json=[payload],
            timeout=20
        )
        
        print(f"📝 UPSERT response: {upsert_r.status_code} - {upsert_r.text[:200]}")
        
        if upsert_r.status_code not in (200, 201):
            raise RuntimeError(f"All operations failed. Last error: {upsert_r.status_code} {upsert_r.text}")
        
        try:
            data = upsert_r.json()
            return data[0] if isinstance(data, list) and data else payload
        except:
            return payload
    
    try:
        data = insert_r.json()
        return data[0] if isinstance(data, list) and data else payload
    except:
        return payload

def update_user_tid(telegram_id: int, table: str = "users", **fields) -> Dict[str, Any]:
    """Update user by telegram_id"""
    url, key, rest = _env()
    if not url or not key:
        raise RuntimeError("Supabase env missing")
    
    r = requests.patch(
        f"{rest}/{table}",
        headers=_headers(key, "return=representation"),
        params={"telegram_id": f"eq.{int(telegram_id)}"},
        json=fields,
        timeout=20
    )
    
    # PostgREST returns 204 if no rows changed - treat as success
    if r.status_code not in (200, 204):
        raise RuntimeError(f"UPDATE failed: {r.status_code} {r.text}")
    
    return r.json()[0] if (r.status_code == 200 and r.text) else {"telegram_id": telegram_id, **fields}

def sb_is_premium_user(telegram_id: int) -> bool:
    """Check if user is premium (lifetime or active subscription)"""
    from datetime import datetime, timezone
    
    user = get_user_by_tid(telegram_id)
    if not user:
        return False
    
    # Check banned status
    if user.get("banned", False):
        return False
    
    # Check premium status
    if not user.get("is_premium", False):
        return False
    
    # Lifetime premium (premium_until is NULL)
    if user.get("premium_until") is None:
        return True
    
    # Time-based premium
    try:
        premium_until = datetime.fromisoformat(user["premium_until"].replace('Z', '+00:00'))
        return premium_until >= datetime.now(timezone.utc)
    except Exception:
        return False

def add_credits(telegram_id: int, amount: int) -> int:
    """Add credits to user and return new total"""
    current_user = get_user_by_tid(telegram_id)
    current_credits = current_user.get("credits", 0) if current_user else 0
    new_total = current_credits + amount
    
    upsert_user_tid(telegram_id, credits=new_total)
    return new_total

def deduct_credits(telegram_id: int, amount: int) -> bool:
    """Deduct credits from user, return success status"""
    current_user = get_user_by_tid(telegram_id)
    if not current_user:
        return False
    
    current_credits = current_user.get("credits", 0)
    if current_credits < amount:
        return False
    
    new_total = current_credits - amount
    upsert_user_tid(telegram_id, credits=new_total)
    return True
