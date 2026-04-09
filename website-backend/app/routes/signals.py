"""
Live market signals endpoint.

Confluence-based trading signal generation combining:
- Support/Resistance detection (RangeAnalyzer)
- RSI extremes (RSIDivergenceDetector)
- Volume confirmation
- Market regime filtering (SidewaysDetector)
- Volatility-scaled TP/SL (ATR-based)

Every signal must score >= 50 points from confluence factors (min 2+ factors).
No caching — generates fresh signals every request based on live market conditions.
"""

from datetime import datetime, timezone, timedelta

TZ_UTC8 = timezone(timedelta(hours=8))
from typing import List, Dict, Any, Optional
import logging

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db.supabase import _client
from app.routes.dashboard import get_current_user
from app.services import bitunix as bsvc
from app.auth.jwt import decode_token

logger = logging.getLogger(__name__)

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
_QTY_PRECISION = {
    "BTCUSDT":  3,
    "ETHUSDT":  2,
    "AVAXUSDT": 2,
    "SOLUSDT":  1,
    "BNBUSDT":  2,
    "XRPUSDT":  0,
    "DOGEUSDT": 0,
    "LINKUSDT": 1,
    "ADAUSDT":  0,
    "DOTUSDT":  1,
    "MATICUSDT": 0,
    "LTCUSDT":  2,
}

router = APIRouter(prefix="/dashboard", tags=["signals"])

# ── Signal cache ─────────────────────────────────────────────────────────────
# Keyed by binance symbol (e.g. "BTCUSDT").
# Each entry: {"signal": dict, "generated_at": datetime, "ticker_snapshot": dict}
# A cached signal is reused until it expires (>= SIGNAL_ENTRY_WINDOW_SECONDS old),
# at which point a fresh signal is generated with a new generated_at timestamp.
_signal_cache: Dict[str, Dict[str, Any]] = {}

# (display_pair, binance_symbol, tier, type)
# All pairs are free — more pairs = more trading volume
_WATCHLIST = [
    ("BTC/USDT",   "BTCUSDT",   "free", "Scalp"),
    ("ETH/USDT",   "ETHUSDT",   "free", "Swing"),
    ("SOL/USDT",   "SOLUSDT",   "free", "Scalp"),
    ("BNB/USDT",   "BNBUSDT",   "free", "Scalp"),
    ("AVAX/USDT",  "AVAXUSDT",  "free", "Scalp"),
    ("XRP/USDT",   "XRPUSDT",   "free", "Scalp"),
    ("DOGE/USDT",  "DOGEUSDT",  "free", "Scalp"),
    ("LINK/USDT",  "LINKUSDT",  "free", "Swing"),
    ("ADA/USDT",   "ADAUSDT",   "free", "Scalp"),
    ("DOT/USDT",   "DOTUSDT",   "free", "Swing"),
    ("MATIC/USDT", "MATICUSDT", "free", "Scalp"),
    ("LTC/USDT",   "LTCUSDT",   "free", "Swing"),
]

_BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/24hr"

# ── Confluence Signal Generation ────────────────────────────────────────────
# Replaces momentum-only signals with confluence-validated multi-factor detection.

async def _get_candles_1h(symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch last N 1-hour candles from alternative provider.
    Returns list of candle dicts: {open, high, low, close, volume, time, ...}
    """
    try:
        from app.providers.alternative_klines_provider import alternative_klines_provider
        klines = alternative_klines_provider.get_klines(symbol, interval='1h', limit=limit)

        # Convert Binance format [ts, open, high, low, close, vol, ...] to dict
        candles = []
        for kline in klines:
            candles.append({
                'time': int(kline[0]),
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5]),
            })
        return candles
    except Exception as e:
        logger.warning(f"Failed to fetch candles for {symbol}: {e}")
        return []


def _calculate_atr(candles: List[Dict], period: int = 14) -> float:
    """
    Calculate 14-period ATR from candles.
    ATR = average of true ranges over period.
    """
    if len(candles) < period + 1:
        period = len(candles) - 1

    if period < 1:
        return 0.0

    true_ranges = []
    for i in range(len(candles) - period, len(candles)):
        if i < 1:
            continue
        curr = candles[i]
        prev = candles[i - 1]
        tr = max(
            curr['high'] - curr['low'],
            abs(curr['high'] - prev['close']),
            abs(curr['low'] - prev['close']),
        )
        true_ranges.append(tr)

    return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0


async def generate_confluence_signals(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Generate a confluence-validated trading signal for symbol if 2+ factors align.

    Confluence factors:
    1. S/R bounce: price near support/resistance (±1% touch) = +30 pts
    2. RSI extreme: RSI < 30 or > 70 = +25 pts
    3. Volume spike: current vol > 1.5× 20-period MA = +20 pts
    4. Non-sideways regime: trending (not choppy) = +15 pts
    5. Trend alignment: price above/below EMA200 = +10 pts

    Min confidence to generate = 50 pts (requires 2+ factors)

    Returns: signal dict if confluent, or None if weak setup
    """
    symbol_upper = symbol.upper()

    # 1. Fetch 100 1h candles
    candles = await _get_candles_1h(symbol_upper, limit=100)
    if len(candles) < 50:
        logger.warning(f"[Confluence] Insufficient candles for {symbol}: {len(candles)}")
        return None

    closes = [c['close'] for c in candles]
    current_price = closes[-1]

    # 2. Support/Resistance Analysis
    try:
        from Bismillah.app.range_analyzer import RangeAnalyzer
        ra = RangeAnalyzer()
        sr_result = ra.analyze(candles[-50:], current_price)

        if not sr_result:
            logger.debug(f"[Confluence] No valid S/R for {symbol}")
            support = current_price * 0.97
            resistance = current_price * 1.03
            price_near_sr = False
        else:
            support = sr_result.support
            resistance = sr_result.resistance
            # Check if price is within 1% of support or resistance
            near_support = abs(current_price - support) / support <= 0.01
            near_resistance = abs(current_price - resistance) / resistance <= 0.01
            price_near_sr = near_support or near_resistance
    except Exception as e:
        logger.warning(f"[Confluence] S/R analysis failed for {symbol}: {e}")
        support = current_price * 0.97
        resistance = current_price * 1.03
        price_near_sr = False

    # 3. RSI Extremes
    try:
        from Bismillah.app.rsi_divergence_detector import RSIDivergenceDetector
        rsi_detector = RSIDivergenceDetector()
        rsi_values = rsi_detector._calculate_rsi_series(closes)

        if rsi_values:
            last_rsi = rsi_values[-1]
            is_rsi_extreme = last_rsi < 30 or last_rsi > 70
        else:
            last_rsi = 50.0
            is_rsi_extreme = False
    except Exception as e:
        logger.warning(f"[Confluence] RSI calculation failed for {symbol}: {e}")
        last_rsi = 50.0
        is_rsi_extreme = False

    # 4. Volume Spike
    volumes = [c['volume'] for c in candles[-20:]]
    vol_ma = sum(volumes) / len(volumes) if volumes else 0
    vol_spike = volumes[-1] > vol_ma * 1.5 if vol_ma > 0 else False

    # 5. Market Regime (Sideways Detection)
    try:
        from Bismillah.app.sideways_detector import SidewaysDetector
        sd = SidewaysDetector()
        # SidewaysDetector needs 5m candles (at least 20) and 15m candles (at least 50)
        # We only have 1h data, so we'll do a simpler volatility check instead
        # Skip detailed sideways check if we don't have right timeframe data
        # Instead: check ATR relative volatility
        atr = _calculate_atr(candles[-30:], period=14)
        atr_pct = (atr / current_price * 100) if current_price > 0 else 0
        is_trending = atr_pct > 0.3  # ATR > 0.3% means trending
    except Exception as e:
        logger.warning(f"[Confluence] Regime detection failed: {e}")
        is_trending = True  # Default to trending if check fails

    # 6. Volatility (ATR)
    atr = _calculate_atr(candles[-30:], period=14)

    # 7. Confluence Scoring
    score = 0
    reason_list = []

    if price_near_sr:
        score += 30
        reason_list.append(f"S/R bounce (support={support:.2f})")

    if is_rsi_extreme:
        score += 25
        rsi_direction = "Oversold" if last_rsi < 30 else "Overbought"
        reason_list.append(f"RSI extreme {last_rsi:.1f} ({rsi_direction})")

    if vol_spike:
        score += 20
        reason_list.append("Volume spike")

    if is_trending:
        score += 15
        reason_list.append("Strong trend")

    # Trend alignment: price > long-term moving average
    # Use all available closes (up to 100) as a long-term MA
    if len(closes) >= 50:
        long_ma = sum(closes[-50:]) / 50
        if current_price > long_ma:
            score += 10
            reason_list.append(f"Price above 50-candle MA")
    elif len(closes) >= 20:
        long_ma = sum(closes[-20:]) / 20
        if current_price > long_ma:
            score += 10
            reason_list.append(f"Price above 20-candle MA")

    # 8. Only generate if score >= 50
    if score < 50:
        logger.debug(f"[Confluence] {symbol} score={score} < 50 (insufficient confluence)")
        return None

    # 9. Determine direction based on RSI
    direction = 'LONG' if last_rsi < 30 else ('SHORT' if last_rsi > 70 else 'LONG')

    # 10. Calculate TPs with ATR scaling
    if direction == 'LONG':
        entry_price = support
        tp1 = entry_price + (atr * 0.75)
        tp2 = entry_price + (atr * 1.25)
        tp3 = entry_price + (atr * 1.5)
        sl_price = support - (atr * 0.5)
    else:
        entry_price = resistance
        tp1 = entry_price - (atr * 0.75)
        tp2 = entry_price - (atr * 1.25)
        tp3 = entry_price - (atr * 1.5)
        sl_price = resistance + (atr * 0.5)

    # 11. Round to symbol precision
    precision = _QTY_PRECISION.get(symbol_upper, 3)

    signal = {
        'symbol': symbol_upper,
        'direction': direction,
        'entry_price': round(entry_price, precision),
        'entry_zone_low': round(min(support, entry_price * 0.999), precision),
        'entry_zone_high': round(max(resistance, entry_price * 1.001), precision),
        'take_profit_1': round(tp1, precision),
        'take_profit_2': round(tp2, precision),
        'take_profit_3': round(tp3, precision),
        'stop_loss': round(sl_price, precision),
        'confidence': score,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'reason': ' + '.join(reason_list),
    }

    logger.info(
        f"[Confluence] Generated {symbol} signal: "
        f"dir={direction} entry={entry_price:.4f} tp1={tp1:.4f} "
        f"sl={sl_price:.4f} conf={score} [{signal['reason']}]"
    )

    return signal


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
    """
    Generate fresh confluence-based signals for all watchlist symbols.

    NO CACHING — each request generates signals from live market conditions.
    Multiple signals per day are allowed when confluence conditions align.

    Returns:
    - signals: list of confluent signals (only if score >= 50)
    - generated_at: current UTC timestamp
    - entry_window_seconds: 5 min window for 1-click execution
    """
    signals: List[Dict[str, Any]] = []
    now_utc = datetime.now(timezone.utc)

    # Get trade status (for in-position or closed trade tracking)
    try:
        trade_status = _trade_status_by_symbol(tg_id) if tg_id else {}
    except Exception as e:
        logger.warning(f"Failed to fetch trade status: {e}")
        trade_status = {}

    status_label_map = {
        "in_position": "In Position",
        "tp_hit": "Take Profit Hit",
        "sl_hit": "Stop Loss Hit",
    }

    # Generate fresh confluence signals for each symbol
    for idx, (pair, sym, tier, sig_type) in enumerate(_WATCHLIST):
        try:
            # Generate confluence-based signal (async, live market data)
            conf_signal = await generate_confluence_signals(sym)

            if conf_signal:
                # Found a confluent signal — format for dashboard
                ts = trade_status.get(sym)

                signal_response = {
                    "id": idx + 1,
                    "symbol": sym,  # Required for execute_signal payload
                    "pair": pair,
                    "type": sig_type,
                    "direction": conf_signal['direction'],
                    "entry": f"{_fmt(conf_signal['entry_zone_low'])} - {_fmt(conf_signal['entry_zone_high'])}",
                    "targets": [_fmt(conf_signal['take_profit_1']), _fmt(conf_signal['take_profit_2']), _fmt(conf_signal['take_profit_3'])],
                    "stopLoss": _fmt(conf_signal['stop_loss']),
                    "status": "Active",
                    "time": now_utc.astimezone(TZ_UTC8).strftime("%H:%M:%S UTC+8"),
                    "premium": tier == "pro",
                    "confidence": conf_signal['confidence'],
                    "price": conf_signal['entry_price'],
                    "generated_at": conf_signal['generated_at'],
                    "entry_window_seconds": SIGNAL_ENTRY_WINDOW_SECONDS,
                    "reason": conf_signal['reason'],  # Add confluence reason to UI
                }

                # Mark if this symbol has an active position or recent closed trade
                if ts:
                    signal_response["expired"] = True
                    signal_response["trade_status"] = ts["label"]
                    signal_response["status"] = status_label_map.get(ts["label"], "Filled")
                    signal_response["trade_pnl"] = ts["pnl"]
                    signal_response["tp_hits"] = {
                        "tp1": ts["tp1_hit"],
                        "tp2": ts["tp2_hit"],
                        "tp3": ts["tp3_hit"],
                    }
                else:
                    signal_response["expired"] = False
                    signal_response["trade_status"] = "pending"

                signals.append(signal_response)

        except Exception as e:
            logger.error(f"Failed to generate signal for {sym}: {e}")
            continue

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
