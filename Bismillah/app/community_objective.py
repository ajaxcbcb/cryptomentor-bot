"""
Healthy community-participation scoring for Decision Tree V2.
"""

from __future__ import annotations

from typing import Any, Dict


def score_community_objective(candidate, market_context, user_profile) -> Dict[str, Any]:
    if not getattr(candidate, "approved", False):
        return {
            "community_score": 0.0,
            "participation_bucket": "not_suitable_for_community",
            "expected_volume_contribution_class": "minimal",
            "community_reject_reason": candidate.reject_reason or "candidate_not_approved",
        }

    engine = str(candidate.engine or "").strip().lower()
    regime = str(candidate.regime or "").strip().lower()
    rr = float(candidate.rr_estimate or 0.0)
    final_score = float(candidate.final_score or 0.0)
    session_quality = float(getattr(market_context, "session_quality", 0.50) or 0.50)
    score = 0.20 + min(0.45, final_score * 0.45) + min(0.15, session_quality * 0.15)

    hold_profile = "intraday"
    friendliness = "standard"
    volume_class = "low"
    bucket = "niche_but_good"

    if regime == "range_mean_reversion" and engine == "scalping":
        score += 0.10
        hold_profile = "short"
        friendliness = "high"
        bucket = "high_quality_broad_participation"
        volume_class = "medium"
    elif regime in {"trend_continuation", "breakout_expansion"} and rr >= 1.8:
        score += 0.08
        hold_profile = "swing"
        friendliness = "medium"
        bucket = "niche_but_good"
        volume_class = "medium"

    if not bool(getattr(user_profile, "allow_fragile_setups", False)) and regime == "breakout_expansion":
        score -= 0.05

    if float(candidate.tradeability_score or 0.0) < 0.65:
        bucket = "fragile"
        volume_class = "minimal"
        score -= 0.12

    if float(candidate.tradeability_score or 0.0) < 0.55:
        bucket = "not_suitable_for_community"
        volume_class = "minimal"
        score = 0.0

    return {
        "community_score": max(0.0, min(1.0, round(score, 4))),
        "participation_bucket": bucket,
        "expected_hold_profile": hold_profile,
        "expected_user_friendliness": friendliness,
        "expected_volume_contribution_class": volume_class,
        "community_reject_reason": "" if score > 0 else "not_suitable_for_community",
    }

