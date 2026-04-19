from __future__ import annotations

from app.storage import repositories


class AnalyticsService:
    def record_symbol_status(self, symbol: str, market_state: str, confidence: float, action: str, reason: str, payload: dict) -> None:
        repositories.upsert_status(symbol, market_state, confidence, action, reason, payload)

    def latest_status(self) -> list[dict]:
        return repositories.get_status()

    def status_for(self, symbol: str) -> dict | None:
        rows = repositories.get_status(symbol)
        return rows[0] if rows else None
