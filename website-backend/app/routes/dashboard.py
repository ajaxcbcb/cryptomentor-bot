from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.jwt import decode_token
from app.db.supabase import _client
from app.services import bitunix as bsvc

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
bearer = HTTPBearer()


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload["sub"])


@router.get("/portfolio")
async def get_portfolio(tg_id: int = Depends(get_current_user)):
    s = _client()

    # User data
    user_res = s.table("users").select(
        "telegram_id, username, first_name, credits, is_premium, premium_until, is_lifetime"
    ).eq("telegram_id", tg_id).limit(1).execute()
    user = user_res.data[0] if user_res.data else {}

    # Autotrade session
    session_res = s.table("autotrade_sessions").select(
        "trading_mode, engine_active, auto_mode_enabled, risk_mode, risk_per_trade, status, current_balance, total_profit"
    ).eq("telegram_id", tg_id).limit(1).execute()
    session = session_res.data[0] if session_res.data else {}

    # Open positions (trades yang belum closed)
    positions_res = s.table("autotrade_trades").select(
        "id, symbol, side, entry_price, qty, leverage, pnl_usdt, tp1_price, tp2_price, tp3_price, tp1_hit, tp2_hit, tp3_hit, opened_at"
    ).eq("telegram_id", tg_id).eq("status", "open").execute()
    positions = positions_res.data or []

    # PnL 30 hari terakhir
    from datetime import datetime, timedelta, timezone
    since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    pnl_res = s.table("autotrade_trades").select("pnl_usdt").eq(
        "telegram_id", tg_id
    ).eq("status", "closed").gte("closed_at", since).execute()
    pnl_30d = sum(float(t.get("pnl_usdt") or 0) for t in (pnl_res.data or []))

    # Live Bitunix data (sync with Telegram bot). Best-effort: if keys are
    # missing or exchange call fails, fall back to Supabase-only values.
    live_account = None
    live_positions = None
    bitunix_error = None
    if bsvc.get_user_api_keys(tg_id):
        try:
            acc = await bsvc.fetch_account(tg_id)
            if acc.get("success"):
                live_account = {
                    "balance": acc.get("available", 0),
                    "available": acc.get("available", 0),
                    "frozen": acc.get("frozen", 0),
                    "margin": acc.get("margin", 0),
                    "cross_unrealized_pnl": acc.get("cross_unrealized_pnl", 0),
                    "isolation_unrealized_pnl": acc.get("isolation_unrealized_pnl", 0),
                    "total_unrealized_pnl": acc.get("total_unrealized_pnl", 0),
                }
            pos = await bsvc.fetch_positions(tg_id)
            if pos.get("success"):
                live_positions = pos.get("positions", [])
        except Exception as e:
            bitunix_error = str(e)

    # Merge: prefer live values when available.
    current_balance = (
        live_account["balance"] if live_account else float(session.get("current_balance") or 0)
    )
    open_positions_live = live_positions if live_positions is not None else positions
    unrealized_pnl = (
        sum(float(p.get("pnl") or 0) for p in live_positions) if live_positions is not None else 0.0
    )

    return {
        "user": user,
        "bitunix": {
            "linked": bsvc.get_user_api_keys(tg_id) is not None,
            "account": live_account,
            "error": bitunix_error,
        },
        "engine": {
            "trading_mode": session.get("trading_mode", "scalping"),
            "stackmentor_active": bool(session.get("engine_active", False)),
            "auto_mode_enabled": bool(session.get("auto_mode_enabled", False)),
            "risk_mode": session.get("risk_mode", "moderate"),
            "is_active": session.get("status") == "active",
            "current_balance": current_balance,
            "total_profit": float(session.get("total_profit") or 0),
        },
        "portfolio": {
            "open_positions": len(open_positions_live),
            "pnl_30d": round(pnl_30d, 2),
            "unrealized_pnl": round(unrealized_pnl, 4),
            "positions": open_positions_live,
        }
    }
