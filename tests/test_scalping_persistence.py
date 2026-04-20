import os
import sys
from types import SimpleNamespace

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

import app.scalping_engine as scalping_engine  # type: ignore
from app.scalping_engine import ScalpingEngine  # type: ignore


@pytest.mark.asyncio
async def test_scalping_save_position_persists_rr_ratio_and_consistent_qty(monkeypatch):
    captured = {}

    class _FakeInsert:
        def __init__(self, row):
            self._row = row

        def execute(self):
            captured["row"] = self._row
            return SimpleNamespace(data=[{"id": 321}])

    class _FakeTable:
        def insert(self, row):
            return _FakeInsert(row)

    class _FakeClient:
        def table(self, _name):
            return _FakeTable()

    monkeypatch.setattr(scalping_engine, "_client", lambda: _FakeClient())

    engine = ScalpingEngine.__new__(ScalpingEngine)
    engine.user_id = 777

    position = SimpleNamespace(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100.0,
        quantity=0.25,
        leverage=10,
        tp_price=103.0,
        sl_price=98.0,
    )
    signal = SimpleNamespace(
        confidence=76,
        rr_ratio=9.9,  # should be overridden by derived levels
        reasons=["trend_align"],
        trade_subtype="trend_scalp",
        playbook_match_score=0.0,
        effective_risk_pct=1.0,
        risk_overlay_pct=0.0,
    )

    trade_id = await engine._save_position_to_db(position, signal, order_id="OID-1")
    assert trade_id == 321
    assert captured["row"]["qty"] == pytest.approx(0.25)
    assert captured["row"]["quantity"] == pytest.approx(0.25)
    assert captured["row"]["original_quantity"] == pytest.approx(0.25)
    assert captured["row"]["remaining_quantity"] == pytest.approx(0.25)
    assert captured["row"]["rr_ratio"] == pytest.approx(1.5)
    assert captured["row"]["trade_subtype"] == "trend_scalp"


@pytest.mark.asyncio
async def test_scalping_save_position_rejects_non_positive_quantity(monkeypatch):
    class _FakeInsert:
        def execute(self):
            raise AssertionError("insert must not be called for non-positive qty")

    class _FakeTable:
        def insert(self, _row):
            return _FakeInsert()

    class _FakeClient:
        def table(self, _name):
            return _FakeTable()

    monkeypatch.setattr(scalping_engine, "_client", lambda: _FakeClient())

    engine = ScalpingEngine.__new__(ScalpingEngine)
    engine.user_id = 778

    position = SimpleNamespace(
        symbol="ETHUSDT",
        side="SELL",
        entry_price=2000.0,
        quantity=0.0,
        leverage=10,
        tp_price=1970.0,
        sl_price=2015.0,
    )
    signal = SimpleNamespace(
        confidence=80,
        rr_ratio=1.5,
        reasons=[],
        trade_subtype="trend_scalp",
        playbook_match_score=0.0,
        effective_risk_pct=1.0,
        risk_overlay_pct=0.0,
    )

    trade_id = await engine._save_position_to_db(position, signal, order_id="OID-2")
    assert trade_id is None


@pytest.mark.asyncio
async def test_scalping_save_position_persists_sideways_trade_subtype_and_bounce_flag(monkeypatch):
    from app.trading_mode import MicroScalpSignal  # type: ignore

    captured = {}

    class _FakeInsert:
        def __init__(self, row):
            self._row = row

        def execute(self):
            captured["row"] = self._row
            return SimpleNamespace(data=[{"id": 654}])

    class _FakeTable:
        def insert(self, row):
            return _FakeInsert(row)

    class _FakeClient:
        def table(self, _name):
            return _FakeTable()

    monkeypatch.setattr(scalping_engine, "_client", lambda: _FakeClient())

    engine = ScalpingEngine.__new__(ScalpingEngine)
    engine.user_id = 779

    position = SimpleNamespace(
        symbol="XRPUSDT",
        side="BUY",
        entry_price=1.2,
        quantity=100.0,
        leverage=10,
        tp_price=1.25,
        sl_price=1.17,
    )
    signal = MicroScalpSignal(
        symbol="XRPUSDT",
        side="LONG",
        entry_price=1.2,
        tp_price=1.25,
        sl_price=1.17,
        rr_ratio=1.67,
        range_support=1.18,
        range_resistance=1.26,
        range_width_pct=2.0,
        confidence=78,
        bounce_confirmed=True,
        rsi_divergence_detected=False,
        volume_ratio=1.4,
        reasons=["Sideways market: range"],
    )

    trade_id = await engine._save_position_to_db(position, signal, order_id="OID-3")
    assert trade_id == 654
    assert captured["row"]["trade_subtype"] == "sideways_scalp"
    assert captured["row"]["bounce_confirmed"] is True
