from __future__ import annotations

from app.core.models import TradeContext, TradeDecision


def evaluate_trade(context: TradeContext, config: object) -> TradeDecision:
    missing: list[str] = []

    if context.market_state.state != "TRENDING":
        missing.append("market_not_trending")
    if not context.liquidity_sweep.has_sweep:
        missing.append("liquidity_sweep_missing")
    if not context.bos.confirmed:
        missing.append("bos_not_confirmed")
    if not context.entry_zone.exists:
        missing.append("entry_zone_missing")
    elif not (context.entry_zone.tapped or context.entry_zone.near_tap):
        missing.append("entry_zone_not_tappable")

    min_conf = float(getattr(config, "min_confidence_score", 0.7))
    if context.confidence.score < min_conf:
        missing.append("confidence_below_threshold")

    if missing:
        return TradeDecision(
            action="SKIP",
            direction="NONE",
            confidence=context.confidence.score,
            reason=",".join(missing),
            proposed_entry_zone=context.entry_zone.preferred_zone,
            metadata={"missing_conditions": missing},
        )

    direction = context.bos.direction if context.bos.direction in ("LONG", "SHORT") else "NONE"
    return TradeDecision(
        action="TRADE",
        direction=direction,
        confidence=context.confidence.score,
        reason="all_conditions_passed",
        invalidation_level=context.entry_zone.preferred_zone.low if direction == "LONG" else context.entry_zone.preferred_zone.high,
        proposed_entry_zone=context.entry_zone.preferred_zone,
        metadata={"missing_conditions": []},
    )
