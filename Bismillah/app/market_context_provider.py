"""
Normalized market context provider for Decision Tree V2.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Iterable, Optional

from app.market_sentiment_detector import detect_market_condition
from app.symbol_memory import get_symbol_memory_batch
from app.trade_candidate import MarketContext
from app.volume_pair_selector import get_ranked_top_volume_pairs, get_selector_health

logger = logging.getLogger(__name__)


def _clamp01(value: Any, default: float = 0.5) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return float(default)


def get_market_context(
    *,
    symbols: Optional[Iterable[str]] = None,
    limit: int = 10,
    runtime_snapshots: Optional[Dict[str, Any]] = None,
) -> MarketContext:
    try:
        btc = detect_market_condition("BTC") or {}
    except Exception as exc:
        logger.warning("[DecisionTreeV2] BTC condition lookup failed: %s", exc)
        btc = {}

    try:
        top_symbols = list(get_ranked_top_volume_pairs(limit=max(1, int(limit or 10))))
    except Exception as exc:
        logger.warning("[DecisionTreeV2] top-volume lookup failed: %s", exc)
        top_symbols = []

    try:
        selector_health = dict(get_selector_health() or {})
    except Exception:
        selector_health = {}

    watch = [str(symbol).upper().strip() for symbol in (symbols or top_symbols) if str(symbol).strip()]
    symbol_memory_summary = get_symbol_memory_batch(watch)
    condition = str(btc.get("condition") or "UNKNOWN").upper()
    confidence = float(btc.get("confidence", 0.0) or 0.0)
    recommended_mode = str(btc.get("recommended_mode") or "").strip().lower()
    session_quality = 0.65
    if condition == "UNKNOWN":
        session_quality = 0.40
    elif condition == "VOLATILE":
        session_quality = 0.35
    elif condition == "SIDEWAYS":
        session_quality = 0.55
    elif condition == "TRENDING":
        session_quality = 0.75

    event_risk = "low"
    if condition == "VOLATILE":
        event_risk = "high"
    elif confidence < 55:
        event_risk = "medium"

    bias = "neutral"
    if recommended_mode == "swing" and condition == "TRENDING":
        bias = "risk_on"
    elif condition == "VOLATILE":
        bias = "defensive"

    suitability = _clamp01((session_quality * 0.7) + ((confidence / 100.0) * 0.3), 0.5)
    if event_risk == "high":
        suitability = max(0.0, suitability - 0.25)

    return MarketContext(
        timestamp=time.time(),
        btc_condition=condition,
        btc_confidence=confidence,
        market_bias=bias,
        session_quality=session_quality,
        event_risk=event_risk,
        volatility_state=condition.lower(),
        top_symbols=top_symbols,
        global_trade_suitability=suitability,
        selector_health=selector_health,
        runtime_snapshots=dict(runtime_snapshots or {}),
        symbol_memory_summary=symbol_memory_summary,
        metadata={"recommended_mode": recommended_mode, "btc_reason": btc.get("reason")},
    )

