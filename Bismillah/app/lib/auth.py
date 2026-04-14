import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import dotenv_values
from jose import jwt

JWT_ALGORITHM = "HS256"


def _resolve_jwt_secret() -> str:
    """
    Resolve JWT secret from env first, then fallback to website-backend/.env.
    """
    secret = (os.getenv("JWT_SECRET") or "").strip()
    if secret:
        return secret

    # auth.py: <repo>/Bismillah/app/lib/auth.py -> parents[3] = <repo>
    repo_root = Path(__file__).resolve().parents[3]
    web_env = repo_root / "website-backend" / ".env"
    if web_env.exists():
        data = dotenv_values(web_env)
        fallback = str(data.get("JWT_SECRET") or "").strip()
        if fallback:
            return fallback

    return "change-this-secret"


def _resolve_frontend_url() -> str:
    return (
        os.getenv("FRONTEND_URL")
        or os.getenv("WEB_DASHBOARD_URL")
        or "https://cryptomentor.id"
    ).rstrip("/")


def create_access_token(telegram_id: int, username: str = "", first_name: str = "") -> str:
    """Generate JWT token matching backend format."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        "sub": str(telegram_id),
        "exp": expire,
        "username": username,
        "first_name": first_name,
    }
    return jwt.encode(payload, _resolve_jwt_secret(), algorithm=JWT_ALGORITHM)


def generate_dashboard_url(telegram_id: int, username: str = "", first_name: str = "", photo_url: str = "") -> str:
    """Generate compact dashboard URL with token-only auto-login."""
    token = create_access_token(telegram_id, username, first_name)
    return f"{_resolve_frontend_url()}/?t={token}"

