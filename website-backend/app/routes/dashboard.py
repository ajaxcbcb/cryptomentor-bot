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


async def _ensure_session(tg_id: int, status: str) -> dict:
    """Upsert autotrade_sessions, creating a new row with sane defaults
    (mirroring the Telegram bot's save_autotrade_session) when none exists.
    """
    from datetime import datetime
    s = _client()

    existing_res = s.table("autotrade_sessions").select("*").eq(
        "telegram_id", int(tg_id)
    ).limit(1).execute()
    existing = (existing_res.data or [None])[0]

    now_iso = datetime.utcnow().isoformat()
    payload = {
        "telegram_id": int(tg_id),
        "status": status,
        "updated_at": now_iso,
    }
    if status == "active":
        payload["engine_active"] = True
    elif status in ("paused", "stopped"):
        payload["engine_active"] = False

    if not existing:
        # Bootstrap a fresh session from the live Bitunix balance so the bot's
        # engine_restore can pick it up on its next cycle.
        balance = 0.0
        try:
            acc = await bsvc.fetch_account(tg_id)
            if acc.get("success"):
                balance = float(acc.get("available", 0) or 0)
        except Exception:
            pass
        payload.update({
            "initial_deposit": balance,
            "current_balance": balance,
            "total_profit": 0,
            "leverage": 10,
            "started_at": now_iso,
        })

    res = s.table("autotrade_sessions").upsert(
        payload, on_conflict="telegram_id"
    ).execute()
    row = (res.data or [payload])[0]
    return {
        "status": row.get("status", status),
        "engine_active": bool(row.get("engine_active", payload.get("engine_active", False))),
        "current_balance": float(row.get("current_balance") or 0),
    }


@router.post("/engine/start")
async def engine_start(tg_id: int = Depends(get_current_user)):
    # Sync with DB: same source of truth as the Telegram bot (user_api_keys).
    keys = bsvc.get_user_api_keys(tg_id)
    if not keys:
        raise HTTPException(
            status_code=409,
            detail="Bitunix API keys not configured. Link your keys before starting the engine.",
        )

    # Verify the keys are actually live before flipping the engine on.
    try:
        conn = await bsvc.fetch_connection(tg_id)
        if not conn.get("online"):
            raise HTTPException(
                status_code=502,
                detail=f"Bitunix connection failed: {conn.get('message') or conn.get('error') or 'offline'}",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bitunix connection error: {e}")

    try:
        result = await _ensure_session(tg_id, "active")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start engine: {e}")
    return {"success": True, "running": True, **result}


@router.post("/engine/stop")
async def engine_stop(tg_id: int = Depends(get_current_user)):
    try:
        result = await _ensure_session(tg_id, "stopped")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop engine: {e}")
    return {"success": True, "running": False, **result}


@router.get("/engine/state")
async def engine_state(tg_id: int = Depends(get_current_user)):
    s = _client()
    res = s.table("autotrade_sessions").select(
        "status, engine_active"
    ).eq("telegram_id", tg_id).limit(1).execute()
    row = (res.data or [{}])[0]
    status = row.get("status")
    return {
        "running": bool(row.get("engine_active")) or status in ("active", "uid_verified"),
        "status": status,
    }


@router.get("/performance")
async def get_performance(tg_id: int = Depends(get_current_user)):
    """
    Live performance metrics computed from autotrade_trades.

    Returns Sharpe, Max Drawdown, Win Rate, Total Trades, Volatility, plus a
    cumulative equity series suitable for charting.
    """
    import math
    from datetime import datetime, timezone
    from collections import defaultdict

    s = _client()

    res = s.table("autotrade_trades").select(
        "pnl_usdt, status, opened_at, closed_at"
    ).eq("telegram_id", tg_id).eq("status", "closed").order("closed_at").execute()
    trades = res.data or []

    total_trades = len(trades)
    wins = sum(1 for t in trades if float(t.get("pnl_usdt") or 0) > 0)
    win_rate = (wins / total_trades * 100) if total_trades else 0.0

    # Starting equity from session, fallback to live Bitunix balance
    sess = s.table("autotrade_sessions").select(
        "initial_deposit, current_balance"
    ).eq("telegram_id", tg_id).limit(1).execute()
    sess_row = (sess.data or [{}])[0]
    start_equity = float(sess_row.get("initial_deposit") or 0)
    if start_equity <= 0:
        try:
            acc = await bsvc.fetch_account(tg_id)
            if acc.get("success"):
                start_equity = float(acc.get("available", 0) or 0)
        except Exception:
            pass
    if start_equity <= 0:
        start_equity = 10000.0  # neutral baseline so chart still renders

    # Bucket pnl per day for the equity curve and daily return series
    by_day = defaultdict(float)
    for t in trades:
        ts = t.get("closed_at") or t.get("opened_at")
        if not ts:
            continue
        try:
            day = datetime.fromisoformat(ts.replace("Z", "+00:00")).date().isoformat()
        except Exception:
            continue
        by_day[day] += float(t.get("pnl_usdt") or 0)

    days_sorted = sorted(by_day.keys())
    equity = start_equity
    equity_series = []
    daily_returns = []
    peak = start_equity
    max_dd_pct = 0.0
    for d in days_sorted:
        prev = equity
        equity += by_day[d]
        if prev > 0:
            daily_returns.append((equity - prev) / prev)
        peak = max(peak, equity)
        if peak > 0:
            dd = (equity - peak) / peak
            if dd < max_dd_pct:
                max_dd_pct = dd
        equity_series.append({"date": d, "equity": round(equity, 2)})

    # Sharpe (annualized, rf=0). Need at least 2 returns and non-zero stdev.
    sharpe = 0.0
    volatility_pct = 0.0
    if len(daily_returns) >= 2:
        mean_r = sum(daily_returns) / len(daily_returns)
        var_r = sum((r - mean_r) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        std_r = math.sqrt(var_r)
        if std_r > 0:
            sharpe = (mean_r / std_r) * math.sqrt(365)
        volatility_pct = std_r * math.sqrt(30) * 100  # ~monthly stdev in %

    # Prepend a baseline point so the chart starts at the initial equity
    if equity_series:
        equity_series = [{"date": "Start", "equity": round(start_equity, 2)}] + equity_series

    return {
        "metrics": {
            "sharpe": round(sharpe, 2),
            "max_drawdown_pct": round(max_dd_pct * 100, 2),
            "win_rate_pct": round(win_rate, 2),
            "total_trades": total_trades,
            "volatility_pct": round(volatility_pct, 2),
        },
        "equity_curve": equity_series,
        "start_equity": round(start_equity, 2),
    }


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
