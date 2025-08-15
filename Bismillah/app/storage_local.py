
# app/storage_local.py
import os
import json
import threading
from typing import Dict, Any, Optional
from datetime import datetime

_LOCK = threading.Lock()
_DATA_DIR = os.getenv("DATA_DIR", "data")
_USERS_PATH = os.path.join(_DATA_DIR, "users_local.json")

def _ensure_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)

def load_users() -> Dict[str, Any]:
    """Load users from local JSON file"""
    with _LOCK:
        _ensure_dir()
        if not os.path.exists(_USERS_PATH):
            return {}
        try:
            with open(_USERS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading local users: {e}")
            return {}

def save_users(users: Dict[str, Any]) -> None:
    """Save users to local JSON file"""
    with _LOCK:
        _ensure_dir()
        tmp = _USERS_PATH + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            os.replace(tmp, _USERS_PATH)
        except Exception as e:
            print(f"Error saving local users: {e}")

def get_user(users: Dict[str, Any], telegram_id: int) -> Dict[str, Any]:
    """Get user from users dict"""
    user_key = str(telegram_id)
    if user_key not in users:
        # Create default user
        users[user_key] = {
            "telegram_id": telegram_id,
            "credits": 100,
            "is_premium": False,
            "premium_until": None,
            "banned": False,
            "created_at": datetime.now().isoformat()
        }
    return users[user_key]

def update_user(users: Dict[str, Any], telegram_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
    """Update user in users dict"""
    user_key = str(telegram_id)
    if user_key not in users:
        users[user_key] = {
            "telegram_id": telegram_id,
            "credits": 100,
            "is_premium": False,
            "premium_until": None,
            "banned": False,
            "created_at": datetime.now().isoformat()
        }
    
    # Update fields
    users[user_key].update(fields)
    users[user_key]["updated_at"] = datetime.now().isoformat()
    
    return users[user_key]
