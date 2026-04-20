import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

from app.admin_daily_report import _summarize_coordinator_pending_snapshot  # type: ignore


def test_summarize_coordinator_pending_snapshot_counts_and_top_symbols():
    snapshot = {
        "users": {
            111: {
                "symbols": {
                    "BTCUSDT": {
                        "pending_order": True,
                        "has_position": True,
                        "pending_owner": "swing",
                        "owner": "swing",
                        "pending_age_seconds": 20.0,
                    },
                    "ETHUSDT": {
                        "pending_order": True,
                        "has_position": False,
                        "pending_owner": "scalp",
                        "owner": "scalp",
                        "pending_age_seconds": 130.0,
                    },
                }
            },
            222: {
                "symbols": {
                    "ETHUSDT": {
                        "pending_order": True,
                        "has_position": False,
                        "pending_owner": "swing",
                        "owner": "swing",
                        "pending_age_seconds": 15.0,
                    },
                    "SOLUSDT": {
                        "pending_order": False,
                        "has_position": False,
                        "pending_owner": None,
                        "owner": "none",
                        "pending_age_seconds": None,
                    },
                }
            },
        }
    }

    out = _summarize_coordinator_pending_snapshot(snapshot, pending_ttl_seconds=90.0, top_n=3)
    assert out["pending_total"] == 3
    assert out["pending_with_position"] == 1
    assert out["pending_without_position"] == 2
    assert out["stale_pending_without_position"] == 1
    assert out["owner_mix"] == {"swing": 2, "scalp": 1}
    assert out["top_symbols"][0] == ("ETHUSDT", 2)
    assert "ETHUSDT(2)" in out["top_symbols_text"]
    assert "swing:2" in out["owner_mix_text"]


def test_summarize_coordinator_pending_snapshot_handles_empty_input():
    out = _summarize_coordinator_pending_snapshot({}, pending_ttl_seconds=90.0, top_n=5)
    assert out["pending_total"] == 0
    assert out["pending_with_position"] == 0
    assert out["pending_without_position"] == 0
    assert out["stale_pending_without_position"] == 0
    assert out["owner_mix_text"] == "-"
    assert out["top_symbols_text"] == "-"
