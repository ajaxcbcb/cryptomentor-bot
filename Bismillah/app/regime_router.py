"""
Per-symbol regime classification for Decision Tree V2.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from app.market_sentiment_detector import detect_market_condition

logger = logging.getLogger(__name__)


async def classify_regime(symbol: str, market_context: Any, raw_signal: Dict[str, Any] | None = None) -> Dict[str, Any]:
    base = str(symbol or "").upper().replace("USDT", "")
    try:
        local = await asyncio.to_thread(detect_market_condition, base or "BTC")
    except Exception as exc:
        logger.debug("[DecisionTreeV2] regime fallback for %s: %s", symbol, exc)
        local = {}

    condition = str((local or {}).get("condition") or getattr(market_context, "btc_condition", "UNKNOWN")).upper()
    confidence = float((local or {}).get("confidence", 0.0) or 0.0)
    recommended_mode = str((local or {}).get("recommended_mode") or "").strip().lower()
    market_bias = str(getattr(market_context, "market_bias", "neutral") or "neutral")
    rr = 0.0
    try:
        rr = float((raw_signal or {}).get("rr_ratio") or (raw_signal or {}).get("rr_estimate") or 0.0)
    except Exception:
        rr = 0.0
    atr_pct = 0.0
    try:
        atr_pct = float((raw_signal or {}).get("atr_pct") or 0.0)
    except Exception:
        atr_pct = 0.0

    regime = "no_trade"
    preferred_engine = "swing"
    allow_secondary_engine = False
    reject_reason = ""

    if condition == "VOLATILE" or atr_pct >= 4.0:
        regime = "high_volatility_unstable"
        preferred_engine = "swing"
        reject_reason = "high_volatility_unstable"
    elif condition == "SIDEWAYS":
        regime = "range_mean_reversion"
        preferred_engine = "scalping"
        allow_secondary_engine = False
    elif condition == "TRENDING" and rr >= 1.8:
        regime = "breakout_expansion"
        preferred_engine = "swing"
        allow_secondary_engine = True
    elif condition == "TRENDING":
        regime = "trend_continuation"
        preferred_engine = "swing"
        allow_secondary_engine = True
    elif recommended_mode == "scalping":
        regime = "range_mean_reversion"
        preferred_engine = "scalping"
    else:
        regime = "no_trade"
        reject_reason = "missing_or_invalid_context"

    if market_bias == "defensive" and regime in {"breakout_expansion", "trend_continuation"}:
        confidence = max(0.0, confidence - 10.0)
        if confidence < 45.0:
            regime = "high_volatility_unstable"
            reject_reason = "high_event_risk_bias"

    return {
        "regime": regime,
        "confidence": confidence,
        "preferred_engine": preferred_engine,
        "allow_secondary_engine": allow_secondary_engine,
        "reject_reason": reject_reason,
    }

