from __future__ import annotations

from app.config import thresholds
from app.core.models import Candle, LiquiditySweepResult


def find_recent_swing_high(candles: list[Candle], lookback: int = thresholds.SWING_LOOKBACK) -> float | None:
    window = candles[-lookback:] if len(candles) >= lookback else candles
    if not window:
        return None
    return max(c.high for c in window[:-1] or window)


def find_recent_swing_low(candles: list[Candle], lookback: int = thresholds.SWING_LOOKBACK) -> float | None:
    window = candles[-lookback:] if len(candles) >= lookback else candles
    if not window:
        return None
    return min(c.low for c in window[:-1] or window)


def calculate_sweep_strength(penetration: float, rejection: float) -> float:
    raw = max(0.0, penetration) + max(0.0, rejection)
    return min(1.0, raw)


def detect_liquidity_sweep(candles: list[Candle], config: object | None = None) -> LiquiditySweepResult:
    if len(candles) < 5:
        return LiquiditySweepResult(has_sweep=False, reasons=["insufficient_candles"])

    last = candles[-1]
    swing_high = find_recent_swing_high(candles)
    swing_low = find_recent_swing_low(candles)

    if swing_high is None or swing_low is None:
        return LiquiditySweepResult(has_sweep=False, reasons=["missing_swings"])

    penetration_high = max(0.0, (last.high - swing_high) / max(swing_high, 1e-9))
    rejection_high = max(0.0, (swing_high - last.close) / max(swing_high, 1e-9))

    penetration_low = max(0.0, (swing_low - last.low) / max(swing_low, 1e-9))
    rejection_low = max(0.0, (last.close - swing_low) / max(swing_low, 1e-9))

    min_pen = thresholds.ATR_MIN_THRESHOLD * thresholds.SWEEP_MIN_PENETRATION_MULT
    if penetration_high >= min_pen and rejection_high > 0:
        return LiquiditySweepResult(
            has_sweep=True,
            sweep_side="BUY_SIDE",
            strength=calculate_sweep_strength(penetration_high, rejection_high),
            level=swing_high,
            reasons=["buy_side_liquidity_swept"],
        )
    if penetration_low >= min_pen and rejection_low > 0:
        return LiquiditySweepResult(
            has_sweep=True,
            sweep_side="SELL_SIDE",
            strength=calculate_sweep_strength(penetration_low, rejection_low),
            level=swing_low,
            reasons=["sell_side_liquidity_swept"],
        )

    return LiquiditySweepResult(has_sweep=False, reasons=["no_meaningful_sweep"])
