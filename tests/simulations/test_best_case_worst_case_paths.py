import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from scripts.run_decision_tree_v2_simulations import run


def test_simulation_runner_emits_retune_key_when_needed():
    payload = run()
    assert all("retune" in row for row in payload["scenarios"])

