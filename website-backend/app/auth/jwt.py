from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from config import JWT_SECRET, JWT_EXPIRE_HOURS

ALGORITHM = "HS256"


def create_token(telegram_id: int, extra: Dict[str, Any] = {}) -> str:
    payload = {
        "sub": str(telegram_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
        **extra,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None
