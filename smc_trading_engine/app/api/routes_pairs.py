from __future__ import annotations

from fastapi import APIRouter, Request

from app.config.pairs import DEFAULT_PAIRS

router = APIRouter(prefix="/pairs", tags=["pairs"])


@router.get("")
async def pairs(request: Request):
    services = request.app.state.services
    statuses = {row["symbol"]: row for row in services.analytics_service.latest_status()}
    return {
        "pairs": [
            {
                "symbol": p,
                "has_status": p in statuses,
                "last_action": statuses.get(p, {}).get("action"),
            }
            for p in DEFAULT_PAIRS
        ]
    }
