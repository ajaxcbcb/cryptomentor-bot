import os
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import decode_token

bearer = HTTPBearer()


def load_admin_ids() -> list[int]:
    ids = set()
    raw_values = [
        os.getenv("ADMIN_IDS", ""),
        os.getenv("ADMIN1", ""),
        os.getenv("ADMIN2", ""),
        os.getenv("ADMIN3", ""),
        os.getenv("ADMIN_USER_ID", ""),
        os.getenv("ADMIN2_USER_ID", ""),
    ]
    for raw in raw_values:
        for token in str(raw).split(","):
            token = token.strip()
            if token.isdigit():
                ids.add(int(token))
    return sorted(ids)


def is_admin_telegram_id(tg_id: int | str | None) -> bool:
    try:
        value = int(tg_id)
    except Exception:
        return False
    return value in set(load_admin_ids())


def augment_user_with_admin(user: dict[str, Any] | None) -> dict[str, Any] | None:
    if not user:
        return user
    out = dict(user)
    out["is_admin"] = is_admin_telegram_id(out.get("telegram_id"))
    return out


def get_current_user_id(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload["sub"])


def require_admin_user(tg_id: int = Depends(get_current_user_id)) -> int:
    if not is_admin_telegram_id(tg_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    return int(tg_id)
