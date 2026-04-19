from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RuntimeState:
    cooldowns: dict[str, datetime] = field(default_factory=dict)
    open_positions: dict[str, dict] = field(default_factory=dict)
    recent_decisions: dict[str, dict] = field(default_factory=dict)


class StateService:
    def __init__(self) -> None:
        self.state = RuntimeState()

    def set_open_position(self, symbol: str, payload: dict) -> None:
        self.state.open_positions[symbol] = payload

    def clear_open_position(self, symbol: str) -> None:
        self.state.open_positions.pop(symbol, None)

    def has_open_position(self, symbol: str) -> bool:
        return symbol in self.state.open_positions

    def set_recent_decision(self, symbol: str, payload: dict) -> None:
        self.state.recent_decisions[symbol] = payload

    def get_recent_decision(self, symbol: str) -> dict | None:
        return self.state.recent_decisions.get(symbol)
