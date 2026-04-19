"""
Mode-Aware Confidence Adaptation (Global, v1)
=============================================

Learns confidence bucket performance per trading mode and returns:
- bucket-specific confidence penalty for entry gating
- bucket-specific risk scale for runtime sizing brake
"""

from __future__ import annotations

import copy
import logging
import os
import threading
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

from app.adaptive_confluence import classify_outcome_class

logger = logging.getLogger(__name__)

_MODES = ("swing", "scalping")
_BUCKET_MIN = 70
_BUCKET_MAX = 99
_BUCKET_STEP = 5
_FALLBACK_LAST_N = 300
_MAX_FETCH_ROWS = 4000

_OUTCOME_INCLUDE = {"strategy_win", "strategy_loss", "timeout_exit"}

_state_lock = threading.Lock()
_state: Dict[str, Any] = {}


def _as_float(raw: Any, default: float = 0.0) -> float:
    try:
        return float(raw)
    except Exception:
        return float(default)


def _as_int(raw: Any, default: int = 0) -> int:
    try:
        return int(raw)
    except Exception:
        return int(default)


def _as_bool(raw: Any, default: bool = False) -> bool:
    if raw is None:
        return bool(default)
    txt = str(raw).strip().lower()
    if txt in {"1", "true", "yes", "y", "on"}:
        return True
    if txt in {"0", "false", "no", "n", "off"}:
        return False
    return bool(default)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(raw: Any) -> Optional[datetime]:
    if not raw:
        return None
    try:
        txt = str(raw)
        if txt.endswith("Z"):
            txt = txt[:-1] + "+00:00"
        dt = datetime.fromisoformat(txt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _read_runtime_cfg() -> Dict[str, Any]:
    return {
        "enabled": _as_bool(os.getenv("CONF_ADAPT_ENABLED", "true"), True),
        "min_support": max(1, _as_int(os.getenv("CONF_ADAPT_MIN_SUPPORT", "30"), 30)),
        "lookback_days": max(1, _as_int(os.getenv("CONF_ADAPT_LOOKBACK_DAYS", "14"), 14)),
        "emergency_max_penalty": max(0, _as_int(os.getenv("CONF_ADAPT_EMERGENCY_MAX_PENALTY", "2"), 2)),
        "emergency_min_risk_scale": _clamp(
            _as_float(os.getenv("CONF_ADAPT_EMERGENCY_MIN_RISK_SCALE", "0.85"), 0.85),
            0.0,
            1.0,
        ),
    }


def _empty_mode_state(mode: str) -> Dict[str, Any]:
    return {
        "mode": mode,
        "sample_size": 0,
        "win_rate_mode": 0.0,
        "timeout_rate_mode": 0.0,
        "median_abs_loss_mode": 1.0,
        "bucket_count": 0,
        "buckets": {},
        "top_bucket": None,
        "worst_bucket": None,
        "active_adaptations": [],
        "source_rows": 0,
        "reason": "bootstrap",
    }


def default_confidence_adaptation_state() -> Dict[str, Any]:
    cfg = _read_runtime_cfg()
    return {
        "enabled": bool(cfg["enabled"]),
        "lookback_days": int(cfg["lookback_days"]),
        "min_support": int(cfg["min_support"]),
        "emergency_max_penalty": int(cfg["emergency_max_penalty"]),
        "emergency_min_risk_scale": float(cfg["emergency_min_risk_scale"]),
        "updated_at": None,
        "decision_reason": "bootstrap",
        "modes": {m: _empty_mode_state(m) for m in _MODES},
    }


def _normalize_trade_type(row: Dict[str, Any]) -> str:
    trade_type = str(row.get("trade_type") or "").strip().lower()
    if trade_type in _MODES:
        return trade_type
    timeframe = str(row.get("timeframe") or "").strip().lower()
    if timeframe == "5m":
        return "scalping"
    return "swing"


def _normalize_confidence_bucket(confidence: Any) -> int:
    conf = _as_float(confidence, _BUCKET_MIN)
    conf = _clamp(conf, _BUCKET_MIN, _BUCKET_MAX)
    bucket = int((int(conf) - _BUCKET_MIN) // _BUCKET_STEP) * _BUCKET_STEP + _BUCKET_MIN
    return int(_clamp(bucket, _BUCKET_MIN, _BUCKET_MAX - (_BUCKET_STEP - 1)))


def _bucket_label(bucket_start: int) -> str:
    return f"{bucket_start}-{bucket_start + (_BUCKET_STEP - 1)}"


def _map_edge_to_adjustments(edge_adj: float) -> Tuple[int, float]:
    e = _as_float(edge_adj, 0.0)
    if e <= -0.35:
        return 6, 0.70
    if e <= -0.20:
        return 4, 0.80
    if e <= -0.05:
        return 2, 0.90
    if e < 0.15:
        return 0, 1.00
    return -1, 1.00


def apply_confidence_risk_brake(playbook_effective_risk_pct: Any, bucket_risk_scale: Any) -> float:
    """
    Apply confidence-derived runtime sizing brake.
    Never increases risk above playbook effective risk.
    """
    base = _clamp(_as_float(playbook_effective_risk_pct, 1.0), 0.25, 10.0)
    scale = _clamp(_as_float(bucket_risk_scale, 1.0), 0.0, 1.0)
    braked = _clamp(base * scale, 0.25, 10.0)
    return min(base, braked)


def _safe_client():
    from app.supabase_repo import _client

    return _client()


def _fetch_closed_rows(limit: int = _MAX_FETCH_ROWS) -> List[Dict[str, Any]]:
    s = _safe_client()
    collected: List[Dict[str, Any]] = []
    page_size = min(1000, max(200, int(limit)))
    page = 0
    while len(collected) < int(limit):
        frm = page * page_size
        to = frm + page_size - 1
        res = (
            s.table("autotrade_trades")
            .select(
                "id,status,close_reason,pnl_usdt,loss_reasoning,confidence,trade_type,timeframe,closed_at"
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
    return collected[: int(limit)]


def _select_mode_sample(rows: List[Dict[str, Any]], now_utc: datetime, lookback_days: int) -> List[Dict[str, Any]]:
    since = now_utc - timedelta(days=max(1, int(lookback_days)))
    sorted_rows = sorted(
        rows,
        key=lambda r: _parse_iso(r.get("closed_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    lookback_rows = [
        r for r in sorted_rows if (_parse_iso(r.get("closed_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= since
    ]
    fallback_rows = sorted_rows[:_FALLBACK_LAST_N]
    if len(lookback_rows) >= len(fallback_rows):
        return lookback_rows
    return fallback_rows


def _build_bucket_metrics(
    sample_rows: List[Dict[str, Any]],
    min_support: int,
) -> Dict[str, Any]:
    if not sample_rows:
        return {
            "sample_size": 0,
            "win_rate_mode": 0.0,
            "timeout_rate_mode": 0.0,
            "median_abs_loss_mode": 1.0,
            "bucket_count": 0,
            "buckets": {},
            "top_bucket": None,
            "worst_bucket": None,
            "active_adaptations": [],
            "reason": "insufficient_sample",
        }

    sample_size = len(sample_rows)
    wins_mode = sum(1 for r in sample_rows if _as_float(r.get("pnl_usdt"), 0.0) > 0.0)
    timeout_mode = sum(1 for r in sample_rows if str(r.get("outcome_class") or "") == "timeout_exit")
    losses_abs = [abs(_as_float(r.get("pnl_usdt"), 0.0)) for r in sample_rows if _as_float(r.get("pnl_usdt"), 0.0) < 0.0]
    median_abs_loss_mode = float(median(losses_abs)) if losses_abs else 1.0
    if median_abs_loss_mode <= 0:
        median_abs_loss_mode = 1.0

    win_rate_mode = wins_mode / sample_size
    timeout_rate_mode = timeout_mode / sample_size

    buckets: Dict[int, List[Dict[str, Any]]] = {}
    for row in sample_rows:
        b = _normalize_confidence_bucket(row.get("confidence"))
        buckets.setdefault(b, []).append(row)

    bucket_state: Dict[str, Any] = {}
    ranked_edges: List[Tuple[float, int]] = []
    active_adaptations: List[Dict[str, Any]] = []

    for b in range(_BUCKET_MIN, _BUCKET_MAX, _BUCKET_STEP):
        b_rows = buckets.get(b, [])
        n = len(b_rows)
        if n > 0:
            avg_pnl = sum(_as_float(r.get("pnl_usdt"), 0.0) for r in b_rows) / n
            wins_bucket = sum(1 for r in b_rows if _as_float(r.get("pnl_usdt"), 0.0) > 0.0)
            timeout_bucket = sum(1 for r in b_rows if str(r.get("outcome_class") or "") == "timeout_exit")
            win_rate_bucket = wins_bucket / n
            timeout_rate_bucket = timeout_bucket / n
            edge_score = (
                0.6 * (avg_pnl / median_abs_loss_mode)
                + 0.3 * (win_rate_bucket - win_rate_mode)
                - 0.1 * (timeout_rate_bucket - timeout_rate_mode)
            )
            shrink = min(1.0, n / 30.0)
            edge_adj = edge_score * shrink
            penalty, risk_scale = _map_edge_to_adjustments(edge_adj)
            reason = "active"
            if n < min_support:
                penalty = 0
                risk_scale = 1.0
                reason = "insufficient_support"
            if penalty != 0 or abs(risk_scale - 1.0) > 1e-9:
                active_adaptations.append(
                    {
                        "bucket": _bucket_label(b),
                        "n": int(n),
                        "edge_adj": round(float(edge_adj), 6),
                        "bucket_penalty": int(penalty),
                        "bucket_risk_scale": round(float(risk_scale), 4),
                    }
                )
            ranked_edges.append((float(edge_adj), b))
        else:
            avg_pnl = 0.0
            win_rate_bucket = 0.0
            timeout_rate_bucket = 0.0
            edge_score = 0.0
            shrink = 0.0
            edge_adj = 0.0
            penalty = 0
            risk_scale = 1.0
            reason = "no_data"

        bucket_state[str(b)] = {
            "bucket": _bucket_label(b),
            "bucket_start": int(b),
            "n": int(n),
            "avg_pnl": round(float(avg_pnl), 6),
            "win_rate_bucket": round(float(win_rate_bucket), 6),
            "timeout_rate_bucket": round(float(timeout_rate_bucket), 6),
            "edge_score": round(float(edge_score), 6),
            "support_shrink": round(float(shrink), 6),
            "edge_adj": round(float(edge_adj), 6),
            "bucket_penalty": int(penalty),
            "bucket_risk_scale": round(float(risk_scale), 4),
            "reason": reason,
        }

    top_bucket = None
    worst_bucket = None
    if ranked_edges:
        ranked_edges.sort(key=lambda x: x[0], reverse=True)
        top_bucket = bucket_state.get(str(ranked_edges[0][1]))
        worst_bucket = bucket_state.get(str(ranked_edges[-1][1]))

    active_adaptations.sort(key=lambda x: x.get("edge_adj", 0.0))

    return {
        "sample_size": int(sample_size),
        "win_rate_mode": round(float(win_rate_mode), 6),
        "timeout_rate_mode": round(float(timeout_rate_mode), 6),
        "median_abs_loss_mode": round(float(median_abs_loss_mode), 6),
        "bucket_count": len([v for v in bucket_state.values() if int(v.get("n", 0) or 0) > 0]),
        "buckets": bucket_state,
        "top_bucket": top_bucket,
        "worst_bucket": worst_bucket,
        "active_adaptations": active_adaptations,
        "reason": "ok",
    }


def build_confidence_adaptation_state(
    closed_rows: List[Dict[str, Any]],
    now_utc: Optional[datetime] = None,
    lookback_days: Optional[int] = None,
    min_support: Optional[int] = None,
    enabled: Optional[bool] = None,
    emergency_max_penalty: Optional[int] = None,
    emergency_min_risk_scale: Optional[float] = None,
) -> Dict[str, Any]:
    cfg = _read_runtime_cfg()
    lookback = max(1, int(lookback_days if lookback_days is not None else cfg["lookback_days"]))
    support = max(1, int(min_support if min_support is not None else cfg["min_support"]))
    is_enabled = bool(cfg["enabled"] if enabled is None else enabled)
    emergency_cap = max(0, int(emergency_max_penalty if emergency_max_penalty is not None else cfg["emergency_max_penalty"]))
    emergency_floor = _clamp(
        float(emergency_min_risk_scale if emergency_min_risk_scale is not None else cfg["emergency_min_risk_scale"]),
        0.0,
        1.0,
    )
    now = now_utc or _utc_now()

    state = default_confidence_adaptation_state()
    state.update(
        {
            "enabled": is_enabled,
            "lookback_days": lookback,
            "min_support": support,
            "emergency_max_penalty": emergency_cap,
            "emergency_min_risk_scale": emergency_floor,
            "updated_at": now.isoformat(),
            "decision_reason": "disabled" if not is_enabled else "refreshed",
        }
    )

    if not is_enabled:
        for mode in _MODES:
            mode_state = _empty_mode_state(mode)
            mode_state["reason"] = "disabled"
            state["modes"][mode] = mode_state
        return state

    prepared: List[Dict[str, Any]] = []
    for raw in closed_rows or []:
        confidence = raw.get("confidence")
        if confidence is None:
            continue
        conf_f = _as_float(confidence, -1.0)
        if conf_f < 0:
            continue
        oc = classify_outcome_class(raw)
        if oc not in _OUTCOME_INCLUDE:
            continue
        row = dict(raw)
        row["confidence"] = conf_f
        row["pnl_usdt"] = _as_float(raw.get("pnl_usdt"), 0.0)
        row["trade_type_norm"] = _normalize_trade_type(raw)
        row["outcome_class"] = oc
        prepared.append(row)

    for mode in _MODES:
        mode_rows = [r for r in prepared if str(r.get("trade_type_norm")) == mode]
        sample_rows = _select_mode_sample(mode_rows, now_utc=now, lookback_days=lookback)
        metrics = _build_bucket_metrics(sample_rows, min_support=support)
        mode_state = _empty_mode_state(mode)
        mode_state.update(metrics)
        mode_state["source_rows"] = len(mode_rows)
        state["modes"][mode] = mode_state

    return state


def refresh_global_confidence_adaptation_state() -> Dict[str, Any]:
    try:
        rows = _fetch_closed_rows(limit=_MAX_FETCH_ROWS)
        nxt = build_confidence_adaptation_state(rows)
    except Exception as e:
        logger.error(f"[ConfAdapt] refresh failed: {e}")
        with _state_lock:
            if not _state:
                _state.update(default_confidence_adaptation_state())
            _state["updated_at"] = _utc_now().isoformat()
            _state["decision_reason"] = "refresh_failed"
        return get_confidence_adaptation_snapshot()

    with _state_lock:
        _state.clear()
        _state.update(nxt)

    for mode in _MODES:
        ms = nxt.get("modes", {}).get(mode, {})
        logger.info(
            "[ConfAdapt] mode=%s sample=%s wr=%.3f timeout=%.3f med_loss=%.4f active=%s top=%s worst=%s",
            mode,
            int(ms.get("sample_size", 0) or 0),
            float(ms.get("win_rate_mode", 0.0) or 0.0),
            float(ms.get("timeout_rate_mode", 0.0) or 0.0),
            float(ms.get("median_abs_loss_mode", 1.0) or 1.0),
            len(ms.get("active_adaptations", []) or []),
            (ms.get("top_bucket") or {}).get("bucket"),
            (ms.get("worst_bucket") or {}).get("bucket"),
        )
    return get_confidence_adaptation_snapshot()


def get_confidence_adaptation_snapshot() -> Dict[str, Any]:
    with _state_lock:
        if not _state:
            _state.update(default_confidence_adaptation_state())
        return copy.deepcopy(_state)


def get_confidence_adaptation(
    mode: str,
    confidence: Any,
    is_emergency: bool = False,
    snapshot: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    st = snapshot or get_confidence_adaptation_snapshot()
    mode_key = str(mode or "swing").strip().lower()
    if mode_key not in _MODES:
        mode_key = "swing"

    bucket_start = _normalize_confidence_bucket(confidence)
    out = {
        "enabled": bool(st.get("enabled", False)),
        "mode": mode_key,
        "is_emergency": bool(is_emergency),
        "confidence": _as_float(confidence, 0.0),
        "bucket": _bucket_label(bucket_start),
        "bucket_start": int(bucket_start),
        "edge_adj": 0.0,
        "bucket_penalty": 0,
        "bucket_risk_scale": 1.0,
        "sample_size": 0,
        "bucket_sample_size": 0,
        "reason": "disabled",
    }

    if not bool(st.get("enabled", False)):
        return out

    mode_state = ((st.get("modes") or {}).get(mode_key) or {})
    bucket_state = ((mode_state.get("buckets") or {}).get(str(bucket_start)) or {})
    out["sample_size"] = int(mode_state.get("sample_size", 0) or 0)
    out["bucket_sample_size"] = int(bucket_state.get("n", 0) or 0)
    out["edge_adj"] = float(bucket_state.get("edge_adj", 0.0) or 0.0)
    out["bucket_penalty"] = int(bucket_state.get("bucket_penalty", 0) or 0)
    out["bucket_risk_scale"] = float(bucket_state.get("bucket_risk_scale", 1.0) or 1.0)
    out["reason"] = str(bucket_state.get("reason") or "ok")

    if bool(is_emergency):
        cap = max(0, int(st.get("emergency_max_penalty", 2) or 2))
        floor = _clamp(float(st.get("emergency_min_risk_scale", 0.85) or 0.85), 0.0, 1.0)
        penalty = int(out["bucket_penalty"])
        if penalty > cap:
            penalty = cap
        risk_scale = max(float(out["bucket_risk_scale"]), floor)
        out["bucket_penalty"] = int(penalty)
        out["bucket_risk_scale"] = float(_clamp(risk_scale, 0.0, 1.0))
        out["reason"] = f"emergency_{out['reason']}"

    return out

