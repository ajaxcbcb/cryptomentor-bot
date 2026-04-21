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
from app.trade_candidate import UserSegmentProfile


@pytest.mark.asyncio
async def test_live_pipeline_rejects_bad_trade_even_if_community_is_good(monkeypatch):
    monkeypatch.setenv("DECISION_TREE_V2_MODE", "live")
    monkeypatch.setattr(coord, "get_market_context", lambda **_kwargs: type("Ctx", (), {"session_quality": 0.8, "event_risk": "low", "btc_condition": "TRENDING", "market_bias": "risk_on"})())
    monkeypatch.setattr(coord, "get_profile", lambda *_args, **_kwargs: UserSegmentProfile(user_id=1, equity=1000.0, equity_source="test", tier="small", max_positions=2, max_cluster_exposure=0.4, max_effective_risk_pct=1.25, min_quality_score=0.74, min_tradeability_score=0.70, max_daily_new_entries=4, frequency_throttle_minutes=90, allow_runner_mode=False, allow_fragile_setups=False, allow_expert_only=False, last_entry_minutes_ago=999.0))
    async def _fake_classify(*args, **kwargs):
        return {"regime": "trend_continuation", "preferred_engine": "swing", "allow_secondary_engine": True, "confidence": 80.0, "reject_reason": ""}
    monkeypatch.setattr(coord, "classify_regime", _fake_classify)
    monkeypatch.setattr(coord, "get_symbol_memory", lambda _symbol: {})
    signal = {"symbol": "BTCUSDT", "side": "LONG", "entry_price": 100.0, "sl": 99.8, "tp1": 100.1, "rr_ratio": 0.5, "confidence": 95.0}
    decisions = await coord.evaluate_swing_cycle(user_id=1, signals=[signal], client=None)
    assert decisions[0].approved is False
    assert decisions[0].reject_reason == "rr_below_threshold"
