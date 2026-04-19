from __future__ import annotations

from app.config.pairs import DEFAULT_PAIRS
from app.core.context_builder import build_trade_context
from app.core.decision_engine import evaluate_trade
from app.data.timeframe_builder import build_timeframe_context


class ScanService:
    def __init__(self, exchange_client, state_service, analytics_service, trade_service, audit_service, config, pairs: list[str] | None = None):
        self.exchange_client = exchange_client
        self.state_service = state_service
        self.analytics_service = analytics_service
        self.trade_service = trade_service
        self.audit_service = audit_service
        self.config = config
        self.pairs = pairs or list(DEFAULT_PAIRS)

    async def scan_once(self) -> list[dict]:
        outcomes: list[dict] = []
        for symbol in self.pairs:
            timeframe_data = await build_timeframe_context(symbol, self.exchange_client, self.config)
            context = build_trade_context(symbol, timeframe_data, self.config)
            decision = evaluate_trade(context, self.config)

            decision_payload = decision.model_dump()
            self.state_service.set_recent_decision(symbol, decision_payload)
            self.audit_service.log_decision(symbol, decision_payload)

            execution = {"executed": False, "reason": "shadow_only"}
            if decision.action == "TRADE" and not getattr(self.config, "shadow_mode", True):
                execution = await self.trade_service.execute_trade_decision(symbol, decision)

            outcome = {
                "symbol": symbol,
                "market_state": context.market_state.state,
                "confidence": context.confidence.score,
                "decision": decision_payload,
                "execution": execution,
                "shadow_mode": bool(getattr(self.config, "shadow_mode", True)),
            }
            self.analytics_service.record_symbol_status(
                symbol=symbol,
                market_state=context.market_state.state,
                confidence=context.confidence.score,
                action=decision.action,
                reason=decision.reason,
                payload=outcome,
            )
            outcomes.append(outcome)
        return outcomes

    async def scan_loop(self):
        import asyncio

        while True:
            await self.scan_once()
            await asyncio.sleep(int(getattr(self.config, "scan_interval_seconds", 20)))
