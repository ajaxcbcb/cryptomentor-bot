import asyncio

from app.config.settings import settings
from app.exchange.bitunix_client import BitunixClient
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.services.scan_service import ScanService
from app.services.state_service import StateService
from app.services.trade_service import TradeService
from app.storage.tables import ensure_tables


def test_scan_once_produces_outcomes():
    async def _run():
        ensure_tables()
        client = BitunixClient()
        state = StateService()
        analytics = AnalyticsService()
        audit = AuditService()
        trade = TradeService(client, state, audit, settings)
        scan = ScanService(client, state, analytics, trade, audit, settings, pairs=["BTCUSDT"])

        out = await scan.scan_once()
        assert len(out) == 1
        assert out[0]["symbol"] == "BTCUSDT"
        assert out[0]["decision"]["action"] in {"TRADE", "SKIP"}

    asyncio.run(_run())
