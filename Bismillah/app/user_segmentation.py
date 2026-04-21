"""
Equity-aware user segmentation for Decision Tree V2.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from app.decision_tree_v2_config import get_config
from app.supabase_repo import _client
from app.trade_candidate import TradeCandidate, UserSegmentProfile

logger = logging.getLogger(__name__)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _utc_day() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _resolve_equity(client: Any, session: Dict[str, Any]) -> Tuple[float, str]:
    if client is not None:
        try:
            acc = client.get_account_info()
            available = _safe_float(acc.get("available"), 0.0)
            frozen = _safe_float(acc.get("frozen"), 0.0)
            unrealized = _safe_float(acc.get("total_unrealized_pnl"), 0.0)
            equity = available + frozen + unrealized
            if equity > 0:
                return float(equity), "live_account_info"
        except Exception as exc:
            logger.debug("[DecisionTreeV2] live equity fetch failed: %s", exc)
    current_balance = _safe_float(session.get("current_balance"), 0.0)
    if current_balance > 0:
        return current_balance, "session_current_balance"
    initial = _safe_float(session.get("initial_deposit"), 0.0)
    if initial > 0:
        return initial, "session_initial_deposit"
    return 0.0, "conservative_fallback_nano"


def _pick_tier(equity: float, cfg: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    for tier, rule in (cfg.get("tiers") or {}).items():
        lo = _safe_float(rule.get("min_equity"), 0.0)
        hi = _safe_float(rule.get("max_equity"), 1e12)
        if lo <= equity <= hi:
            return str(tier), dict(rule)
    return "nano", dict((cfg.get("tiers") or {}).get("nano") or {})


def _session_row(user_id: int) -> Dict[str, Any]:
    s = _client()
    res = (
        s.table("autotrade_sessions")
        .select("initial_deposit,current_balance,total_profit,status")
        .eq("telegram_id", int(user_id))
        .limit(1)
        .execute()
    )
    return dict((res.data or [{}])[0] or {})


def _usage_snapshot(user_id: int) -> Dict[str, Any]:
    s = _client()
    open_res = (
        s.table("autotrade_trades")
        .select("symbol,side,opened_at,trade_type")
        .eq("telegram_id", int(user_id))
        .eq("status", "open")
        .execute()
    )
    open_rows = list(open_res.data or [])
    daily_res = (
        s.table("autotrade_trades")
        .select("opened_at")
        .eq("telegram_id", int(user_id))
        .gte("opened_at", _utc_day())
        .execute()
    )
    daily_rows = list(daily_res.data or [])
    last_res = (
        s.table("autotrade_trades")
        .select("opened_at")
        .eq("telegram_id", int(user_id))
        .order("opened_at", desc=True)
        .limit(1)
        .execute()
    )
    last_opened = str((last_res.data or [{}])[0].get("opened_at") or "")
    last_entry_minutes_ago = None
    if last_opened:
        try:
            dt = datetime.fromisoformat(last_opened.replace("Z", "+00:00"))
            last_entry_minutes_ago = max(0.0, (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 60.0)
        except Exception:
            last_entry_minutes_ago = None
    majors = {"BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"}
    cluster_count = sum(1 for row in open_rows if str(row.get("symbol") or "").upper() in majors)
    open_count = len(open_rows)
    cluster_exposure = (cluster_count / open_count) if open_count else 0.0
    return {
        "open_positions": open_count,
        "daily_new_entries_today": len(daily_rows),
        "last_entry_minutes_ago": last_entry_minutes_ago,
        "correlated_cluster_exposure": cluster_exposure,
        "open_rows": open_rows,
    }


def get_profile(user_id: int, *, client: Any = None) -> UserSegmentProfile:
    cfg = get_config()
    session = _session_row(int(user_id))
    usage = _usage_snapshot(int(user_id))
    equity, source = _resolve_equity(client, session)
    tier, tier_cfg = _pick_tier(equity, cfg)
    initial = max(_safe_float(session.get("initial_deposit"), equity), 0.0)
    drawdown_ratio = 0.0
    if initial > 0 and equity > 0:
        drawdown_ratio = max(0.0, (initial - equity) / initial)

    tightened = False
    tightening_cfg = dict(cfg.get("drawdown_tightening") or {})
    if drawdown_ratio > _safe_float(tightening_cfg.get(tier), 1.0):
        tightened = True
        tier_cfg["min_quality_score"] = _safe_float(tier_cfg.get("min_quality_score")) + _safe_float(tightening_cfg.get("quality_bump"), 0.04)
        tier_cfg["min_tradeability_score"] = _safe_float(tier_cfg.get("min_tradeability_score")) + _safe_float(tightening_cfg.get("tradeability_bump"), 0.04)
        tier_cfg["max_daily_new_entries"] = max(1, int(round(_safe_float(tier_cfg.get("max_daily_new_entries"), 1) * _safe_float(tightening_cfg.get("daily_entries_multiplier"), 0.5))))
        tier_cfg["max_effective_risk_pct"] = _safe_float(tier_cfg.get("max_effective_risk_pct"), 1.0) * _safe_float(tightening_cfg.get("risk_multiplier"), 0.75)

    return UserSegmentProfile(
        user_id=int(user_id),
        equity=float(equity),
        equity_source=source,
        tier=tier,
        max_positions=int(tier_cfg.get("max_positions", 1)),
        max_cluster_exposure=float(tier_cfg.get("max_cluster_exposure", 0.25)),
        max_effective_risk_pct=float(tier_cfg.get("max_effective_risk_pct", 0.5)),
        min_quality_score=float(tier_cfg.get("min_quality_score", 0.8)),
        min_tradeability_score=float(tier_cfg.get("min_tradeability_score", 0.75)),
        max_daily_new_entries=int(tier_cfg.get("max_daily_new_entries", 1)),
        frequency_throttle_minutes=int(tier_cfg.get("frequency_throttle_minutes", 180)),
        allow_runner_mode=bool(tier_cfg.get("allow_runner_mode", False)),
        allow_fragile_setups=bool(tier_cfg.get("allow_fragile_setups", False)),
        allow_expert_only=bool(tier_cfg.get("allow_expert_only", False)),
        drawdown_ratio=float(drawdown_ratio),
        daily_new_entries_today=int(usage.get("daily_new_entries_today", 0)),
        open_positions=int(usage.get("open_positions", 0)),
        correlated_cluster_exposure=float(usage.get("correlated_cluster_exposure", 0.0)),
        last_entry_minutes_ago=usage.get("last_entry_minutes_ago"),
        tightened=tightened,
        metadata={"session": session, "usage": usage, "tier_config": tier_cfg},
    )


def score_candidate_for_segment(candidate: TradeCandidate, profile: UserSegmentProfile) -> Dict[str, Any]:
    score = 0.60
    rr = float(candidate.rr_estimate or 0.0)
    if rr >= 2.0:
        score += 0.15
    elif rr < 1.2:
        score -= 0.20

    if candidate.regime == "breakout_expansion" and profile.tier in {"nano", "micro"}:
        score -= 0.20
    if candidate.participation_bucket in {"fragile", "expert_only"} and not profile.allow_expert_only:
        score -= 0.25
    if candidate.engine == "scalping" and candidate.regime == "range_mean_reversion":
        score += 0.05
    if profile.drawdown_ratio > 0:
        score -= min(0.20, profile.drawdown_ratio)

    return {"user_segment_score": max(0.0, min(1.0, round(score, 4)))}

