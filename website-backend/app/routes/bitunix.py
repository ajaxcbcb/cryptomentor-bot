"""
Live Bitunix endpoints for the website frontend.

These mirror the Telegram bot's status/history handlers so values shown on
the website are in sync with what the user sees in Telegram.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt import decode_token
from app.services import bitunix as bsvc

router = APIRouter(prefix="/bitunix", tags=["bitunix"])
bearer = HTTPBearer()


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload["sub"])


def _require_keys(tg_id: int):
    keys = bsvc.get_user_api_keys(tg_id)
    if not keys:
        raise HTTPException(
            status_code=409,
            detail="Bitunix API keys not configured. Please set them up via the Telegram bot (/autotrade).",
        )
    return keys


# ------------------------------------------------------------------ status -- #

@router.get("/status")
async def bitunix_status(tg_id: int = Depends(get_current_user)):
    """Whether the user has linked Bitunix keys and if the connection is live."""
    keys = bsvc.get_user_api_keys(tg_id)
    if not keys:
        return {"linked": False, "online": False, "key_hint": None}
    try:
        conn = await bsvc.fetch_connection(tg_id)
    except Exception as e:
        return {"linked": True, "online": False, "key_hint": keys["key_hint"], "error": str(e)}
    return {
        "linked": True,
        "online": bool(conn.get("online")),
        "key_hint": keys["key_hint"],
        "message": conn.get("message"),
    }


# ----------------------------------------------------------------- account -- #

@router.get("/account")
async def bitunix_account(tg_id: int = Depends(get_current_user)):
    _require_keys(tg_id)
    try:
        res = await bsvc.fetch_account(tg_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bitunix error: {e}")
    if not res.get("success"):
        raise HTTPException(status_code=502, detail=res.get("message") or "Bitunix account fetch failed")

    return {
        "balance": res.get("available", 0),
        "available": res.get("available", 0),
        "frozen": res.get("frozen", 0),
        "margin": res.get("margin", 0),
        "bonus": res.get("bonus", 0),
        "cross_unrealized_pnl": res.get("cross_unrealized_pnl", 0),
        "isolation_unrealized_pnl": res.get("isolation_unrealized_pnl", 0),
        "total_unrealized_pnl": res.get("total_unrealized_pnl", 0),
        "position_mode": res.get("position_mode"),
    }


# --------------------------------------------------------------- positions -- #

@router.get("/positions")
async def bitunix_positions(tg_id: int = Depends(get_current_user)):
    _require_keys(tg_id)
    try:
        res = await bsvc.fetch_positions(tg_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bitunix error: {e}")
    if not res.get("success"):
        raise HTTPException(status_code=502, detail=res.get("message") or "Bitunix positions fetch failed")

    positions = res.get("positions", [])
    total_upnl = sum(float(p.get("pnl") or 0) for p in positions)
    return {
        "total_positions": len(positions),
        "total_unrealized_pnl": round(total_upnl, 4),
        "positions": positions,
    }


# ----------------------------------------------------------------- history -- #

@router.get("/trade-history")
async def bitunix_trade_history(
    tg_id: int = Depends(get_current_user),
    symbol: str | None = None,
):
    _require_keys(tg_id)
    try:
        res = await bsvc.fetch_trade_history(tg_id, symbol=symbol)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bitunix error: {e}")
    if not res.get("success"):
        raise HTTPException(status_code=502, detail=res.get("message") or "Bitunix history fetch failed")
    return res


# ---------------------------------------------------------------- portfolio -- #
# One-shot endpoint the dashboard can call to get everything it needs,
# mirroring the Telegram `/status` → portfolio view.

@router.get("/portfolio")
async def bitunix_portfolio(tg_id: int = Depends(get_current_user)):
    _require_keys(tg_id)
    try:
        acc = await bsvc.fetch_account(tg_id)
        pos = await bsvc.fetch_positions(tg_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bitunix error: {e}")

    if not acc.get("success"):
        raise HTTPException(status_code=502, detail=acc.get("message") or "Bitunix account fetch failed")
    if not pos.get("success"):
        raise HTTPException(status_code=502, detail=pos.get("message") or "Bitunix positions fetch failed")

    positions = pos.get("positions", [])
    return {
        "account": {
            "balance": acc.get("available", 0),
            "available": acc.get("available", 0),
            "frozen": acc.get("frozen", 0),
            "margin": acc.get("margin", 0),
            "bonus": acc.get("bonus", 0),
            "cross_unrealized_pnl": acc.get("cross_unrealized_pnl", 0),
            "isolation_unrealized_pnl": acc.get("isolation_unrealized_pnl", 0),
            "total_unrealized_pnl": acc.get("total_unrealized_pnl", 0),
            "position_mode": acc.get("position_mode"),
        },
        "positions": positions,
        "open_positions": len(positions),
        "unrealized_pnl": round(sum(float(p.get("pnl") or 0) for p in positions), 4),
    }
