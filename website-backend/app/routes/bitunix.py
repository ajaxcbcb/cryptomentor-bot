"""
Live Bitunix endpoints for the website frontend.

These mirror the Telegram bot's status/history handlers so values shown on
the website are in sync with what the user sees in Telegram.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging
import time

from app.auth.jwt import decode_token
from app.db.supabase import _client
from app.services import bitunix as bsvc
from app.services import one_click_trades as one_click_repo
try:
    from Bismillah.app.symbol_coordinator import get_coordinator
except Exception:  # pragma: no cover
    get_coordinator = None

router = APIRouter(prefix="/bitunix", tags=["bitunix"])
bearer = HTTPBearer()
logger = logging.getLogger(__name__)

class TPSLUpdate(BaseModel):
    symbol: str
    tp_price: float = 0.0
    sl_price: float = 0.0

class ApiKeysInput(BaseModel):
    api_key: str
    api_secret: str


class ClosePositionInput(BaseModel):
    symbol: str
    side: str | None = None
    source: str | None = None


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


def _norm_symbol(symbol: str | None) -> str:
    return str(symbol or "").replace("/", "").upper().strip()


def _norm_side(side: str | None) -> str:
    s = str(side or "").upper().strip()
    if s in ("LONG", "BUY"):
        return "LONG"
    if s in ("SHORT", "SELL"):
        return "SHORT"
    return ""


def _conn_error(conn: dict) -> str:
    if isinstance(conn, dict):
        err = conn.get("error") or conn.get("message")
        if err:
            return str(err)
    return "Invalid API Keys"


def _is_same_position(live_pos: dict, db_trade: dict) -> bool:
    if _norm_symbol(live_pos.get("symbol")) != _norm_symbol(db_trade.get("symbol")):
        return False
    if _norm_side(live_pos.get("side")) != _norm_side(db_trade.get("side")):
        return False

    # Try quantity similarity first (most stable)
    try:
        live_qty = float(live_pos.get("qty") or live_pos.get("size") or 0)
        db_qty = float(db_trade.get("qty") or db_trade.get("quantity") or 0)
        if live_qty > 0 and db_qty > 0:
            diff_pct = abs(live_qty - db_qty) / max(live_qty, db_qty)
            if diff_pct <= 0.2:
                return True
    except Exception:
        pass

    # Fallback to entry-price similarity
    try:
        live_entry = float(live_pos.get("entry_price") or 0)
        db_entry = float(db_trade.get("entry_price") or 0)
        if live_entry > 0 and db_entry > 0:
            diff_pct = abs(live_entry - db_entry) / max(live_entry, db_entry)
            if diff_pct <= 0.03:
                return True
    except Exception:
        pass

    # Final fallback: symbol+side already match.
    return True


def _annotate_position_sources(tg_id: int, positions: list[dict]) -> list[dict]:
    """
    Mark each live exchange position as:
    - source=1_click: matched with an open row in one_click_trades
    - source=autotrade: matched with an open row in autotrade_trades
    - source=1_click (fallback): unmatched live position (manual/legacy)
    """
    try:
        s = _client()
        one_click_open = one_click_repo.get_open_trades(tg_id)
        remaining_one_click = list(one_click_open)
        db_res = s.table("autotrade_trades").select(
            "id, symbol, side, qty, quantity, entry_price, status"
        ).eq("telegram_id", int(tg_id)).eq("status", "open").execute()
        db_open = db_res.data or []
    except Exception:
        # Safe fallback: if DB lookup fails, classify as autotrade to avoid
        # exposing close-manual action on potentially managed positions.
        fallback = []
        for pos in positions:
            enriched = dict(pos)
            enriched["source"] = "autotrade"
            enriched["source_label"] = "AutoTrade"
            enriched["autotrade_trade_id"] = None
            fallback.append(enriched)
        return fallback

    remaining_db = list(db_open)
    annotated: list[dict] = []

    for pos in positions:
        enriched = dict(pos)
        source = "1_click"
        matched_trade_id = None

        # First-class 1-click attribution (preferred)
        for idx, oc_trade in enumerate(remaining_one_click):
            if _is_same_position(
                enriched,
                {
                    "symbol": oc_trade.get("symbol"),
                    "side": oc_trade.get("side"),
                    "qty": oc_trade.get("qty"),
                    "entry_price": oc_trade.get("entry_price"),
                },
            ):
                source = "1_click"
                matched_trade_id = oc_trade.get("id")
                remaining_one_click.pop(idx)
                break

        # Fallback to managed autotrade attribution
        if source != "1_click" or matched_trade_id is None:
            source = "1_click"
            matched_trade_id = None
            for idx, db_trade in enumerate(remaining_db):
                if _is_same_position(enriched, db_trade):
                    source = "autotrade"
                    matched_trade_id = db_trade.get("id")
                    remaining_db.pop(idx)
                    break

        enriched["source"] = source
        enriched["source_label"] = "AutoTrade" if source == "autotrade" else "1-Click"
        enriched["autotrade_trade_id"] = matched_trade_id
        annotated.append(enriched)

    return annotated


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

    positions = _annotate_position_sources(tg_id, res.get("positions", []))
    total_upnl = sum(float(p.get("pnl") or 0) for p in positions)
    return {
        "total_positions": len(positions),
        "autotrade_positions": sum(1 for p in positions if p.get("source") == "autotrade"),
        "one_click_positions": sum(1 for p in positions if p.get("source") == "1_click"),
        "total_unrealized_pnl": round(total_upnl, 4),
        "positions": positions,
    }


@router.post("/positions/close")
async def bitunix_close_position(
    req: ClosePositionInput,
    tg_id: int = Depends(get_current_user),
):
    """
    Close a live position with reduce-only market order.
    This endpoint is intended for 1-click/manual positions from web dashboard.
    """
    _require_keys(tg_id)

    symbol = _norm_symbol(req.symbol)
    if not symbol:
        raise HTTPException(status_code=400, detail="Missing symbol")

    if req.source and req.source != "1_click":
        raise HTTPException(status_code=400, detail="Only 1-click positions can be closed from this action")

    try:
        live = await bsvc.fetch_positions(tg_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bitunix error: {e}")
    if not live.get("success"):
        raise HTTPException(status_code=502, detail=live.get("message") or "Bitunix positions fetch failed")

    positions = _annotate_position_sources(tg_id, live.get("positions", []))
    target_side = _norm_side(req.side)

    target = None
    for p in positions:
        if _norm_symbol(p.get("symbol")) != symbol:
            continue
        if p.get("source") != "1_click":
            continue
        if target_side and _norm_side(p.get("side")) != target_side:
            continue
        target = p
        break

    if not target:
        raise HTTPException(status_code=404, detail="1-click position not found (or already closed)")

    position_side = _norm_side(target.get("side"))
    qty = float(target.get("qty") or target.get("size") or 0)
    if qty <= 0:
        raise HTTPException(status_code=400, detail="Position size is zero")
    if position_side not in ("LONG", "SHORT"):
        raise HTTPException(status_code=400, detail="Unable to resolve position side")

    close_side = "SELL" if position_side == "LONG" else "BUY"
    try:
        close_res = await bsvc.close_market_position(
            telegram_id=tg_id,
            symbol=symbol,
            close_side=close_side,
            qty=qty,
            position_side=position_side,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Close order failed: {e}")

    if not close_res.get("success"):
        raise HTTPException(
            status_code=502,
            detail=close_res.get("error") or close_res.get("message") or "Close order rejected by exchange",
        )

    if get_coordinator:
        try:
            coordinator = get_coordinator()
            await coordinator.confirm_closed(tg_id, symbol, time.time())
        except Exception as e:
            logger.warning(f"[1ClickClose:{tg_id}] Coordinator sync failed for {symbol}: {e}")

    try:
        one_click_repo.mark_closed_manual(
            tg_id=tg_id,
            symbol=symbol,
            side=position_side,
        )
    except Exception as e:
        logger.warning(f"[1ClickClose:{tg_id}] one_click_trades close sync failed for {symbol}: {e}")

    return {
        "success": True,
        "symbol": symbol,
        "source": "1_click",
        "closed_qty": qty,
        "order": close_res,
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
    try:
        conn = await bsvc.fetch_connection_with_keys(keys.api_key, keys.api_secret)
    except PermissionError as e:
        raise HTTPException(status_code=500, detail=f"Bitunix client unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Connection check failed: {e}")

    if not conn.get("online"):
        raise HTTPException(
            status_code=400,
            detail=f"Connection failed: {_conn_error(conn)}"
        )

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
    try:
        conn = await bsvc.fetch_connection_with_keys(keys.api_key, keys.api_secret)
    except PermissionError as e:
        raise HTTPException(status_code=500, detail=f"Bitunix client unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Connection check failed: {e}")

    if not conn.get("online"):
        raise HTTPException(status_code=400, detail=f"Connection failed: {_conn_error(conn)}")

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
