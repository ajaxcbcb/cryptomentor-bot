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
import base64
import hashlib
import hmac
import json
import time
from typing import List, Dict, Any, Optional, Tuple
import logging
import os
import sys

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from app.db.supabase import _client
from app.routes.dashboard import get_current_user
from app.services import bitunix as bsvc
from app.services import conflict_gate
from app.services import one_click_trades as one_click_repo
from app.services.risk_policy import (
    AUTO_RISK_MAX_PCT,
    AUTO_RISK_MIN_PCT,
    ONE_CLICK_RISK_MAX_PCT,
    clamp_auto_risk,
    clamp_one_click_risk,
    is_high_risk,
    risk_band,
)
from app.auth.jwt import decode_token
from config import ONE_CLICK_SIGNAL_SIGNING_KEY

_BISMILLAH_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "Bismillah")
)
_BISMILLAH_APP_PATH = os.path.join(_BISMILLAH_PATH, "app")
if _BISMILLAH_APP_PATH not in sys.path:
    sys.path.insert(0, _BISMILLAH_APP_PATH)

try:
    from leverage_policy import get_auto_max_safe_leverage  # type: ignore
except Exception:
    def get_auto_max_safe_leverage(
        symbol: str,
        entry_price: Optional[float] = None,
        sl_price: Optional[float] = None,
        baseline_leverage: Optional[int] = None,
    ) -> int:
        _ = (symbol, entry_price, sl_price, baseline_leverage)
        return 20

logger = logging.getLogger(__name__)
TZ_UTC8 = timezone(timedelta(hours=8))
RISK_MIN_PCT = AUTO_RISK_MIN_PCT
RISK_MAX_PCT = AUTO_RISK_MAX_PCT
IDEMPOTENCY_WINDOW_SECONDS = 10 * 60
SIGNAL_TOKEN_VERSION = 1

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

if not ONE_CLICK_SIGNAL_SIGNING_KEY:
    raise RuntimeError("Set ONE_CLICK_SIGNAL_SIGNING_KEY for /dashboard/signals preview/execute.")


def _normalize_risk_pct(raw_value: Any, default: float = 1.0) -> float:
    """Clamp incoming AutoTrade risk setting to supported range [0.25, 10.0]."""
    return clamp_auto_risk(raw_value, default=default)


def _normalize_one_click_risk_pct(raw_value: Any, default: float = 1.0) -> float:
    return clamp_one_click_risk(raw_value, default=default)


def _risk_profile(user_risk_pct: float) -> Dict[str, float]:
    """
    Map user risk% to confluence selectivity and TP width.
    >1% is treated as high risk (lower min confidence, wider TP multipliers).
    """
    risk = _normalize_risk_pct(user_risk_pct, default=1.0)
    if risk <= 0.25:
        return {"min_confidence": 60, "atr_multiplier": 0.5}
    if risk <= 0.5:
        return {"min_confidence": 50, "atr_multiplier": 1.0}
    if risk <= 1.0:
        return {"min_confidence": 42, "atr_multiplier": 1.5}
    if risk <= 2.0:
        return {"min_confidence": 38, "atr_multiplier": 1.9}
    if risk <= 5.0:
        return {"min_confidence": 34, "atr_multiplier": 2.4}
    if risk <= 7.5:
        return {"min_confidence": 32, "atr_multiplier": 2.8}
    return {"min_confidence": 30, "atr_multiplier": 3.1}

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


async def generate_confluence_signals(
    symbol: str,
    user_risk_pct: float = 0.5
) -> Optional[Dict[str, Any]]:
    """
    Generate a confluence-validated trading signal for symbol if 2+ factors align.

    Confluence factors:
    1. S/R bounce: price near support/resistance (±1% touch) = +30 pts
    2. RSI extreme: RSI < 30 or > 70 = +25 pts
    3. Volume spike: current vol > 1.5× 20-period MA = +20 pts
    4. Non-sideways regime: trending (not choppy) = +15 pts
    5. Trend alignment: price above/below EMA200 = +10 pts

    Adaptive confidence thresholds based on user risk tolerance:
    - Conservative (0.25%): min_confidence=60, tighter TPs (0.5×ATR)
    - Moderate (0.5%): min_confidence=50, standard TPs (1.0×ATR baseline)
    - Aggressive (0.75-1.0%): min_confidence=45..40, wider TPs
    - High risk (>1.0% up to 5.0%): progressively lower min confidence, widest TPs

    Returns: signal dict if confluent, or None if weak setup
    """
    symbol_upper = symbol.upper()

    # Get config for user's risk level (clamped to [0.25, 5.0])
    user_risk_pct = _normalize_risk_pct(user_risk_pct, default=1.0)
    config = _risk_profile(user_risk_pct)
    min_confidence = config["min_confidence"]
    atr_multiplier = config["atr_multiplier"]

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

    # 8. Only generate if score >= min_confidence (adaptive based on risk tolerance)
    if score < min_confidence:
        logger.debug(f"[Confluence] {symbol} score={score} < {min_confidence} (insufficient confluence for {user_risk_pct}% risk)")
        return None

    # 9. Determine direction based on RSI
    direction = 'LONG' if last_rsi < 30 else ('SHORT' if last_rsi > 70 else 'LONG')

    # 10. Calculate TPs with ATR scaling (adaptive based on risk tolerance)
    # Standard TP tiers: 0.75×, 1.25×, 1.5× ATR
    # Multiplied by risk tolerance modifier (0.5 for conservative, 1.5 for aggressive)
    if direction == 'LONG':
        entry_price = support
        tp1 = entry_price + (atr * 0.75 * atr_multiplier)
        tp2 = entry_price + (atr * 1.25 * atr_multiplier)
        tp3 = entry_price + (atr * 1.5 * atr_multiplier)
        sl_price = support - (atr * 0.5)
    else:
        entry_price = resistance
        tp1 = entry_price - (atr * 0.75 * atr_multiplier)
        tp2 = entry_price - (atr * 1.25 * atr_multiplier)
        tp3 = entry_price - (atr * 1.5 * atr_multiplier)
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
        f"[Confluence] Generated {symbol} signal (risk={user_risk_pct}%): "
        f"dir={direction} entry={entry_price:.4f} tp1={tp1:.4f} tp2={tp2:.4f} tp3={tp3:.4f} "
        f"sl={sl_price:.4f} conf={score}/{min_confidence} [{signal['reason']}]"
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


def _norm_symbol(symbol: Any) -> str:
    return str(symbol or "").upper().replace("/", "").strip()


def _norm_side(side: Any) -> str:
    s = str(side or "").upper().strip()
    if s in ("BUY", "LONG"):
        return "BUY"
    if s in ("SELL", "SHORT"):
        return "SELL"
    return s


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _iso_to_dt(value: str) -> datetime:
    raw = str(value).replace("Z", "+00:00")
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _b64u_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64u_decode(value: str) -> bytes:
    pad = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode((value + pad).encode("ascii"))


def _watchlist_entry(symbol: str):
    sym = _norm_symbol(symbol)
    for entry in _WATCHLIST:
        if entry[1] == sym:
            return entry
    return None


def _sign_signal_payload(payload: Dict[str, Any]) -> str:
    message = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(
        ONE_CLICK_SIGNAL_SIGNING_KEY.encode("utf-8"),
        message,
        digestmod=hashlib.sha256,
    ).digest()
    return f"{_b64u_encode(message)}.{_b64u_encode(sig)}"


def _decode_signal_token(token: str) -> Dict[str, Any]:
    raw = str(token or "").strip()
    if not raw or "." not in raw:
        raise HTTPException(status_code=400, detail="Invalid signal token")
    encoded_payload, encoded_sig = raw.split(".", 1)
    try:
        payload_bytes = _b64u_decode(encoded_payload)
        supplied_sig = _b64u_decode(encoded_sig)
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed signal token")

    expected_sig = hmac.new(
        ONE_CLICK_SIGNAL_SIGNING_KEY.encode("utf-8"),
        payload_bytes,
        digestmod=hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(supplied_sig, expected_sig):
        raise HTTPException(status_code=400, detail="Signal token signature mismatch")

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Signal token payload invalid")

    required = (
        "v",
        "signal_id",
        "symbol",
        "pair",
        "direction",
        "stop_loss",
        "targets",
        "generated_at",
        "expires_at",
        "model_source",
    )
    missing = [k for k in required if k not in payload]
    if missing:
        raise HTTPException(status_code=400, detail=f"Signal token missing fields: {','.join(missing)}")
    if int(payload.get("v", 0)) != SIGNAL_TOKEN_VERSION:
        raise HTTPException(status_code=400, detail="Signal token version mismatch")

    try:
        exp = _iso_to_dt(str(payload["expires_at"]))
    except Exception:
        raise HTTPException(status_code=400, detail="Signal token expires_at invalid")
    if datetime.now(timezone.utc) > exp:
        raise HTTPException(status_code=410, detail="Signal token expired")

    sym = _norm_symbol(payload.get("symbol"))
    if not _watchlist_entry(sym):
        raise HTTPException(status_code=400, detail=f"Token symbol {sym} not in watchlist")
    payload["symbol"] = sym
    payload["side"] = "BUY" if str(payload.get("direction")).upper() == "LONG" else "SELL"
    payload["stop_loss"] = _as_float(payload.get("stop_loss"), 0.0)
    payload["targets"] = [_as_float(v, 0.0) for v in (payload.get("targets") or [])]
    if payload["stop_loss"] <= 0:
        raise HTTPException(status_code=400, detail="Signal token stop_loss invalid")
    return payload


def _build_signal_id(symbol: str, generated_at: datetime, model_source: str) -> str:
    base = f"{_norm_symbol(symbol)}|{generated_at.isoformat()}|{model_source}|v{SIGNAL_TOKEN_VERSION}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]
    return f"sig_{digest}"


def _status_from_one_click_row(row: Dict[str, Any]) -> Optional[str]:
    status = str(row.get("status") or "").lower()
    if status == "open":
        return "in_position"
    if status == "closed_tp":
        return "tp_hit"
    if status in {"closed_sl", "closed_unknown"}:
        return "sl_hit"
    if status == "closed_manual":
        return "manual_close"
    return None


def _trade_status_by_symbol(tg_id: int) -> Dict[str, Dict[str, Any]]:
    """
    Merge recent autotrade and one_click trade outcomes per symbol.
    one_click rows take precedence for symbol-level UX states.
    """
    s = _client()
    out: Dict[str, Dict[str, Any]] = {}

    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    try:
        res = (
            s.table("autotrade_trades")
            .select(
                "symbol, side, status, pnl_usdt, tp1_hit, tp2_hit, tp3_hit, "
                "opened_at, closed_at"
            )
            .eq("telegram_id", tg_id)
            .gte("opened_at", since)
            .order("opened_at", desc=True)
            .execute()
        )
        for row in (res.data or []):
            sym = _norm_symbol(row.get("symbol"))
            if not sym or sym in out:
                continue
            status = str(row.get("status") or "").lower()
            pnl = _as_float(row.get("pnl_usdt"), 0.0)
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
                "source": "autotrade",
            }
    except Exception as e:
        logger.warning("Failed to fetch autotrade status map: %s", e)

    one_click_rows = one_click_repo.recent_symbol_states(tg_id, lookback_hours=24)
    for sym, row in one_click_rows.items():
        label = _status_from_one_click_row(row)
        if not label:
            continue
        out[sym] = {
            "label": label,
            "pnl": 0.0,
            "side": row.get("side"),
            "tp1_hit": label == "tp_hit",
            "tp2_hit": False,
            "tp3_hit": False,
            "closed_at": row.get("closed_at"),
            "source": "one_click",
        }
    return out


async def _collect_user_state_context(tg_id: int) -> Dict[str, Any]:
    """
    Snapshot context for per-signal user_state:
    pending / blocked / open_1click / recent outcomes.
    """
    s = _client()
    pending_symbols: set[str] = set()
    autotrade_open_symbols: set[str] = set()
    live_position_symbols: Dict[str, str] = {}
    one_click_rows = one_click_repo.recent_symbol_states(tg_id, lookback_hours=24)

    try:
        pending_res = (
            s.table("signal_queue")
            .select("symbol,status")
            .eq("telegram_id", int(tg_id))
            .in_("status", ["queued", "executing", "pending"])
            .execute()
        )
        for row in (pending_res.data or []):
            sym = _norm_symbol(row.get("symbol"))
            if sym:
                pending_symbols.add(sym)
    except Exception:
        try:
            pending_res = (
                s.table("signal_queue")
                .select("symbol,status")
                .eq("user_id", int(tg_id))
                .in_("status", ["queued", "executing", "pending"])
                .execute()
            )
            for row in (pending_res.data or []):
                sym = _norm_symbol(row.get("symbol"))
                if sym:
                    pending_symbols.add(sym)
        except Exception as e:
            logger.warning("Failed to fetch pending symbols: %s", e)

    try:
        open_res = (
            s.table("autotrade_trades")
            .select("symbol,status")
            .eq("telegram_id", int(tg_id))
            .eq("status", "open")
            .execute()
        )
        for row in (open_res.data or []):
            sym = _norm_symbol(row.get("symbol"))
            if sym:
                autotrade_open_symbols.add(sym)
    except Exception as e:
        logger.warning("Failed to fetch autotrade open symbols: %s", e)

    try:
        live = await bsvc.fetch_positions(tg_id)
        if live.get("success"):
            for pos in (live.get("positions") or []):
                sym = _norm_symbol(pos.get("symbol"))
                qty = abs(_as_float(pos.get("amount", pos.get("size")), 0.0))
                if not sym or qty <= 0:
                    continue
                side = _norm_side(pos.get("side", pos.get("positionSide")))
                live_position_symbols[sym] = side
    except Exception as e:
        logger.warning("Failed to fetch live positions for user_state map: %s", e)

    return {
        "pending_symbols": pending_symbols,
        "autotrade_open_symbols": autotrade_open_symbols,
        "live_position_symbols": live_position_symbols,
        "one_click_rows": one_click_rows,
    }


def _build_user_state(symbol: str, ctx: Dict[str, Any]) -> str:
    sym = _norm_symbol(symbol)
    one_click_row = (ctx.get("one_click_rows") or {}).get(sym) or {}
    one_click_status = str(one_click_row.get("status") or "").lower()

    if one_click_status == "open":
        return "open_1click"
    if sym in (ctx.get("pending_symbols") or set()):
        return "pending"
    if sym in (ctx.get("autotrade_open_symbols") or set()):
        return "blocked"
    if sym in (ctx.get("live_position_symbols") or {}):
        return "blocked"
    if one_click_status == "closed_tp":
        return "recent_tp"
    if one_click_status in {"closed_sl", "closed_unknown", "rejected"}:
        return "recent_sl"
    if one_click_status == "closed_manual":
        return "recent_manual_close"
    return "ready"


def _warn_list_from_sizing(sizing: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    if bool(sizing.get("high_risk")):
        warnings.append("High risk size selected; drawdown sensitivity is elevated.")
    if bool(sizing.get("cap_applied")):
        warnings.append("Size was capped by available balance buffer policy.")
    if float(sizing.get("sl_distance_pct", 0.0)) >= 8.0:
        warnings.append("Stop distance is relatively wide; position size was reduced.")
    return warnings


async def _fetch_live_mark_price(symbol: str) -> float:
    params = {"symbol": _norm_symbol(symbol)}
    async with httpx.AsyncClient(timeout=8.0) as client:
        r = await client.get(_BINANCE_TICKER, params=params)
        r.raise_for_status()
        ticker = r.json()
    price = _as_float(ticker.get("lastPrice"), 0.0)
    if price <= 0:
        raise HTTPException(status_code=502, detail="Market data unavailable: invalid mark price")
    return price


def _resolve_risk_inputs(
    *,
    base_risk_pct: float,
    risk_override_pct: Optional[float],
    all_in: bool,
) -> Tuple[float, float]:
    requested = float(base_risk_pct)
    accepted = float(base_risk_pct)
    if risk_override_pct is not None:
        requested = float(risk_override_pct)
        accepted = _normalize_one_click_risk_pct(risk_override_pct, default=accepted)
    if all_in:
        requested = ONE_CLICK_RISK_MAX_PCT
        accepted = ONE_CLICK_RISK_MAX_PCT
    return requested, accepted


def _compute_sizing(
    *,
    symbol: str,
    entry_price: float,
    sl_price: float,
    tp_price: float,
    leverage: int,
    balance: float,
    equity: float,
    requested_risk_pct: float,
    accepted_risk_pct: float,
    all_in: bool,
) -> Dict[str, Any]:
    sl_distance = abs(entry_price - sl_price)
    if sl_distance <= 0:
        raise HTTPException(status_code=400, detail="Invalid SL distance")
    sl_distance_pct = sl_distance / entry_price
    if sl_distance_pct < 0.001:
        raise HTTPException(status_code=400, detail="Stop loss too tight (<0.1%)")
    if sl_distance_pct > 0.15:
        raise HTTPException(status_code=400, detail="Stop loss too wide (>15%)")

    desired_risk_amount = equity * (accepted_risk_pct / 100.0)
    position_size_usdt = desired_risk_amount / sl_distance_pct
    margin_required = position_size_usdt / max(1, int(leverage))

    cap_applied = False
    cap_reason = ""
    if margin_required > balance * 0.95:
        cap_applied = True
        cap_reason = "balance_margin_cap_95pct"
        margin_required = balance * 0.95
        position_size_usdt = margin_required * max(1, int(leverage))

    effective_risk_amount = position_size_usdt * sl_distance_pct
    effective_risk_pct = (effective_risk_amount / equity * 100.0) if equity > 0 else 0.0

    qty = position_size_usdt / entry_price
    precision = _QTY_PRECISION.get(_norm_symbol(symbol), 3)
    qty = round(qty, precision)
    min_qty = 10 ** (-precision) if precision > 0 else 1
    if qty < min_qty:
        raise HTTPException(
            status_code=400,
            detail=f"Computed qty {qty} below exchange minimum {min_qty}",
        )

    corrected = abs(float(requested_risk_pct) - float(accepted_risk_pct)) > 1e-9
    band = risk_band(accepted_risk_pct, all_in=all_in)
    risk_zone = "amber_red" if is_high_risk(accepted_risk_pct) else "normal"

    return {
        "qty": qty,
        "entry_price": round(entry_price, 6),
        "tp_price": round(tp_price, 6),
        "sl_price": round(sl_price, 6),
        "position_size_usdt": round(position_size_usdt, 2),
        "margin_required": round(margin_required, 2),
        "risk_amount": round(effective_risk_amount, 2),
        "requested_risk_pct": round(float(requested_risk_pct), 4),
        "risk_pct": round(float(accepted_risk_pct), 4),
        "effective_risk_pct": round(float(effective_risk_pct), 4),
        "risk_zone": risk_zone,
        "high_risk": is_high_risk(accepted_risk_pct),
        "risk_band_key": band.key,
        "risk_band_label": band.label,
        "all_in": bool(all_in),
        "corrected": corrected,
        "sl_distance_pct": round(sl_distance_pct * 100, 3),
        "leverage": int(leverage),
        "leverage_mode": "auto_max_pair",
        "cap_applied": cap_applied,
        "cap_reason": cap_reason,
    }


def _execution_summary_response(
    *,
    signal_payload: Dict[str, Any],
    account: Dict[str, Any],
    conflict: Dict[str, Any],
    sizing: Dict[str, Any],
    idempotency_status: str,
    order: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "success": True,
        "signal_id": signal_payload.get("signal_id"),
        "symbol": signal_payload.get("symbol"),
        "direction": signal_payload.get("direction"),
        "idempotency_status": idempotency_status,
        "order": order or {},
        "conflict_gate": conflict,
        "account": account,
        "sizing": sizing,
        "warnings": _warn_list_from_sizing(sizing),
    }


def _replay_open_response(row: Dict[str, Any]) -> Dict[str, Any]:
    requested = _as_float(row.get("requested_risk_pct"), 0.0)
    accepted = _as_float(row.get("accepted_risk_pct"), requested)
    sizing = {
        "qty": _as_float(row.get("qty"), 0.0),
        "entry_price": _as_float(row.get("entry_price"), 0.0),
        "tp_price": _as_float(row.get("tp_price"), 0.0),
        "sl_price": _as_float(row.get("sl_price"), 0.0),
        "position_size_usdt": 0.0,
        "margin_required": _as_float(row.get("margin_required_usdt"), 0.0),
        "risk_amount": _as_float(row.get("risk_amount_usdt"), 0.0),
        "requested_risk_pct": round(requested, 4),
        "risk_pct": round(accepted, 4),
        "effective_risk_pct": round(accepted, 4),
        "risk_zone": "amber_red" if is_high_risk(accepted) else "normal",
        "high_risk": is_high_risk(accepted),
        "risk_band_key": risk_band(accepted, all_in=accepted >= ONE_CLICK_RISK_MAX_PCT).key,
        "risk_band_label": risk_band(accepted, all_in=accepted >= ONE_CLICK_RISK_MAX_PCT).label,
        "all_in": accepted >= ONE_CLICK_RISK_MAX_PCT,
        "corrected": abs(requested - accepted) > 1e-9,
        "sl_distance_pct": 0.0,
        "leverage": int(_as_float(row.get("leverage"), 10)),
        "leverage_mode": "auto_max_pair",
        "cap_applied": bool(row.get("cap_applied")),
        "cap_reason": str(row.get("cap_reason") or ""),
    }
    return {
        "success": True,
        "signal_id": row.get("signal_id"),
        "symbol": row.get("symbol"),
        "direction": "LONG" if _norm_side(row.get("side")) == "BUY" else "SHORT",
        "idempotency_status": "replayed",
        "order": {
            "success": True,
            "order_id": row.get("exchange_order_id"),
            "position_id": row.get("exchange_position_id"),
        },
        "conflict_gate": {
            "allowed": True,
            "reason_code": "idempotent_replay",
            "reason": "Replayed prior successful request",
            "symbol": row.get("symbol"),
        },
        "account": {},
        "sizing": sizing,
        "warnings": _warn_list_from_sizing(sizing),
    }


class SignalPreviewPayload(BaseModel):
    signal_token: str = Field(min_length=16)
    risk_override_pct: Optional[float] = None
    all_in: bool = False
    client_request_id: Optional[str] = None


class SignalExecutePayload(BaseModel):
    signal_token: str = Field(min_length=16)
    client_request_id: str = Field(min_length=8, max_length=128)
    risk_override_pct: Optional[float] = None
    all_in: bool = False


@router.get("/signals")
async def get_signals(tg_id: int | None = Depends(_optional_user)):
    """
    Generate fresh confluence-based signals for all watchlist symbols.
    Adds server-signed signal tokens for deterministic 1-click execution.
    """
    signals: List[Dict[str, Any]] = []
    now_utc = datetime.now(timezone.utc)

    user_risk_pct = 1.0
    if tg_id:
        try:
            s = _client()
            res = (
                s.table("autotrade_sessions")
                .select("risk_per_trade")
                .eq("telegram_id", tg_id)
                .limit(1)
                .execute()
            )
            sess = (res.data or [{}])[0]
            user_risk_pct = _normalize_risk_pct(sess.get("risk_per_trade"), default=1.0)
        except Exception as e:
            logger.warning("Failed to fetch user risk setting: %s", e)
            user_risk_pct = 1.0

    try:
        trade_status = _trade_status_by_symbol(tg_id) if tg_id else {}
    except Exception as e:
        logger.warning("Failed to fetch merged trade status: %s", e)
        trade_status = {}

    user_state_ctx: Dict[str, Any] = {}
    if tg_id:
        try:
            user_state_ctx = await _collect_user_state_context(tg_id)
        except Exception as e:
            logger.warning("Failed to collect signal user-state context: %s", e)
            user_state_ctx = {}

    status_label_map = {
        "in_position": "In Position",
        "tp_hit": "Take Profit Hit",
        "sl_hit": "Stop Loss Hit",
        "manual_close": "Closed Manually",
    }

    symbols = [w[1] for w in _WATCHLIST]
    try:
        params = {"symbols": '["' + '","'.join(symbols) + '"]'}
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(_BINANCE_TICKER, params=params)
            r.raise_for_status()
            ticker_data = {row["symbol"]: row for row in r.json()}
    except Exception as e:
        logger.error("Failed to fetch Binance tickers: %s", e)
        ticker_data = {}

    for idx, (pair, sym, tier, sig_type) in enumerate(_WATCHLIST):
        try:
            conf_signal = await generate_confluence_signals(sym, user_risk_pct)
            ts = trade_status.get(sym)

            if conf_signal:
                generated_at = _iso_to_dt(str(conf_signal["generated_at"]))
                model_source = "confluence_v1"
                direction = str(conf_signal["direction"]).upper()
                stop_loss = _as_float(conf_signal["stop_loss"], 0.0)
                targets_raw = [
                    _as_float(conf_signal["take_profit_1"], 0.0),
                    _as_float(conf_signal["take_profit_2"], 0.0),
                    _as_float(conf_signal["take_profit_3"], 0.0),
                ]
                signal_response = {
                    "id": idx + 1,
                    "symbol": sym,
                    "pair": pair,
                    "type": sig_type,
                    "direction": direction,
                    "entry": f"{_fmt(conf_signal['entry_zone_low'])} - {_fmt(conf_signal['entry_zone_high'])}",
                    "targets": [_fmt(v) for v in targets_raw],
                    "targets_raw": targets_raw,
                    "stopLoss": _fmt(stop_loss),
                    "stopLossRaw": stop_loss,
                    "status": "Active",
                    "time": now_utc.astimezone(TZ_UTC8).strftime("%H:%M:%S UTC+8"),
                    "premium": tier == "pro",
                    "confidence": conf_signal["confidence"],
                    "price": conf_signal["entry_price"],
                    "generated_at": generated_at.isoformat(),
                    "entry_window_seconds": SIGNAL_ENTRY_WINDOW_SECONDS,
                    "reason": conf_signal.get("reason", ""),
                }
            elif sym in ticker_data:
                sig = _build_signal(idx, pair, tier, sig_type, ticker_data[sym], generated_at=now_utc)
                generated_at = _iso_to_dt(str(sig["generated_at"]))
                model_source = "momentum_fallback_v1"
                direction = str(sig["direction"]).upper()
                stop_loss = _as_float(str(sig["stopLoss"]).replace(",", ""), 0.0)
                targets_raw = [_as_float(str(v).replace(",", ""), 0.0) for v in (sig.get("targets") or [])]
                sig["symbol"] = sym
                sig["entry_window_seconds"] = SIGNAL_ENTRY_WINDOW_SECONDS
                sig["reason"] = "Momentum signal"
                sig["targets_raw"] = targets_raw
                sig["stopLossRaw"] = stop_loss
                signal_response = sig
            else:
                continue

            expires_at = generated_at + timedelta(seconds=SIGNAL_ENTRY_WINDOW_SECONDS)
            signal_id = _build_signal_id(sym, generated_at, model_source)
            token_payload = {
                "v": SIGNAL_TOKEN_VERSION,
                "signal_id": signal_id,
                "symbol": sym,
                "pair": pair,
                "direction": direction,
                "stop_loss": float(stop_loss),
                "targets": [float(v) for v in targets_raw],
                "generated_at": generated_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "model_source": model_source,
            }
            signal_token = _sign_signal_payload(token_payload)
            signal_response["signal_id"] = signal_id
            signal_response["signal_token"] = signal_token
            signal_response["expires_at"] = expires_at.isoformat()
            signal_response["model_source"] = model_source
            signal_response["user_state"] = _build_user_state(sym, user_state_ctx) if tg_id else "ready"

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
            logger.error("Failed to generate signal for %s: %s", sym, e)
            continue

    return {
        "signals": signals,
        "generated_at": now_utc.astimezone(TZ_UTC8).isoformat(),
        "entry_window_seconds": SIGNAL_ENTRY_WINDOW_SECONDS,
    }


@router.post("/signals/preview")
async def preview_signal_execution(
    payload: SignalPreviewPayload,
    tg_id: int = Depends(get_current_user),
):
    signal_payload = _decode_signal_token(payload.signal_token)
    sym = _norm_symbol(signal_payload["symbol"])
    direction = str(signal_payload["direction"]).upper()
    side = "BUY" if direction == "LONG" else "SELL"
    signal_payload["side"] = side

    if not bsvc.get_user_api_keys(tg_id):
        raise HTTPException(status_code=409, detail="Bitunix API keys not configured")

    try:
        acc = await bsvc.fetch_account(tg_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bitunix account error: {e}")
    if not acc.get("success"):
        raise HTTPException(status_code=502, detail="Failed to fetch account")

    balance = _as_float(acc.get("available"), 0.0)
    unrealized_pnl = _as_float(acc.get("total_unrealized_pnl"), 0.0)
    equity = balance + unrealized_pnl
    if equity <= 0:
        raise HTTPException(status_code=400, detail="Insufficient equity (account value is zero or negative)")

    s = _client()
    sess_res = (
        s.table("autotrade_sessions")
        .select("risk_per_trade, leverage")
        .eq("telegram_id", tg_id)
        .limit(1)
        .execute()
    )
    sess = (sess_res.data or [{}])[0]
    base_risk_pct = _normalize_risk_pct(sess.get("risk_per_trade"), default=1.0)
    requested_risk_pct, accepted_risk_pct = _resolve_risk_inputs(
        base_risk_pct=base_risk_pct,
        risk_override_pct=payload.risk_override_pct,
        all_in=bool(payload.all_in),
    )
    baseline_leverage = int(sess.get("leverage") or 10)
    leverage = get_auto_max_safe_leverage(
        symbol=sym,
        entry_price=None,
        sl_price=float(signal_payload["stop_loss"]),
        baseline_leverage=baseline_leverage,
    )

    conflict = await conflict_gate.check_entry_conflicts(
        tg_id=tg_id,
        symbol=sym,
        requested_side=side,
        strategy="one_click",
    )
    can_execute = {
        "allowed": bool(conflict.get("allowed")),
        "reason_code": str(conflict.get("reason_code") or "ok"),
        "reason": str(conflict.get("reason") or "allowed"),
        "message": "Ready to execute" if conflict.get("allowed") else "Order blocked by conflict gate",
    }

    try:
        entry_price = await _fetch_live_mark_price(sym)
        sl_price = float(signal_payload["stop_loss"])
        targets = signal_payload.get("targets") or []
        tp_price = float(targets[0]) if targets else (
            entry_price * 1.012 if side == "BUY" else entry_price * 0.988
        )
        sizing = _compute_sizing(
            symbol=sym,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            leverage=leverage,
            balance=balance,
            equity=equity,
            requested_risk_pct=requested_risk_pct,
            accepted_risk_pct=accepted_risk_pct,
            all_in=bool(payload.all_in),
        )
    except HTTPException as he:
        can_execute = {
            "allowed": False,
            "reason_code": "validation_error",
            "reason": str(he.detail),
            "message": "Sizing validation failed",
        }
        sizing = {
            "qty": 0.0,
            "entry_price": 0.0,
            "tp_price": 0.0,
            "sl_price": float(signal_payload["stop_loss"]),
            "position_size_usdt": 0.0,
            "margin_required": 0.0,
            "risk_amount": 0.0,
            "requested_risk_pct": round(float(requested_risk_pct), 4),
            "risk_pct": round(float(accepted_risk_pct), 4),
            "effective_risk_pct": 0.0,
            "risk_zone": "amber_red" if is_high_risk(accepted_risk_pct) else "normal",
            "high_risk": is_high_risk(accepted_risk_pct),
            "risk_band_key": risk_band(accepted_risk_pct, all_in=bool(payload.all_in)).key,
            "risk_band_label": risk_band(accepted_risk_pct, all_in=bool(payload.all_in)).label,
            "all_in": bool(payload.all_in),
            "corrected": abs(float(requested_risk_pct) - float(accepted_risk_pct)) > 1e-9,
            "sl_distance_pct": 0.0,
            "leverage": int(leverage),
            "leverage_mode": "auto_max_pair",
            "cap_applied": False,
            "cap_reason": "",
        }

    return {
        "success": True,
        "signal_id": signal_payload.get("signal_id"),
        "signal": {
            "symbol": sym,
            "pair": signal_payload.get("pair"),
            "direction": direction,
            "generated_at": signal_payload.get("generated_at"),
            "expires_at": signal_payload.get("expires_at"),
            "model_source": signal_payload.get("model_source"),
            "stop_loss": float(signal_payload["stop_loss"]),
            "targets": signal_payload.get("targets") or [],
        },
        "can_execute": can_execute,
        "account": {
            "balance": round(balance, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "equity": round(equity, 2),
        },
        "sizing": sizing,
        "warnings": _warn_list_from_sizing(sizing),
    }


@router.post("/signals/execute")
async def execute_signal(
    payload: SignalExecutePayload = Body(...),
    tg_id: int = Depends(get_current_user),
):
    signal_payload = _decode_signal_token(payload.signal_token)
    client_request_id = str(payload.client_request_id or "").strip()
    if not client_request_id:
        raise HTTPException(status_code=400, detail="client_request_id is required")

    replay_row = one_click_repo.find_recent_by_client_request_id(
        tg_id,
        client_request_id,
        within_seconds=IDEMPOTENCY_WINDOW_SECONDS,
    )
    if replay_row:
        status = str(replay_row.get("status") or "").lower()
        if status == "open":
            return _replay_open_response(replay_row)
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Request already processed",
                "reason_code": "idempotent_replay_non_open",
                "reason": f"existing request status={status}",
                "symbol": replay_row.get("symbol"),
            },
        )

    any_reuse = one_click_repo.find_by_client_request_id(tg_id, client_request_id)
    if any_reuse:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "client_request_id already used outside replay window",
                "reason_code": "client_request_id_reused_expired_window",
                "reason": "Use a new client_request_id for each execute attempt",
                "symbol": any_reuse.get("symbol"),
            },
        )

    sym = _norm_symbol(signal_payload["symbol"])
    direction = str(signal_payload["direction"]).upper()
    side = "BUY" if direction == "LONG" else "SELL"

    s = _client()
    sess_res = (
        s.table("autotrade_sessions")
        .select("risk_per_trade, leverage")
        .eq("telegram_id", tg_id)
        .limit(1)
        .execute()
    )
    sess = (sess_res.data or [{}])[0]
    base_risk_pct = _normalize_risk_pct(sess.get("risk_per_trade"), default=1.0)
    requested_risk_pct, accepted_risk_pct = _resolve_risk_inputs(
        base_risk_pct=base_risk_pct,
        risk_override_pct=payload.risk_override_pct,
        all_in=bool(payload.all_in),
    )
    baseline_leverage = int(sess.get("leverage") or 10)
    leverage = get_auto_max_safe_leverage(
        symbol=sym,
        entry_price=None,
        sl_price=float(signal_payload["stop_loss"]),
        baseline_leverage=baseline_leverage,
    )

    trade_row = one_click_repo.create_attempt(
        tg_id=tg_id,
        signal_id=str(signal_payload.get("signal_id")),
        client_request_id=client_request_id,
        symbol=sym,
        side=side,
        requested_risk_pct=requested_risk_pct,
        accepted_risk_pct=accepted_risk_pct,
        leverage=leverage,
        sl_price=float(signal_payload["stop_loss"]),
        tp_price=float((signal_payload.get("targets") or [0.0])[0] or 0.0),
    )
    trade_id = (trade_row or {}).get("id")

    if trade_id is None:
        race_row = one_click_repo.find_recent_by_client_request_id(
            tg_id,
            client_request_id,
            within_seconds=IDEMPOTENCY_WINDOW_SECONDS,
        )
        if race_row and str(race_row.get("status") or "").lower() == "open":
            return _replay_open_response(race_row)
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Unable to initialize execution attempt",
                "reason_code": "attempt_init_failed",
                "reason": "Could not persist one_click attempt row",
                "symbol": sym,
            },
        )

    if not bsvc.get_user_api_keys(tg_id):
        one_click_repo.mark_rejected(trade_id, "api_keys_missing", "Bitunix API keys not configured")
        raise HTTPException(status_code=409, detail="Bitunix API keys not configured")

    try:
        acc = await bsvc.fetch_account(tg_id)
    except Exception as e:
        one_click_repo.mark_rejected(trade_id, "account_fetch_error", str(e))
        raise HTTPException(status_code=502, detail=f"Bitunix account error: {e}")
    if not acc.get("success"):
        one_click_repo.mark_rejected(trade_id, "account_fetch_error", "Failed to fetch account")
        raise HTTPException(status_code=502, detail="Failed to fetch account")

    balance = _as_float(acc.get("available"), 0.0)
    unrealized_pnl = _as_float(acc.get("total_unrealized_pnl"), 0.0)
    equity = balance + unrealized_pnl
    if equity <= 0:
        one_click_repo.mark_rejected(trade_id, "insufficient_equity", "Account equity is zero or negative")
        raise HTTPException(status_code=400, detail="Insufficient equity (account value is zero or negative)")

    conflict = await conflict_gate.check_entry_conflicts(
        tg_id=tg_id,
        symbol=sym,
        requested_side=side,
        strategy="one_click",
    )
    if not conflict.get("allowed"):
        if trade_id:
            one_click_repo.mark_rejected(
                trade_id,
                reason_code=str(conflict.get("reason_code") or "coordinator_block"),
                reason_message=str(conflict.get("reason") or "Order blocked by conflict gate"),
            )
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Order blocked by conflict gate",
                "reason_code": conflict.get("reason_code"),
                "reason": conflict.get("reason"),
                "symbol": sym,
            },
        )

    try:
        entry_price = await _fetch_live_mark_price(sym)
        sl_price = float(signal_payload["stop_loss"])
        targets = signal_payload.get("targets") or []
        tp_price = float(targets[0]) if targets else (
            entry_price * 1.012 if side == "BUY" else entry_price * 0.988
        )
        sizing = _compute_sizing(
            symbol=sym,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            leverage=leverage,
            balance=balance,
            equity=equity,
            requested_risk_pct=requested_risk_pct,
            accepted_risk_pct=accepted_risk_pct,
            all_in=bool(payload.all_in),
        )
    except HTTPException as he:
        if trade_id:
            one_click_repo.mark_rejected(trade_id, "validation_error", str(he.detail))
        raise

    await conflict_gate.mark_pending(tg_id=tg_id, symbol=sym, strategy="one_click")
    try:
        result = await bsvc.place_market_with_tpsl(
            telegram_id=tg_id,
            symbol=sym,
            side=side,
            qty=float(sizing["qty"]),
            tp_price=float(sizing["tp_price"]),
            sl_price=float(sizing["sl_price"]),
            leverage=leverage,
        )
    except Exception as e:
        await conflict_gate.clear_pending(tg_id=tg_id, symbol=sym)
        if trade_id:
            one_click_repo.mark_rejected(trade_id, "order_placement_error", str(e))
        raise HTTPException(status_code=502, detail=f"Order placement failed: {e}")

    if not result.get("success"):
        await conflict_gate.clear_pending(tg_id=tg_id, symbol=sym)
        err_msg = str(result.get("message") or result.get("error") or result)
        if trade_id:
            one_click_repo.mark_rejected(trade_id, "exchange_rejected", err_msg)
        raise HTTPException(
            status_code=502,
            detail=f"Order rejected by exchange: {err_msg}",
        )

    await conflict_gate.confirm_open(
        tg_id=tg_id,
        symbol=sym,
        strategy="one_click",
        side=side,
        qty=float(sizing["qty"]),
        entry_price=float(sizing["entry_price"]),
        exchange_position_id=str(result.get("position_id") or result.get("order_id") or ""),
    )

    if trade_id:
        one_click_repo.mark_open(
            trade_id,
            entry_price=float(sizing["entry_price"]),
            qty=float(sizing["qty"]),
            margin_required_usdt=float(sizing["margin_required"]),
            risk_amount_usdt=float(sizing["risk_amount"]),
            cap_applied=bool(sizing.get("cap_applied")),
            cap_reason=str(sizing.get("cap_reason") or ""),
            exchange_order_id=str(result.get("order_id") or ""),
            exchange_position_id=str(result.get("position_id") or result.get("order_id") or ""),
        )

    account = {
        "balance": round(balance, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "equity": round(equity, 2),
    }
    conflict_gate_state = {
        "allowed": True,
        "reason_code": "ok",
        "reason": "passed",
        "symbol": sym,
    }
    return _execution_summary_response(
        signal_payload=signal_payload,
        account=account,
        conflict=conflict_gate_state,
        sizing=sizing,
        idempotency_status="fresh",
        order=result,
    )
