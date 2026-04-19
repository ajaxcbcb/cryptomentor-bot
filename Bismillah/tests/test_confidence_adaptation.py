import unittest
from datetime import datetime, timedelta, timezone
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.confidence_adaptation import (
    _map_edge_to_adjustments,
    _normalize_confidence_bucket,
    apply_confidence_risk_brake,
    build_confidence_adaptation_state,
    get_confidence_adaptation,
)


def _iso(hours_ago: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


class ConfidenceAdaptationTests(unittest.TestCase):
    def test_bucket_assignment_and_mapping(self):
        self.assertEqual(_normalize_confidence_bucket(69), 70)
        self.assertEqual(_normalize_confidence_bucket(70), 70)
        self.assertEqual(_normalize_confidence_bucket(74.9), 70)
        self.assertEqual(_normalize_confidence_bucket(75), 75)
        self.assertEqual(_normalize_confidence_bucket(98), 95)
        self.assertEqual(_normalize_confidence_bucket(130), 95)

        self.assertEqual(_map_edge_to_adjustments(-0.40), (6, 0.70))
        self.assertEqual(_map_edge_to_adjustments(-0.25), (4, 0.80))
        self.assertEqual(_map_edge_to_adjustments(-0.10), (2, 0.90))
        self.assertEqual(_map_edge_to_adjustments(0.00), (0, 1.00))
        self.assertEqual(_map_edge_to_adjustments(0.20), (-1, 1.00))

    def test_support_floor_keeps_low_sample_bucket_neutral(self):
        rows = []
        # Ten poor 95-99 trades (below min_support=30), should stay neutral.
        for i in range(10):
            rows.append(
                {
                    "status": "closed_sl",
                    "close_reason": "closed_sl",
                    "pnl_usdt": -4.0,
                    "loss_reasoning": "",
                    "confidence": 96,
                    "trade_type": "swing",
                    "timeframe": "1h",
                    "closed_at": _iso(i),
                }
            )
        # Add enough baseline rows in another bucket to keep mode sample meaningful.
        for i in range(40):
            rows.append(
                {
                    "status": "closed_tp",
                    "close_reason": "closed_tp",
                    "pnl_usdt": 1.0,
                    "loss_reasoning": "",
                    "confidence": 72,
                    "trade_type": "swing",
                    "timeframe": "1h",
                    "closed_at": _iso(i + 12),
                }
            )

        state = build_confidence_adaptation_state(rows, min_support=30, lookback_days=14, enabled=True)
        bucket_95 = state["modes"]["swing"]["buckets"]["95"]
        self.assertEqual(bucket_95["reason"], "insufficient_support")
        self.assertEqual(bucket_95["bucket_penalty"], 0)
        self.assertEqual(bucket_95["bucket_risk_scale"], 1.0)

    def test_outcome_filter_excludes_ops_reconcile_and_keeps_timeout(self):
        rows = [
            {
                "status": "closed_tp",
                "close_reason": "closed_tp",
                "pnl_usdt": 1.2,
                "loss_reasoning": "",
                "confidence": 75,
                "trade_type": "scalping",
                "timeframe": "5m",
                "closed_at": _iso(1),
            },
            {
                "status": "closed_sl",
                "close_reason": "closed_sl",
                "pnl_usdt": -1.0,
                "loss_reasoning": "",
                "confidence": 76,
                "trade_type": "scalping",
                "timeframe": "5m",
                "closed_at": _iso(2),
            },
            {
                "status": "max_hold_time_exceeded",
                "close_reason": "max_hold_time_exceeded",
                "pnl_usdt": -0.4,
                "loss_reasoning": "",
                "confidence": 78,
                "trade_type": "scalping",
                "timeframe": "5m",
                "closed_at": _iso(3),
            },
            {
                "status": "stale_reconcile",
                "close_reason": "stale_reconcile",
                "pnl_usdt": -2.0,
                "loss_reasoning": "reconciled from exchange",
                "confidence": 90,
                "trade_type": "scalping",
                "timeframe": "5m",
                "closed_at": _iso(4),
            },
        ]

        state = build_confidence_adaptation_state(rows, min_support=1, lookback_days=14, enabled=True)
        scalping_sample = state["modes"]["scalping"]["sample_size"]
        # 3 included: strategy_win, strategy_loss, timeout_exit. ops_reconcile excluded.
        self.assertEqual(scalping_sample, 3)

    def test_risk_brake_invariants(self):
        self.assertEqual(apply_confidence_risk_brake(2.0, 0.8), 1.6)
        # Never above playbook effective risk.
        self.assertEqual(apply_confidence_risk_brake(2.0, 1.0), 2.0)
        # Clamp lower bound.
        self.assertEqual(apply_confidence_risk_brake(0.30, 0.2), 0.25)
        # Clamp upper bound before/after scaling.
        self.assertEqual(apply_confidence_risk_brake(20.0, 1.0), 10.0)

    def test_emergency_cap_and_floor(self):
        snapshot = {
            "enabled": True,
            "emergency_max_penalty": 2,
            "emergency_min_risk_scale": 0.85,
            "modes": {
                "swing": {
                    "sample_size": 120,
                    "buckets": {
                        "95": {
                            "n": 40,
                            "edge_adj": -0.50,
                            "bucket_penalty": 6,
                            "bucket_risk_scale": 0.70,
                            "reason": "active",
                        }
                    },
                }
            },
        }
        normal = get_confidence_adaptation("swing", 96, is_emergency=False, snapshot=snapshot)
        emergency = get_confidence_adaptation("swing", 96, is_emergency=True, snapshot=snapshot)
        self.assertEqual(normal["bucket_penalty"], 6)
        self.assertEqual(normal["bucket_risk_scale"], 0.70)
        self.assertEqual(emergency["bucket_penalty"], 2)
        self.assertEqual(emergency["bucket_risk_scale"], 0.85)


if __name__ == "__main__":
    unittest.main()
