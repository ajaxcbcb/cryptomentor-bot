import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from scripts.run_decision_tree_v2_simulations import run


def test_simulation_classifications_are_expected_values():
    payload = run()
    allowed = {
        "stable_optimal",
        "stable_but_too_conservative",
        "stable_but_too_active",
        "unstable_overtrading",
        "unstable_underfiltering",
        "ui_contract_risk",
        "telegram_explanation_risk",
        "portfolio_risk_instability",
        "drawdown_instability",
    }
    assert set(row["classification"] for row in payload["scenarios"]).issubset(allowed)

