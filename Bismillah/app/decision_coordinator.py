"""
Decision Tree V2 coordinator.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Iterable, List, Optional

from app.candidate_approver import approve_candidate
from app.community_objective import score_community_objective
from app.decision_explanations import (
    build_approved_display_reason,
    build_no_trade_cycle_message,
    build_reject_display_reason,
)
from app.decision_tree_v2_config import get_config, get_v2_mode
from app.market_context_provider import get_market_context
from app.portfolio_allocator import allocate
from app.regime_router import classify_regime
from app.symbol_memory import get_symbol_memory
from app.trade_candidate import CandidateDecision, TradeCandidate, make_trace_id
from app.tradeability import score_tradeability
from app.user_segmentation import get_profile, score_candidate_for_segment
from app.supabase_repo import _client

logger = logging.getLogger(__name__)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _signal_dict(raw_signal: Any) -> Dict[str, Any]:
    if isinstance(raw_signal, dict):
        return dict(raw_signal)
    payload: Dict[str, Any] = {}
    for key in dir(raw_signal):
        if key.startswith("_"):
            continue
        try:
            value = getattr(raw_signal, key)
        except Exception:
            continue
        if callable(value):
            continue
        payload[key] = value
    return payload


def _normalize_candidate(
    *,
    user_id: int,
    engine: str,
    signal: Dict[str, Any],
    regime_info: Dict[str, Any],
    profile,
    execution_mode: str,
) -> TradeCandidate:
    symbol = str(signal.get("symbol") or "").upper().strip()
    side = str(signal.get("side") or "").upper().strip()
    if side == "BUY":
        side = "LONG"
    elif side == "SELL":
        side = "SHORT"
    entry_price = _safe_float(signal.get("entry_price"), 0.0)
    tp_hint = _safe_float(signal.get("tp1", signal.get("tp_price")), 0.0)
    sl = _safe_float(signal.get("sl", signal.get("sl_price")), 0.0)
    rr = _safe_float(signal.get("rr_ratio", signal.get("rr_estimate")), 0.0)
    confidence = _safe_float(signal.get("confidence"), 0.0)
    if not tp_hint:
        tp_hint = _safe_float(signal.get("tp"), 0.0)
    setup_name = str(signal.get("trade_subtype") or signal.get("setup_name") or ("sideways_scalp" if signal.get("is_sideways") else "default_setup"))
    expected_hold_profile = "short" if str(engine).lower() in {"scalp", "scalping"} else "swing"
    return TradeCandidate(
        user_id=int(user_id),
        symbol=symbol,
        engine="scalping" if str(engine).lower() in {"scalp", "scalping"} else "swing",
        side=side or "LONG",
        regime=str(regime_info.get("regime") or "no_trade"),
        setup_name=setup_name,
        entry_price=entry_price,
        stop_loss=sl,
        take_profit_hint=tp_hint,
        rr_estimate=rr,
        signal_confidence=confidence,
        metadata={
            "preferred_engine": regime_info.get("preferred_engine"),
            "allow_secondary_engine": regime_info.get("allow_secondary_engine"),
            "regime_confidence": regime_info.get("confidence"),
        },
        quality_bucket="unknown",
        expected_hold_profile=expected_hold_profile,
        expected_user_friendliness="standard",
        expected_volume_contribution_class="minimal",
        user_equity_tier=profile.tier,
        max_recommended_position_count=profile.max_positions,
        max_recommended_cluster_exposure=profile.max_cluster_exposure,
        source_signal_payload=signal,
        execution_mode=execution_mode,
        recommended_risk_pct=_safe_float(signal.get("effective_risk_pct", signal.get("base_risk_pct")), profile.max_effective_risk_pct),
    )


def _quality_bucket(value: float) -> str:
    if value >= 0.85:
        return "premium"
    if value >= 0.72:
        return "high"
    if value >= 0.60:
        return "borderline"
    return "weak"


def _enrich_candidate_scores(candidate, *, community_score: float) -> None:
    cfg = get_config()
    scoring = dict(cfg.get("scoring") or {})
    signal_confidence_norm = max(0.0, min(1.0, float(candidate.signal_confidence or 0.0) / 100.0))
    quality_score = (
        signal_confidence_norm * float(scoring.get("quality_signal_confidence", 0.40))
        + float(candidate.tradeability_score or 0.0) * float(scoring.get("quality_tradeability", 0.25))
        + float(candidate.approval_score or 0.0) * float(scoring.get("quality_approval", 0.20))
        + float(candidate.user_segment_score or 0.0) * float(scoring.get("quality_user_segment", 0.15))
    )
    community_adjustment = min(
        float(scoring.get("community_weight", 0.05)),
        float(scoring.get("community_weight", 0.05)) * max(0.0, min(1.0, community_score)),
    )
    final_score = max(
        0.0,
        min(
            1.0,
            quality_score + community_adjustment - max(0.0, min(float(scoring.get("portfolio_penalty_max", 0.35)), float(candidate.portfolio_penalty or 0.0))),
        ),
    )
    candidate.final_score = round(final_score, 4)
    candidate.quality_bucket = _quality_bucket(final_score)
    candidate.metadata["decision_quality_score"] = round(quality_score, 4)
    candidate.metadata["decision_community_adjustment"] = round(community_adjustment, 4)


def _should_failopen(exc: Exception) -> bool:
    cfg = get_config()
    if bool(cfg.get("failopen_to_legacy", True)):
        logger.warning("[DecisionTreeV2] fail-open to legacy due to: %s", exc)
        return True
    return False


def _log_candidate_decisions(cycle_id: str, decisions: Iterable[CandidateDecision]) -> None:
    cfg = get_config()
    if not bool(cfg.get("log_all_candidates", True)):
        return
    rows: List[Dict[str, Any]] = []
    for decision in decisions:
        candidate = decision.candidate
        rows.append(
            {
                "decision_trace_id": candidate.decision_trace_id,
                "cycle_id": cycle_id,
                "user_id": candidate.user_id,
                "symbol": candidate.symbol,
                "engine": candidate.engine,
                "side": candidate.side,
                "regime": candidate.regime,
                "setup_name": candidate.setup_name,
                "quality_bucket": candidate.quality_bucket,
                "participation_bucket": candidate.participation_bucket,
                "expected_hold_profile": candidate.expected_hold_profile,
                "expected_user_friendliness": candidate.expected_user_friendliness,
                "expected_volume_contribution_class": candidate.expected_volume_contribution_class,
                "user_equity_tier": candidate.user_equity_tier,
                "signal_confidence": candidate.signal_confidence,
                "tradeability_score": candidate.tradeability_score,
                "approval_score": candidate.approval_score,
                "community_score": candidate.community_score,
                "user_segment_score": candidate.user_segment_score,
                "portfolio_penalty": candidate.portfolio_penalty,
                "final_score": candidate.final_score,
                "recommended_risk_pct": candidate.recommended_risk_pct,
                "approved": decision.approved,
                "reject_reason": decision.reject_reason,
                "display_reason": decision.display_reason,
                "approval_audit": candidate.approval_audit,
                "metadata": {
                    **candidate.metadata,
                    "execution_mode": decision.execution_mode,
                    "source_signal_payload": candidate.source_signal_payload,
                    "allocation": decision.allocation.to_dict() if decision.allocation else None,
                },
            }
        )
    if not rows:
        return
    try:
        _client().table("trade_candidates_log").insert(rows).execute()
    except Exception as exc:
        logger.debug("[DecisionTreeV2] candidate log skipped: %s", exc)


def _legacy_pass_through(signal: Dict[str, Any], user_id: int, engine: str) -> CandidateDecision:
    candidate = TradeCandidate(
        user_id=int(user_id),
        symbol=str(signal.get("symbol") or "").upper(),
        engine="scalping" if str(engine).lower() in {"scalp", "scalping"} else "swing",
        side=str(signal.get("side") or "").upper() or "LONG",
        regime="legacy",
        setup_name=str(signal.get("trade_subtype") or signal.get("setup_name") or "legacy"),
        entry_price=_safe_float(signal.get("entry_price"), 0.0),
        stop_loss=_safe_float(signal.get("sl", signal.get("sl_price")), 0.0),
        take_profit_hint=_safe_float(signal.get("tp1", signal.get("tp_price", signal.get("tp"))), 0.0),
        rr_estimate=_safe_float(signal.get("rr_ratio"), 0.0),
        signal_confidence=_safe_float(signal.get("confidence"), 0.0),
        approved=True,
        execution_mode="legacy",
        source_signal_payload=signal,
        display_reason="Legacy execution path preserved.",
        final_score=1.0,
        quality_bucket="legacy",
    )
    return CandidateDecision(candidate=candidate, approved=True, display_reason=candidate.display_reason, execution_mode="legacy")


async def evaluate_swing_cycle(
    *,
    user_id: int,
    signals: Iterable[Dict[str, Any]],
    client: Any = None,
    runtime_snapshots: Optional[Dict[str, Any]] = None,
    mixed_mode: bool = False,
) -> List[CandidateDecision]:
    mode = get_v2_mode()
    if mode == "legacy":
        return [_legacy_pass_through(_signal_dict(signal), user_id, "swing") for signal in signals]
    cycle_id = make_trace_id("cycle")
    try:
        raw_signals = [_signal_dict(signal) for signal in signals]
        market_context = get_market_context(symbols=[s.get("symbol") for s in raw_signals], runtime_snapshots=runtime_snapshots)
        profile = get_profile(int(user_id), client=client)
        decisions: List[CandidateDecision] = []
        for signal in raw_signals:
            regime_info = await classify_regime(str(signal.get("symbol") or ""), market_context, signal)
            candidate = _normalize_candidate(
                user_id=int(user_id),
                engine="swing",
                signal=signal,
                regime_info=regime_info,
                profile=profile,
                execution_mode=mode,
            )
            symbol_memory = get_symbol_memory(candidate.symbol)
            tradeability = score_tradeability(candidate, market_context, symbol_memory)
            candidate.tradeability_score = float(tradeability.get("tradeability_score", 0.0) or 0.0)
            if tradeability.get("hard_reject_reason"):
                candidate.reject_reason = str(tradeability.get("hard_reject_reason"))
            user_segment = score_candidate_for_segment(candidate, profile)
            candidate.user_segment_score = float(user_segment.get("user_segment_score", 0.0) or 0.0)
            approval = approve_candidate(candidate, user_profile=profile, market_context=market_context, symbol_memory=symbol_memory)
            candidate.approval_score = float(approval.get("approval_score", 0.0) or 0.0)
            candidate.approval_audit = dict(approval.get("rule_audit") or {})
            candidate.approved = bool(approval.get("approved", False))
            candidate.reject_reason = str(approval.get("reject_reason") or candidate.reject_reason or "")
            community = score_community_objective(candidate, market_context, profile)
            candidate.community_score = float(community.get("community_score", 0.0) or 0.0)
            candidate.participation_bucket = str(community.get("participation_bucket") or candidate.participation_bucket)
            candidate.expected_hold_profile = str(community.get("expected_hold_profile") or candidate.expected_hold_profile)
            candidate.expected_user_friendliness = str(community.get("expected_user_friendliness") or candidate.expected_user_friendliness)
            candidate.expected_volume_contribution_class = str(community.get("expected_volume_contribution_class") or candidate.expected_volume_contribution_class)
            _enrich_candidate_scores(candidate, community_score=candidate.community_score)
            if float(candidate.final_score or 0.0) < float(profile.min_quality_score or 0.0):
                candidate.approved = False
                candidate.reject_reason = candidate.reject_reason or "tier_quality_block"
            decision = CandidateDecision(
                candidate=candidate,
                approved=bool(candidate.approved),
                reject_reason=candidate.reject_reason,
                display_reason="",
                rule_audit=dict(candidate.approval_audit or {}),
                execution_mode=mode,
            )
            decision.display_reason = build_approved_display_reason(candidate) if decision.approved else build_reject_display_reason(candidate, decision.reject_reason)
            candidate.display_reason = decision.display_reason
            decisions.append(decision)
        allocations = allocate(decisions, user_profile=profile)
        for decision, allocation in zip([d for d in decisions if d.approved], allocations):
            decision.allocation = allocation
            decision.candidate.portfolio_penalty = allocation.portfolio_penalty
            if allocation.allocated:
                decision.candidate.recommended_risk_pct = allocation.recommended_risk_pct
            else:
                decision.approved = False
                decision.reject_reason = "portfolio_allocation_block"
                decision.display_reason = build_reject_display_reason(decision.candidate, decision.reject_reason)
        _log_candidate_decisions(cycle_id, decisions)
        return decisions
    except Exception as exc:
        if _should_failopen(exc):
            return [_legacy_pass_through(_signal_dict(signal), user_id, "swing") for signal in signals]
        raise


async def evaluate_scalping_signal(
    *,
    user_id: int,
    signal: Any,
    client: Any = None,
    runtime_snapshots: Optional[Dict[str, Any]] = None,
    mixed_mode: bool = False,
) -> CandidateDecision:
    mode = get_v2_mode()
    normalized = _signal_dict(signal)
    if mode == "legacy":
        return _legacy_pass_through(normalized, user_id, "scalping")
    try:
        market_context = get_market_context(symbols=[normalized.get("symbol")], runtime_snapshots=runtime_snapshots)
        profile = get_profile(int(user_id), client=client)
        regime_info = await classify_regime(str(normalized.get("symbol") or ""), market_context, normalized)
        candidate = _normalize_candidate(
            user_id=int(user_id),
            engine="scalping",
            signal=normalized,
            regime_info=regime_info,
            profile=profile,
            execution_mode=mode,
        )
        if bool(normalized.get("is_sideways")):
            candidate.regime = "range_mean_reversion"
        symbol_memory = get_symbol_memory(candidate.symbol)
        tradeability = score_tradeability(candidate, market_context, symbol_memory)
        candidate.tradeability_score = float(tradeability.get("tradeability_score", 0.0) or 0.0)
        user_segment = score_candidate_for_segment(candidate, profile)
        candidate.user_segment_score = float(user_segment.get("user_segment_score", 0.0) or 0.0)
        approval = approve_candidate(candidate, user_profile=profile, market_context=market_context, symbol_memory=symbol_memory)
        candidate.approval_score = float(approval.get("approval_score", 0.0) or 0.0)
        candidate.approval_audit = dict(approval.get("rule_audit") or {})
        candidate.approved = bool(approval.get("approved", False))
        candidate.reject_reason = str(approval.get("reject_reason") or candidate.reject_reason or "")
        community = score_community_objective(candidate, market_context, profile)
        candidate.community_score = float(community.get("community_score", 0.0) or 0.0)
        candidate.participation_bucket = str(community.get("participation_bucket") or candidate.participation_bucket)
        candidate.expected_hold_profile = str(community.get("expected_hold_profile") or candidate.expected_hold_profile)
        candidate.expected_user_friendliness = str(community.get("expected_user_friendliness") or candidate.expected_user_friendliness)
        candidate.expected_volume_contribution_class = str(community.get("expected_volume_contribution_class") or candidate.expected_volume_contribution_class)
        _enrich_candidate_scores(candidate, community_score=candidate.community_score)
        if float(candidate.final_score or 0.0) < float(profile.min_quality_score or 0.0):
            candidate.approved = False
            candidate.reject_reason = candidate.reject_reason or "tier_quality_block"
        decision = CandidateDecision(
            candidate=candidate,
            approved=bool(candidate.approved),
            reject_reason=candidate.reject_reason,
            display_reason="",
            rule_audit=dict(candidate.approval_audit or {}),
            execution_mode=mode,
        )
        if decision.approved:
            alloc = allocate([decision], user_profile=profile)
            if alloc:
                decision.allocation = alloc[0]
                decision.candidate.portfolio_penalty = alloc[0].portfolio_penalty
                decision.candidate.recommended_risk_pct = alloc[0].recommended_risk_pct
                if not alloc[0].allocated:
                    decision.approved = False
                    decision.reject_reason = "portfolio_allocation_block"
        decision.display_reason = build_approved_display_reason(candidate) if decision.approved else build_reject_display_reason(candidate, decision.reject_reason)
        candidate.display_reason = decision.display_reason
        _log_candidate_decisions(make_trace_id("cycle"), [decision])
        return decision
    except Exception as exc:
        if _should_failopen(exc):
            return _legacy_pass_through(normalized, user_id, "scalping")
        raise


async def evaluate_mixed_cycle(**kwargs) -> List[CandidateDecision]:
    return await evaluate_swing_cycle(**kwargs)


def summarize_cycle(decisions: Iterable[CandidateDecision]) -> str:
    return build_no_trade_cycle_message(decisions)
