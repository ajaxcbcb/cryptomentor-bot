from __future__ import annotations

from datetime import datetime, timezone
import logging
import os
import sys
from typing import Optional

from app.core.cooldown import is_pair_in_cooldown, update_pair_cooldown
from app.core.models import OrderRequest, TradeDecision
from app.exchange.execution import execute_order

logger = logging.getLogger(__name__)

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_BISMILLAH_APP_PATH = os.path.join(_ROOT, "Bismillah", "app")
if _BISMILLAH_APP_PATH not in sys.path:
    sys.path.insert(0, _BISMILLAH_APP_PATH)

try:
    from leverage_policy import get_auto_max_safe_leverage  # type: ignore
except Exception:
    def get_auto_max_safe_leverage(
        symbol: str,
        entry_price: Optional[float] = None,
        sl_price: Optional[float] = None,
        baseline_leverage: Optional[int] = None,
    ) -> int:
        _ = (symbol, entry_price, sl_price, baseline_leverage)
        return int(baseline_leverage or 20)


class TradeService:
    def __init__(self, exchange_client, state_service, audit_service, config) -> None:
        self.exchange_client = exchange_client
        self.state_service = state_service
        self.audit_service = audit_service
        self.config = config

    async def execute_trade_decision(self, symbol: str, decision: TradeDecision) -> dict:
        now = datetime.now(timezone.utc)

        if decision.action != "TRADE":
            return {"executed": False, "reason": "decision_skip"}

        if self.state_service.has_open_position(symbol):
            return {"executed": False, "reason": "position_already_open"}

        if is_pair_in_cooldown(symbol, {"cooldowns": self.state_service.state.cooldowns}, now, self.config):
            return {"executed": False, "reason": "pair_in_cooldown"}

        if not getattr(self.config, "execution_enabled", False):
            return {"executed": False, "reason": "execution_disabled_feature_flag"}

        side = "BUY" if decision.direction == "LONG" else "SELL"
        baseline_leverage = int(getattr(self.config, "default_leverage", 20))
        effective_leverage = get_auto_max_safe_leverage(
            symbol=symbol,
            entry_price=None,
            sl_price=decision.invalidation_level,
            baseline_leverage=baseline_leverage,
        )
        logger.info(
            "[SMC] leverage_mode=auto_max_safe symbol=%s baseline_leverage=%sx effective_leverage=%sx",
            symbol,
            baseline_leverage,
            effective_leverage,
        )
        req = OrderRequest(
            symbol=symbol,
            side=side,
            order_type="MARKET",
            size=1.0,
            leverage=effective_leverage,
            stop_loss=decision.invalidation_level,
        )
        result = await execute_order(self.exchange_client, req)

        self.audit_service.log_execution(symbol, result.success, result.message, result.model_dump())
        if result.success:
            self.state_service.set_open_position(symbol, {
                "symbol": symbol,
                "side": decision.direction,
                "opened_at": now.isoformat(),
            })
            update_pair_cooldown(symbol, {"cooldowns": self.state_service.state.cooldowns}, now, self.config)

        return {
            "executed": result.success,
            "reason": result.message or result.status,
            "order": result.model_dump(),
        }

    async def close_position_if_needed(self, symbol: str, reason: str) -> dict:
        # Placeholder for advanced management path.
        self.state_service.clear_open_position(symbol)
        return {"closed": True, "symbol": symbol, "reason": reason}
