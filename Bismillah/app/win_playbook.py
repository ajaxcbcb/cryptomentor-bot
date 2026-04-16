"""
Global Win Playbook + Runtime Risk Overlay
=========================================

Learns from recent strategy winners/losers, scores incoming signal reasons
against high-lift playbook tags, and applies a runtime-only risk overlay.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.adaptive_confluence import classify_outcome_class, fetch_closed_trades

logger = logging.getLogger(__name__)

TARGET_STRATEGY_SAMPLE = 300
TARGET_LOOKBACK_DAYS = 14

WIN_RATE_FLOOR = 0.75
EXPECTANCY_FLOOR = 0.0

BASE_RISK_MIN_PCT = 0.25
BASE_RISK_MAX_PCT = 5.0
OVERLAY_MAX_PCT = 5.0
EFFECTIVE_RISK_MAX_PCT = 10.0

RAMP_STEP_UP_PCT = 0.25
BRAKE_STEP_DOWN_PCT = 0.50
OVERLAY_UPDATE_MIN_INTERVAL_SECONDS = 120

STRONG_MATCH_THRESHOLD = 0.55
MIN_SAMPLE_FOR_GUARDRAILS = 40

_TAG_RULES: Dict[str, Tuple[str, ...]] = {
    "btc_alignment": ("btc", "bias aligned", "aligned"),
    "smc_bos": ("bos", "hh+hl", "lh+ll", "choch"),
    "ob_fvg": ("order block", " ob", "fvg"),
    "volume_confirmation": ("volume spike", "volume confirmation", "volume"),
    "trend_alignment": ("uptrend", "downtrend", "trend"),
    "ema_alignment": ("ema", "cross"),
    "rsi_context": ("rsi", "overbought", "oversold"),
    "sr_bounce": ("s/r bounce", "support", "resistance", "bounce"),
    "range_context": ("range", "ranging", "sideways"),
    "atr_context": ("atr",),
}
_TAG_ORDER: List[str] = list(_TAG_RULES.keys())

_NOISE_CONTAINS = (
    "error:",
    "insufficient",
    "conflicting timeframes",
    "market moved too fast",
    "retry",
)

_state_lock = threading.Lock()
_state: Dict[str, Any] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _default_state() -> Dict[str, Any]:
    return {
        "updated_at": None,
        "sample_size": 0,
        "wins": 0,
        "losses": 0,
        "rolling_win_rate": 0.0,
        "rolling_expectancy": 0.0,
        "baseline_win_rate": 0.0,
        "active_tags": [],
        "active_tag_names": [],
        "min_support": 0,
        "risk_overlay_pct": 0.0,
        "last_overlay_update_ts": 0.0,
        "last_overlay_action": "bootstrap",
        "guardrails_healthy": False,
        "refresh_error": "",
    }


def _as_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)


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


def _normalize_reason_list(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw if str(x).strip()]
    if isinstance(raw, str):
        txt = raw.strip()
        if not txt:
            return []
        # Existing rows may be CSV/joined strings.
        if "," in txt:
            return [p.strip() for p in txt.split(",") if p.strip()]
        return [txt]
    return [str(raw)]


def _clean_reason_text(reason: str) -> str:
    txt = str(reason or "").strip().lower()
    # Remove obvious emoji/symbol noise while preserving signal text.
    txt = re.sub(r"[^\w\s:+\-/\.]", " ", txt, flags=re.UNICODE)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def _extract_tags_from_reason(reason: str) -> List[str]:
    txt = _clean_reason_text(reason)
    if not txt:
        return []
    if any(noise in txt for noise in _NOISE_CONTAINS):
        return []

    tags: List[str] = []
    for tag in _TAG_ORDER:
        needles = _TAG_RULES[tag]
        if any(n in txt for n in needles):
            tags.append(tag)

    # Fallback compact phrase tag to avoid dropping meaningful non-standard reasons.
    if not tags:
        phrase = re.sub(r"\b\d+(\.\d+)?x?\b", " ", txt)
        phrase = re.sub(r"[^a-z0-9\s]", " ", phrase)
        words = [w for w in phrase.split() if len(w) > 2]
        if words:
            tags.append("reason:" + "_".join(words[:5]))
    return tags


def extract_reason_tags(raw_reasons: Any) -> List[str]:
    tags: List[str] = []
    seen = set()
    for reason in _normalize_reason_list(raw_reasons):
        for tag in _extract_tags_from_reason(reason):
            if tag and tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return tags


def _select_learning_sample(closed_trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now_utc = _utc_now()
    strategy_rows: List[Dict[str, Any]] = []
    for row in closed_trades:
        oc = classify_outcome_class(row)
        if oc not in {"strategy_win", "strategy_loss"}:
            continue
        entry = dict(row)
        entry["outcome_class"] = oc
        strategy_rows.append(entry)

    strategy_rows.sort(
        key=lambda r: _parse_iso(r.get("closed_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    last_n = strategy_rows[:TARGET_STRATEGY_SAMPLE]
    since_lookback = now_utc - timedelta(days=TARGET_LOOKBACK_DAYS)
    lookback_rows = [
        r for r in strategy_rows
        if (_parse_iso(r.get("closed_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= since_lookback
    ]
    return lookback_rows if len(lookback_rows) >= len(last_n) else last_n


def _build_tag_stats(sample: List[Dict[str, Any]], baseline_win_rate: float) -> Tuple[List[Dict[str, Any]], int]:
    sample_size = len(sample)
    if sample_size <= 0:
        return [], 0

    min_support = max(3, min(15, int(sample_size * 0.04)))
    counts: Dict[str, int] = {}
    win_counts: Dict[str, int] = {}

    for row in sample:
        tags = set(extract_reason_tags(row.get("entry_reasons", [])))
        is_win = str(row.get("outcome_class")) == "strategy_win"
        for tag in tags:
            counts[tag] = counts.get(tag, 0) + 1
            if is_win:
                win_counts[tag] = win_counts.get(tag, 0) + 1

    active_tags: List[Dict[str, Any]] = []
    for tag, support in counts.items():
        if support < min_support:
            continue
        wins = win_counts.get(tag, 0)
        win_rate = (wins / support) if support > 0 else 0.0
        lift = win_rate - baseline_win_rate
        if lift <= 0:
            continue
        support_share = support / sample_size
        weight = max(0.0, lift) * (0.5 + support_share)
        active_tags.append({
            "tag": tag,
            "support": int(support),
            "wins": int(wins),
            "win_rate": round(win_rate, 6),
            "lift": round(lift, 6),
            "support_share": round(support_share, 6),
            "weight": round(weight, 6),
        })

    active_tags.sort(
        key=lambda x: (float(x.get("weight", 0)), int(x.get("support", 0)), float(x.get("lift", 0))),
        reverse=True,
    )
    return active_tags, min_support


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _normalize_base_risk_pct(raw: Any) -> float:
    return _clamp(_as_float(raw, default=1.0), BASE_RISK_MIN_PCT, BASE_RISK_MAX_PCT)


def _compute_guardrails(sample_size: int, rolling_win_rate: float, rolling_expectancy: float) -> bool:
    if sample_size < MIN_SAMPLE_FOR_GUARDRAILS:
        return False
    return rolling_win_rate >= WIN_RATE_FLOOR and rolling_expectancy > EXPECTANCY_FLOOR


def _calc_match_score_from_snapshot(reason_tags: Iterable[str], snapshot: Dict[str, Any]) -> Tuple[float, List[str]]:
    tags = set(reason_tags or [])
    active = snapshot.get("active_tags", []) or []
    if not tags or not active:
        return 0.0, []

    weights = {str(t.get("tag")): _as_float(t.get("weight"), 0.0) for t in active}
    total_weight = sum(weights.values())
    if total_weight <= 0:
        return 0.0, []

    matched = [tag for tag in weights.keys() if tag in tags]
    matched_weight = sum(weights.get(tag, 0.0) for tag in matched)
    score = matched_weight / total_weight if total_weight > 0 else 0.0
    return round(score, 3), matched


def is_strong_playbook_match(match_score: float, matched_tags: List[str]) -> bool:
    return bool(matched_tags) and float(match_score) >= STRONG_MATCH_THRESHOLD


def compute_playbook_match_from_reasons(raw_reasons: Any, snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    snap = snapshot or get_win_playbook_snapshot()
    reason_tags = extract_reason_tags(raw_reasons)
    score, matched = _calc_match_score_from_snapshot(reason_tags, snap)
    return {
        "playbook_match_score": score,
        "matched_tags": matched,
        "reason_tags": reason_tags,
        "strong_match": is_strong_playbook_match(score, matched),
    }


def _apply_overlay_step(strong_match: bool, guardrails_healthy: bool, now_ts: float) -> Tuple[float, str]:
    with _state_lock:
        current = _state.get("risk_overlay_pct", 0.0)
        current = _clamp(_as_float(current, 0.0), 0.0, OVERLAY_MAX_PCT)
        last_update_ts = _as_float(_state.get("last_overlay_update_ts"), 0.0)
        if now_ts - last_update_ts < OVERLAY_UPDATE_MIN_INTERVAL_SECONDS:
            return current, "hold_rate_limited"

        action = "hold"
        if strong_match and guardrails_healthy:
            current = _clamp(current + RAMP_STEP_UP_PCT, 0.0, OVERLAY_MAX_PCT)
            action = "ramp_up"
        elif not guardrails_healthy:
            current = _clamp(current - BRAKE_STEP_DOWN_PCT, 0.0, OVERLAY_MAX_PCT)
            action = "brake_down"

        _state["risk_overlay_pct"] = round(current, 3)
        _state["last_overlay_update_ts"] = now_ts
        _state["last_overlay_action"] = action
        return float(_state["risk_overlay_pct"]), action


def refresh_global_win_playbook_state() -> Dict[str, Any]:
    """
    Rebuild global playbook stats from recent strategy trades.
    Keeps `risk_overlay_pct` runtime state intact (runtime-only overlay).
    """
    prev = get_win_playbook_snapshot()
    carry_overlay = _clamp(_as_float(prev.get("risk_overlay_pct"), 0.0), 0.0, OVERLAY_MAX_PCT)
    carry_last_overlay_ts = _as_float(prev.get("last_overlay_update_ts"), 0.0)
    carry_last_action = str(prev.get("last_overlay_action") or "hold")

    try:
        closed_rows = fetch_closed_trades(limit=2500)
        sample = _select_learning_sample(closed_rows)
        wins = [r for r in sample if str(r.get("outcome_class")) == "strategy_win"]
        losses = [r for r in sample if str(r.get("outcome_class")) == "strategy_loss"]
        sample_size = len(sample)
        baseline_win_rate = (len(wins) / sample_size) if sample_size else 0.0
        rolling_expectancy = (
            sum(_as_float(r.get("pnl_usdt"), 0.0) for r in sample) / sample_size
            if sample_size else 0.0
        )

        active_tags, min_support = _build_tag_stats(sample, baseline_win_rate)
        guardrails = _compute_guardrails(
            sample_size=sample_size,
            rolling_win_rate=baseline_win_rate,
            rolling_expectancy=rolling_expectancy,
        )

        next_state = _default_state()
        next_state.update({
            "updated_at": _utc_now().isoformat(),
            "sample_size": sample_size,
            "wins": len(wins),
            "losses": len(losses),
            "rolling_win_rate": round(baseline_win_rate, 6),
            "rolling_expectancy": round(rolling_expectancy, 6),
            "baseline_win_rate": round(baseline_win_rate, 6),
            "active_tags": active_tags,
            "active_tag_names": [str(t.get("tag")) for t in active_tags],
            "min_support": int(min_support),
            "risk_overlay_pct": round(carry_overlay, 3),
            "last_overlay_update_ts": carry_last_overlay_ts,
            "last_overlay_action": carry_last_action,
            "guardrails_healthy": bool(guardrails),
            "refresh_error": "",
        })

        with _state_lock:
            _state.clear()
            _state.update(next_state)

        # Guardrails brake: gently reduce overlay if health degraded.
        if not guardrails:
            _apply_overlay_step(strong_match=False, guardrails_healthy=False, now_ts=time.time())

        return get_win_playbook_snapshot()
    except Exception as e:
        logger.error(f"[WinPlaybook] Refresh failed: {e}")
        with _state_lock:
            if not _state:
                _state.update(_default_state())
            _state["refresh_error"] = str(e)
            _state["updated_at"] = _utc_now().isoformat()
        return get_win_playbook_snapshot()


def get_win_playbook_snapshot() -> Dict[str, Any]:
    with _state_lock:
        if not _state:
            _state.update(_default_state())
        return dict(_state)


def evaluate_signal_risk(base_risk_pct: float, raw_reasons: Any) -> Dict[str, Any]:
    """
    Score signal against active playbook tags and compute runtime risk overlay.
    """
    base_risk = _normalize_base_risk_pct(base_risk_pct)
    snapshot = get_win_playbook_snapshot()
    match = compute_playbook_match_from_reasons(raw_reasons, snapshot=snapshot)
    strong_match = bool(match.get("strong_match"))
    guardrails_healthy = bool(snapshot.get("guardrails_healthy", False))
    overlay, action = _apply_overlay_step(
        strong_match=strong_match,
        guardrails_healthy=guardrails_healthy,
        now_ts=time.time(),
    )
    effective_risk = _clamp(base_risk + overlay, BASE_RISK_MIN_PCT, EFFECTIVE_RISK_MAX_PCT)
    return {
        "base_risk_pct": round(base_risk, 3),
        "risk_overlay_pct": round(overlay, 3),
        "effective_risk_pct": round(effective_risk, 3),
        "playbook_match_score": round(_as_float(match.get("playbook_match_score"), 0.0), 3),
        "playbook_match_tags": list(match.get("matched_tags", [])),
        "playbook_reason_tags": list(match.get("reason_tags", [])),
        "playbook_strong_match": strong_match,
        "guardrails_healthy": guardrails_healthy,
        "overlay_action": action,
        "rolling_win_rate": round(_as_float(snapshot.get("rolling_win_rate"), 0.0), 6),
        "rolling_expectancy": round(_as_float(snapshot.get("rolling_expectancy"), 0.0), 6),
        "sample_size": int(snapshot.get("sample_size", 0) or 0),
    }

