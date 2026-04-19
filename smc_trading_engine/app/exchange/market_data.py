from __future__ import annotations

from app.exchange.base import ExchangeClient


async def fetch_candles(client: ExchangeClient, symbol: str, timeframe: str, limit: int = 200):
    return await client.get_candles(symbol, timeframe, limit)


async def fetch_ticker(client: ExchangeClient, symbol: str) -> float:
    return await client.get_ticker(symbol)
