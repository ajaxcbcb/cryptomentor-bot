
# app/chat_store.py
import os
import json
from typing import Optional

DATA_DIR = os.getenv("DATA_DIR", "data")
CHAT_MAP_PATH = os.path.join(DATA_DIR, "chat_map.json")

def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _load_chat_map():
    _ensure_dir()
    if not os.path.exists(CHAT_MAP_PATH):
        return {}
    try:
        with open(CHAT_MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_chat_map(data):
    _ensure_dir()
    tmp = CHAT_MAP_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, CHAT_MAP_PATH)

def remember_chat(user_id: int, chat_id: int):
    """Remember that user has consented to receive DMs"""
    chat_map = _load_chat_map()
    chat_map[str(user_id)] = chat_id
    _save_chat_map(chat_map)

def get_private_chat_id(user_id: int) -> Optional[int]:
    """Get stored chat ID for user (indicates consent)"""
    chat_map = _load_chat_map()
    chat_id = chat_map.get(str(user_id))
    return int(chat_id) if chat_id else None


# app/chat_store.py
import os
import json
import threading
import time
from typing import Optional, Dict, Any

_LOCK = threading.Lock()
_DATA_DIR = os.getenv("DATA_DIR", "data")
_PATH = os.path.join(_DATA_DIR, "chat_map.json")

def _ensure_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)

def _load() -> Dict[str, Any]:
    if not os.path.exists(_PATH):
        return {}
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save(d: Dict[str, Any]):
    tmp = _PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, _PATH)

def remember_chat(user_id: int, chat_id: int) -> None:
    """Store user's chat_id when they interact with bot"""
    with _LOCK:
        _ensure_dir()
        d = _load()
        d[str(user_id)] = {"chat_id": int(chat_id), "ts": int(time.time())}
        _save(d)

def get_chat_id(user_id: int) -> Optional[int]:
    """Get stored chat_id for user (returns None if user hasn't started bot)"""
    d = _load()
    rec = d.get(str(user_id))
    return int(rec["chat_id"]) if rec and "chat_id" in rec else None

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
