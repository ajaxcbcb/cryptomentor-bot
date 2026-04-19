from __future__ import annotations

from app.core.models import Candle


def rolling_range(candles: list[Candle], lookback: int) -> float:
    window = candles[-lookback:] if len(candles) >= lookback else candles
    if not window:
        return 0.0
    high = max(c.high for c in window)
    low = min(c.low for c in window)
    return max(0.0, high - low)


def average_body_size(candles: list[Candle], lookback: int = 20) -> float:
    window = candles[-lookback:] if len(candles) >= lookback else candles
    if not window:
        return 0.0
    return sum(abs(c.close - c.open) for c in window) / len(window)


def atr(candles: list[Candle], period: int = 14) -> float:
    if len(candles) < 2:
        return 0.0
    trs: list[float] = []
    for i in range(1, len(candles)):
        cur = candles[i]
        prev = candles[i - 1]
        tr = max(cur.high - cur.low, abs(cur.high - prev.close), abs(cur.low - prev.close))
        trs.append(tr)
    if not trs:
        return 0.0
    use = trs[-period:] if len(trs) >= period else trs
    return sum(use) / len(use)


def rsi(candles: list[Candle], period: int = 14) -> float:
    if len(candles) <= period:
        return 50.0
    gains = 0.0
    losses = 0.0
    for i in range(-period, 0):
        delta = candles[i].close - candles[i - 1].close
        if delta >= 0:
            gains += delta
        else:
            losses += abs(delta)
    if losses == 0:
        return 100.0
    rs = (gains / period) / (losses / period)
    return 100 - (100 / (1 + rs))
