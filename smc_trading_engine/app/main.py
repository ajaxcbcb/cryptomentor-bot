from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI

from app.api import routes_admin, routes_health, routes_pairs, routes_status, routes_trades
from app.config.settings import settings
from app.exchange.bitunix_client import BitunixClient
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.services.scan_service import ScanService
from app.services.scheduler import Scheduler
from app.services.state_service import StateService
from app.services.trade_service import TradeService
from app.storage.tables import ensure_tables
from app.utils.logging import setup_logging


def build_services() -> SimpleNamespace:
    exchange_client = BitunixClient()
    state_service = StateService()
    analytics_service = AnalyticsService()
    audit_service = AuditService()
    trade_service = TradeService(exchange_client, state_service, audit_service, settings)
    scan_service = ScanService(exchange_client, state_service, analytics_service, trade_service, audit_service, settings)
    scheduler = Scheduler(scan_service)
    return SimpleNamespace(
        exchange_client=exchange_client,
        state_service=state_service,
        analytics_service=analytics_service,
        audit_service=audit_service,
        trade_service=trade_service,
        scan_service=scan_service,
        scheduler=scheduler,
    )


def create_app() -> FastAPI:
    setup_logging(settings.log_level)
    ensure_tables()

    app = FastAPI(title="SMC Trading Engine", version="0.1.0")
    app.state.services = build_services()

    app.include_router(routes_health.router)
    app.include_router(routes_pairs.router)
    app.include_router(routes_status.router)
    app.include_router(routes_trades.router)
    app.include_router(routes_admin.router)

    @app.on_event("startup")
    async def on_startup() -> None:
        if settings.app_env != "test":
            await app.state.services.scheduler.start()

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await app.state.services.scheduler.stop()

    return app


app = create_app()
