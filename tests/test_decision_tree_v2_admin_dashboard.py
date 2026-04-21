import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

from app.decision_tree_v2_live_dashboard import (  # type: ignore
    format_live_dashboard_message,
    format_live_symbol_breakdown_message,
    write_live_dashboard_snapshot,
)


def test_format_live_dashboard_message_contains_core_sections():
    snapshot = {
        "generated_at": "2026-04-21T05:00:00+00:00",
        "window_minutes": 30,
        "top_pairs": {
            "pairs": ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT"],
            "health": {"source": "fresh", "pair_count": 4},
        },
        "db": {
            "live_candidate_count": 12,
            "approved_count": 1,
            "rejected_count": 11,
            "symbol_histogram": {"BTCUSDT": 6, "ETHUSDT": 4},
            "reject_histogram": {"tradeability_below_threshold": 10},
            "tier_histogram": {"nano": 8, "micro": 4},
            "recent_samples": [
                {
                    "symbol": "BTCUSDT",
                    "tier": "nano",
                    "approved": False,
                    "reject_reason": "tradeability_below_threshold",
                    "final_score": 0.394,
                }
            ],
        },
        "journal": {
            "available": True,
            "metrics": {
                "signal_generated": 20,
                "decision_tree_live_apply": 7,
                "v2_rejected": 6,
                "v2_rejection_cooldown_active": 3,
                "sideways_paused": 12,
            },
            "recent_lines": [
                "Scanning 10 top-volume pairs: BTCUSDT, ETHUSDT, XRPUSDT, SOLUSDT",
                "BTCUSDT sideways entry paused by governor (mode=pause)",
            ],
        },
    }

    message = format_live_dashboard_message(snapshot)

    assert "Decision Tree V2 Live Dashboard" in message
    assert "Top-volume" in message
    assert "BTCUSDT" in message
    assert "tradeability_below_threshold" in message
    assert "Sideways paused" in message


def test_symbol_breakdown_and_export(tmp_path, monkeypatch):
    snapshot = {
        "generated_at": "2026-04-21T05:00:00+00:00",
        "window_minutes": 120,
        "journal": {
            "metrics": {
                "signal_generated": 44,
                "decision_tree_live_apply": 14,
                "v2_rejected": 10,
                "v2_rejection_cooldown_active": 4,
                "sideways_paused": 22,
            },
            "symbol_stats": {
                "BTCUSDT": {
                    "scanned": 12,
                    "signal_generated": 8,
                    "candidate_funnel": 4,
                    "v2_selected": 2,
                    "v2_rejected": 2,
                    "cooldown_active": 1,
                    "sideways_paused": 6,
                }
            },
        },
    }

    message = format_live_symbol_breakdown_message(snapshot)
    assert "Decision Tree V2 Symbol Breakdown" in message
    assert "BTCUSDT" in message
    assert "sc=12" in message

    import app.decision_tree_v2_live_dashboard as dashboard  # type: ignore

    monkeypatch.setattr(dashboard, "_ROOT", tmp_path)
    out_path = write_live_dashboard_snapshot(snapshot)
    assert out_path.endswith(".json")
    assert (tmp_path / "logs" / "decision_tree_v2").exists()
