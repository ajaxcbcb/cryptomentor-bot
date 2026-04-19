from __future__ import annotations

from fastapi import APIRouter

from app.storage import repositories

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("/open")
async def open_trades():
    return {"items": repositories.get_open_positions()}


@router.get("/history")
async def trade_history(limit: int = 100):
    return {"items": repositories.get_executions(limit=limit)}
