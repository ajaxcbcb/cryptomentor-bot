from __future__ import annotations

from app.core.models import Candle


def validate_candles(candles: list[Candle]) -> list[str]:
    errors: list[str] = []
    if not candles:
        errors.append("empty_candles")
        return errors
    for i, c in enumerate(candles):
        if c.high < c.low:
            errors.append(f"invalid_high_low_at_{i}")
        if i > 0 and candles[i].timestamp <= candles[i - 1].timestamp:
            errors.append(f"non_ascending_timestamp_at_{i}")
    return errors
