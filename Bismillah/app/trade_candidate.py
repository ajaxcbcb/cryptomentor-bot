"""
Decision Tree V2 dataclasses.
"""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Dict, List, Optional


def _primitive(value: Any) -> Any:
    if is_dataclass(value):
        return _primitive(asdict(value))
    if isinstance(value, dict):
        return {str(k): _primitive(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_primitive(v) for v in value]
    if isinstance(value, float):
        if math.isfinite(value):
            return float(value)
        return None
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return str(value)


def make_trace_id(prefix: str = "dtv2") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


@dataclass
class MarketContext:
    timestamp: float = field(default_factory=time.time)
    btc_condition: str = "UNKNOWN"
    btc_confidence: float = 0.0
    market_bias: str = "neutral"
    session_quality: float = 0.50
    event_risk: str = "unknown"
    volatility_state: str = "unknown"
    top_symbols: List[str] = field(default_factory=list)
    global_trade_suitability: float = 0.50
    selector_health: Dict[str, Any] = field(default_factory=dict)
    runtime_snapshots: Dict[str, Any] = field(default_factory=dict)
    symbol_memory_summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass
class UserSegmentProfile:
    user_id: int
    equity: float
    equity_source: str
    tier: str
    max_positions: int
    max_cluster_exposure: float
    max_effective_risk_pct: float
    min_quality_score: float
    min_tradeability_score: float
    max_daily_new_entries: int
    frequency_throttle_minutes: int
    allow_runner_mode: bool
    allow_fragile_setups: bool
    allow_expert_only: bool
    drawdown_ratio: float = 0.0
    daily_new_entries_today: int = 0
    open_positions: int = 0
    correlated_cluster_exposure: float = 0.0
    last_entry_minutes_ago: Optional[float] = None
    tightened: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass
class TradeCandidate:
    user_id: int
    symbol: str
    engine: str
    side: str
    regime: str
    setup_name: str
    entry_price: float
    stop_loss: float
    take_profit_hint: float
    rr_estimate: float
    signal_confidence: float
    tradeability_score: float = 0.0
    approval_score: float = 0.0
    community_score: float = 0.0
    user_segment_score: float = 0.0
    portfolio_penalty: float = 0.0
    final_score: float = 0.0
    recommended_risk_pct: float = 0.0
    reject_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_bucket: str = "unknown"
    participation_bucket: str = "not_suitable_for_community"
    expected_hold_profile: str = "unknown"
    expected_user_friendliness: str = "unknown"
    expected_volume_contribution_class: str = "minimal"
    user_equity_tier: str = "nano"
    max_recommended_position_count: int = 1
    max_recommended_cluster_exposure: float = 0.25
    approved: bool = False
    approval_audit: Dict[str, Any] = field(default_factory=dict)
    decision_trace_id: str = field(default_factory=make_trace_id)
    source_signal_payload: Dict[str, Any] = field(default_factory=dict)
    display_reason: str = ""
    execution_mode: str = "legacy"

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass
class AllocationDecision:
    decision_trace_id: str
    symbol: str
    allocated: bool
    recommended_risk_pct: float
    portfolio_penalty: float
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _primitive(self)


@dataclass
class CandidateDecision:
    candidate: TradeCandidate
    approved: bool
    reject_reason: str = ""
    display_reason: str = ""
    rule_audit: Dict[str, Any] = field(default_factory=dict)
    allocation: Optional[AllocationDecision] = None
    execution_mode: str = "legacy"

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "candidate": self.candidate.to_dict(),
            "approved": bool(self.approved),
            "reject_reason": str(self.reject_reason or ""),
            "display_reason": str(self.display_reason or ""),
            "rule_audit": _primitive(self.rule_audit),
            "allocation": self.allocation.to_dict() if self.allocation else None,
            "execution_mode": str(self.execution_mode or ""),
        }
        return _primitive(payload)

