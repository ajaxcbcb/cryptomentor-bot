"""
Live market signals endpoint.

Pulls real-time 24h ticker data from Binance's public spot API and derives
lightweight directional signals for the dashboard. No hardcoded prices —
every value reflects the current market state at request time.

Symbols are intentionally a small fixed set so the dashboard stays snappy
and matches the existing three-card layout. Tier (free vs pro) is decided
per symbol so the gating UI keeps working.
"""

from datetime import datetime, timezone, timedelta

TZ_UTC8 = timezone(timedelta(hours=8))
from typing import List, Dict, Any

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db.supabase import _client
from app.routes.dashboard import get_current_user
from app.services import bitunix as bsvc
from app.auth.jwt import decode_token

_bearer = HTTPBearer(auto_error=False)

def _optional_user(
    request: Request,
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> int | None:
    """Return tg_id if a valid JWT is present, else None (public access)."""
    if creds and creds.credentials:
        payload = decode_token(creds.credentials)
        if payload:
            return int(payload["sub"])
    return None

# Window during which a freshly announced signal can still be entered via
# 1-click. The position size is dynamically scaled by the live SL distance
# so a late entry stays risk-equivalent to an on-time entry.
SIGNAL_ENTRY_WINDOW_SECONDS = 5 * 60

# Quantity precision per symbol — mirrors Bismillah/app/autotrade_engine.py.
_QTY_PRECISION = {"BTCUSDT": 3, "ETHUSDT": 2, "AVAXUSDT": 2}

router = APIRouter(prefix="/dashboard", tags=["signals"])

# ── Signal cache ─────────────────────────────────────────────────────────────
# Keyed by binance symbol (e.g. "BTCUSDT").
# Each entry: {"signal": dict, "generated_at": datetime, "ticker_snapshot": dict}
# A cached signal is reused until it expires (>= SIGNAL_ENTRY_WINDOW_SECONDS old),
# at which point a fresh signal is generated with a new generated_at timestamp.
_signal_cache: Dict[str, Dict[str, Any]] = {}

# (display_pair, binance_symbol, tier, type)
_WATCHLIST = [
    ("BTC/USDT", "BTCUSDT", "free", "Scalp"),
    ("ETH/USDT", "ETHUSDT", "pro",  "Swing"),
    ("AVAX/USDT", "AVAXUSDT", "pro", "Scalp"),
]

_BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/24hr"


def _fmt(price: float) -> str:
    if price >= 1000:
        return f"{price:,.0f}"
    if price >= 10:
        return f"{price:,.2f}"
    if price >= 1:
        return f"{price:,.3f}"
    return f"{price:,.5f}"


def _build_signal(idx: int, pair: str, tier: str, sig_type: str, ticker: dict, generated_at: datetime = None) -> Dict[str, Any]:
    last = float(ticker["lastPrice"])
    high = float(ticker["highPrice"])
    low = float(ticker["lowPrice"])
    change_pct = float(ticker["priceChangePercent"])

    # Direction: positive 24h momentum -> LONG, negative -> SHORT.
    direction = "LONG" if change_pct >= 0 else "SHORT"

    # Confidence scales with absolute momentum, capped to a reasonable band.
    confidence = int(max(60, min(95, 65 + abs(change_pct) * 2.5)))

    # Entry zone: a tight band around current price (0.2% wide).
    band = last * 0.002
    if direction == "LONG":
        entry_low, entry_high = last - band, last + band
        # TPs above entry, SL just below recent low.
        tp1 = last * 1.012
        tp2 = last * 1.025
        tp3 = last * 1.04
        stop = max(low * 0.998, last * 0.985)
    else:
        entry_low, entry_high = last - band, last + band
        tp1 = last * 0.988
        tp2 = last * 0.975
        tp3 = last * 0.96
        stop = min(high * 1.002, last * 1.015)

    targets = [_fmt(tp1), _fmt(tp2), _fmt(tp3)] if sig_type == "Scalp" else [_fmt(tp1), _fmt(tp2)]

    ts = generated_at or datetime.now(timezone.utc)
    # Human-readable signal time (UTC+8)
    signal_time_str = ts.astimezone(TZ_UTC8).strftime("%H:%M:%S UTC+8")

    return {
        "id": idx + 1,
        "pair": pair,
        "type": sig_type,
        "direction": direction,
        "entry": f"{_fmt(entry_low)} - {_fmt(entry_high)}",
        "targets": targets,
        "stopLoss": _fmt(stop),
        "status": "Active",
        "time": signal_time_str,
        "premium": tier == "pro",
        "confidence": confidence,
        "price": last,
        "change_24h": change_pct,
        "generated_at": ts.isoformat(),
    }


def _trade_status_by_symbol(tg_id: int) -> Dict[str, Dict[str, Any]]:
    """For each Bitunix symbol the user's autotrade has acted on recently,
    return the most relevant trade's status snapshot: in_position (still
    open), tp_hit (closed in profit / a TP was hit), or sl_hit (closed at
    a loss). Looks back 24h so closed trades stay visible long enough for
    the user to see the outcome on the dashboard.
    """
    from datetime import timedelta
    s = _client()
    out: Dict[str, Dict[str, Any]] = {}

    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    res = s.table("autotrade_trades").select(
        "symbol, side, status, pnl_usdt, tp1_hit, tp2_hit, tp3_hit, "
        "opened_at, closed_at"
    ).eq("telegram_id", tg_id).gte("opened_at", since).order(
        "opened_at", desc=True
    ).execute()

    for row in (res.data or []):
        sym = (row.get("symbol") or "").upper().replace("/", "")
        if not sym or sym in out:
            continue  # ordered DESC so first hit is the freshest

        status = (row.get("status") or "").lower()
        pnl = float(row.get("pnl_usdt") or 0)
        any_tp_hit = bool(row.get("tp1_hit") or row.get("tp2_hit") or row.get("tp3_hit"))

        if status == "open":
            label = "in_position"
        elif any_tp_hit or pnl > 0:
            label = "tp_hit"
        else:
            label = "sl_hit"

        out[sym] = {
            "label": label,
            "pnl": round(pnl, 4),
            "side": row.get("side"),
            "tp1_hit": bool(row.get("tp1_hit")),
            "tp2_hit": bool(row.get("tp2_hit")),
            "tp3_hit": bool(row.get("tp3_hit")),
            "closed_at": row.get("closed_at"),
        }

    return out


@router.get("/signals")
async def get_signals(tg_id: int | None = Depends(_optional_user)):
    symbols = [w[1] for w in _WATCHLIST]
    # Binance accepts a JSON-encoded array via the `symbols` query param.
    params = {"symbols": '["' + '","'.join(symbols) + '"]'}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(_BINANCE_TICKER, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Market data unavailable: {e}")

    try:
        trade_status = _trade_status_by_symbol(tg_id) if tg_id else {}
    except Exception:
        trade_status = {}

    status_label_map = {
        "in_position": "In Position",
        "tp_hit": "Take Profit Hit",
        "sl_hit": "Stop Loss Hit",
    }

    by_symbol = {row["symbol"]: row for row in data}
    signals: List[Dict[str, Any]] = []
    now_utc = datetime.now(timezone.utc)

    for idx, (pair, sym, tier, sig_type) in enumerate(_WATCHLIST):
        ticker = by_symbol.get(sym)
        if not ticker:
            continue

        # ── Cache logic: reuse generated_at if signal is still within window ──
        cached = _signal_cache.get(sym)
        if cached and (now_utc - cached["generated_at"]).total_seconds() < SIGNAL_ENTRY_WINDOW_SECONDS:
            # Signal still alive — keep the original generated_at
            gen_at = cached["generated_at"]
        else:
            # Signal expired or first time — stamp a fresh generated_at
            gen_at = now_utc
            _signal_cache[sym] = {"generated_at": gen_at}

        sig = _build_signal(idx, pair, tier, sig_type, ticker, generated_at=gen_at)
        ts = trade_status.get(sym)
        if ts:
            sig["expired"] = True
            sig["trade_status"] = ts["label"]
            sig["status"] = status_label_map.get(ts["label"], "Filled")
            sig["trade_pnl"] = ts["pnl"]
            sig["tp_hits"] = {
                "tp1": ts["tp1_hit"],
                "tp2": ts["tp2_hit"],
                "tp3": ts["tp3_hit"],
            }
        else:
            sig["expired"] = False
            sig["trade_status"] = "pending"
        sig["entry_window_seconds"] = SIGNAL_ENTRY_WINDOW_SECONDS
        signals.append(sig)

    return {
        "signals": signals,
        "generated_at": now_utc.astimezone(TZ_UTC8).isoformat(),
        "entry_window_seconds": SIGNAL_ENTRY_WINDOW_SECONDS,
    }


# ----------------------------------------------------------- 1-click order ---

def _watchlist_entry(symbol: str):
    sym = (symbol or "").upper().replace("/", "")
    for entry in _WATCHLIST:
        if entry[1] == sym:
            return entry
    return None


async def _live_signal(sym: str, sig_type: str, pair: str, tier: str) -> Dict[str, Any]:
    """Re-derive a fresh signal for the symbol using current ticker data.
    Used at execution time so late entries follow the live SL distance
    instead of the values rendered in the user's stale UI."""
    params = {"symbol": sym}
    async with httpx.AsyncClient(timeout=8.0) as client:
        r = await client.get(_BINANCE_TICKER, params=params)
        r.raise_for_status()
        ticker = r.json()
    return _build_signal(0, pair, tier, sig_type, ticker)


@router.post("/signals/execute")
async def execute_signal(
    payload: Dict[str, Any] = Body(...),
    tg_id: int = Depends(get_current_user),
):
    """Open a 1-click market position based on the dashboard signal.

    The position size is computed dynamically from the live SL distance:
    qty = (balance * risk%) / |entry - sl|

    so a user entering 4 minutes after the signal — when price has drifted
    closer to or away from the SL — still risks the same fixed % of equity.
    Only allowed within SIGNAL_ENTRY_WINDOW_SECONDS of the signal's
    `generated_at` timestamp.
    """
    symbol = (payload.get("symbol") or "").upper().replace("/", "")
    generated_at_raw = payload.get("generated_at")

    wl = _watchlist_entry(symbol)
    if not wl:
        raise HTTPException(status_code=400, detail=f"Symbol {symbol} not in watchlist")
    pair, sym, tier, sig_type = wl

    # Window check (5 minutes from announcement).
    if not generated_at_raw:
        raise HTTPException(status_code=400, detail="Missing signal generated_at")
    try:
        gen_at = datetime.fromisoformat(generated_at_raw.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid generated_at")
    if gen_at.tzinfo is None:
        gen_at = gen_at.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - gen_at).total_seconds()
    if age < 0:
        age = 0
    if age > SIGNAL_ENTRY_WINDOW_SECONDS:
        raise HTTPException(
            status_code=410,
            detail=f"Signal entry window expired ({int(age)}s old, max {SIGNAL_ENTRY_WINDOW_SECONDS}s)",
        )

    # Verify Bitunix keys + connection (same gating as engine_start).
    if not bsvc.get_user_api_keys(tg_id):
        raise HTTPException(status_code=409, detail="Bitunix API keys not configured")

    # Fetch live account balance + user's autotrade session for risk/leverage.
    try:
        acc = await bsvc.fetch_account(tg_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bitunix account error: {e}")
    if not acc.get("success"):
        raise HTTPException(status_code=502, detail="Failed to fetch account balance")
    balance = float(acc.get("available", 0) or 0)
    if balance <= 0:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    s = _client()
    sess_res = s.table("autotrade_sessions").select(
        "risk_per_trade, leverage"
    ).eq("telegram_id", tg_id).limit(1).execute()
    sess = (sess_res.data or [{}])[0]
    risk_pct = float(sess.get("risk_per_trade") or 2.0)
    leverage = int(sess.get("leverage") or 10)

    # Re-derive the signal from live market data so dynamic sizing reflects
    # the *current* SL distance, not the stale snapshot in the user's UI.
    try:
        live_sig = await _live_signal(sym, sig_type, pair, tier)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Market data unavailable: {e}")

    direction = live_sig["direction"]
    side = "BUY" if direction == "LONG" else "SELL"
    entry_price = float(live_sig["price"])

    # entry zone string is "low - high"; pull the SL we serialized as text.
    sl_price = float(str(live_sig["stopLoss"]).replace(",", ""))
    # First TP is also stringified — recompute numerically for safety.
    if direction == "LONG":
        tp_price = entry_price * 1.012
    else:
        tp_price = entry_price * 0.988

    sl_distance = abs(entry_price - sl_price)
    if sl_distance <= 0:
        raise HTTPException(status_code=400, detail="Invalid SL distance")
    sl_distance_pct = sl_distance / entry_price
    if sl_distance_pct < 0.001:
        raise HTTPException(status_code=400, detail="Stop loss too tight (<0.1%)")
    if sl_distance_pct > 0.15:
        raise HTTPException(status_code=400, detail="Stop loss too wide (>15%)")

    # Risk-based sizing: qty such that loss-at-SL == balance * risk%.
    risk_amount = balance * (risk_pct / 100.0)
    position_size_usdt = risk_amount / sl_distance_pct
    margin_required = position_size_usdt / leverage
    if margin_required > balance * 0.95:
        margin_required = balance * 0.95
        position_size_usdt = margin_required * leverage

    qty = position_size_usdt / entry_price
    precision = _QTY_PRECISION.get(sym, 3)
    qty = round(qty, precision)
    min_qty = 10 ** (-precision) if precision > 0 else 1
    if qty < min_qty:
        raise HTTPException(
            status_code=400,
            detail=f"Computed qty {qty} below exchange minimum {min_qty}",
        )

    try:
        result = await bsvc.place_market_with_tpsl(
            telegram_id=tg_id,
            symbol=sym,
            side=side,
            qty=qty,
            tp_price=tp_price,
            sl_price=sl_price,
            leverage=leverage,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Order placement failed: {e}")

    if not result.get("success"):
        raise HTTPException(
            status_code=502,
            detail=f"Order rejected by exchange: {result.get('message') or result}",
        )

    return {
        "success": True,
        "order": result,
        "sizing": {
            "qty": qty,
            "entry_price": round(entry_price, 6),
            "tp_price": round(tp_price, 6),
            "sl_price": round(sl_price, 6),
            "position_size_usdt": round(position_size_usdt, 2),
            "margin_required": round(margin_required, 2),
            "risk_amount": round(risk_amount, 2),
            "risk_pct": risk_pct,
            "sl_distance_pct": round(sl_distance_pct * 100, 3),
            "leverage": leverage,
            "signal_age_seconds": int(age),
        },
    }
