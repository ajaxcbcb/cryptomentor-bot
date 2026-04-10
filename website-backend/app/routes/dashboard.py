from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.jwt import decode_token
from app.db.supabase import _client
from app.services import bitunix as bsvc
import logging

logger = logging.getLogger(__name__)

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


@router.get("/settings")
async def get_settings(tg_id: int = Depends(get_current_user)):
    """
    Get current trading settings (risk_per_trade, leverage, etc.)

    Returns:
    - risk_per_trade: Current risk percentage (0.25, 0.5, 0.75, 1.0)
    - leverage: Current leverage setting
    - trading_mode: Current mode (auto, scalping, swing)
    - risk_mode: Risk profile (conservative, moderate, aggressive)
    - equity: LIVE equity from Bitunix (balance + unrealized PnL) — used for risk calcs
    - balance: Free available balance
    - unrealized_pnl: Current open position P&L
    """
    s = _client()
    res = s.table("autotrade_sessions").select(
        "risk_per_trade, leverage, trading_mode, risk_mode"
    ).eq("telegram_id", tg_id).limit(1).execute()

    row = (res.data or [{}])[0]

    # Fetch LIVE equity from Bitunix (critical for accurate risk calculations)
    # Equity = available + frozen + unrealized_pnl
    equity = 0.0
    available = 0.0
    frozen = 0.0
    unrealized_pnl = 0.0
    try:
        acc = await bsvc.fetch_account(tg_id)
        if acc.get("success"):
            available = float(acc.get("available", 0) or 0)   # free/usable balance
            frozen = float(acc.get("frozen", 0) or 0)         # locked in open positions
            unrealized_pnl = float(acc.get("total_unrealized_pnl", 0) or 0)

            # Equity = available + frozen (total wallet) + unrealized PnL
            equity = available + frozen + unrealized_pnl

            logger.info(
                f"[Equity:{tg_id}] available=${available:.2f} frozen=${frozen:.2f} "
                f"unrealized=${unrealized_pnl:.2f} => equity=${equity:.2f}"
            )
    except Exception as e:
        logger.warning(f"Failed to fetch live equity for {tg_id}: {e}")

    return {
        "success": True,
        "risk_per_trade": float(row.get("risk_per_trade") or 0.5),
        "leverage": int(row.get("leverage") or 10),
        "trading_mode": row.get("trading_mode") or "auto",
        "risk_mode": row.get("risk_mode") or "moderate",
        "equity": round(equity, 2),           # available + frozen + unrealized (for risk sizing)
        "balance": round(available, 2),        # free/available balance only
        "frozen": round(frozen, 2),            # locked in open positions
        "unrealized_pnl": round(unrealized_pnl, 2),
    }


@router.put("/settings/risk")
async def update_risk_setting(    payload: dict,
    tg_id: int = Depends(get_current_user)
):
    """
    Update risk_per_trade for user (0.25, 0.5, 0.75, 1.0 percent).

    Fixed dollar risk: position_size = (balance × risk%) / SL_distance
    - Tight SL → Larger position (same dollar risk)
    - Wide SL → Smaller position (same dollar risk)

    Args:
        payload: {"risk_per_trade": 0.5} or {"risk_per_trade": 0.25}

    Returns:
        {"success": True, "risk_per_trade": 0.5, "note": "Updated successfully"}
    """
    from datetime import datetime

    risk = float(payload.get("risk_per_trade") or 0.5)

    # Validate: only allow 0.25, 0.5, 0.75, 1.0
    valid_risks = [0.25, 0.5, 0.75, 1.0]
    if risk not in valid_risks:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid risk: {risk}. Must be one of {valid_risks}"
        )

    s = _client()
    try:
        # Ensure we're storing as a float for consistency
        risk_value = float(risk)
        s.table("autotrade_sessions").update({
            "risk_per_trade": risk_value,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("telegram_id", tg_id).execute()

        logger.info(f"[RiskSetting:{tg_id}] Updated risk_per_trade to {risk_value}%")
    except Exception as e:
        logger.error(f"[RiskSetting:{tg_id}] Failed to update risk: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update risk: {e}")

    return {
        "success": True,
        "risk_per_trade": risk,
        "note": f"Risk updated to {risk}% per trade (stored as float: {float(risk)})"
    }


@router.put("/settings/leverage")
async def update_leverage(
    payload: dict,
    tg_id: int = Depends(get_current_user)
):
    """
    Update leverage setting (1-20x).
    """
    from datetime import datetime

    leverage = payload.get("leverage")
    if leverage is None:
        raise HTTPException(status_code=400, detail="Missing 'leverage' field")

    try:
        leverage = int(leverage)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Leverage must be an integer")

    if leverage < 1 or leverage > 20:
        raise HTTPException(status_code=400, detail="Leverage must be between 1 and 20")

    s = _client()
    try:
        s.table("autotrade_sessions").update({
            "leverage": leverage,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("telegram_id", tg_id).execute()
        logger.info(f"[Leverage:{tg_id}] Updated to {leverage}x")
    except Exception as e:
        logger.error(f"[Leverage:{tg_id}] Failed to update: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update leverage: {e}")

    return {"success": True, "leverage": leverage}


@router.put("/settings/margin-mode")
async def update_margin_mode(
    payload: dict,
    tg_id: int = Depends(get_current_user)
):
    """
    Update margin mode ('cross' or 'isolated').
    """
    from datetime import datetime

    margin_mode = str(payload.get("margin_mode", "")).strip().lower()
    if margin_mode not in ("cross", "isolated"):
        raise HTTPException(
            status_code=400,
            detail="Invalid margin_mode. Must be 'cross' or 'isolated'."
        )

    s = _client()
    try:
        s.table("autotrade_sessions").update({
            "margin_mode": margin_mode,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("telegram_id", tg_id).execute()
        logger.info(f"[MarginMode:{tg_id}] Updated to {margin_mode}")
    except Exception as e:
        logger.error(f"[MarginMode:{tg_id}] Failed to update: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update margin mode: {e}")

    return {"success": True, "margin_mode": margin_mode}


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


@router.get("/system")
async def system_health():
    """Public health check — no auth required. Safe to open directly in browser."""
    import sys, os
    from datetime import datetime, timezone
    return {
        "status": "ok",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "bismillah_available": bsvc._BITUNIX_AVAILABLE,
        "encryption_key_set": bool(os.getenv("ENCRYPTION_KEY")),
        "supabase_url_set": bool(os.getenv("SUPABASE_URL")),
        "hint": "Visit /api/dashboard/debug with a valid JWT to see user-specific key/account status.",
    }


@router.get("/debug")
async def debug_connector(tg_id: int = Depends(get_current_user)):
    """User-specific diagnostic — requires JWT in Authorization header.
    Easiest way: open browser DevTools → Network tab → copy the
    Authorization header from any /api/ request, then use curl or
    fetch() from the console:
      fetch('/api/dashboard/debug', {headers:{Authorization:'Bearer <token>'}}).then(r=>r.json()).then(console.log)
    """
    keys = bsvc.get_user_api_keys(tg_id)
    result = {
        "tg_id": tg_id,
        "keys_found": keys is not None,
        "key_hint": keys.get("key_hint") if keys else None,
        "bismillah_available": bsvc._BITUNIX_AVAILABLE,
        "account": None,
        "positions": None,
        "error": None,
    }
    if keys:
        try:
            acc = await bsvc.fetch_account(tg_id)
            result["account"] = {
                "success": acc.get("success"),
                "available": acc.get("available"),
                "msg": acc.get("message"),
            }
            pos = await bsvc.fetch_positions(tg_id)
            result["positions"] = {
                "success": pos.get("success"),
                "count": len(pos.get("positions", [])),
                "msg": pos.get("message"),
            }
        except Exception as e:
            result["error"] = str(e)
    else:
        result["error"] = "No API keys found — check ENCRYPTION_KEY env var and user_api_keys table"
    return result


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
            else:
                bitunix_error = acc.get("message") or acc.get("error") or "Account fetch returned failure"
            pos = await bsvc.fetch_positions(tg_id)
            if pos.get("success"):
                live_positions = pos.get("positions", [])
            elif not bitunix_error:
                bitunix_error = pos.get("message") or pos.get("error") or "Positions fetch returned failure"
        except Exception as e:
            bitunix_error = str(e)
    else:
        bitunix_error = "API keys not found or could not be decrypted"

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
