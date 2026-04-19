import os
import sys
import unittest

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


if __name__ == "__main__":
    unittest.main()
