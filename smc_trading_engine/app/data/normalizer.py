from __future__ import annotations

from datetime import datetime, timezone

from app.core.models import Candle


def normalize_candle_payload(payload: list[dict]) -> list[Candle]:
    candles: list[Candle] = []
    for row in payload:
        ts = row.get("timestamp") or row.get("ts") or row.get("time")
        if isinstance(ts, (int, float)):
            ts_dt = datetime.fromtimestamp(float(ts) / (1000.0 if ts > 10_000_000_000 else 1.0), tz=timezone.utc)
        else:
            ts_dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        candles.append(
            Candle(
                timestamp=ts_dt,
                open=float(row.get("open", 0)),
                high=float(row.get("high", 0)),
                low=float(row.get("low", 0)),
                close=float(row.get("close", 0)),
                volume=float(row.get("volume", 0)),
            )
        )
    candles.sort(key=lambda c: c.timestamp)
    return candles
