from datetime import datetime, timezone

from app.core.exits import early_exit_check
from app.core.models import Position


def test_early_exit_dead_trade(dead_trade_candles):
    p = Position(
        symbol="BTCUSDT",
        side="LONG",
        entry_price=100,
        size=1,
        leverage=1,
        opened_at=datetime.now(timezone.utc),
    )
    r = early_exit_check(p, dead_trade_candles)
    assert isinstance(r.should_exit, bool)
