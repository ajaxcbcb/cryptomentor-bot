from __future__ import annotations

from app.data.validators import validate_candles


async def build_timeframe_context(symbol: str, exchange_client, config: object) -> dict[str, list]:
    timeframes = tuple(getattr(config, "default_timeframes", ("1m", "5m", "15m", "1h")))
    result: dict[str, list] = {}
    for tf in timeframes:
        candles = await exchange_client.get_candles(symbol, tf, limit=200)
        errors = validate_candles(candles)
        if errors:
            raise ValueError(f"invalid_candles:{symbol}:{tf}:{','.join(errors)}")
        result[tf] = candles
    return result
