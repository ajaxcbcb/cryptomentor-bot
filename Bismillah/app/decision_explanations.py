"""
User-safe explanation helpers for Decision Tree V2.
"""

from __future__ import annotations

from typing import Iterable, List

from app.trade_candidate import CandidateDecision, TradeCandidate


def _label(candidate: TradeCandidate) -> str:
    return f"{candidate.symbol} {candidate.side}".strip()


def build_reject_display_reason(candidate: TradeCandidate, reject_reason: str) -> str:
    reason = str(reject_reason or candidate.reject_reason or "filtered_by_decision_tree").strip()
    if reason == "invalid_candidate":
        return f"{_label(candidate)} skipped: invalid prices or incomplete signal."
    if reason == "regime_no_trade":
        return f"{_label(candidate)} skipped: market regime is not tradeable."
    if reason == "regime_engine_mismatch":
        return f"{_label(candidate)} skipped: setup does not fit the active engine."
    if reason == "rr_below_threshold":
        return f"{_label(candidate)} skipped: reward-to-risk is below the required minimum."
    if reason == "tradeability_below_threshold":
        return f"{_label(candidate)} skipped: market conditions are too messy right now."
    if reason == "tier_quality_block":
        return f"{_label(candidate)} skipped: setup quality is too low for this equity tier."
    if reason == "tier_tradeability_block":
        return f"{_label(candidate)} skipped: conditions are not clean enough for this equity tier."
    if reason == "frequency_throttle_block":
        return f"{_label(candidate)} skipped: entry throttle is active to avoid overtrading."
    if reason == "daily_entry_limit_block":
        return f"{_label(candidate)} skipped: daily entry limit has been reached."
    if reason == "cluster_exposure_block":
        return f"{_label(candidate)} skipped: portfolio cluster exposure is already too high."
    if reason == "symbol_memory_unstable":
        return f"{_label(candidate)} skipped: recent symbol behavior has been unstable."
    if reason == "event_risk_high":
        return f"{_label(candidate)} skipped: event risk is too high right now."
    return f"{_label(candidate)} skipped: {reason.replace('_', ' ')}."


def build_approved_display_reason(candidate: TradeCandidate) -> str:
    return (
        f"{_label(candidate)} approved: quality={candidate.quality_bucket}, "
        f"regime={candidate.regime}, final_score={candidate.final_score:.2f}."
    )


def build_no_trade_cycle_message(decisions: Iterable[CandidateDecision]) -> str:
    reasons: List[str] = []
    for decision in decisions:
        if decision.approved:
            continue
        txt = str(decision.reject_reason or decision.display_reason or "").strip()
        if txt and txt not in reasons:
            reasons.append(txt)
    if not reasons:
        return "No trade this cycle: no approved setups passed the quality and safety filters."
    top = ", ".join(reasons[:3])
    return f"No trade this cycle: {top.replace('_', ' ')}."


def build_risk_clamp_explanation(symbol: str, before_pct: float, after_pct: float) -> str:
    return (
        f"{symbol} risk clamped from {float(before_pct):.2f}% to {float(after_pct):.2f}% "
        "by tier/portfolio safety rules."
    )

