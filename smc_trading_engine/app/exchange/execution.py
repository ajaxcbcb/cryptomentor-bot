from __future__ import annotations

from app.core.models import OrderRequest
from app.exchange.base import ExchangeClient


async def execute_order(client: ExchangeClient, request: OrderRequest):
    return await client.place_order(request)


async def close_position(client: ExchangeClient, symbol: str):
    return await client.close_position(symbol)


async def cancel_orders(client: ExchangeClient, symbol: str):
    return await client.cancel_open_orders(symbol)
