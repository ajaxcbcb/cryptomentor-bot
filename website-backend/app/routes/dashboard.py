from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.auth.jwt import decode_token
from app.db.supabase import _client
from app.services import bitunix as bsvc
from app.services.risk_policy import (
    AUTO_RISK_MAX_PCT,
    AUTO_RISK_MIN_PCT,
    ONE_CLICK_WARN_THRESHOLD_PCT,
    HIGH_RISK_WARN_PCT,
    LOW_EQUITY_THRESHOLD_USD,
    LOW_EQUITY_MIN_RISK_PCT,
    auto_risk_min_by_equity,
    clamp_auto_risk,
    is_high_risk,
    is_valid_one_click_tier,
    normalize_one_click_shared_risk,
    one_click_risk_tiers,
    one_click_warn_required,
    risk_band,
    snap_one_click_risk_tier,
)
import asyncio
import os
import sys
from datetime import datetime, timezone
import httpx
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
bearer = HTTPBearer()
ALLOWED_RISK_MIN = AUTO_RISK_MIN_PCT
ALLOWED_RISK_MAX = AUTO_RISK_MAX_PCT
AUTOTRADE_LEVERAGE_MODE = "auto_max_pair"
AUTOTRADE_LEVERAGE_MIN = 1
AUTOTRADE_LEVERAGE_MAX = 200

# Autotrade engines persist multiple closed variants, not only plain "closed".
CLOSED_STATUSES = [
    "closed",
    "closed_tp",
    "closed_sl",
    "closed_tp1",
    "closed_tp2",
    "closed_tp3",
    "closed_flip",
    "closed_manual",
]


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload["sub"])


def _load_admin_ids() -> list[int]:
    """Load admin IDs from multiple env keys for resilience."""
    ids = set()
    raw_values = [
        os.getenv("ADMIN_IDS", ""),
        os.getenv("ADMIN1", ""),
        os.getenv("ADMIN2", ""),
        os.getenv("ADMIN_USER_ID", ""),
        os.getenv("ADMIN2_USER_ID", ""),
    ]
    for raw in raw_values:
        for token in str(raw).split(","):
            token = token.strip()
            if token.isdigit():
                ids.add(int(token))
    return sorted(ids)


def _fmt_price(v: float) -> str:
    try:
        return f"{float(v):,.4f}"
    except Exception:
        return str(v)


def _fmt_money(v: float) -> str:
    try:
        return f"{float(v):,.2f}"
    except Exception:
        return str(v)


def _telegram_safe_text(value: str) -> str:
    """Normalize escaped newlines/tabs so Telegram renders readable message blocks."""
    text = str(value or "")
    # Handle double-escaped payloads first, then regular escaped sequences.
    return (
        text
        .replace("\\\\r\\\\n", "\n")
        .replace("\\\\n", "\n")
        .replace("\\\\t", "\t")
        .replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
    )


async def _send_telegram_html(
    client: httpx.AsyncClient,
    bot_token: str,
    chat_id: int,
    text: str,
    reply_markup: dict | None = None,
) -> tuple[bool, str | None]:
    try:
        payload = {
            "chat_id": int(chat_id),
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        resp = await client.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json=payload,
        )
        if resp.status_code >= 400:
            return False, f"http_{resp.status_code}"
        body = resp.json() if resp.text else {}
        if not body.get("ok", False):
            return False, str(body.get("description") or "telegram_api_error")
        return True, None
    except Exception as e:
        return False, str(e)


def _fetch_all_user_ids() -> list[int]:
    s = _client()
    user_ids: list[int] = []
    seen: set[int] = set()
    offset = 0
    page = 1000
    while True:
        res = s.table("users").select("telegram_id").range(offset, offset + page - 1).execute()
        batch = res.data or []
        for row in batch:
            raw = row.get("telegram_id")
            try:
                uid = int(raw)
            except Exception:
                continue
            if uid <= 0 or uid in seen:
                continue
            seen.add(uid)
            user_ids.append(uid)
        if len(batch) < page:
            break
        offset += page
    return user_ids


class SampleTradeBroadcastRequest(BaseModel):
    pair: str = "BTCUSDT"
    direction: str = "Long"
    entry_price: float = 66112.6
    tp_price: float = 67320.0
    sl_price: float = 65550.0
    risk_pnl_usd: float = 50.33
    risk_pct_equity: float = 1.0
    order_id: str = "CM-SAMPLE-001"
    close_price: float = 67320.0
    closed_pnl_usd: float = 63.44
    close_reason: str = "TP Hit"
    trade_url: str = "https://cryptomentor.id"
    target_chat_id: int | None = None


class EngineAutoModePayload(BaseModel):
    enabled: bool


class EngineModePayload(BaseModel):
    trading_mode: str


class EngineStackMentorPayload(BaseModel):
    enabled: bool


AUTO_MODE_MIXED_LOCK_REASON = (
    "Mixed mode uses per-symbol auto routing and bypasses legacy global auto-switch."
)


def _normalize_trading_mode(mode_value: Any) -> str:
    mode = str(mode_value or "").strip().lower()
    if mode in {"scalping", "swing", "mixed"}:
        return mode
    return "swing"


def _is_auto_mode_locked(mode_value: Any) -> bool:
    return _normalize_trading_mode(mode_value) == "mixed"


def _get_autotrade_session_row(tg_id: int) -> dict:
    s = _client()
    res = s.table("autotrade_sessions").select("*").eq(
        "telegram_id", int(tg_id)
    ).limit(1).execute()
    row = (res.data or [None])[0]
    return row or {}


def _upsert_autotrade_session_fields(tg_id: int, fields: dict[str, Any]) -> dict:
    payload = {
        "telegram_id": int(tg_id),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    s = _client()
    res = s.table("autotrade_sessions").upsert(
        payload, on_conflict="telegram_id"
    ).execute()
    if res.data:
        row = (res.data or [None])[0]
        if row:
            return row
    return _get_autotrade_session_row(tg_id)


def _derive_running_from_session(session_row: dict) -> bool:
    status = str(session_row.get("status") or "").strip().lower()
    engine_active = bool(session_row.get("engine_active"))
    is_stopped = status == "stopped"
    return (not is_stopped) and (engine_active or status in ("active", "uid_verified"))


def _is_engine_runtime_running(tg_id: int, session_row: dict | None = None) -> bool:
    fallback_running = _derive_running_from_session(session_row or {})
    try:
        from app.routes import engine as engine_routes

        ae = engine_routes._get_engine()
        return bool(ae.is_running(int(tg_id)))
    except Exception as e:
        logger.debug(f"[EngineControl:{tg_id}] Runtime running check fallback: {e}")
        return fallback_running


async def _switch_user_mode_runtime(tg_id: int, trading_mode: str) -> dict:
    target_mode = _normalize_trading_mode(trading_mode)
    try:
        from app.routes import engine as engine_routes

        # Ensure Bismillah app.* modules are registered before importing manager.
        for submod in ("trading_mode", "supabase_repo", "trading_mode_manager"):
            engine_routes._load_bismillah_submodule(submod, f"bismillah.app.{submod}")

        manager_mod = sys.modules.get("app.trading_mode_manager")
        if manager_mod is None:
            raise RuntimeError("trading_mode_manager module is not available")

        TradingModeManager = getattr(manager_mod, "TradingModeManager", None)
        TradingMode = getattr(manager_mod, "TradingMode", None)
        if TradingModeManager is None or TradingMode is None:
            raise RuntimeError("Trading mode runtime dependencies are unavailable")

        bot_token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
        if not bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

        from telegram import Bot

        bot = Bot(token=bot_token)
        target_enum = TradingMode.from_string(target_mode)
        result = await TradingModeManager.switch_mode(
            user_id=int(tg_id),
            new_mode=target_enum,
            bot=bot,
            context=None,
            switch_source="manual",
        )
        if not isinstance(result, dict):
            return {"success": False, "message": "Invalid switch_mode response"}
        return result
    except ModuleNotFoundError as e:
        missing_module = str(getattr(e, "name", "") or "").strip() or "unknown"
        return {
            "success": False,
            "error_code": "runtime_dependency_missing",
            "dependency": missing_module,
            "message": (
                f"runtime_dependency_missing:{missing_module} "
                "Install required runtime dependencies in website-backend venv "
                "(python-telegram-bot[job-queue]==21.6)."
            ),
        }
    except Exception as e:
        return {
            "success": False,
            "error_code": "runtime_switch_failed",
            "message": str(e),
        }


def _build_engine_controls_state(session_row: dict, runtime_running: bool | None = None) -> dict:
    session = session_row or {}
    trading_mode = _normalize_trading_mode(session.get("trading_mode"))
    auto_locked = _is_auto_mode_locked(trading_mode)
    auto_mode_enabled = bool(session.get("auto_mode_enabled", False))
    if auto_locked:
        auto_mode_enabled = False
    stackmentor_enabled = bool(session.get("stackmentor_enabled", True))
    running = _derive_running_from_session(session) if runtime_running is None else bool(runtime_running)
    return {
        "trading_mode": trading_mode,
        "auto_mode_enabled": auto_mode_enabled,
        "auto_mode_locked": auto_locked,
        "auto_mode_lock_reason": AUTO_MODE_MIXED_LOCK_REASON if auto_locked else None,
        "stackmentor_enabled": stackmentor_enabled,
        # Backward-compatible alias used by current web app state mapping.
        "stackmentor_active": stackmentor_enabled,
        "status": session.get("status"),
        "engine_active": bool(session.get("engine_active", False)),
        "is_active": str(session.get("status") or "").strip().lower() == "active",
        "running": running,
    }


@router.post("/admin/broadcast-sample-trades")
async def admin_broadcast_sample_trades(
    payload: SampleTradeBroadcastRequest,
    tg_id: int = Depends(get_current_user),
):
    """
    Admin-only: broadcast two sample trade notifications to all Telegram users:
    1) Trade opened
    2) Trade closed
    """
    admin_ids = _load_admin_ids()
    if tg_id not in admin_ids:
        raise HTTPException(status_code=403, detail="Admin access required")

    bot_token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not bot_token:
        raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN is not configured")

    now_str = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M:%S UTC")
    direction = str(payload.direction or "Long").strip().title()

    open_text = (
        "🚀 <b>Cryptomentor AI | Trade Opened</b>\n\n"
        f"📈 <b>Direction:</b> {direction}\n"
        f"🪙 <b>Pair:</b> {payload.pair}\n"
        f"🎯 <b>Entry:</b> {_fmt_price(payload.entry_price)}\n"
        f"🏁 <b>Take Profit:</b> {_fmt_price(payload.tp_price)}\n"
        f"🛡️ <b>Stop Loss:</b> {_fmt_price(payload.sl_price)}\n"
        f"💵 <b>Risk PnL:</b> ${_fmt_money(payload.risk_pnl_usd)}\n"
        f"📊 <b>Risk on Equity:</b> {_fmt_money(payload.risk_pct_equity)}%\n"
        f"🧾 <b>Order ID:</b> {payload.order_id}\n"
        f"🕒 <b>Date & Time:</b> {now_str}\n\n"
        "🤖 <i>Execution confirmed by AutoTrade Engine.</i>"
    )
    closed_text = (
        "✅ <b>Cryptomentor AI | Trade Closed</b>\n\n"
        f"🪙 <b>Pair:</b> {payload.pair}\n"
        f"📈 <b>Direction:</b> {direction}\n"
        f"🎯 <b>Entry:</b> {_fmt_price(payload.entry_price)}\n"
        f"🏁 <b>Exit:</b> {_fmt_price(payload.close_price)}\n"
        f"💰 <b>PnL:</b> ${_fmt_money(payload.closed_pnl_usd)}\n"
        f"🏆 <b>Result:</b> {payload.close_reason}\n"
        f"🧾 <b>Order ID:</b> {payload.order_id}\n"
        f"🕒 <b>Date & Time:</b> {now_str}\n\n"
        "📌 <i>Risk managed. Trade completed professionally.</i>"
    )

    reply_markup = {
        "inline_keyboard": [[
            {"text": "📊 View Trade Details", "url": payload.trade_url or "https://cryptomentor.id"}
        ]]
    }

    if payload.target_chat_id:
        target_uids = [int(payload.target_chat_id)]
    else:
        target_uids = await asyncio.to_thread(_fetch_all_user_ids)
    if not target_uids:
        return {
            "success": True,
            "message": "No users found to broadcast.",
            "total_users": 0,
            "open_sent": 0,
            "open_failed": 0,
            "closed_sent": 0,
            "closed_failed": 0,
        }

    open_sent = 0
    open_failed = 0
    closed_sent = 0
    closed_failed = 0

    async with httpx.AsyncClient(timeout=12.0) as client:
        for uid in target_uids:
            ok_open, _ = await _send_telegram_html(
                client=client,
                bot_token=bot_token,
                chat_id=uid,
                text=open_text,
                reply_markup=reply_markup,
            )
            if ok_open:
                open_sent += 1
            else:
                open_failed += 1

            await asyncio.sleep(0.04)

            ok_closed, _ = await _send_telegram_html(
                client=client,
                bot_token=bot_token,
                chat_id=uid,
                text=closed_text,
                reply_markup=reply_markup,
            )
            if ok_closed:
                closed_sent += 1
            else:
                closed_failed += 1

            await asyncio.sleep(0.04)

    logger.info(
        "[AdminBroadcastSampleTrades] requester=%s users=%s open=(%s/%s) closed=(%s/%s)",
        tg_id, len(target_uids), open_sent, open_failed, closed_sent, closed_failed
    )

    return {
        "success": True,
        "total_users": len(target_uids),
        "open_sent": open_sent,
        "open_failed": open_failed,
        "closed_sent": closed_sent,
        "closed_failed": closed_failed,
    }


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
        "status, engine_active, trading_mode, auto_mode_enabled, stackmentor_enabled"
    ).eq("telegram_id", tg_id).limit(1).execute()
    row = (res.data or [{}])[0]
    is_running = _is_engine_runtime_running(tg_id, row)
    engine = _build_engine_controls_state(row, runtime_running=is_running)
    return {
        "running": is_running,
        "status": row.get("status"),
        "engine": engine,
        "trading_mode": engine.get("trading_mode", "swing"),
    }


@router.put("/engine/auto-mode")
async def update_engine_auto_mode(
    payload: EngineAutoModePayload,
    tg_id: int = Depends(get_current_user),
):
    session = _get_autotrade_session_row(tg_id)
    current_mode = _normalize_trading_mode(session.get("trading_mode"))
    next_enabled = bool(payload.enabled)
    if _is_auto_mode_locked(current_mode):
        next_enabled = False
    row = _upsert_autotrade_session_fields(
        tg_id,
        {
            "trading_mode": current_mode,
            "auto_mode_enabled": next_enabled,
        },
    )
    engine = _build_engine_controls_state(row)
    return {
        "success": True,
        "engine": engine,
    }


@router.put("/engine/mode")
async def update_engine_mode(
    payload: EngineModePayload,
    tg_id: int = Depends(get_current_user),
):
    requested_mode = str(payload.trading_mode or "").strip().lower()
    if requested_mode not in {"scalping", "swing", "mixed"}:
        raise HTTPException(status_code=400, detail="trading_mode must be scalping, swing, or mixed")

    session = _get_autotrade_session_row(tg_id)
    current_mode = _normalize_trading_mode(session.get("trading_mode"))
    is_running = _is_engine_runtime_running(tg_id, session)
    runtime_action = "persisted_only"

    if is_running and requested_mode != current_mode:
        switch_result = await _switch_user_mode_runtime(tg_id, requested_mode)
        if not switch_result.get("success"):
            error_code = str(switch_result.get("error_code") or "").strip().lower()
            status_code = 503 if error_code == "runtime_dependency_missing" else 500
            raise HTTPException(
                status_code=status_code,
                detail=f"Failed to switch mode: {switch_result.get('message') or 'unknown error'}",
            )
        runtime_action = "switched_live"
        session = _get_autotrade_session_row(tg_id)
    else:
        session = _upsert_autotrade_session_fields(
            tg_id,
            {"trading_mode": requested_mode},
        )

    if requested_mode == "mixed":
        # Mixed mode bypasses legacy global auto-switching.
        session = _upsert_autotrade_session_fields(
            tg_id,
            {
                "trading_mode": "mixed",
                "auto_mode_enabled": False,
            },
        )

    running_after = _is_engine_runtime_running(tg_id, session)
    engine = _build_engine_controls_state(session, runtime_running=running_after)
    return {
        "success": True,
        "runtime_action": runtime_action,
        "engine": engine,
    }


@router.put("/engine/stackmentor")
async def update_engine_stackmentor(
    payload: EngineStackMentorPayload,
    tg_id: int = Depends(get_current_user),
):
    session = _upsert_autotrade_session_fields(
        tg_id,
        {"stackmentor_enabled": bool(payload.enabled)},
    )
    engine = _build_engine_controls_state(session)
    return {
        "success": True,
        "note": "StackMentor toggle is preference-only in this release.",
        "engine": engine,
    }


@router.get("/settings")
async def get_settings(tg_id: int = Depends(get_current_user)):
    """
    Get current trading settings (risk_per_trade, leverage, etc.)

    Returns:
    - risk_per_trade: Current risk percentage (0.25% to 10.0%)
    - leverage: Baseline leverage value (legacy compatibility only)
    - leverage_mode: AutoTrade leverage policy mode
    - trading_mode: Current mode (scalping, swing, mixed)
    - risk_mode: Risk profile (conservative, moderate, aggressive)
    - equity: LIVE equity from Bitunix (balance + unrealized PnL) — used for risk calcs
    - balance: Free available balance
    - unrealized_pnl: Current open position P&L
    """
    s = _client()
    res = s.table("autotrade_sessions").select(
        "risk_per_trade, leverage, margin_mode, trading_mode, risk_mode"
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

    min_risk_pct = auto_risk_min_by_equity(equity)
    stored_risk = row.get("risk_per_trade")
    risk_value = clamp_auto_risk(stored_risk, default=3.0, equity=equity)
    one_click_risk_value = normalize_one_click_shared_risk(stored_risk, default=3.0)
    leverage_baseline = int(row.get("leverage") or 10)
    leverage_baseline = max(AUTOTRADE_LEVERAGE_MIN, min(AUTOTRADE_LEVERAGE_MAX, leverage_baseline))
    band = risk_band(risk_value, all_in=False)
    return {
        "success": True,
        "risk_per_trade": risk_value,
        "one_click_risk_per_trade": one_click_risk_value,
        "leverage": leverage_baseline,
        "leverage_baseline": leverage_baseline,
        "leverage_mode": AUTOTRADE_LEVERAGE_MODE,
        "leverage_range": {
            "min": AUTOTRADE_LEVERAGE_MIN,
            "max": AUTOTRADE_LEVERAGE_MAX,
        },
        "leverage_note": "AutoTrade executes with max leverage allowed for each pair.",
        "margin_mode": row.get("margin_mode") or "cross",
        "trading_mode": row.get("trading_mode") or "swing",
        "risk_mode": row.get("risk_mode") or "moderate",
        "equity": round(equity, 2),           # available + frozen + unrealized (for risk sizing)
        "balance": round(available, 2),        # free/available balance only
        "frozen": round(frozen, 2),            # locked in open positions
        "unrealized_pnl": round(unrealized_pnl, 2),
        "risk_policy": {
            "mode": "autotrade",
            "min_pct": min_risk_pct,
            "max_pct": ALLOWED_RISK_MAX,
            "high_risk_warn_pct": HIGH_RISK_WARN_PCT,
            "low_equity_threshold_usd": LOW_EQUITY_THRESHOLD_USD,
            "low_equity_min_pct": LOW_EQUITY_MIN_RISK_PCT,
            "low_equity_guard_active": min_risk_pct > ALLOWED_RISK_MIN,
            "band_key": band.key,
            "band_label": band.label,
            "high_risk": is_high_risk(risk_value),
        },
        "one_click_risk_policy": {
            "mode": "one_click",
            "tiers": list(one_click_risk_tiers()),
            "all_in_pct": float(max(one_click_risk_tiers())),
            "warning_threshold_pct": ONE_CLICK_WARN_THRESHOLD_PCT,
            "snap_rule": "nearest_tier",
            "high_risk_warning": one_click_warn_required(one_click_risk_value),
        },
    }


@router.put("/settings/risk")
async def update_risk_setting(    payload: dict,
    tg_id: int = Depends(get_current_user)
):
    """
    Update shared risk_per_trade for user.

    scope=autotrade: 0.25% up to 10.0% (auto risk policy).
    scope=one_click: exact tier only (3/5/10/25/50/100).

    Fixed dollar risk: position_size = (balance × risk%) / SL_distance
    - Tight SL → Larger position (same dollar risk)
    - Wide SL → Smaller position (same dollar risk)

    Args:
        payload: {"risk_per_trade": 0.5} or {"risk_per_trade": 0.25}

    Returns:
        {"success": True, "risk_per_trade": 0.5, "note": "Updated successfully"}
    """
    from datetime import datetime

    raw_scope = payload.get("scope")
    scope = str(raw_scope or "").strip().lower()

    try:
        risk = float(payload.get("risk_per_trade") or 3.0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="risk_per_trade must be a number")

    # Backward compatibility: old clients may omit scope while sending one-click tiers.
    if not scope:
        if is_valid_one_click_tier(risk) and risk > ALLOWED_RISK_MAX:
            scope = "one_click"
        else:
            scope = "autotrade"
    if scope not in {"autotrade", "one_click"}:
        raise HTTPException(status_code=400, detail="scope must be 'autotrade' or 'one_click'")

    s = _client()
    row_res = (
        s.table("autotrade_sessions")
        .select("current_balance, initial_deposit")
        .eq("telegram_id", tg_id)
        .limit(1)
        .execute()
    )
    row = (row_res.data or [{}])[0]

    equity = 0.0
    try:
        acc = await bsvc.fetch_account(tg_id)
        if acc.get("success"):
            available = float(acc.get("available", 0) or 0)
            frozen = float(acc.get("frozen", 0) or 0)
            unrealized_pnl = float(acc.get("total_unrealized_pnl", 0) or 0)
            equity = available + frozen + unrealized_pnl
    except Exception as exc:
        logger.warning(f"[RiskSetting:{tg_id}] Live equity fetch failed: {exc}")

    if equity <= 0:
        equity = float(row.get("current_balance") or row.get("initial_deposit") or 0)

    min_risk_pct = auto_risk_min_by_equity(equity)
    if scope == "one_click":
        tiers = list(one_click_risk_tiers())
        if not is_valid_one_click_tier(risk):
            tiers_text = ", ".join(str(int(t)) for t in tiers)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid one_click risk: {risk}. Must be one of [{tiers_text}]",
            )
        requested = float(risk)
        accepted = snap_one_click_risk_tier(requested, default=3.0)
        risk_value = accepted
    else:
        if risk < min_risk_pct or risk > ALLOWED_RISK_MAX:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid risk: {risk}. Must be between {min_risk_pct}% and {ALLOWED_RISK_MAX}%"
            )
        requested = float(risk)
        accepted = clamp_auto_risk(requested, default=3.0, equity=equity)
        risk_value = accepted

    try:
        s.table("autotrade_sessions").update({
            "risk_per_trade": float(risk_value),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("telegram_id", tg_id).execute()
        logger.info(f"[RiskSetting:{tg_id}] Updated risk_per_trade to {risk_value}% (scope={scope})")
    except Exception as e:
        logger.error(f"[RiskSetting:{tg_id}] Failed to update risk: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update risk: {e}")

    one_click_synced = normalize_one_click_shared_risk(risk_value, default=3.0)
    band = risk_band(accepted, all_in=(scope == "one_click" and accepted >= max(one_click_risk_tiers())))
    return {
        "success": True,
        "scope": scope,
        "risk_per_trade": accepted,
        "one_click_risk_per_trade": one_click_synced,
        "risk_policy": {
            "mode": "autotrade" if scope == "autotrade" else "one_click",
            "requested_pct": requested,
            "accepted_pct": accepted,
            "min_pct": min_risk_pct,
            "max_pct": ALLOWED_RISK_MAX,
            "high_risk_warn_pct": HIGH_RISK_WARN_PCT,
            "low_equity_threshold_usd": LOW_EQUITY_THRESHOLD_USD,
            "low_equity_min_pct": LOW_EQUITY_MIN_RISK_PCT,
            "low_equity_guard_active": min_risk_pct > ALLOWED_RISK_MIN,
            "equity_used_usd": round(float(equity), 2),
            "band_key": band.key,
            "band_label": band.label,
            "high_risk": is_high_risk(float(min(accepted, ALLOWED_RISK_MAX))),
        },
        "one_click_risk_policy": {
            "mode": "one_click",
            "tiers": list(one_click_risk_tiers()),
            "all_in_pct": float(max(one_click_risk_tiers())),
            "warning_threshold_pct": ONE_CLICK_WARN_THRESHOLD_PCT,
            "snap_rule": "nearest_tier",
            "high_risk_warning": one_click_warn_required(one_click_synced),
        },
        "note": f"Risk updated to {accepted}% per trade (scope={scope})",
    }


@router.put("/settings/leverage")
async def update_leverage(
    payload: dict,
    tg_id: int = Depends(get_current_user)
):
    """
    Update baseline leverage setting (1-20x).
    Note: AutoTrade execution uses max leverage allowed for each pair.
    """
    from datetime import datetime

    leverage = payload.get("leverage")
    if leverage is None:
        raise HTTPException(status_code=400, detail="Missing 'leverage' field")

    try:
        leverage = int(leverage)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Leverage must be an integer")

    if leverage < AUTOTRADE_LEVERAGE_MIN or leverage > AUTOTRADE_LEVERAGE_MAX:
        raise HTTPException(
            status_code=400,
            detail=f"Leverage must be between {AUTOTRADE_LEVERAGE_MIN} and {AUTOTRADE_LEVERAGE_MAX}"
        )

    s = _client()
    try:
        s.table("autotrade_sessions").update({
            "leverage": leverage,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("telegram_id", tg_id).execute()
        logger.info(
            f"[Leverage:{tg_id}] Updated baseline to {leverage}x "
            f"(execution mode={AUTOTRADE_LEVERAGE_MODE})"
        )
    except Exception as e:
        logger.error(f"[Leverage:{tg_id}] Failed to update: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update leverage: {e}")

    return {
        "success": True,
        "leverage": leverage,
        "leverage_baseline": leverage,
        "leverage_mode": AUTOTRADE_LEVERAGE_MODE,
        "note": "Baseline saved. AutoTrade execution uses max leverage allowed for each pair."
    }


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
    # Delegate to the canonical implementation to avoid payload drift.
    from app.routes.performance import build_performance_payload

    return await build_performance_payload(tg_id=int(tg_id))


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
        "trading_mode, engine_active, auto_mode_enabled, stackmentor_enabled, risk_mode, risk_per_trade, status, current_balance, total_profit"
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
    ).in_("status", CLOSED_STATUSES).gte("closed_at", since).execute()
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

    engine_controls = _build_engine_controls_state(session)
    return {
        "user": user,
        "bitunix": {
            "linked": bsvc.get_user_api_keys(tg_id) is not None,
            "account": live_account,
            "error": bitunix_error,
        },
        "engine": {
            "trading_mode": engine_controls.get("trading_mode", "swing"),
            "stackmentor_active": engine_controls.get("stackmentor_active", True),
            "stackmentor_enabled": engine_controls.get("stackmentor_enabled", True),
            "auto_mode_enabled": engine_controls.get("auto_mode_enabled", False),
            "auto_mode_locked": engine_controls.get("auto_mode_locked", False),
            "auto_mode_lock_reason": engine_controls.get("auto_mode_lock_reason"),
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


# ─────────────────────────────────────────────────────────────────────────────
# REFERRAL (Community Partners) endpoints
# ─────────────────────────────────────────────────────────────────────────────

import re as _re

APPROVED_REFERRAL_STATUSES = ("approved", "uid_verified", "active", "verified")


def _is_unknown_column_error(exc: Exception, column: str) -> bool:
    msg = str(exc).lower()
    col = column.lower()
    return col in msg and ("schema cache" in msg or "column" in msg or "does not exist" in msg)


def _count_partner_members_live(s, partner_telegram_id: int, community_code: str | None) -> Optional[int]:
    """Count approved referrals with canonical + legacy attribution fallback."""
    statuses = list(APPROVED_REFERRAL_STATUSES)
    total = 0
    has_result = False
    resolved_partner_col_available = True

    # Canonical attribution: resolved partner ownership.
    try:
        primary_res = (
            s.table("user_verifications")
            .select("telegram_id", count="exact")
            .eq("resolved_partner_telegram_id", int(partner_telegram_id))
            .in_("status", statuses)
            .execute()
        )
        total += int(primary_res.count or 0)
        has_result = True
    except Exception as exc:
        if _is_unknown_column_error(exc, "resolved_partner_telegram_id"):
            resolved_partner_col_available = False
            logger.info(
                "[Referral] resolved_partner_telegram_id unavailable; using legacy community_code fallback only."
            )
        else:
            logger.error(
                "[Referral] Failed primary partner member-count query partner_id=%s: %s",
                partner_telegram_id,
                exc,
            )

    # Legacy attribution: rows tied to partner community_code.
    code = str(community_code or "").strip().lower()
    if code:
        try:
            fallback_query = (
                s.table("user_verifications")
                .select("telegram_id", count="exact")
                .eq("community_code", code)
                .in_("status", statuses)
            )
            # Avoid double-counting rows already captured by canonical attribution.
            if resolved_partner_col_available:
                fallback_query = fallback_query.is_("resolved_partner_telegram_id", "null")
            fallback_res = fallback_query.execute()
            total += int(fallback_res.count or 0)
            has_result = True
        except Exception as exc:
            # Retry without canonical null-filter when resolved column is missing.
            if resolved_partner_col_available and _is_unknown_column_error(exc, "resolved_partner_telegram_id"):
                resolved_partner_col_available = False
                logger.info(
                    "[Referral] resolved_partner_telegram_id unavailable during fallback query; retrying without null filter."
                )
                try:
                    fallback_res = (
                        s.table("user_verifications")
                        .select("telegram_id", count="exact")
                        .eq("community_code", code)
                        .in_("status", statuses)
                        .execute()
                    )
                    total += int(fallback_res.count or 0)
                    has_result = True
                except Exception as retry_exc:
                    if _is_unknown_column_error(retry_exc, "community_code"):
                        logger.info(
                            "[Referral] community_code unavailable; cannot run legacy member-count fallback."
                        )
                    else:
                        logger.error(
                            "[Referral] Failed legacy partner member-count query partner_id=%s code=%s: %s",
                            partner_telegram_id,
                            code,
                            retry_exc,
                        )
            elif _is_unknown_column_error(exc, "community_code"):
                logger.info("[Referral] community_code unavailable; cannot run legacy member-count fallback.")
            else:
                logger.error(
                    "[Referral] Failed legacy partner member-count query partner_id=%s code=%s: %s",
                    partner_telegram_id,
                    code,
                    exc,
                )

    return total if has_result else None


def _slugify(name: str) -> str:
    slug = _re.sub(r'[^a-zA-Z0-9]', '', name.lower())
    return slug[:20]


class ReferralRegisterInput(BaseModel):
    community_name: str
    bitunix_referral_code: str
    bitunix_uid: str


@router.get("/referral")
async def get_referral(tg_id: int = Depends(get_current_user)):
    """Get current user's referral/community partner status."""
    s = _client()
    res = s.table("community_partners").select("*").eq("telegram_id", tg_id).limit(1).execute()
    row = (res.data or [None])[0]
    if not row:
        return {"registered": False}

    status = row.get("status", "pending")
    code = row.get("community_code", "")
    invite_link = f"https://cryptomentor.id/?ref={code}" if status == "active" else None
    live_member_count = _count_partner_members_live(s, tg_id, code)
    member_count = int(row.get("member_count") or 0) if live_member_count is None else int(live_member_count)
    if live_member_count is None:
        logger.warning(
            "[Referral] Falling back to stored member_count partner_id=%s code=%s value=%s",
            tg_id,
            code,
            member_count,
        )

    return {
        "registered": True,
        "status": status,
        "community_name": row.get("community_name"),
        "community_code": code,
        "bitunix_referral_code": row.get("bitunix_referral_code"),
        "bitunix_referral_url": row.get("bitunix_referral_url"),
        "member_count": member_count,
        "invite_link": invite_link,
        "created_at": row.get("created_at"),
    }


@router.post("/referral/register")
async def register_referral(
    payload: ReferralRegisterInput,
    tg_id: int = Depends(get_current_user),
):
    """Register as a community partner / referral partner."""
    name = payload.community_name.strip()
    if len(name) < 3:
        raise HTTPException(status_code=400, detail="Community name must be at least 3 characters")
    if len(name) > 50:
        raise HTTPException(status_code=400, detail="Community name must be at most 50 characters")

    ref_code = payload.bitunix_referral_code.strip()
    if len(ref_code) < 2:
        raise HTTPException(status_code=400, detail="Invalid Bitunix referral code")

    uid = payload.bitunix_uid.strip()
    if not uid.isdigit() or len(uid) < 5:
        raise HTTPException(status_code=400, detail="Invalid Bitunix UID (minimum 5 digits)")

    s = _client()

    # Generate unique community code
    import random
    code = _slugify(name)
    existing = s.table("community_partners").select("id").eq("community_code", code).limit(1).execute()
    if existing.data:
        code = code + str(random.randint(10, 99))

    ref_url = f"https://www.bitunix.com/register?vipCode={ref_code}"

    try:
        s.table("community_partners").upsert({
            "telegram_id": int(tg_id),
            "community_name": name,
            "community_code": code,
            "bitunix_referral_code": ref_code,
            "bitunix_referral_url": ref_url,
            "bitunix_uid": uid,
            "status": "pending",
            "member_count": 0,
            "updated_at": datetime.utcnow().isoformat(),
        }, on_conflict="telegram_id").execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save registration: {e}")

    # Notify admins via Telegram bot (best-effort)
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    _admin_id_set = set()
    for _key in ("ADMIN_IDS", "ADMIN1", "ADMIN2", "ADMIN3", "ADMIN_USER_ID", "ADMIN2_USER_ID"):
        for _part in os.getenv(_key, "").split(","):
            _part = _part.strip()
            if _part.isdigit():
                _admin_id_set.add(int(_part))
    admin_ids = sorted(_admin_id_set)
    if bot_token and admin_ids:
        msg = _telegram_safe_text(
            (
            "🔔 <b>New Referral Partner Registration (Web)</b>\n\n"
            "<b>Applicant Details</b>\n"
            f"• Telegram ID: <code>{tg_id}</code>\n"
            f"• Community Name: <b>{name}</b>\n"
            f"• Community Code: <code>{code}</code>\n"
            f"• Bitunix Referral Code: <code>{ref_code}</code>\n"
            f"• Bitunix UID: <code>{uid}</code>\n"
            f"• Bitunix URL: <code>{ref_url}</code>\n\n"
            "Please choose an action:"
            )
        )
        admin_reply_markup = {
            "inline_keyboard": [[
                {"text": "✅ APPROVE", "callback_data": f"community_acc_{tg_id}"},
                {"text": "❌ REJECT",  "callback_data": f"community_reject_{tg_id}"},
            ]]
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            for admin_id in admin_ids:
                try:
                    await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={
                            "chat_id": admin_id,
                            "text": msg,
                            "parse_mode": "HTML",
                            "disable_web_page_preview": True,
                            "reply_markup": admin_reply_markup,
                        },
                    )
                except Exception:
                    pass

    return {
        "success": True,
        "community_code": code,
        "status": "pending",
        "message": "Pendaftaran berhasil! Admin akan mereview dalam 1-2 hari kerja.",
    }
