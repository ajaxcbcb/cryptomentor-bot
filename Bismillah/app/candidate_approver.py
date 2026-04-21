"""
Hard approval gate for Decision Tree V2.
"""

from __future__ import annotations

import math
import os
from typing import Any, Dict

from app.decision_tree_v2_config import get_config


def _is_finite_positive(value: Any) -> bool:
    try:
        v = float(value)
    except Exception:
        return False
    return math.isfinite(v) and v > 0


def _effective_tradeability_threshold(candidate, user_profile, market_context) -> Dict[str, float]:
    """
    Compute a bounded, scalping-only adaptive threshold to reduce prolonged
    no-trade stalls without bypassing core safety constraints.
    """
    base_min = float(user_profile.min_tradeability_score or 0.0)
    effective_min = float(base_min)
    relax_delta = 0.0

    engine = str(getattr(candidate, "engine", "") or "").strip().lower()
    if engine not in {"scalp", "scalping"}:
        return {
            "base_min_tradeability_score": base_min,
            "effective_min_tradeability_score": effective_min,
            "relax_delta": relax_delta,
        }

    event_risk = str(getattr(market_context, "event_risk", "unknown") or "unknown").strip().lower()
    if event_risk == "high":
        return {
            "base_min_tradeability_score": base_min,
            "effective_min_tradeability_score": effective_min,
            "relax_delta": relax_delta,
        }

    max_relax = max(0.0, min(0.15, float(os.getenv("SCALPING_TRADEABILITY_RELAX_MAX", "0.10") or 0.10)))
    min_floor = max(0.45, min(0.75, float(os.getenv("SCALPING_TRADEABILITY_MIN_FLOOR", "0.56") or 0.56)))
    min_inactive_minutes = max(30.0, float(os.getenv("SCALPING_TRADEABILITY_RELAX_MIN_INACTIVE_MINUTES", "60") or 60))
    full_relax_minutes = max(
        min_inactive_minutes + 60.0,
        float(os.getenv("SCALPING_TRADEABILITY_RELAX_FULL_MINUTES", "360") or 360),
    )

    daily_new_entries = int(getattr(user_profile, "daily_new_entries_today", 0) or 0)
    open_positions = int(getattr(user_profile, "open_positions", 0) or 0)
    inactivity_minutes = getattr(user_profile, "last_entry_minutes_ago", None)

    if daily_new_entries == 0 and open_positions == 0 and inactivity_minutes is not None:
        inactive = max(0.0, float(inactivity_minutes))
        if inactive >= min_inactive_minutes:
            ramp = min(1.0, (inactive - min_inactive_minutes) / max(1.0, full_relax_minutes - min_inactive_minutes))
            # Start small, then ramp towards the cap.
            relax_delta = max_relax * (0.25 + 0.75 * ramp)

    effective_min = max(min_floor, base_min - relax_delta)
    return {
        "base_min_tradeability_score": round(base_min, 4),
        "effective_min_tradeability_score": round(effective_min, 4),
        "relax_delta": round(relax_delta, 4),
    }


def approve_candidate(candidate, *, user_profile, market_context, symbol_memory) -> Dict[str, Any]:
    cfg = get_config()
    engine_key = "scalping" if str(candidate.engine).strip().lower() in {"scalp", "scalping"} else "swing"
    rr_thresholds = dict(((cfg.get("rr_thresholds") or {}).get(engine_key)) or {})
    min_rr = float(rr_thresholds.get(candidate.regime, 999.0))
    audit: Dict[str, Any] = {"rules": []}

    if not (_is_finite_positive(candidate.entry_price) and _is_finite_positive(candidate.stop_loss) and _is_finite_positive(candidate.take_profit_hint)):
        return {"approved": False, "reject_reason": "invalid_candidate", "approval_score": 0.0, "rule_audit": {"rules": ["invalid_candidate"]}}

    if candidate.regime in {"high_volatility_unstable", "no_trade"}:
        return {"approved": False, "reject_reason": "regime_no_trade", "approval_score": 0.0, "rule_audit": {"rules": ["regime_no_trade"]}}

    preferred_engine = str(candidate.metadata.get("preferred_engine") or "").strip().lower()
    allow_secondary = bool(candidate.metadata.get("allow_secondary_engine", False))
    normalized_engine = str(candidate.engine or "").strip().lower()
    if preferred_engine and preferred_engine != normalized_engine and not allow_secondary:
        return {"approved": False, "reject_reason": "regime_engine_mismatch", "approval_score": 0.0, "rule_audit": {"rules": ["regime_engine_mismatch"]}}

    if float(candidate.rr_estimate or 0.0) < min_rr:
        return {"approved": False, "reject_reason": "rr_below_threshold", "approval_score": 0.0, "rule_audit": {"rules": ["rr_below_threshold"], "required_rr": min_rr}}

    tradeability_policy = _effective_tradeability_threshold(candidate, user_profile, market_context)
    min_tradeability_score = float(tradeability_policy.get("effective_min_tradeability_score", user_profile.min_tradeability_score) or 0.0)
    if float(candidate.tradeability_score or 0.0) < min_tradeability_score:
        return {
            "approved": False,
            "reject_reason": "tradeability_below_threshold",
            "approval_score": 0.0,
            "rule_audit": {
                "rules": ["tradeability_below_threshold"],
                **tradeability_policy,
            },
        }

    event_risk = str(getattr(market_context, "event_risk", "unknown") or "unknown").lower()
    if event_risk == "high":
        return {"approved": False, "reject_reason": "event_risk_high", "approval_score": 0.0, "rule_audit": {"rules": ["event_risk_high"]}}

    if int(user_profile.daily_new_entries_today or 0) >= int(user_profile.max_daily_new_entries or 0):
        return {"approved": False, "reject_reason": "daily_entry_limit_block", "approval_score": 0.0, "rule_audit": {"rules": ["daily_entry_limit_block"]}}

    if user_profile.last_entry_minutes_ago is not None and float(user_profile.last_entry_minutes_ago) < float(user_profile.frequency_throttle_minutes or 0):
        return {"approved": False, "reject_reason": "frequency_throttle_block", "approval_score": 0.0, "rule_audit": {"rules": ["frequency_throttle_block"], "minutes_since_last_entry": user_profile.last_entry_minutes_ago}}

    if int(user_profile.open_positions or 0) >= int(user_profile.max_positions or 0):
        return {"approved": False, "reject_reason": "max_positions_block", "approval_score": 0.0, "rule_audit": {"rules": ["max_positions_block"]}}

    if float(user_profile.correlated_cluster_exposure or 0.0) >= float(user_profile.max_cluster_exposure or 0.0):
        return {"approved": False, "reject_reason": "cluster_exposure_block", "approval_score": 0.0, "rule_audit": {"rules": ["cluster_exposure_block"]}}

    if symbol_memory:
        if float(symbol_memory.get("stopout_density", 0.0) or 0.0) >= 0.60 or float(symbol_memory.get("fakeout_density", 0.0) or 0.0) >= 0.50:
            return {"approved": False, "reject_reason": "symbol_memory_unstable", "approval_score": 0.0, "rule_audit": {"rules": ["symbol_memory_unstable"]}}

    approval_score = (
        min(1.0, max(0.0, float(candidate.signal_confidence or 0.0) / 100.0)) * 0.45
        + min(1.0, max(0.0, float(candidate.tradeability_score or 0.0))) * 0.35
        + min(1.0, max(0.0, float(candidate.rr_estimate or 0.0) / max(min_rr, 1e-9))) * 0.20
    )
    audit["rules"].append("approved")
    audit["required_rr"] = min_rr
    return {"approved": True, "reject_reason": "", "approval_score": round(min(1.0, approval_score), 4), "rule_audit": audit}
