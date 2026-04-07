from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.jwt import decode_token
from app.db.supabase import _client

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

    return {
        "user": user,
        "engine": {
            "trading_mode": session.get("trading_mode", "scalping"),
            "stackmentor_active": bool(session.get("engine_active", False)),
            "auto_mode_enabled": bool(session.get("auto_mode_enabled", False)),
            "risk_mode": session.get("risk_mode", "moderate"),
            "is_active": session.get("status") == "active",
            "current_balance": float(session.get("current_balance") or 0),
            "total_profit": float(session.get("total_profit") or 0),
        },
        "portfolio": {
            "open_positions": len(positions),
            "pnl_30d": round(pnl_30d, 2),
            "positions": positions,
        }
    }
