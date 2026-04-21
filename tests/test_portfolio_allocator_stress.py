import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

from app.portfolio_allocator import allocate
from app.trade_candidate import CandidateDecision, TradeCandidate, UserSegmentProfile


def _decision(symbol: str, score: float):
    candidate = TradeCandidate(
        user_id=1,
        symbol=symbol,
        engine="swing",
        side="LONG",
        regime="trend_continuation",
        setup_name="t",
        entry_price=100.0,
        stop_loss=99.0,
        take_profit_hint=102.0,
        rr_estimate=2.0,
        signal_confidence=80.0,
        final_score=score,
        recommended_risk_pct=2.0,
        approved=True,
    )
    return CandidateDecision(candidate=candidate, approved=True)


def test_allocator_penalizes_same_family_and_respects_max_positions():
    profile = UserSegmentProfile(
        user_id=1,
        equity=5000.0,
        equity_source="test",
        tier="medium",
        max_positions=2,
        max_cluster_exposure=0.5,
        max_effective_risk_pct=2.0,
        min_quality_score=0.7,
        min_tradeability_score=0.65,
        max_daily_new_entries=6,
        frequency_throttle_minutes=60,
        allow_runner_mode=False,
        allow_fragile_setups=False,
        allow_expert_only=True,
    )
    decisions = [_decision("BTCUSDT", 0.9), _decision("ETHUSDT", 0.8), _decision("DOGEUSDT", 0.7)]
    out = allocate(decisions, user_profile=profile)
    assert out[0].allocated is True
    assert out[1].recommended_risk_pct <= out[0].recommended_risk_pct
    assert sum(1 for row in out if row.allocated) == 2

