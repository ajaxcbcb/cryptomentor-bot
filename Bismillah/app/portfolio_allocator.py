"""
Portfolio-aware allocation for approved Decision Tree V2 candidates.
"""

from __future__ import annotations

from typing import Iterable, List

from app.trade_candidate import AllocationDecision, CandidateDecision


def _family(symbol: str) -> str:
    sym = str(symbol or "").upper()
    if sym.startswith(("BTC", "ETH", "SOL", "BNB", "XRP")):
        return "majors"
    return "alts"


def allocate(decisions: Iterable[CandidateDecision], *, user_profile) -> List[AllocationDecision]:
    approved = [decision for decision in decisions if decision.approved]
    approved.sort(key=lambda d: (-float(d.candidate.final_score or 0.0), str(d.candidate.symbol)))
    out: List[AllocationDecision] = []
    allocated_count = int(user_profile.open_positions or 0)
    family_counts = {}

    for decision in approved:
        candidate = decision.candidate
        notes = []
        family = _family(candidate.symbol)
        family_count = int(family_counts.get(family, 0))
        base_risk = float(candidate.recommended_risk_pct or user_profile.max_effective_risk_pct or 0.0)
        base_risk = min(base_risk, float(user_profile.max_effective_risk_pct or 0.0))
        penalty = min(0.35, family_count * 0.10)
        if allocated_count >= int(user_profile.max_positions or 0):
            alloc = AllocationDecision(
                decision_trace_id=candidate.decision_trace_id,
                symbol=candidate.symbol,
                allocated=False,
                recommended_risk_pct=0.0,
                portfolio_penalty=0.35,
                notes=["max_positions_reached"],
            )
            decision.approved = False
            decision.reject_reason = "max_positions_block"
            decision.display_reason = decision.display_reason or "Skipped: portfolio already full."
            decision.allocation = alloc
            out.append(alloc)
            continue
        adjusted_risk = max(0.0, min(base_risk, base_risk * (1.0 - penalty)))
        if family_count > 0:
            notes.append("correlated_family_penalty")
        if adjusted_risk < 0.25:
            notes.append("risk_below_min_after_penalty")
            adjusted_risk = 0.0
        allocated = adjusted_risk > 0.0
        if allocated:
            allocated_count += 1
            family_counts[family] = family_count + 1
        alloc = AllocationDecision(
            decision_trace_id=candidate.decision_trace_id,
            symbol=candidate.symbol,
            allocated=allocated,
            recommended_risk_pct=round(adjusted_risk, 4),
            portfolio_penalty=round(penalty, 4),
            notes=notes,
        )
        decision.allocation = alloc
        candidate.portfolio_penalty = alloc.portfolio_penalty
        candidate.recommended_risk_pct = alloc.recommended_risk_pct
        out.append(alloc)
    return out

