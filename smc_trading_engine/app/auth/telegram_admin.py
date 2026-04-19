from __future__ import annotations

from fastapi import Header, HTTPException

from app.config.settings import settings


def _parse_admin_ids() -> set[int]:
    ids: set[int] = set()
    for token in str(settings.telegram_admin_ids or "").split(","):
        token = token.strip()
        if token.isdigit():
            ids.add(int(token))
    return ids


async def require_admin(x_telegram_admin_id: str | None = Header(default=None)) -> int:
    if not settings.telegram_auth_enabled:
        return 0
    if not x_telegram_admin_id or not x_telegram_admin_id.isdigit():
        raise HTTPException(status_code=401, detail="Missing admin header")
    admin_id = int(x_telegram_admin_id)
    if admin_id not in _parse_admin_ids():
        raise HTTPException(status_code=403, detail="Not authorized")
    return admin_id
