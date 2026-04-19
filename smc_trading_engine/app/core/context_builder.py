from __future__ import annotations

from app.core.confidence import calculate_confidence
from app.core.decision_engine import evaluate_trade
from app.core.entry_zone import detect_entry_zone
from app.core.liquidity import detect_liquidity_sweep
from app.core.market_state import detect_market_state
from app.core.models import ConfidenceResult, TradeContext
from app.core.structure import detect_bos


def _higher_tf_bias(candles_1h, candles_15m) -> str:
    if not candles_1h or not candles_15m:
        return "NEUTRAL"
    if candles_1h[-1].close > candles_1h[-2].close and candles_15m[-1].close > candles_15m[-2].close:
        return "LONG"
    if candles_1h[-1].close < candles_1h[-2].close and candles_15m[-1].close < candles_15m[-2].close:
        return "SHORT"
    return "NEUTRAL"


def build_trade_context(symbol: str, timeframe_data: dict[str, list], config: object) -> TradeContext:
    candles_5m = timeframe_data.get("5m", [])
    candles_15m = timeframe_data.get("15m", candles_5m)
    candles_1h = timeframe_data.get("1h", candles_15m)

    market_state = detect_market_state(candles_15m)
    liquidity = detect_liquidity_sweep(candles_5m)
    bos = detect_bos(candles_5m)
    direction = bos.direction if bos.direction in ("LONG", "SHORT") else "LONG"
    entry_zone = detect_entry_zone(candles_5m, direction)
    current_price = candles_5m[-1].close if candles_5m else 0.0
    bias = _higher_tf_bias(candles_1h, candles_15m)

    context = TradeContext(
        symbol=symbol,
        market_state=market_state,
        liquidity_sweep=liquidity,
        bos=bos,
        entry_zone=entry_zone,
        confidence=ConfidenceResult(score=0.0, components={}),
        higher_timeframe_bias=bias,
        current_price=current_price,
        missing_conditions=[],
        debug={"timeframes": list(timeframe_data.keys())},
    )
    context.confidence = calculate_confidence(context)

    preview_decision = evaluate_trade(context, config)
    context.missing_conditions = list(preview_decision.metadata.get("missing_conditions", []))
    return context
