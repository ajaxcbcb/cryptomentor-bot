import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

try:
    from Bismillah.app.admin_daily_report import _format_playbook_clusters_brief  # type: ignore
except ImportError:
    from app.admin_daily_report import _format_playbook_clusters_brief  # type: ignore


def test_format_playbook_clusters_brief_handles_empty():
    assert _format_playbook_clusters_brief([]) == "-"


def test_format_playbook_clusters_brief_includes_key_stats():
    rows = [
        {
            "label": "swing • tag:volume_confirmation",
            "support": 12,
            "win_rate": 0.75,
            "expectancy_usdt": 0.63,
            "median_r": 1.2,
        }
    ]
    txt = _format_playbook_clusters_brief(rows, max_items=1)
    assert "volume_confirmation" in txt
    assert "n=12" in txt
    assert "wr=75.0%" in txt
    assert "exp=+0.6300" in txt
