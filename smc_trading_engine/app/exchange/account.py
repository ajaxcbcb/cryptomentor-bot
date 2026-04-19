from __future__ import annotations

from app.exchange.base import ExchangeClient


async def fetch_account(client: ExchangeClient):
    return await client.get_account_info()


async def fetch_open_position(client: ExchangeClient, symbol: str):
    return await client.get_open_position(symbol)
