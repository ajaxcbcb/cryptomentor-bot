import os
import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from jose import jwt

# Configure based on backend patterns
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret")
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

def generate_dashboard_url(telegram_id: int, username: str = "", first_name: str = "", photo_url: str = "") -> str:
    """Generate a dashboard URL with auto-login token and user data."""
    token = create_access_token(telegram_id, username, first_name)

    user_data = {
        "id": str(telegram_id),
        "username": username or first_name or str(telegram_id),
        "first_name": first_name or username,
        "photo_url": photo_url or f"https://ui-avatars.com/api/?name={first_name or str(telegram_id)}&background=d946ef&color=fff&bold=true",
        "is_premium": False,
        "credits": 0
    }

    encoded_user = urllib.parse.quote(json.dumps(user_data))
    return f"{FRONTEND_URL}/?token={token}&user={encoded_user}"
