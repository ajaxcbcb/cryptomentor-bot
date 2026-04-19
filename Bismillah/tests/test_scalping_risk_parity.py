import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.engine_runtime_shared import (  # noqa: E402
    apply_scalping_confidence_relief,
    build_scalping_risk_parity_state,
    classify_scalping_risk_parity_regime,
    get_scalping_risk_parity_controls,
)
from app.scalping_engine import ScalpingEngine  # noqa: E402


class ScalpingRiskParityTests(unittest.TestCase):
    def test_regime_boundaries(self):
        self.assertEqual(classify_scalping_risk_parity_regime(0.84, 0.85, 1.00), "under_risk")
        self.assertEqual(classify_scalping_risk_parity_regime(0.85, 0.85, 1.00), "balanced")
        self.assertEqual(classify_scalping_risk_parity_regime(1.00, 0.85, 1.00), "balanced")
        self.assertEqual(classify_scalping_risk_parity_regime(1.01, 0.85, 1.00), "over_risk")

    def test_sparse_swing_fallback_uses_active_sessions(self):
        opened_rows = [
            {"trade_type": "scalping", "effective_risk_pct": 3.5, "timeframe": "5m"},
            {"trade_type": "scalping", "effective_risk_pct": 3.5, "timeframe": "5m"},
            {"trade_type": "swing", "effective_risk_pct": 5.0, "timeframe": "1h"},
        ]
        session_rows = [
            {"trading_mode": "swing", "engine_active": True, "risk_per_trade": 5.0},
            {"trading_mode": "swing", "engine_active": True, "risk_per_trade": 4.0},
        ]
        cfg = {
            "enabled": True,
            "target_min": 0.85,
            "target_max": 1.00,
            "lookback_hours": 24,
            "min_swing_sample": 20,
            "dynamic_time_enabled": True,
            "dynamic_cap_enabled": True,
            "dynamic_conf_relief_enabled": True,
            "cap_base_pct": 0.50,
            "cap_tight_pct": 0.45,
            "cap_tighter_pct": 0.40,
        }
        state = build_scalping_risk_parity_state(opened_rows, session_rows, cfg=cfg)
        self.assertEqual(state["swing_baseline_source"], "active_swing_sessions")
        self.assertEqual(state["regime"], "under_risk")
        self.assertAlmostEqual(state["ratio"], 3.5 / 4.5, places=3)

    def test_confidence_relief_caps_penalty_and_scale_floor(self):
        conf_adapt = {
            "bucket_penalty": 6,
            "bucket_risk_scale": 0.70,
            "reason": "active",
        }
        controls = {
            "enabled": True,
            "regime": "under_risk",
            "dynamic_conf_relief_enabled": True,
            "conf_relief_max_penalty": 2,
            "conf_relief_min_scale": 0.85,
        }
        adjusted = apply_scalping_confidence_relief(conf_adapt, controls)
        self.assertEqual(adjusted["bucket_penalty"], 2)
        self.assertEqual(adjusted["bucket_risk_scale"], 0.85)
        self.assertTrue(adjusted["parity_conf_relief_applied"])

    def test_over_risk_tightens_cap_and_time_profile(self):
        opened_rows = [
            {"trade_type": "scalping", "effective_risk_pct": 6.0, "timeframe": "5m"},
            {"trade_type": "scalping", "effective_risk_pct": 6.0, "timeframe": "5m"},
            {"trade_type": "swing", "effective_risk_pct": 5.0, "timeframe": "1h"},
            {"trade_type": "swing", "effective_risk_pct": 5.0, "timeframe": "1h"},
        ]
        cfg = {
            "enabled": True,
            "target_min": 0.85,
            "target_max": 1.00,
            "lookback_hours": 24,
            "min_swing_sample": 1,
            "dynamic_time_enabled": True,
            "dynamic_cap_enabled": True,
            "dynamic_conf_relief_enabled": True,
            "cap_base_pct": 0.50,
            "cap_tight_pct": 0.45,
            "cap_tighter_pct": 0.40,
        }
        state = build_scalping_risk_parity_state(opened_rows, [], cfg=cfg)
        controls = get_scalping_risk_parity_controls(state)
        self.assertEqual(state["regime"], "over_risk")
        self.assertEqual(controls["time_profile"]["good"], 0.6)
        self.assertEqual(controls["time_profile"]["neutral"], 0.4)
        self.assertEqual(controls["cap_pct"], 0.40)
        self.assertLessEqual(max(controls["time_profile"].values()), 1.0)

    def test_effective_risk_from_qty_formula(self):
        risk = ScalpingEngine._effective_risk_pct_from_qty(
            entry_price=100.0,
            sl_price=99.0,
            quantity=10.0,
            equity=1000.0,
        )
        self.assertAlmostEqual(risk, 1.0, places=6)

    def test_time_multiplier_profile_uses_controls(self):
        engine = object.__new__(ScalpingEngine)
        engine.user_id = 1
        controls = {
            "time_profile": {"best": 1.0, "good": 1.0, "neutral": 0.7, "avoid": 0.0}
        }
        should_trade_good, mult_good = ScalpingEngine.is_optimal_trading_time(engine, controls, hour_utc=9)
        should_trade_neutral, mult_neutral = ScalpingEngine.is_optimal_trading_time(engine, controls, hour_utc=22)
        should_trade_avoid, mult_avoid = ScalpingEngine.is_optimal_trading_time(engine, controls, hour_utc=2)
        self.assertTrue(should_trade_good)
        self.assertEqual(mult_good, 1.0)
        self.assertTrue(should_trade_neutral)
        self.assertEqual(mult_neutral, 0.7)
        self.assertFalse(should_trade_avoid)
        self.assertEqual(mult_avoid, 0.0)


if __name__ == "__main__":
    unittest.main()
