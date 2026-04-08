"""
Live Bitunix endpoints for the website frontend.

These mirror the Telegram bot's status/history handlers so values shown on
the website are in sync with what the user sees in Telegram.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.auth.jwt import decode_token
from app.services import bitunix as bsvc

router = APIRouter(prefix="/bitunix", tags=["bitunix"])
bearer = HTTPBearer()

class TPSLUpdate(BaseModel):
    symbol: str
    tp_price: float = 0.0
    sl_price: float = 0.0

class ApiKeysInput(BaseModel):
    api_key: str
    api_secret: str


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


# ------------------------------------------------------------- update tpsl -- #

@router.post("/positions/tpsl")
async def bitunix_update_tpsl(
    req: TPSLUpdate,
    tg_id: int = Depends(get_current_user),
):
    """
    Update Take Profit and/or Stop Loss for an open position.
    Mirrors the self-healing and modification functions from the Telegram bot.
    """
    _require_keys(tg_id)
    try:
        # If both are provided or just TP is provided, we can use set_position_tpsl
        # If ONLY SL is provided, we use set_position_sl. Or we can just use set_position_tpsl always
        # since it correctly mirrors both.
        if req.tp_price > 0 or (req.tp_price == 0 and req.sl_price > 0):
            res = await bsvc.set_position_tpsl(tg_id, req.symbol, req.tp_price, req.sl_price)
        else:
            # If everything is 0, we can still submit to clear them
            res = await bsvc.set_position_tpsl(tg_id, req.symbol, req.tp_price, req.sl_price)
            
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bitunix error: {e}")
        
    if not res.get("success"):
        raise HTTPException(status_code=502, detail=res.get("error") or res.get("message") or "Bitunix TP/SL update failed")
        
    return res


# ----------------------------------------------------------------- keys ---- #

@router.post("/keys")
async def bitunix_save_keys(
    keys: ApiKeysInput,
    tg_id: int = Depends(get_current_user),
):
    """
    Test and save Bitunix API Keys for the user.
    """
    from app.bitunix_autotrade_client import BitunixAutoTradeClient
    
    # 1. Test connection first
    client = BitunixAutoTradeClient(api_key=keys.api_key, api_secret=keys.api_secret)
    conn = client.check_connection()
    if not conn.get("online"):
        raise HTTPException(
            status_code=400, 
            detail=f"Connection failed: {conn.get('error', 'Invalid API Keys')}"
        )
        
    # 2. Connection passed, encrypt and save
    try:
        bsvc.save_user_api_keys(tg_id, keys.api_key, keys.api_secret)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save keys securely: {e}")
        
    return {"success": True, "message": "API Keys securely linked."}

@router.post("/keys/test")
async def bitunix_test_keys(
    keys: ApiKeysInput,
    tg_id: int = Depends(get_current_user),
):
    """
    Dry-run test for Bitunix API Keys without saving them.
    """
    from app.bitunix_autotrade_client import BitunixAutoTradeClient
    
    client = BitunixAutoTradeClient(api_key=keys.api_key, api_secret=keys.api_secret)
    conn = client.check_connection()
    
    if not conn.get("online"):
        return {
            "success": False, 
            "message": f"Connection failed: {conn.get('error', 'Invalid API Keys')}"
        }
    return {"success": True, "message": "Connection successful! Keys are valid."}

@router.delete("/keys")
async def bitunix_delete_keys(
    tg_id: int = Depends(get_current_user),
):
    """
    Delete Bitunix API Keys for the user.
    """
    try:
        bsvc.delete_user_api_keys(tg_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete keys: {e}")
        
    return {"success": True, "message": "API Keys removed."}
