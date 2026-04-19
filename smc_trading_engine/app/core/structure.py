from __future__ import annotations

from app.config import thresholds
from app.core.models import BOSResult, Candle
from app.data.indicators import average_body_size


def find_structure_levels(candles: list[Candle], lookback: int = thresholds.SWING_LOOKBACK) -> tuple[float, float]:
    window = candles[-lookback:] if len(candles) >= lookback else candles
    if not window:
        return 0.0, 0.0
    high = max(c.high for c in window[:-1] or window)
    low = min(c.low for c in window[:-1] or window)
    return high, low


def displacement_strength(candles: list[Candle]) -> float:
    if len(candles) < 2:
        return 0.0
    last = candles[-1]
    body = abs(last.close - last.open)
    avg_body = average_body_size(candles[:-1], lookback=20)
    if avg_body <= 0:
        return 0.0
    return body / avg_body


def is_valid_bos_close(last_close: float, level: float, direction: str, min_break_pct: float = 0.0005) -> bool:
    if direction == "LONG":
        return last_close > level * (1 + min_break_pct)
    if direction == "SHORT":
        return last_close < level * (1 - min_break_pct)
    return False


def detect_bos(candles: list[Candle], config: object | None = None) -> BOSResult:
    if len(candles) < 8:
        return BOSResult(confirmed=False, reasons=["insufficient_candles"])

    high, low = find_structure_levels(candles)
    last = candles[-1]
    disp = displacement_strength(candles)

    if is_valid_bos_close(last.close, high, "LONG") and disp >= thresholds.BOS_DISPLACEMENT_MIN:
        return BOSResult(
            confirmed=True,
            direction="LONG",
            displacement=disp,
            level_broken=high,
            reasons=["bullish_bos_confirmed"],
        )

    if is_valid_bos_close(last.close, low, "SHORT") and disp >= thresholds.BOS_DISPLACEMENT_MIN:
        return BOSResult(
            confirmed=True,
            direction="SHORT",
            displacement=disp,
            level_broken=low,
            reasons=["bearish_bos_confirmed"],
        )

    return BOSResult(confirmed=False, displacement=disp, reasons=["no_confirmed_bos"])
