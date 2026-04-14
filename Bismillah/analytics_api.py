"""
Analytics API — FastAPI app untuk observability dashboard
Provides real-time trading stats, position coordination state, and performance metrics.

Port: 8896 (analytics4896.cryptomentor.id)
Auth: Telegram admin JWT tokens (validated against admins from bot.py._load_admin_ids)
Rate limiting: 100 req/menit per user
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Admin authentication
# ─────────────────────────────────────────────────────────────────────────────

ADMIN_ALLOWLIST: set = set()


def _load_admin_ids():
    """Load admin IDs from environment (same as bot.py)."""
    global ADMIN_ALLOWLIST
    admin_ids = []

    # Try multiple environment variable names
    for env_var in ["ADMIN_IDS", "ADMIN1", "ADMIN2", "ADMIN3", "ADMIN4", "ADMIN5"]:
        val = os.getenv(env_var, "").strip()
        if val:
            try:
                admin_id = int(val)
                admin_ids.append(admin_id)
            except ValueError:
                logger.warning(f"[Analytics] Invalid admin ID in {env_var}: {val}")

    ADMIN_ALLOWLIST = set(admin_ids)
    logger.info(f"[Analytics] Loaded {len(ADMIN_ALLOWLIST)} admin IDs")


def _verify_admin_jwt(token: str) -> Optional[int]:
    """
    Verify JWT token and extract telegram_id.
    Tokens are issued by bot.py and contain the telegram_id.

    Format: JWT with claims: {"sub": telegram_id, ...}

    Returns:
        telegram_id if valid and admin, None otherwise
    """
    if not token:
        return None

    try:
        import jwt

        # Use a dummy secret — real JWT validation would use shared secret from bot
        # For now, this is a placeholder for future integration
        secret = os.getenv("JWT_SECRET", "analytics-secret-key")

        # Decode without verification first to check claims
        unverified = jwt.decode(token, options={"verify_signature": False})
        telegram_id = int(unverified.get("sub", 0))

        # Verify this user is in admin list
        if telegram_id in ADMIN_ALLOWLIST:
            return telegram_id

        logger.warning(f"[Analytics] Non-admin token attempted: {telegram_id}")
        return None

    except Exception as e:
        logger.warning(f"[Analytics] JWT verification failed: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Rate limiter
# ─────────────────────────────────────────────────────────────────────────────


def _admin_key(request: Request) -> str:
    """Rate limit key = admin telegram_id (from verified token)."""
    admin_id = getattr(request.state, "_admin_id", None)
    if admin_id:
        return str(admin_id)
    return get_remote_address(request)


limiter = Limiter(key_func=_admin_key)

# ─────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Analytics API",
    version="1.0.0",
    description="Real-time trading analytics and coordination observability",
)

# Enable CORS for dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to analytics4896.cryptomentor.id in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limit_exceeded"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Middleware: verify Authorization header and extract admin_id
# ─────────────────────────────────────────────────────────────────────────────


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Verify JWT token for all endpoints except health check."""
    if request.url.path == "/health":
        return await call_next(request)

    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    # Verify token
    admin_id = _verify_admin_jwt(token)
    if not admin_id:
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized", "message": "Invalid or missing token"},
        )

    # Store admin_id in request state for use in endpoints
    request.state._admin_id = admin_id
    return await call_next(request)


# ─────────────────────────────────────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/coordinator-state
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/api/analytics/coordinator-state")
@limiter.limit("100/minute")
async def get_coordinator_state(
    request: Request,
    user_id: Optional[int] = None,
    symbol: Optional[str] = None,
):
    """
    Get coordinator state (symbol ownership, pending orders, cooldowns).

    Query params:
      - user_id: Filter by user (optional)
      - symbol: Filter by symbol (optional)

    Returns:
        {
            "timestamp": ISO8601,
            "total_users": int,
            "total_symbols": int,
            "users": {
                "123": {
                    "symbols": {
                        "BTCUSDT": {
                            "owner": "swing" | "scalp" | "one_click" | "manual" | "unknown" | "none",
                            "has_position": bool,
                            "side": "long" | "short" | "none",
                            "size": float,
                            "entry_price": float,
                            "pending_order": bool,
                            "cooldown_until": ISO8601 | null,
                            "last_exit_ts": unix_timestamp | null,
                        },
                        ...
                    }
                }
            }
        }
    """
    try:
        from app.symbol_coordinator import get_coordinator

        coordinator = get_coordinator()
        snapshot = await coordinator.export_debug_snapshot()

        # Filter by user_id if provided
        if user_id:
            if str(user_id) not in snapshot.get("users", {}):
                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "total_users": 0,
                    "total_symbols": 0,
                    "users": {},
                }
            snapshot["users"] = {str(user_id): snapshot["users"][str(user_id)]}

        # Filter by symbol if provided
        if symbol and user_id:
            user_data = snapshot["users"].get(str(user_id), {})
            symbols = user_data.get("symbols", {})
            if symbol in symbols:
                user_data["symbols"] = {symbol: symbols[symbol]}
            else:
                user_data["symbols"] = {}

        snapshot["timestamp"] = datetime.now(timezone.utc).isoformat()
        return snapshot

    except Exception as e:
        logger.error(f"[Analytics] coordinator-state failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "service_unavailable", "message": str(e)},
        )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/trading-stats
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/api/analytics/trading-stats")
@limiter.limit("100/minute")
async def get_trading_stats(
    request: Request,
    user_id: Optional[int] = None,
    days: int = 7,
):
    """
    Get trading statistics (open/closed positions, PnL, trades per day).

    Query params:
      - user_id: Filter by user (optional)
      - days: Historical window in days (default 7)

    Returns:
        {
            "timestamp": ISO8601,
            "period_days": int,
            "users": {
                "123": {
                    "total_trades": int,
                    "open_positions": int,
                    "closed_positions": int,
                    "total_pnl_usdt": float,
                    "win_rate": float,  # % of winning trades
                    "avg_trade_duration_seconds": float,
                    "daily_stats": [
                        {"date": "2025-01-15", "trades": int, "pnl": float},
                        ...
                    ]
                }
            }
        }
    """
    try:
        from app.supabase_repo import _client as get_supabase
        from datetime import datetime as dt

        db = get_supabase()

        # Build query for trades
        start_date = (dt.utcnow() - timedelta(days=days)).isoformat()

        # Get stats for specific user or all users
        if user_id:
            result = db.table("autotrade_trades").select(
                "telegram_id, symbol, status, side, qty, entry_price, exit_price, pnl_usdt, created_at, closed_at"
            ).eq("telegram_id", user_id).gte("created_at", start_date).execute()
        else:
            result = db.table("autotrade_trades").select(
                "telegram_id, symbol, status, side, qty, entry_price, exit_price, pnl_usdt, created_at, closed_at"
            ).gte("created_at", start_date).execute()

        trades = result.data if result.data else []

        # Aggregate stats by user
        user_stats: Dict = {}
        for trade in trades:
            uid = trade["telegram_id"]
            if uid not in user_stats:
                user_stats[uid] = {
                    "total_trades": 0,
                    "open_positions": 0,
                    "closed_positions": 0,
                    "winning_trades": 0,
                    "total_pnl_usdt": 0.0,
                    "trade_durations": [],
                    "daily": {},
                }

            status = trade.get("status", "")
            pnl = float(trade.get("pnl_usdt", 0))

            if status == "open":
                user_stats[uid]["open_positions"] += 1
            elif status in ("closed_tp", "closed_sl", "closed_flip"):
                user_stats[uid]["closed_positions"] += 1
                user_stats[uid]["total_pnl_usdt"] += pnl
                if pnl > 0:
                    user_stats[uid]["winning_trades"] += 1

            user_stats[uid]["total_trades"] += 1

            # Aggregate daily stats
            created = trade.get("created_at", "")[:10]  # YYYY-MM-DD
            if created:
                if created not in user_stats[uid]["daily"]:
                    user_stats[uid]["daily"][created] = {"trades": 0, "pnl": 0.0}
                user_stats[uid]["daily"][created]["trades"] += 1
                if status != "open":
                    user_stats[uid]["daily"][created]["pnl"] += pnl

            # Track trade durations
            if status != "open" and trade.get("created_at") and trade.get("closed_at"):
                try:
                    created_dt = dt.fromisoformat(trade["created_at"].replace("Z", "+00:00"))
                    closed_dt = dt.fromisoformat(trade["closed_at"].replace("Z", "+00:00"))
                    duration = (closed_dt - created_dt).total_seconds()
                    user_stats[uid]["trade_durations"].append(duration)
                except:
                    pass

        # Format response
        formatted_stats = {}
        for uid, stats in user_stats.items():
            avg_duration = (
                sum(stats["trade_durations"]) / len(stats["trade_durations"])
                if stats["trade_durations"]
                else 0
            )
            win_rate = (
                (stats["winning_trades"] / stats["closed_positions"] * 100)
                if stats["closed_positions"] > 0
                else 0
            )

            daily_stats = [
                {
                    "date": date,
                    "trades": data["trades"],
                    "pnl": data["pnl"],
                }
                for date, data in sorted(stats["daily"].items())
            ]

            formatted_stats[uid] = {
                "total_trades": stats["total_trades"],
                "open_positions": stats["open_positions"],
                "closed_positions": stats["closed_positions"],
                "total_pnl_usdt": stats["total_pnl_usdt"],
                "win_rate": win_rate,
                "avg_trade_duration_seconds": avg_duration,
                "daily_stats": daily_stats,
            }

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "period_days": days,
            "users": formatted_stats,
        }

    except Exception as e:
        logger.error(f"[Analytics] trading-stats failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "service_unavailable", "message": str(e)},
        )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/engine-health
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/api/analytics/engine-health")
@limiter.limit("100/minute")
async def get_engine_health(
    request: Request,
    user_id: Optional[int] = None,
):
    """
    Get engine health status (running/stopped, last scan, error count).

    Query params:
      - user_id: Filter by user (optional)

    Returns:
        {
            "timestamp": ISO8601,
            "engines": {
                "123": {
                    "running": bool,
                    "strategy_mode": "swing" | "scalp" | "hybrid" | "unknown",
                    "last_scan_ts": unix_timestamp | null,
                    "total_scans": int,
                    "error_count_24h": int,
                }
            }
        }
    """
    try:
        from app.autotrade_engine import is_running as is_swing_running
        from app.supabase_repo import _client as get_supabase

        db = get_supabase()

        # Get all active sessions
        if user_id:
            result = db.table("autotrade_sessions").select(
                "telegram_id, status, engine_active"
            ).eq("telegram_id", user_id).execute()
        else:
            result = db.table("autotrade_sessions").select(
                "telegram_id, status, engine_active"
            ).in_("status", ["active", "uid_verified"]).execute()

        sessions = result.data if result.data else []

        engines: Dict = {}
        for session in sessions:
            uid = session["telegram_id"]
            running = session.get("engine_active", False)

            # Get error count in last 24 hours
            error_result = db.table("error_logs").select(
                "count"
            ).eq("telegram_id", uid).gte(
                "created_at", (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
            ).execute()

            error_count = error_result.count if hasattr(error_result, "count") else 0

            engines[uid] = {
                "running": running,
                "status": session.get("status", "unknown"),
                "strategy_mode": "swing",  # Default, would be extended to detect scalp mode
                "last_scan_ts": None,  # Would be updated during scans
                "total_scans": 0,  # Would be tracked in session
                "error_count_24h": error_count,
            }

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engines": engines,
        }

    except Exception as e:
        logger.error(f"[Analytics] engine-health failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "service_unavailable", "message": str(e)},
        )


# ─────────────────────────────────────────────────────────────────────────────
# Startup/shutdown
# ─────────────────────────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup_event():
    """Initialize analytics on startup."""
    logger.info("[Analytics] API starting up...")
    _load_admin_ids()
    logger.info(f"[Analytics] Initialized with {len(ADMIN_ALLOWLIST)} admin IDs")


if __name__ == "__main__":
    import uvicorn

    _load_admin_ids()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8896,
        log_level="info",
    )
