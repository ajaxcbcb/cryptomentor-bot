from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.auth.telegram_admin import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/rescan")
async def rescan_once(request: Request, admin_id: int = Depends(require_admin)):
    services = request.app.state.services
    result = await services.scan_service.scan_once()
    return {"ok": True, "triggered_by": admin_id, "result": result}
