"""
Tradeability scoring for Decision Tree V2.
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict


def _finite_positive(value: Any) -> bool:
    try:
        val = float(value)
    except Exception:
        return False
    return math.isfinite(val) and val > 0.0


def _clamp01(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return float(default)


def score_tradeability(candidate, market_context, symbol_memory: Dict[str, Any]) -> Dict[str, Any]:
    if not (_finite_positive(candidate.entry_price) and _finite_positive(candidate.stop_loss)):
        return {"tradeability_score": 0.0, "components": {}, "hard_reject_reason": "invalid_candidate"}

    if symbol_memory and bool(symbol_memory.get("unstable", False)):
        return {"tradeability_score": 0.0, "components": {}, "hard_reject_reason": "symbol_memory_unstable"}

    source = dict(candidate.source_signal_payload or {})
    now_ts = time.time()
    signal_ts = 0.0
    try:
        signal_ts = float(source.get("timestamp") or source.get("_queued_at_ts") or 0.0)
    except Exception:
        signal_ts = 0.0
    signal_age_seconds = max(0.0, now_ts - signal_ts) if signal_ts > 0 else 0.0
    age_score = 1.0 if signal_age_seconds <= 60 else (0.70 if signal_age_seconds <= 180 else 0.35)

    atr_pct = abs(float(source.get("atr_pct", 0.0) or 0.0))
    if atr_pct <= 0:
        atr_shape = 0.55
    elif atr_pct < 0.2:
        atr_shape = 0.45
    elif atr_pct <= 2.5:
        atr_shape = 0.85
    elif atr_pct <= 4.0:
        atr_shape = 0.60
    else:
        atr_shape = 0.20

    volume_ratio = abs(float(source.get("volume_ratio", source.get("vol_ratio", 1.0)) or 1.0))
    volume_quality = 0.40 if volume_ratio < 1.0 else min(1.0, 0.45 + (min(volume_ratio, 3.0) / 3.0) * 0.55)

    rr = abs(float(candidate.rr_estimate or 0.0))
    structure_cleanliness = min(1.0, max(0.25, rr / 2.5))
    session_quality = _clamp01(getattr(market_context, "session_quality", 0.50), 0.50)
    stability = 1.0 - min(0.70, float(symbol_memory.get("stopout_density", 0.0) or 0.0))

    tradeability_score = (
        age_score * 0.15
        + atr_shape * 0.15
        + volume_quality * 0.20
        + structure_cleanliness * 0.25
        + session_quality * 0.15
        + stability * 0.10
    )

    hard_reject_reason = ""
    if atr_shape <= 0.20:
        hard_reject_reason = "tradeability_below_threshold"
    if session_quality < 0.25:
        hard_reject_reason = "event_risk_high"

    return {
        "tradeability_score": round(_clamp01(tradeability_score), 4),
        "components": {
            "signal_age_score": round(age_score, 4),
            "atr_shape": round(atr_shape, 4),
            "volume_quality": round(volume_quality, 4),
            "structure_cleanliness": round(structure_cleanliness, 4),
            "session_quality": round(session_quality, 4),
            "symbol_stability": round(stability, 4),
        },
        "hard_reject_reason": hard_reject_reason,
    }
