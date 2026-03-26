# app/chat_store.py
"""
Chat Store - Manages user chat IDs for broadcast consent
"""
import os
import json
import threading
import time
from typing import Optional, Dict, Any

_LOCK = threading.Lock()
_DATA_DIR = os.getenv("DATA_DIR", "data")
_PATH = os.path.join(_DATA_DIR, "chat_map.json")

def _ensure_dir():
    """Ensure data directory exists"""
    os.makedirs(_DATA_DIR, exist_ok=True)

def _load() -> Dict[str, Any]:
    """Load chat map from disk"""
    if not os.path.exists(_PATH):
        return {}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save(d: Dict[str, Any]):
    """Save chat map to disk atomically"""
    _ensure_dir()
    tmp = _PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, _PATH)

def remember_chat(user_id: int, chat_id: int) -> None:
    """
    Store user's chat_id when they interact with bot
    
    This indicates user consent to receive messages
    """
    with _LOCK:
        _ensure_dir()
        d = _load()
        d[str(user_id)] = {"chat_id": int(chat_id), "ts": int(time.time())}
        _save(d)

def get_private_chat_id(user_id: int) -> Optional[int]:
    """
    Get stored chat_id for user
    
    Returns None if user hasn't started bot (no consent)
    This is used by autosignal to check if user can receive broadcasts
    """
    d = _load()
    rec = d.get(str(user_id))
    return int(rec["chat_id"]) if rec and "chat_id" in rec else None

def get_chat_id(user_id: int) -> Optional[int]:
    """Alias for get_private_chat_id for backward compatibility"""
    return get_private_chat_id(user_id)

def get_all_consented_users() -> Dict[str, Dict]:
    """Get all users who have given consent (started the bot)"""
    return _load()

def remove_chat(user_id: int) -> None:
    """Remove user's chat consent (if they block the bot)"""
    with _LOCK:
        _ensure_dir()
        d = _load()
        d.pop(str(user_id), None)
        _save(d)
