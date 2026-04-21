import os
import sys
from types import SimpleNamespace

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

from app.position_state_manager import label_position_state


def test_position_state_manager_runner_advisory():
    position = SimpleNamespace(entry_price=100.0, tp_price=110.0, sl_price=95.0, side="BUY", opened_at=0.0, max_hold_until=1000.0)
    profile = SimpleNamespace(allow_runner_mode=True)
    out = label_position_state(position=position, user_profile=profile, current_price=116.0, elapsed_seconds=200.0)
    assert out["state"] == "runner"
    assert out["runner_allowed"] is True

