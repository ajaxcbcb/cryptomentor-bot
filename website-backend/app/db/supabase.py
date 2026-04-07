from typing import Optional, Dict, Any
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY


def _client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_user_by_tid(tg_id: int) -> Optional[Dict[str, Any]]:
    res = _client().table("users").select("*").eq("telegram_id", tg_id).limit(1).execute()
    return res.data[0] if res.data else None


def upsert_web_login(tg_id: int, username: str, first_name: str, last_name: str = None) -> Dict[str, Any]:
    """Update profile info saat login via website. Tidak mengubah credits."""
    s = _client()
    existing = get_user_by_tid(tg_id)

    if existing:
        update = {"updated_at": "now()"}
        if username:
            update["username"] = username.lstrip("@").lower()
        if first_name:
            update["first_name"] = first_name
        if last_name:
            update["last_name"] = last_name
        s.table("users").update(update).eq("telegram_id", tg_id).execute()
        return get_user_by_tid(tg_id)

    # User belum pernah pakai bot, buat dengan 0 credits
    row = {
        "telegram_id": tg_id,
        "username": (username or "").lstrip("@").lower() or None,
        "first_name": first_name or "User",
        "last_name": last_name,
        "credits": 0,
    }
    s.table("users").insert(row).execute()
    return get_user_by_tid(tg_id) or row
