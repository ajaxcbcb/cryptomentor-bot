import os
import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.scalping_engine import ScalpingEngine  # noqa: E402


class _Cfg:
    max_concurrent_positions = 1


class ScalpingReconcileCapacityTests(unittest.IsolatedAsyncioTestCase):
    async def test_jit_reconcile_unblocks_capacity(self):
        engine = object.__new__(ScalpingEngine)
        engine.user_id = 123
        engine.positions = {"BTCUSDT": object()}
        engine.config = _Cfg()
        engine._stale_reconcile_enabled = True
        engine._stale_reconcile_jit_on_capacity = True

        async def _fake_run(_reason: str):
            engine.positions.pop("BTCUSDT", None)
            return {"healed_count": 1, "pruned_local_count": 1}

        engine._run_stale_reconcile = _fake_run

        ok = await engine._ensure_capacity_for_entry()
        self.assertTrue(ok)
        self.assertEqual(len(engine.positions), 0)

    async def test_capacity_reject_when_still_full(self):
        engine = object.__new__(ScalpingEngine)
        engine.user_id = 123
        engine.positions = {"BTCUSDT": object()}
        engine.config = _Cfg()
        engine._stale_reconcile_enabled = False
        engine._stale_reconcile_jit_on_capacity = False

        async def _fake_run(_reason: str):
            return {"healed_count": 0, "pruned_local_count": 0}

        engine._run_stale_reconcile = _fake_run

        ok = await engine._ensure_capacity_for_entry()
        self.assertFalse(ok)

    @patch("app.trade_history.apply_open_trade_reconcile")
    @patch("app.trade_history.inspect_open_trade_drift")
    async def test_reconcile_emits_alert_for_each_healed_close(self, mock_inspect, mock_apply):
        engine = object.__new__(ScalpingEngine)
        engine.user_id = 555
        engine.client = object()
        engine.positions = {}
        engine._stale_reconcile_enabled = True
        engine._stale_reconcile_jit_on_capacity = True
        engine._stale_reconcile_lock = asyncio.Lock()
        engine._last_jit_reconcile_ts = 0.0
        engine._notify_user_once = AsyncMock(return_value=None)

        async def _fake_prune():
            return 0

        engine._prune_stale_local_positions = _fake_prune

        mock_inspect.return_value = {"exchange_fetch_ok": True, "open_trades": []}
        mock_apply.return_value = {
            "exchange_fetch_ok": True,
            "db_open_count": 1,
            "exchange_open_count": 0,
            "stale_symbols": ["BTCUSDT"],
            "healed_count": 1,
            "healed_trade_ids": [77],
            "healed_closes": [
                {
                    "trade_id": 77,
                    "symbol": "BTCUSDT",
                    "side": "LONG",
                    "entry_price": 100.0,
                    "exit_price": 101.5,
                    "pnl_usdt": 1.5,
                    "close_reason": "stale_reconcile",
                    "trade_type": "scalping",
                }
            ],
        }

        out = await engine._run_stale_reconcile("periodic")
        self.assertEqual(out["healed_count"], 1)
        engine._notify_user_once.assert_awaited_once()
        _, kwargs = engine._notify_user_once.await_args
        self.assertEqual(kwargs["dedupe_key"], "reconcile_close:scalping:77")
        self.assertIn("Trade Closed", kwargs["message"])
        self.assertIn("BTCUSDT", kwargs["message"])


if __name__ == "__main__":
    unittest.main()
