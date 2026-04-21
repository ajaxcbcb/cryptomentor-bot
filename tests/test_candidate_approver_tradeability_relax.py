import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

from app.candidate_approver import approve_candidate  # type: ignore
from app.trade_candidate import MarketContext, TradeCandidate, UserSegmentProfile  # type: ignore


def _build_profile(*, last_entry_minutes_ago=240.0) -> UserSegmentProfile:
    return UserSegmentProfile(
        user_id=1,
        equity=1000.0,
        equity_source="test",
        tier="small",
        max_positions=2,
        max_cluster_exposure=0.4,
        max_effective_risk_pct=1.25,
        min_quality_score=0.74,
        min_tradeability_score=0.70,
        max_daily_new_entries=4,
        frequency_throttle_minutes=90,
        allow_runner_mode=False,
        allow_fragile_setups=False,
        allow_expert_only=False,
        daily_new_entries_today=0,
        open_positions=0,
        correlated_cluster_exposure=0.0,
        last_entry_minutes_ago=last_entry_minutes_ago,
    )


def _build_candidate(*, engine="scalping", tradeability_score=0.64) -> TradeCandidate:
    return TradeCandidate(
        user_id=1,
        symbol="BTCUSDT",
        engine=engine,
        side="LONG",
        regime="trend_continuation",
        setup_name="trend_scalp",
        entry_price=100.0,
        stop_loss=99.0,
        take_profit_hint=102.0,
        rr_estimate=2.0,
        signal_confidence=82.0,
        tradeability_score=tradeability_score,
    )


def test_scalping_tradeability_threshold_relaxes_for_prolonged_inactivity(monkeypatch):
    monkeypatch.setenv("SCALPING_TRADEABILITY_RELAX_MAX", "0.10")
    monkeypatch.setenv("SCALPING_TRADEABILITY_MIN_FLOOR", "0.56")
    monkeypatch.setenv("SCALPING_TRADEABILITY_RELAX_MIN_INACTIVE_MINUTES", "60")
    monkeypatch.setenv("SCALPING_TRADEABILITY_RELAX_FULL_MINUTES", "360")

    profile = _build_profile(last_entry_minutes_ago=240.0)
    candidate = _build_candidate(engine="scalping", tradeability_score=0.64)
    market_context = MarketContext(event_risk="low", session_quality=0.8)

    decision = approve_candidate(
        candidate,
        user_profile=profile,
        market_context=market_context,
        symbol_memory={},
    )
    assert decision["approved"] is True
    assert decision["reject_reason"] == ""


def test_tradeability_relaxation_disabled_when_event_risk_high(monkeypatch):
    monkeypatch.setenv("SCALPING_TRADEABILITY_RELAX_MAX", "0.10")
    monkeypatch.setenv("SCALPING_TRADEABILITY_MIN_FLOOR", "0.56")
    monkeypatch.setenv("SCALPING_TRADEABILITY_RELAX_MIN_INACTIVE_MINUTES", "60")
    monkeypatch.setenv("SCALPING_TRADEABILITY_RELAX_FULL_MINUTES", "360")

    profile = _build_profile(last_entry_minutes_ago=240.0)
    candidate = _build_candidate(engine="scalping", tradeability_score=0.64)
    market_context = MarketContext(event_risk="high", session_quality=0.8)

    decision = approve_candidate(
        candidate,
        user_profile=profile,
        market_context=market_context,
        symbol_memory={},
    )
    assert decision["approved"] is False
    assert decision["reject_reason"] == "tradeability_below_threshold"
    assert decision["rule_audit"]["base_min_tradeability_score"] == pytest.approx(0.70)
    assert decision["rule_audit"]["effective_min_tradeability_score"] == pytest.approx(0.70)
    assert decision["rule_audit"]["relax_delta"] == pytest.approx(0.0)


def test_tradeability_relaxation_is_scalping_only(monkeypatch):
    monkeypatch.setenv("SCALPING_TRADEABILITY_RELAX_MAX", "0.10")
    monkeypatch.setenv("SCALPING_TRADEABILITY_MIN_FLOOR", "0.56")
    monkeypatch.setenv("SCALPING_TRADEABILITY_RELAX_MIN_INACTIVE_MINUTES", "60")
    monkeypatch.setenv("SCALPING_TRADEABILITY_RELAX_FULL_MINUTES", "360")

    profile = _build_profile(last_entry_minutes_ago=240.0)
    candidate = _build_candidate(engine="swing", tradeability_score=0.64)
    market_context = MarketContext(event_risk="low", session_quality=0.8)

    decision = approve_candidate(
        candidate,
        user_profile=profile,
        market_context=market_context,
        symbol_memory={},
    )
    assert decision["approved"] is False
    assert decision["reject_reason"] == "tradeability_below_threshold"
    assert decision["rule_audit"]["base_min_tradeability_score"] == pytest.approx(0.70)
    assert decision["rule_audit"]["effective_min_tradeability_score"] == pytest.approx(0.70)
    assert decision["rule_audit"]["relax_delta"] == pytest.approx(0.0)
