import asyncio

from app.core.models import OrderRequest
from app.exchange.bitunix_client import BitunixClient


def test_bitunix_client_candles_and_order():
    async def _run():
        c = BitunixClient()
        candles = await c.get_candles("BTCUSDT", "5m", limit=5)
        assert len(candles) == 5

        r = await c.place_order(OrderRequest(symbol="BTCUSDT", side="BUY", size=1, leverage=5))
        assert r.success is True

    asyncio.run(_run())
