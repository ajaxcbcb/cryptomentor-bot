from __future__ import annotations

from app.storage import repositories


class AuditService:
    def log_decision(self, symbol: str, decision: dict) -> None:
        repositories.insert_decision(
            symbol=symbol,
            action=decision.get("action", "SKIP"),
            direction=decision.get("direction", "NONE"),
            confidence=float(decision.get("confidence", 0.0)),
            reason=decision.get("reason", ""),
            payload=decision,
        )

    def log_execution(self, symbol: str, success: bool, message: str, payload: dict) -> None:
        repositories.insert_execution(symbol=symbol, success=success, message=message, payload=payload)
