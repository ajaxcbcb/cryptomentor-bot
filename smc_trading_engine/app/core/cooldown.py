from __future__ import annotations

from datetime import datetime, timedelta, timezone


def is_pair_in_cooldown(symbol: str, state: dict, now: datetime, config: object) -> bool:
    cooldowns = state.setdefault("cooldowns", {})
    until = cooldowns.get(symbol)
    if not until:
        return False
    return now < until


def update_pair_cooldown(symbol: str, state: dict, now: datetime, config: object) -> None:
    minutes = int(getattr(config, "pair_cooldown_minutes", 30))
    state.setdefault("cooldowns", {})[symbol] = now.replace(tzinfo=timezone.utc) + timedelta(minutes=minutes)
