"""
Lightweight Decision Tree V2 scenario runner.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_BISMILLAH = _ROOT / "Bismillah"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_BISMILLAH) not in sys.path:
    sys.path.insert(0, str(_BISMILLAH))

from app.community_objective import score_community_objective
from app.portfolio_allocator import allocate
from app.trade_candidate import CandidateDecision, TradeCandidate, UserSegmentProfile


def _profile(tier: str) -> UserSegmentProfile:
    base = {
        "nano": dict(equity=50.0, max_positions=1, max_cluster_exposure=0.25, max_effective_risk_pct=0.5, min_quality_score=0.82, min_tradeability_score=0.78, max_daily_new_entries=1, frequency_throttle_minutes=180, allow_runner_mode=False, allow_fragile_setups=False, allow_expert_only=False),
        "small": dict(equity=900.0, max_positions=2, max_cluster_exposure=0.40, max_effective_risk_pct=1.25, min_quality_score=0.74, min_tradeability_score=0.70, max_daily_new_entries=4, frequency_throttle_minutes=90, allow_runner_mode=False, allow_fragile_setups=False, allow_expert_only=False),
        "large": dict(equity=15000.0, max_positions=4, max_cluster_exposure=0.60, max_effective_risk_pct=3.0, min_quality_score=0.66, min_tradeability_score=0.62, max_daily_new_entries=8, frequency_throttle_minutes=30, allow_runner_mode=True, allow_fragile_setups=True, allow_expert_only=True),
    }[tier]
    return UserSegmentProfile(user_id=1, equity_source="simulation", tier=tier, drawdown_ratio=0.0, daily_new_entries_today=0, open_positions=0, correlated_cluster_exposure=0.0, last_entry_minutes_ago=999.0, tightened=False, metadata={}, **base)


def _candidate(symbol: str, score: float, engine: str = "swing", regime: str = "trend_continuation") -> TradeCandidate:
    return TradeCandidate(
        user_id=1,
        symbol=symbol,
        engine=engine,
        side="LONG",
        regime=regime,
        setup_name="simulation",
        entry_price=100.0,
        stop_loss=98.0,
        take_profit_hint=104.0,
        rr_estimate=2.0,
        signal_confidence=80.0,
        tradeability_score=score,
        approval_score=score,
        community_score=score,
        user_segment_score=score,
        final_score=score,
        recommended_risk_pct=1.0,
        approved=True,
        quality_bucket="high",
        source_signal_payload={"symbol": symbol},
    )


def _classification(avg_final_score: float, allocated_count: int) -> str:
    if allocated_count == 0:
        return "stable_but_too_conservative"
    if avg_final_score >= 0.75:
        return "stable_optimal"
    if avg_final_score >= 0.55:
        return "stable_but_too_active"
    return "unstable_underfiltering"


def run() -> dict:
    output = {"generated_at": datetime.now(timezone.utc).isoformat(), "scenarios": []}
    for tier in ("nano", "small", "large"):
        profile = _profile(tier)
        decisions = [
            CandidateDecision(candidate=_candidate("BTCUSDT", 0.82), approved=True, execution_mode="simulation"),
            CandidateDecision(candidate=_candidate("ETHUSDT", 0.74), approved=True, execution_mode="simulation"),
            CandidateDecision(candidate=_candidate("DOGEUSDT", 0.61, engine="scalping", regime="range_mean_reversion"), approved=True, execution_mode="simulation"),
        ]
        allocations = allocate(decisions, user_profile=profile)
        allocated_count = sum(1 for alloc in allocations if alloc.allocated)
        avg_score = sum(float(d.candidate.final_score or 0.0) for d in decisions) / max(1, len(decisions))
        output["scenarios"].append(
            {
                "tier": tier,
                "classification": _classification(avg_score, allocated_count),
                "allocated_count": allocated_count,
                "average_final_score": round(avg_score, 4),
                "allocations": [alloc.to_dict() for alloc in allocations],
                "retune": None if allocated_count > 0 else {"max_daily_new_entries": "raise only after more sample"},
            }
        )
    return output


if __name__ == "__main__":
    payload = run()
    out_dir = Path(os.getenv("DECISION_TREE_V2_OUTPUT_DIR", "logs/decision_tree_v2"))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"simulation_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(path), "scenario_count": len(payload["scenarios"])}, indent=2))
