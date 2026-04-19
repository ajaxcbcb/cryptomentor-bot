import os
import sys
from types import SimpleNamespace

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

import app.trade_history as trade_history  # type: ignore


class _FakeTable:
    def __init__(self, seed_row: dict, sink: dict):
        self._seed_row = dict(seed_row)
        self._sink = sink
        self._update_payload = None

    def select(self, *_args, **_kwargs):
        self._update_payload = None
        return self

    def update(self, payload):
        self._update_payload = dict(payload or {})
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self._update_payload is None:
            return SimpleNamespace(data=[dict(self._seed_row)])
        self._sink["update"] = dict(self._update_payload)
        return SimpleNamespace(data=[dict(self._seed_row), dict(self._update_payload)])


class _FakeDB:
    def __init__(self, seed_row: dict, sink: dict):
        self._table = _FakeTable(seed_row=seed_row, sink=sink)

    def table(self, name: str):
        assert name == "autotrade_trades"
        return self._table


def test_save_trade_close_enforces_win_reason_tags_even_with_manual_reasoning(monkeypatch):
    captured = {}
    seed_row = {
        "id": 123,
        "symbol": "BTCUSDT",
        "side": "LONG",
        "entry_price": 100.0,
        "status": "open",
        "close_reason": "",
        "pnl_usdt": 0.0,
        "entry_reasons": ["volume confirmation"],
        "confidence": 80,
        "rr_ratio": 2.0,
        "playbook_match_score": 0.0,
        "effective_risk_pct": 1.0,
        "risk_overlay_pct": 0.0,
    }
    monkeypatch.setattr(trade_history, "_db", lambda: _FakeDB(seed_row, captured))

    trade_history.save_trade_close(
        trade_id=123,
        exit_price=102.0,
        pnl_usdt=2.0,
        close_reason="closed_tp",
        win_metadata={"win_reasoning": "manual winner"},
    )

    update = captured["update"]
    assert update["win_reasoning"] == "manual winner"
    assert update.get("win_reason_tags"), "Winning close updates must persist non-empty win_reason_tags"


def test_save_trade_close_sets_structured_auto_loss_reasoning_when_missing(monkeypatch):
    captured = {}
    seed_row = {
        "id": 456,
        "symbol": "ETHUSDT",
        "side": "SHORT",
        "entry_price": 2000.0,
        "status": "open",
        "close_reason": "",
        "pnl_usdt": 0.0,
        "entry_reasons": ["rsi overbought"],
        "confidence": 70,
        "rr_ratio": 1.5,
        "playbook_match_score": 0.0,
        "effective_risk_pct": 1.0,
        "risk_overlay_pct": 0.0,
    }
    monkeypatch.setattr(trade_history, "_db", lambda: _FakeDB(seed_row, captured))

    trade_history.save_trade_close(
        trade_id=456,
        exit_price=2010.0,
        pnl_usdt=-1.25,
        close_reason="closed_sl",
        loss_reasoning="",
    )

    update = captured["update"]
    assert update["loss_reasoning"].startswith("auto_loss_reason: close_reason=closed_sl; pnl=")
    assert "source=structured_fallback" in update["loss_reasoning"]
