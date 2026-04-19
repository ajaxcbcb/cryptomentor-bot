from __future__ import annotations

from app.core.models import Candle, EarlyExitResult, Position


def calculate_net_move_from_entry(position: Position, candles_since_entry: list[Candle]) -> float:
    if not candles_since_entry:
        return 0.0
    last = candles_since_entry[-1].close
    if position.side == "LONG":
        return (last - position.entry_price) / max(position.entry_price, 1e-9)
    return (position.entry_price - last) / max(position.entry_price, 1e-9)


def calculate_momentum_score(candles_since_entry: list[Candle]) -> float:
    if len(candles_since_entry) < 2:
        return 0.0
    positive = 0
    for i in range(1, len(candles_since_entry)):
        if candles_since_entry[i].close >= candles_since_entry[i - 1].close:
            positive += 1
    return positive / max(1, len(candles_since_entry) - 1)


def has_trade_stalled(position: Position, candles_since_entry: list[Candle], stall_bars: int = 5) -> bool:
    if len(candles_since_entry) < stall_bars:
        return False
    net = abs(calculate_net_move_from_entry(position, candles_since_entry[-stall_bars:]))
    return net < 0.001


def early_exit_check(position: Position, candles_since_entry: list[Candle], config: object | None = None) -> EarlyExitResult:
    momentum = calculate_momentum_score(candles_since_entry)
    net_move = calculate_net_move_from_entry(position, candles_since_entry)
    stalled = has_trade_stalled(position, candles_since_entry)

    should_exit = stalled and momentum < 0.45 and net_move <= 0.0
    reason = "trade_stalled_low_momentum" if should_exit else "hold"
    return EarlyExitResult(should_exit=should_exit, reason=reason, metrics={
        "momentum": momentum,
        "net_move": net_move,
        "stalled": 1.0 if stalled else 0.0,
    })
