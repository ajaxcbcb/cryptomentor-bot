import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.trade_history import (  # noqa: E402
    inspect_open_trade_drift,
    apply_open_trade_reconcile,
    reconcile_open_trades_with_exchange,
)


class _DummyClient:
    def __init__(self, positions=None, success=True, error=""):
        self._positions = positions or []
        self._success = bool(success)
        self._error = error

    def get_positions(self):
        if self._success:
            return {"success": True, "positions": list(self._positions)}
        return {"success": False, "error": self._error or "failed"}


class TradeReconcileTests(unittest.TestCase):
    @patch("app.trade_history.get_open_trades")
    def test_inspect_full_match_no_stale(self, mock_get_open_trades):
        mock_get_open_trades.return_value = [
            {"id": 11, "symbol": "BTCUSDT", "status": "open"},
            {"id": 12, "symbol": "ETHUSDT", "status": "open"},
        ]
        client = _DummyClient(
            positions=[
                {"symbol": "BTCUSDT", "qty": 0.1},
                {"symbol": "ETHUSDT", "size": 1},
            ]
        )

        drift = inspect_open_trade_drift(1, client, trade_type="swing")
        self.assertTrue(drift["exchange_fetch_ok"])
        self.assertEqual(drift["db_open_count"], 2)
        self.assertEqual(drift["exchange_open_count"], 2)
        self.assertEqual(drift["stale_trade_ids"], [])
        self.assertEqual(drift["stale_symbols"], [])
        self.assertFalse(drift["has_drift"])

    @patch("app.trade_history.get_open_trades")
    def test_inspect_partial_stale(self, mock_get_open_trades):
        mock_get_open_trades.return_value = [
            {"id": 21, "symbol": "BTCUSDT", "status": "open"},
            {"id": 22, "symbol": "XRPUSDT", "status": "open"},
        ]
        client = _DummyClient(positions=[{"symbol": "BTCUSDT", "qty": 0.2}])

        drift = inspect_open_trade_drift(2, client, trade_type="scalping")
        self.assertTrue(drift["exchange_fetch_ok"])
        self.assertEqual(drift["db_open_count"], 2)
        self.assertEqual(drift["exchange_open_count"], 1)
        self.assertEqual(drift["stale_trade_ids"], [22])
        self.assertEqual(drift["stale_symbols"], ["XRPUSDT"])
        self.assertTrue(drift["has_drift"])

    @patch("app.trade_history.get_open_trades")
    def test_inspect_exchange_failure(self, mock_get_open_trades):
        mock_get_open_trades.return_value = [{"id": 31, "symbol": "BTCUSDT", "status": "open"}]
        client = _DummyClient(success=False, error="timeout")

        drift = inspect_open_trade_drift(3, client, trade_type=None)
        self.assertFalse(drift["exchange_fetch_ok"])
        self.assertIn("timeout", drift["exchange_error"])
        self.assertEqual(drift["stale_trade_ids"], [])

    @patch("app.trade_history._build_stale_reconcile_close_payload")
    @patch("app.trade_history.save_trade_close")
    def test_apply_closes_only_stale_rows(self, mock_save_trade_close, mock_payload):
        mock_payload.return_value = {
            "symbol": "XRPUSDT",
            "close_reason": "stale_reconcile",
            "exit_price": 1.0,
            "pnl_usdt": 0.0,
            "loss_reasoning": "reconciled",
        }
        drift = {
            "exchange_fetch_ok": True,
            "exchange_error": "",
            "db_open_count": 2,
            "exchange_open_count": 1,
            "live_symbols": ["BTCUSDT"],
            "stale_trade_ids": [42],
            "stale_symbols": ["XRPUSDT"],
            "open_trades": [
                {"id": 41, "symbol": "BTCUSDT", "status": "open"},
                {"id": 42, "symbol": "XRPUSDT", "status": "open"},
            ],
        }
        client = _DummyClient(positions=[{"symbol": "BTCUSDT", "qty": 0.1}])

        result = apply_open_trade_reconcile(4, client, trade_type="scalping", drift=drift)
        self.assertEqual(result["healed_count"], 1)
        self.assertEqual(result["healed_trade_ids"], [42])
        self.assertEqual(result["healed_symbols"], ["XRPUSDT"])
        self.assertEqual(len(result["healed_closes"]), 1)
        self.assertEqual(result["healed_closes"][0]["trade_id"], 42)
        self.assertEqual(result["healed_closes"][0]["symbol"], "XRPUSDT")
        self.assertEqual(result["healed_closes"][0]["close_reason"], "stale_reconcile")
        mock_save_trade_close.assert_called_once()
        _, kwargs = mock_save_trade_close.call_args
        self.assertEqual(kwargs["trade_id"], 42)
        self.assertEqual(kwargs["close_reason"], "stale_reconcile")

    @patch("app.trade_history.apply_open_trade_reconcile")
    def test_wrapper_compat_returns_healed_count(self, mock_apply):
        mock_apply.return_value = {"healed_count": 3}
        client = _DummyClient()
        healed = reconcile_open_trades_with_exchange(99, client, trade_type="swing")
        self.assertEqual(healed, 3)


if __name__ == "__main__":
    unittest.main()
