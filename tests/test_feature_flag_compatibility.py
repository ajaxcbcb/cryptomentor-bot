import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

import app.decision_coordinator as coord  # type: ignore


@pytest.mark.asyncio
async def test_legacy_mode_returns_pass_through(monkeypatch):
    monkeypatch.setenv("DECISION_TREE_V2_MODE", "legacy")
    decision = await coord.evaluate_scalping_signal(user_id=1, signal={"symbol": "ETHUSDT", "side": "LONG", "entry_price": 100, "sl": 99, "tp": 102, "rr_ratio": 2.0, "confidence": 80}, client=None)
    assert decision.approved is True
    assert decision.execution_mode == "legacy"

