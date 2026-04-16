import asyncio
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

from app.scalping_engine import ScalpingEngine  # type: ignore
from app.trading_mode import ScalpingConfig, ScalpingPosition  # type: ignore


class _DummyClient:
    def __init__(self, price: float):
        self.price = price
        self.sl_updates = []

    def get_ticker(self, symbol: str):
        return {"success": True, "mark_price": self.price}

    def set_position_sl(self, symbol: str, sl: float):
        self.sl_updates.append((symbol, float(sl)))
        return {"success": True}


def _mk_engine(price: float = 101.0):
    engine = ScalpingEngine.__new__(ScalpingEngine)
    cfg = ScalpingConfig()
    cfg.adaptive_timeout_protection_enabled = True
    cfg.timeout_be_trigger_pct = 0.20
    cfg.timeout_trailing_trigger_pct = 0.35
    cfg.timeout_late_tighten_multiplier = 1.4
    cfg.timeout_protection_min_update_seconds = 0
    cfg.timeout_near_flat_usdt_threshold = 0.02
    cfg.max_hold_time = 1800

    engine.user_id = 1
    engine.client = _DummyClient(price)
    engine.config = cfg
    return engine


def test_timeout_phase_boundaries():
    engine = _mk_engine()
    assert engine._timeout_phase(100, 1000) == "early"
    assert engine._timeout_phase(600, 1000) == "mid"
    assert engine._timeout_phase(900, 1000) == "late"


def test_apply_timeout_protection_moves_sl_to_breakeven_mid_phase():
    engine = _mk_engine(price=101.0)  # +1% favorable move
    pos = ScalpingPosition(
        user_id=1,
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100.0,
        quantity=1.0,
        leverage=10,
        tp_price=103.0,
        sl_price=99.0,
        opened_at=time.time() - 1000,  # mid-phase for 1800s max hold
    )
    setattr(pos, "initial_sl_price", 99.0)
    setattr(pos, "timeout_protection_applied", False)
    setattr(pos, "timeout_protection_phase", "early")
    setattr(pos, "timeout_last_sl_update_ts", 0.0)

    asyncio.run(engine._apply_timeout_protection(pos))

    assert engine.client.sl_updates, "Expected SL update call"
    _, new_sl = engine.client.sl_updates[-1]
    assert new_sl >= 100.0
    assert pos.breakeven_set is True
    assert getattr(pos, "timeout_protection_applied", False) is True

