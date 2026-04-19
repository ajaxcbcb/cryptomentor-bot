from __future__ import annotations

from app.config import thresholds
from app.core.models import Candle, MarketStateResult
from app.data.indicators import atr as calc_atr, rolling_range


def calculate_atr(candles: list[Candle], period: int = thresholds.ATR_LOOKBACK) -> float:
    return calc_atr(candles, period)


def calculate_range_width(candles: list[Candle], lookback: int = thresholds.RANGE_LOOKBACK) -> float:
    return rolling_range(candles, lookback)


def calculate_trend_strength(candles: list[Candle], lookback: int = thresholds.TREND_LOOKBACK) -> float:
    window = candles[-lookback:] if len(candles) >= lookback else candles
    if len(window) < 2:
        return 0.0
    up = sum(1 for i in range(1, len(window)) if window[i].close > window[i - 1].close)
    down = sum(1 for i in range(1, len(window)) if window[i].close < window[i - 1].close)
    total = max(1, up + down)
    dominant = max(up, down)
    return dominant / total


def detect_market_state(candles: list[Candle], config: object | None = None) -> MarketStateResult:
    if len(candles) < 20:
        return MarketStateResult(state="UNCLEAR", reasons=["insufficient_candles"], metrics={})

    atr_v = calculate_atr(candles)
    range_v = calculate_range_width(candles)
    trend_v = calculate_trend_strength(candles)
    last_price = candles[-1].close or 1.0

    atr_ratio = atr_v / max(last_price, 1e-9)
    range_ratio = range_v / max(last_price, 1e-9)

    metrics = {
        "atr": atr_v,
        "atr_ratio": atr_ratio,
        "range_width": range_v,
        "range_ratio": range_ratio,
        "trend_strength": trend_v,
    }

    if atr_ratio < thresholds.ATR_MIN_THRESHOLD:
        return MarketStateResult(state="LOW_VOLATILITY", reasons=["atr_below_threshold"], metrics=metrics)

    if trend_v >= thresholds.TREND_STRENGTH_THRESHOLD and range_ratio >= thresholds.ATR_MIN_THRESHOLD * thresholds.RANGE_MIN_MULTIPLIER:
        return MarketStateResult(state="TRENDING", reasons=["strong_directional_flow"], metrics=metrics)

    if trend_v < 0.52:
        return MarketStateResult(state="SIDEWAYS", reasons=["weak_directional_flow"], metrics=metrics)

    return MarketStateResult(state="UNCLEAR", reasons=["mixed_conditions"], metrics=metrics)
