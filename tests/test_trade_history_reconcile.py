import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

import app.trade_history as trade_history  # type: ignore


def test_reconcile_uses_exchange_roundtrip_when_available(monkeypatch):
    open_rows = [
        {
            "id": 101,
            "symbol": "BTCUSDT",
            "side": "LONG",
            "entry_price": 100.0,
            "qty": 1.0,
            "order_id": "OPEN-1",
            "opened_at": "2026-04-18T00:00:00+00:00",
            "tp1_hit": False,
            "tp2_hit": False,
            "tp3_hit": False,
        }
    ]
    monkeypatch.setattr(
        trade_history,
        "get_open_trades",
        lambda _tg, trade_type=None: open_rows,
    )

    captured = []

    def _capture_close(**kwargs):
        captured.append(kwargs)

    monkeypatch.setattr(trade_history, "save_trade_close", _capture_close)

    class _Client:
        def get_positions(self):
            return {"success": True, "positions": []}

        def get_roundtrip_financials(self, **_kwargs):
            return {
                "success": True,
                "net_pnl": 2.5,
                "close_avg_price": 102.4,
            }

    result = trade_history.apply_open_trade_reconcile(999, _Client())
    assert result["healed_count"] == 1
    assert len(result["healed_closes"]) == 1
    healed_row = result["healed_closes"][0]
    assert healed_row["trade_id"] == 101
    assert healed_row["symbol"] == "BTCUSDT"
    assert healed_row["side"] == "LONG"
    assert healed_row["entry_price"] == 100.0
    assert healed_row["exit_price"] == 102.4
    assert healed_row["pnl_usdt"] == 2.5
    assert healed_row["close_reason"] == "stale_reconcile"
    assert healed_row["trade_type"] == "unknown"
    assert len(captured) == 1
    assert captured[0]["trade_id"] == 101
    assert captured[0]["close_reason"] == "stale_reconcile"
    assert captured[0]["pnl_usdt"] == 2.5
    assert captured[0]["exit_price"] == 102.4
    assert "source=exchange_history" in captured[0]["loss_reasoning"]


def test_reconcile_fallback_forces_stale_reconcile_zero_pnl_without_roundtrip(monkeypatch):
    open_rows = [
        {
            "id": 202,
            "symbol": "ETHUSDT",
            "side": "SHORT",
            "entry_price": 2500.0,
            "qty": 0.4,
            "order_id": "OPEN-2",
            "opened_at": "2026-04-18T01:00:00+00:00",
            "tp1_hit": True,   # should be ignored when roundtrip data is unavailable
            "tp2_hit": False,
            "tp3_hit": False,
        }
    ]
    monkeypatch.setattr(
        trade_history,
        "get_open_trades",
        lambda _tg, trade_type=None: open_rows,
    )

    captured = []

    def _capture_close(**kwargs):
        captured.append(kwargs)

    monkeypatch.setattr(trade_history, "save_trade_close", _capture_close)

    class _Client:
        def get_positions(self):
            return {"success": True, "positions": []}

        def get_roundtrip_financials(self, **_kwargs):
            return {"success": False, "error": "history unavailable"}

    result = trade_history.apply_open_trade_reconcile(123, _Client())
    assert result["healed_count"] == 1
    assert len(result["healed_closes"]) == 1
    healed_row = result["healed_closes"][0]
    assert healed_row["trade_id"] == 202
    assert healed_row["symbol"] == "ETHUSDT"
    assert healed_row["side"] == "SHORT"
    assert healed_row["entry_price"] == 2500.0
    assert healed_row["exit_price"] == 2500.0
    assert healed_row["pnl_usdt"] == 0.0
    assert healed_row["close_reason"] == "stale_reconcile"
    assert healed_row["trade_type"] == "unknown"
    assert len(captured) == 1
    assert captured[0]["trade_id"] == 202
    assert captured[0]["close_reason"] == "stale_reconcile"
    assert captured[0]["pnl_usdt"] == 0.0
    assert captured[0]["exit_price"] == 2500.0
    assert "source=fallback_zero_pnl" in captured[0]["loss_reasoning"]


def test_reconcile_passes_trade_type_filter(monkeypatch):
    seen = {"trade_type": None}

    def _fake_get_open_trades(_tg, trade_type=None):
        seen["trade_type"] = trade_type
        return []

    monkeypatch.setattr(trade_history, "get_open_trades", _fake_get_open_trades)

    class _Client:
        def get_positions(self):
            return {"success": True, "positions": []}

    healed = trade_history.reconcile_open_trades_with_exchange(55, _Client(), trade_type="scalping")
    assert healed == 0
    assert seen["trade_type"] == "scalping"
