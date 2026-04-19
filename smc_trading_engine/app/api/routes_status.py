from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/status", tags=["status"])


@router.get("")
async def status_all(request: Request):
    services = request.app.state.services
    return {"items": services.analytics_service.latest_status()}


@router.get("/{symbol}")
async def status_symbol(symbol: str, request: Request):
    services = request.app.state.services
    row = services.analytics_service.status_for(symbol.upper())
    if not row:
        raise HTTPException(status_code=404, detail="status_not_found")
    return row
