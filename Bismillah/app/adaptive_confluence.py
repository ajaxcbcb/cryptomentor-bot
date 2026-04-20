"""
Adaptive Confluence Controller (Global, v1)
===========================================

Global controller that adjusts entry strictness based on recent *strategy*
outcomes while excluding ops/reconcile closures from learning.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Single-row key for adaptive state table.
STATE_ID = 1

# Learning window and controller safety caps.
TARGET_STRATEGY_SAMPLE = 300
TARGET_LOOKBACK_DAYS = 14
ADAPT_MIN_INTERVAL_HOURS = 6

CONF_DELTA_MIN = -3
CONF_DELTA_MAX = 8
VOL_DELTA_MIN = 0.0
VOL_DELTA_MAX = 0.4
STEP_CONF = 1
STEP_VOL = 0.05

OPS_CLOSE_STATUSES = {
    "stale_startup_reconcile",
    "legacy_stale_reconcile_backfill",
    "stale_reconcile",
}
TIMEOUT_CLOSE_STATUSES = {"max_hold_time_exceeded", "sideways_max_hold_exceeded"}


def default_adaptive_state() -> Dict[str, Any]:
    return {
        "id": STATE_ID,
        "mode": "balanced",
        "conf_delta": 0,
        "volume_min_ratio_delta": 0.0,
        "ob_fvg_requirement_mode": "soft",  # soft | required_when_risk_high
        "strategy_loss_rate": 0.0,
        "entry_without_ob_fvg_loss_share": 0.0,
        "entry_without_volume_loss_share": 0.0,
        "trade_count_per_day": 0.0,
        "strategy_sample_size": 0,
        "ops_reconcile_rate": 0.0,
        "baseline_loss_rate": None,
        "baseline_trade_count_per_day": None,
        "target_loss_lower": None,
        "target_loss_upper": None,
        "last_adapted_at": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "decision_reason": "default_state",
    }


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _parse_iso(dt_raw: Any) -> Optional[datetime]:
    if not dt_raw:
        return None
    try:
        txt = str(dt_raw)
        if txt.endswith("Z"):
            txt = txt[:-1] + "+00:00"
        dt = datetime.fromisoformat(txt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _has_keyword(text: str, needles: List[str]) -> bool:
    t = (text or "").lower()
    return any(n.lower() in t for n in needles)


def _normalize_reasons(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        # Existing rows may be comma-joined.
        return [x.strip() for x in raw.split(",") if x.strip()]
    return [str(raw)]


def has_volume_confirmation(entry_reasons: Any) -> bool:
    reasons = _normalize_reasons(entry_reasons)
    return any("volume" in r.lower() for r in reasons)


def has_ob_or_fvg(entry_reasons: Any) -> bool:
    reasons = _normalize_reasons(entry_reasons)
    return any(("ob" in r.lower()) or ("order block" in r.lower()) or ("fvg" in r.lower()) for r in reasons)


def classify_outcome_class(trade: Dict[str, Any]) -> str:
    """
    Normalize outcome class from trade row.
    Uses status as primary source and close_reason as secondary.
    """
    status = str(trade.get("status") or "").strip().lower()
    close_reason = str(trade.get("close_reason") or "").strip().lower()
    reason_hint = close_reason or status
    pnl = _to_float(trade.get("pnl_usdt"), 0.0)
    loss_reasoning = str(trade.get("loss_reasoning") or "")

    if reason_hint in TIMEOUT_CLOSE_STATUSES:
        return "timeout_exit"

    if (
        reason_hint in OPS_CLOSE_STATUSES
        or _has_keyword(loss_reasoning, ["reconciled from exchange", "position no longer open"])
    ):
        return "ops_reconcile"

    # Closed SL that is not ops reconcile counts as strategy loss.
    if reason_hint in {"closed_sl", "sl"}:
        return "strategy_loss"

    # Closed TP/positive close as strategy win.
    if reason_hint.startswith("closed_tp") or reason_hint in {"closed_flip", "closed_manual"}:
        return "strategy_win" if pnl >= 0 else "strategy_loss"

    # Generic closed fallback from status.
    if status.startswith("closed"):
        return "strategy_loss" if pnl < 0 else "strategy_win"

    return "unknown"


def _select_learning_sample(closed_trades: List[Dict[str, Any]], now_utc: datetime) -> List[Dict[str, Any]]:
    strategy = []
    for t in closed_trades:
        cls = classify_outcome_class(t)
        if cls in {"strategy_loss", "strategy_win"}:
            row = dict(t)
            row["outcome_class"] = cls
            strategy.append(row)

    strategy.sort(key=lambda r: _parse_iso(r.get("closed_at")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    last_300 = strategy[:TARGET_STRATEGY_SAMPLE]
    since_14 = now_utc - timedelta(days=TARGET_LOOKBACK_DAYS)
    in_14d = [r for r in strategy if (_parse_iso(r.get("closed_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= since_14]

    # "last 300 closed strategy trades or last 14 days (whichever larger sample available)"
    if len(in_14d) >= len(last_300):
        return in_14d
    return last_300


def build_adaptive_metrics(closed_trades: List[Dict[str, Any]], now_utc: Optional[datetime] = None) -> Dict[str, Any]:
    now = now_utc or datetime.now(timezone.utc)
    sample = _select_learning_sample(closed_trades, now)
    sample_size = len(sample)

    strategy_losses = [r for r in sample if r.get("outcome_class") == "strategy_loss"]
    strategy_wins = [r for r in sample if r.get("outcome_class") == "strategy_win"]
    strategy_total = len(strategy_losses) + len(strategy_wins)
    strategy_loss_rate = (len(strategy_losses) / strategy_total) if strategy_total > 0 else 0.0

    loss_without_ob_fvg = 0
    loss_without_volume = 0
    for r in strategy_losses:
        reasons = r.get("entry_reasons", [])
        if not has_ob_or_fvg(reasons):
            loss_without_ob_fvg += 1
        if not has_volume_confirmation(reasons):
            loss_without_volume += 1

    entry_without_ob_fvg_loss_share = (loss_without_ob_fvg / len(strategy_losses)) if strategy_losses else 0.0
    entry_without_volume_loss_share = (loss_without_volume / len(strategy_losses)) if strategy_losses else 0.0

    # Trade/day on sample span.
    sample_times = [_parse_iso(r.get("closed_at")) for r in sample]
    sample_times = [t for t in sample_times if t is not None]
    if sample_times:
        span_days = max(1.0, (max(sample_times) - min(sample_times)).total_seconds() / 86400.0)
    else:
        span_days = float(TARGET_LOOKBACK_DAYS)
    trade_count_per_day = (strategy_total / span_days) if span_days > 0 else 0.0

    # Ops reconcile rate over all provided closed rows.
    all_with_class = [{"outcome_class": classify_outcome_class(r)} for r in closed_trades]
    ops_count = sum(1 for r in all_with_class if r["outcome_class"] == "ops_reconcile")
    ops_reconcile_rate = (ops_count / len(all_with_class)) if all_with_class else 0.0

    return {
        "strategy_loss_rate": round(strategy_loss_rate, 6),
        "entry_without_ob_fvg_loss_share": round(entry_without_ob_fvg_loss_share, 6),
        "entry_without_volume_loss_share": round(entry_without_volume_loss_share, 6),
        "trade_count_per_day": round(trade_count_per_day, 6),
        "strategy_sample_size": strategy_total,
        "strategy_loss_count": len(strategy_losses),
        "strategy_win_count": len(strategy_wins),
        "ops_reconcile_rate": round(ops_reconcile_rate, 6),
        "sample_span_days": round(span_days, 3),
    }


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def compute_next_adaptive_state(
    prev_state: Dict[str, Any],
    metrics: Dict[str, Any],
    now_utc: Optional[datetime] = None,
) -> Dict[str, Any]:
    now = now_utc or datetime.now(timezone.utc)
    out = dict(default_adaptive_state())
    out.update(prev_state or {})
    out.update({k: metrics.get(k) for k in (
        "strategy_loss_rate",
        "entry_without_ob_fvg_loss_share",
        "entry_without_volume_loss_share",
        "trade_count_per_day",
        "strategy_sample_size",
        "ops_reconcile_rate",
    )})

    prev_conf = int(out.get("conf_delta", 0) or 0)
    prev_vol = float(out.get("volume_min_ratio_delta", 0.0) or 0.0)
    prev_mode = str(out.get("ob_fvg_requirement_mode") or "soft")

    last_adapted = _parse_iso(out.get("last_adapted_at"))
    if last_adapted and (now - last_adapted) < timedelta(hours=ADAPT_MIN_INTERVAL_HOURS):
        out["decision_reason"] = "rate_limited"
        out["updated_at"] = now.isoformat()
        return out

    sample_size = int(metrics.get("strategy_sample_size", 0) or 0)
    if sample_size < 40:
        out["decision_reason"] = "insufficient_sample"
        out["updated_at"] = now.isoformat()
        return out

    loss_rate = float(metrics.get("strategy_loss_rate", 0.0) or 0.0)
    trade_per_day = float(metrics.get("trade_count_per_day", 0.0) or 0.0)
    ob_loss_share = float(metrics.get("entry_without_ob_fvg_loss_share", 0.0) or 0.0)
    vol_loss_share = float(metrics.get("entry_without_volume_loss_share", 0.0) or 0.0)

    baseline_loss = out.get("baseline_loss_rate")
    if baseline_loss is None:
        baseline_loss = loss_rate
        out["baseline_loss_rate"] = baseline_loss
        out["target_loss_lower"] = _clamp(float(baseline_loss) - 0.03, 0.05, 0.9)
        out["target_loss_upper"] = _clamp(float(baseline_loss) + 0.03, 0.05, 0.9)
    baseline_trade_per_day = out.get("baseline_trade_count_per_day")
    if baseline_trade_per_day is None:
        baseline_trade_per_day = max(1.0, trade_per_day)
        out["baseline_trade_count_per_day"] = baseline_trade_per_day

    target_lower = float(out.get("target_loss_lower", 0.25))
    target_upper = float(out.get("target_loss_upper", 0.31))
    healthy_trade_floor = float(out.get("baseline_trade_count_per_day", 1.0)) * 0.75

    conf = prev_conf
    vol = prev_vol
    mode = prev_mode
    decision = "hold"

    if loss_rate > target_upper and trade_per_day >= healthy_trade_floor:
        conf += STEP_CONF
        vol += STEP_VOL
        if ob_loss_share >= 0.45 or vol_loss_share >= 0.45:
            mode = "required_when_risk_high"
        decision = "tighten_quality"
    elif loss_rate < target_lower and trade_per_day < healthy_trade_floor:
        conf -= STEP_CONF
        vol -= STEP_VOL
        if mode == "required_when_risk_high":
            mode = "soft"
        decision = "relax_for_volume"
    else:
        # No directional move, but still enforce safe mode based on concentrated
        # weak-confluence losses.
        if ob_loss_share >= 0.5 and loss_rate >= target_upper:
            mode = "required_when_risk_high"
            decision = "enforce_ob_fvg_high_risk"

    out["conf_delta"] = int(_clamp(conf, CONF_DELTA_MIN, CONF_DELTA_MAX))
    out["volume_min_ratio_delta"] = round(_clamp(vol, VOL_DELTA_MIN, VOL_DELTA_MAX), 4)
    out["ob_fvg_requirement_mode"] = mode if mode in {"soft", "required_when_risk_high"} else "soft"
    out["last_adapted_at"] = now.isoformat()
    out["updated_at"] = now.isoformat()
    out["decision_reason"] = decision
    return out


def _safe_client():
    from app.supabase_repo import _client
    return _client()


def fetch_closed_trades(limit: int = 2500) -> List[Dict[str, Any]]:
    """
    Fetch recent closed trades for adaptive metrics.
    Uses pagination and keeps payload compact.
    """
    s = _safe_client()
    collected: List[Dict[str, Any]] = []
    page_size = min(1000, max(100, limit))
    page = 0
    while len(collected) < limit:
        frm = page * page_size
        to = frm + page_size - 1
        res = (
            s.table("autotrade_trades")
            .select(
                "id,status,close_reason,pnl_usdt,loss_reasoning,entry_reasons,closed_at,"
                "entry_price,sl_price,qty,quantity,original_quantity,trade_type,timeframe"
            )
            .neq("status", "open")
            .order("closed_at", desc=True)
            .range(frm, to)
            .execute()
        )
        rows = res.data or []
        if not rows:
            break
        collected.extend(rows)
        if len(rows) < page_size:
            break
        page += 1
    return collected[:limit]


def load_adaptive_state() -> Dict[str, Any]:
    s = _safe_client()
    try:
        res = s.table("adaptive_config_state").select("*").eq("id", STATE_ID).limit(1).execute()
        if res.data:
            row = dict(res.data[0])
            base = default_adaptive_state()
            base.update(row)
            return base
    except Exception as e:
        logger.warning(f"[Adaptive] load state failed, using default: {e}")
    return default_adaptive_state()


def save_adaptive_state(state: Dict[str, Any]) -> bool:
    s = _safe_client()
    payload = dict(default_adaptive_state())
    payload.update(state or {})
    payload["id"] = STATE_ID
    try:
        s.table("adaptive_config_state").upsert(payload, on_conflict="id").execute()
        return True
    except Exception as e:
        logger.warning(f"[Adaptive] save state failed: {e}")
        return False


def refresh_global_adaptive_state() -> Dict[str, Any]:
    prev = load_adaptive_state()
    closed = fetch_closed_trades(limit=2500)
    metrics = build_adaptive_metrics(closed)
    nxt = compute_next_adaptive_state(prev, metrics)
    save_adaptive_state(nxt)
    logger.info(
        "[Adaptive] decision=%s sample=%s loss_rate=%.3f trade_day=%.2f conf_delta=%s vol_delta=%.2f ob_mode=%s",
        nxt.get("decision_reason"),
        nxt.get("strategy_sample_size"),
        float(nxt.get("strategy_loss_rate") or 0.0),
        float(nxt.get("trade_count_per_day") or 0.0),
        nxt.get("conf_delta"),
        float(nxt.get("volume_min_ratio_delta") or 0.0),
        nxt.get("ob_fvg_requirement_mode"),
    )
    return nxt


def get_adaptive_overrides() -> Dict[str, Any]:
    """
    Lightweight reader for engines.
    Returns bounded overlay values and latest metrics.
    """
    st = load_adaptive_state()
    return {
        "conf_delta": int(_clamp(int(st.get("conf_delta", 0) or 0), CONF_DELTA_MIN, CONF_DELTA_MAX)),
        "volume_min_ratio_delta": float(_clamp(float(st.get("volume_min_ratio_delta", 0.0) or 0.0), VOL_DELTA_MIN, VOL_DELTA_MAX)),
        "ob_fvg_requirement_mode": st.get("ob_fvg_requirement_mode", "soft"),
        "strategy_loss_rate": float(st.get("strategy_loss_rate", 0.0) or 0.0),
        "ops_reconcile_rate": float(st.get("ops_reconcile_rate", 0.0) or 0.0),
        "trade_count_per_day": float(st.get("trade_count_per_day", 0.0) or 0.0),
        "strategy_sample_size": int(st.get("strategy_sample_size", 0) or 0),
        "decision_reason": st.get("decision_reason", ""),
        "updated_at": st.get("updated_at"),
    }
