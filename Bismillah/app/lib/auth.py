import os
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


def generate_dashboard_url(telegram_id: int, username: str = "", first_name: str = "", photo_url: str = "") -> str:
    """Generate a compact dashboard URL with token-only auto-login."""
    token = create_access_token(telegram_id, username, first_name)
    # Frontend can derive fallback user profile from JWT payload.
    # Keep URL as short as possible for better Telegram UX.
    return f"{FRONTEND_URL}/?t={token}"
