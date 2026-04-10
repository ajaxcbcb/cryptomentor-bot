import os
import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from jose import jwt

# Configure based on backend patterns
JWT_SECRET = <REDACTED_JWT_SECRET>
JWT_ALGORITHM = "HS256"
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://cryptomentor.id")

def create_access_token(telegram_id: int, username: str = "", first_name: str = "") -> str:
    """Generate a JWT token for the user, matching the backend format."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        "sub": str(telegram_id),
        "exp": expire,
        "username": username,
        "first_name": first_name
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _default_avatar_url(name: str) -> str:
    safe_name = urllib.parse.quote(name or "User")
    return (
        f"https://ui-avatars.com/api/?name={safe_name}"
        "&background=d946ef&color=fff&bold=true"
    )


def generate_dashboard_url(telegram_id: int, username: str = "", first_name: str = "", photo_url: str = "") -> str:
    """Generate a compact dashboard URL with auto-login token and minimal user data."""
    token = create_access_token(telegram_id, username, first_name)

    display_name = first_name or username or str(telegram_id)
    user_data = {
        "id": str(telegram_id),
        "username": (username or display_name).lstrip("@"),
        "first_name": display_name,
        "photo_url": photo_url or _default_avatar_url(display_name),
        "is_premium": False,
        "credits": 0,
    }

    # Compact JSON (no spaces) to keep Telegram confirmation URL short.
    encoded_user = urllib.parse.quote(
        json.dumps(user_data, ensure_ascii=False, separators=(",", ":"))
    )

    # Short query keys reduce URL length. Frontend supports both new and legacy keys.
    return f"{FRONTEND_URL}/?t={token}&u={encoded_user}"
