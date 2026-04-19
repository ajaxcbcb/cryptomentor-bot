from __future__ import annotations

import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone

import httpx

from app.config.settings import settings
from app.core.models import AccountInfo, Candle, OrderRequest, OrderResult, Position
from app.exchange.mappers import map_account_info, map_order_result


class BitunixClient:
    """
    Bitunix adapter scaffold.
    TODO: Replace endpoint paths/signing shape with final Bitunix contract in each method.
    """

    def __init__(self, base_url: str | None = None, api_key: str | None = None, api_secret: str | None = None):
        self.base_url = (base_url or settings.bitunix_base_url).rstrip("/")
        self.api_key = api_key or settings.bitunix_api_key
        self.api_secret = api_secret or settings.bitunix_api_secret

    def _headers(self, method: str, path: str, body: str = "") -> dict[str, str]:
        ts = str(int(time.time() * 1000))
        prehash = f"{ts}{method.upper()}{path}{body}"
        signature = hmac.new(self.api_secret.encode("utf-8"), prehash.encode("utf-8"), hashlib.sha256).hexdigest() if self.api_secret else ""
        return {
            "X-Bitunix-Key": self.api_key,
            "X-Bitunix-Sign": signature,
            "X-Bitunix-Ts": ts,
            "Content-Type": "application/json",
        }

    async def get_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        # TODO(bitunix): map to real candles endpoint and response schema.
        now = datetime.now(timezone.utc)
        step = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
        }.get(timeframe, timedelta(minutes=1))
        base = 100.0 if "BTC" not in symbol else 60000.0
        candles: list[Candle] = []
        for i in range(limit):
            ts = now - step * (limit - i)
            price = base + (i * 0.5)
            candles.append(
                Candle(timestamp=ts, open=price, high=price * 1.001, low=price * 0.999, close=price * 1.0002, volume=10 + i)
            )
        return candles

    async def get_ticker(self, symbol: str) -> float:
        candles = await self.get_candles(symbol, "1m", limit=1)
        return candles[-1].close

    async def get_open_position(self, symbol: str) -> Position | None:
        return None

    async def get_account_info(self) -> AccountInfo:
        # TODO(bitunix): map to account endpoint response.
        return map_account_info({"equity": 10000, "available": 9000, "margin": 1000, "unrealized_pnl": 0})

    async def place_order(self, request: OrderRequest) -> OrderResult:
        # TODO(bitunix): send real order request.
        return map_order_result(True, request.symbol, {"status": "simulated", "order_id": f"sim-{int(time.time())}"}, "simulated_place_order")

    async def close_position(self, symbol: str) -> OrderResult:
        return map_order_result(True, symbol, {"status": "simulated_closed"}, "simulated_close_position")

    async def cancel_open_orders(self, symbol: str) -> list[OrderResult]:
        return [map_order_result(True, symbol, {"status": "simulated_cancel"}, "simulated_cancel_orders")]
