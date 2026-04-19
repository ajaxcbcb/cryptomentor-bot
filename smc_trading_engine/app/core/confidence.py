from __future__ import annotations

from app.config.thresholds import CONFIDENCE_WEIGHTS
from app.core.models import ConfidenceResult, TradeContext


def normalize_score(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 0.0
    return max(0.0, min(1.0, (value - min_value) / (max_value - min_value)))


def weighted_sum(components: dict[str, float], weights: dict[str, float]) -> float:
    total = 0.0
    weight_total = 0.0
    for key, weight in weights.items():
        total += components.get(key, 0.0) * weight
        weight_total += weight
    if weight_total <= 0:
        return 0.0
    return total / weight_total


def calculate_confidence(context: TradeContext, config: object | None = None) -> ConfidenceResult:
    components = {
        "market_state": 1.0 if context.market_state.state == "TRENDING" else 0.0,
        "liquidity_sweep": context.liquidity_sweep.strength if context.liquidity_sweep.has_sweep else 0.0,
        "bos": normalize_score(context.bos.displacement, 0.0, 2.0) if context.bos.confirmed else 0.0,
        "entry_zone": 1.0 if context.entry_zone.tapped else (0.7 if context.entry_zone.near_tap else 0.0),
        "higher_timeframe_bias": 1.0 if context.higher_timeframe_bias in ("LONG", "SHORT") else 0.5,
    }
    score = weighted_sum(components, CONFIDENCE_WEIGHTS)
    return ConfidenceResult(score=score, components=components)
