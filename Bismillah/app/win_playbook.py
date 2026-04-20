"""
Global Win Playbook + Runtime Risk Overlay
=========================================

Learns from strategy winners/losers, scores incoming signal reasons against
high-lift playbook patterns, and applies a runtime-only risk overlay.
"""

from __future__ import annotations

import logging
import math
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from app.adaptive_confluence import classify_outcome_class, fetch_closed_trades

logger = logging.getLogger(__name__)

TARGET_STRATEGY_SAMPLE = 300
TARGET_LOOKBACK_DAYS = 14
MAX_PLAYBOOK_FETCH_ROWS = 10000

WIN_RATE_FLOOR = 0.75
EXPECTANCY_R_FLOOR = 0.0

BASE_RISK_MIN_PCT = 0.25
BASE_RISK_MAX_PCT = 5.0
OVERLAY_MAX_PCT = 5.0
EFFECTIVE_RISK_MAX_PCT = 10.0

RAMP_STEP_UP_PCT = 0.25
BRAKE_STEP_DOWN_PCT = 0.50
OVERLAY_UPDATE_MIN_INTERVAL_SECONDS = 120

STRONG_MATCH_THRESHOLD = 0.55
MIN_SAMPLE_FOR_GUARDRAILS = 40
MIN_VALID_R_SAMPLE_FOR_GUARDRAILS = 30
MIN_MODE_SAMPLE_FOR_MODE_MATCH = 40

PAIR_MIN_SUPPORT_ABS = 10
PAIR_MIN_SUPPORT_SHARE = 0.04
HISTORICAL_REASON_TAG_MIN_WINS = 3

MODE_SWING = "swing"
MODE_SCALPING = "scalping"
_MODE_ORDER: Tuple[str, ...] = (MODE_SWING, MODE_SCALPING)

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


def _default_mode_state(mode: str) -> Dict[str, Any]:
    return {
        "mode": mode,
        "sample_size": 0,
        "wins": 0,
        "losses": 0,
        "rolling_win_rate": 0.0,
        "rolling_expectancy_pnl": 0.0,
        "rolling_expectancy_r": 0.0,
        "valid_r_sample_size": 0,
        "active_tags": [],
        "active_tag_names": [],
        "active_pairs": [],
        "active_pair_keys": [],
        "min_support": 0,
        "pair_min_support": 0,
        "match_eligible": False,
    }


def _default_state() -> Dict[str, Any]:
    return {
        "updated_at": None,
        "sample_size": 0,
        "wins": 0,
        "losses": 0,
        "rolling_win_rate": 0.0,
        # Backward-compatible key retained (raw pnl expectancy).
        "rolling_expectancy": 0.0,
        "rolling_expectancy_pnl": 0.0,
        "rolling_expectancy_r": 0.0,
        "valid_r_sample_size": 0,
        "baseline_win_rate": 0.0,
        "active_tags": [],
        "active_tag_names": [],
        "active_pairs": [],
        "active_pair_keys": [],
        "historical_vocab_tags": [],
        "mode_stats": {m: _default_mode_state(m) for m in _MODE_ORDER},
        "min_support": 0,
        "pair_min_support": 0,
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
        if "," in txt:
            return [p.strip() for p in txt.split(",") if p.strip()]
        return [txt]
    return [str(raw)]


def _clean_reason_text(reason: str) -> str:
    txt = str(reason or "").strip().lower()
    txt = re.sub(r"[^\w\s:+\-/\.]", " ", txt, flags=re.UNICODE)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def _fallback_reason_tag(clean_text: str) -> Optional[str]:
    phrase = re.sub(r"\b\d+(\.\d+)?x?\b", " ", clean_text)
    phrase = re.sub(r"[^a-z0-9\s]", " ", phrase)
    words = [w for w in phrase.split() if len(w) > 2]
    if not words:
        return None
    return "reason:" + "_".join(words[:5])


def _extract_tags_from_reason(
    reason: str,
    *,
    fallback_vocab: Optional[Sequence[str]] = None,
    allow_new_fallback: bool = True,
) -> List[str]:
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

    if tags:
        return tags

    fallback = _fallback_reason_tag(txt)
    if not fallback:
        return []
    vocab = set(fallback_vocab or [])
    if allow_new_fallback or fallback in vocab:
        return [fallback]
    return []


def extract_reason_tags(
    raw_reasons: Any,
    *,
    fallback_vocab: Optional[Sequence[str]] = None,
    allow_new_fallback: bool = True,
) -> List[str]:
    tags: List[str] = []
    seen = set()
    for reason in _normalize_reason_list(raw_reasons):
        for tag in _extract_tags_from_reason(
            reason,
            fallback_vocab=fallback_vocab,
            allow_new_fallback=allow_new_fallback,
        ):
            if tag and tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return tags


def _resolve_row_mode(row: Dict[str, Any]) -> str:
    trade_type = str(row.get("trade_type") or "").strip().lower()
    timeframe = str(row.get("timeframe") or "").strip().lower()
    if trade_type in {MODE_SWING, MODE_SCALPING}:
        return trade_type
    if timeframe == "5m":
        return MODE_SCALPING
    return MODE_SWING


def _resolve_mode_hint(
    *,
    trade_type: Optional[str] = None,
    timeframe: Optional[str] = None,
    mode_hint: Optional[str] = None,
) -> str:
    raw_mode = str(mode_hint or trade_type or "").strip().lower()
    tf = str(timeframe or "").strip().lower()
    if raw_mode in {"scalp", MODE_SCALPING}:
        return MODE_SCALPING
    if raw_mode == MODE_SWING:
        return MODE_SWING
    if tf == "5m":
        return MODE_SCALPING
    return MODE_SWING


def _extract_strategy_rows(closed_trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    strategy_rows: List[Dict[str, Any]] = []
    for row in closed_trades:
        oc = classify_outcome_class(row)
        if oc not in {"strategy_win", "strategy_loss"}:
            continue
        entry = dict(row)
        entry["outcome_class"] = oc
        entry["mode"] = _resolve_row_mode(entry)
        strategy_rows.append(entry)
    return strategy_rows


def _select_learning_sample(strategy_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now_utc = _utc_now()
    rows = list(strategy_rows or [])
    rows.sort(
        key=lambda r: _parse_iso(r.get("closed_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    last_n = rows[:TARGET_STRATEGY_SAMPLE]
    since_lookback = now_utc - timedelta(days=TARGET_LOOKBACK_DAYS)
    lookback_rows = [
        r for r in rows
        if (_parse_iso(r.get("closed_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= since_lookback
    ]
    return lookback_rows if len(lookback_rows) >= len(last_n) else last_n


def _resolve_qty_for_r_multiple(row: Dict[str, Any]) -> Optional[float]:
    for key in ("qty", "quantity", "original_quantity"):
        q = _as_float(row.get(key), 0.0)
        if abs(q) > 0:
            return float(abs(q))
    return None


def _realized_r_multiple(row: Dict[str, Any]) -> Optional[float]:
    pnl = _as_float(row.get("pnl_usdt"), 0.0)
    entry = _as_float(row.get("entry_price"), 0.0)
    sl = _as_float(row.get("sl_price"), 0.0)
    qty = _resolve_qty_for_r_multiple(row)
    if entry <= 0 or sl <= 0 or qty is None:
        return None
    risk_usdt = abs(entry - sl) * qty
    if risk_usdt <= 0:
        return None
    return float(pnl / risk_usdt)


def _build_historical_reason_vocabulary(strategy_rows: List[Dict[str, Any]]) -> List[str]:
    reason_tag_wins: Dict[str, int] = {}
    for row in strategy_rows:
        if str(row.get("outcome_class")) != "strategy_win":
            continue
        tags = extract_reason_tags(row.get("entry_reasons", []), allow_new_fallback=True)
        for tag in tags:
            if not str(tag).startswith("reason:"):
                continue
            reason_tag_wins[tag] = reason_tag_wins.get(tag, 0) + 1

    selected = [
        (tag, wins)
        for tag, wins in reason_tag_wins.items()
        if int(wins) >= HISTORICAL_REASON_TAG_MIN_WINS
    ]
    selected.sort(key=lambda x: (int(x[1]), str(x[0])), reverse=True)
    return [str(tag) for tag, _ in selected]


def _calc_single_min_support(sample_size: int) -> int:
    if sample_size <= 0:
        return 0
    return max(3, min(15, int(sample_size * 0.04)))


def _calc_pair_min_support(sample_size: int) -> int:
    if sample_size <= 0:
        return 0
    return max(PAIR_MIN_SUPPORT_ABS, int(math.ceil(sample_size * PAIR_MIN_SUPPORT_SHARE)))


def _build_pair_keys(tags: Sequence[str]) -> List[str]:
    uniq = sorted(set(str(t) for t in tags if str(t).strip()))
    out: List[str] = []
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            out.append(f"{uniq[i]}+{uniq[j]}")
    return out


def _build_tag_stats(
    sample: List[Dict[str, Any]],
    baseline_win_rate: float,
    *,
    fallback_vocab: Sequence[str],
) -> Tuple[List[Dict[str, Any]], int]:
    sample_size = len(sample)
    if sample_size <= 0:
        return [], 0

    min_support = _calc_single_min_support(sample_size)
    counts: Dict[str, int] = {}
    win_counts: Dict[str, int] = {}

    for row in sample:
        tags = set(
            extract_reason_tags(
                row.get("entry_reasons", []),
                fallback_vocab=fallback_vocab,
                allow_new_fallback=False,
            )
        )
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
            "tag": str(tag),
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


def _build_pair_stats(
    sample: List[Dict[str, Any]],
    baseline_win_rate: float,
    *,
    fallback_vocab: Sequence[str],
) -> Tuple[List[Dict[str, Any]], int]:
    sample_size = len(sample)
    if sample_size <= 0:
        return [], 0

    min_support = _calc_pair_min_support(sample_size)
    pair_counts: Dict[str, int] = {}
    pair_win_counts: Dict[str, int] = {}

    for row in sample:
        tags = extract_reason_tags(
            row.get("entry_reasons", []),
            fallback_vocab=fallback_vocab,
            allow_new_fallback=False,
        )
        pairs = set(_build_pair_keys(tags))
        is_win = str(row.get("outcome_class")) == "strategy_win"
        for pair_key in pairs:
            pair_counts[pair_key] = pair_counts.get(pair_key, 0) + 1
            if is_win:
                pair_win_counts[pair_key] = pair_win_counts.get(pair_key, 0) + 1

    active_pairs: List[Dict[str, Any]] = []
    for pair_key, support in pair_counts.items():
        if support < min_support:
            continue
        wins = pair_win_counts.get(pair_key, 0)
        win_rate = (wins / support) if support > 0 else 0.0
        lift = win_rate - baseline_win_rate
        if lift <= 0:
            continue
        support_share = support / sample_size
        # Slightly favor paired confluence patterns versus singles when lift is positive.
        weight = max(0.0, lift) * (0.6 + support_share)
        tags = pair_key.split("+")
        active_pairs.append({
            "key": pair_key,
            "pair": tags,
            "support": int(support),
            "wins": int(wins),
            "win_rate": round(win_rate, 6),
            "lift": round(lift, 6),
            "support_share": round(support_share, 6),
            "weight": round(weight, 6),
        })

    active_pairs.sort(
        key=lambda x: (float(x.get("weight", 0)), int(x.get("support", 0)), float(x.get("lift", 0))),
        reverse=True,
    )
    return active_pairs, min_support


def _build_mode_stats(
    sample: List[Dict[str, Any]],
    *,
    fallback_vocab: Sequence[str],
) -> Dict[str, Any]:
    out: Dict[str, Any] = {m: _default_mode_state(m) for m in _MODE_ORDER}
    for mode in _MODE_ORDER:
        mode_rows = [r for r in sample if _resolve_row_mode(r) == mode]
        sample_size = len(mode_rows)
        wins = [r for r in mode_rows if str(r.get("outcome_class")) == "strategy_win"]
        losses = [r for r in mode_rows if str(r.get("outcome_class")) == "strategy_loss"]
        win_rate = (len(wins) / sample_size) if sample_size else 0.0
        expectancy_pnl = (
            sum(_as_float(r.get("pnl_usdt"), 0.0) for r in mode_rows) / sample_size
            if sample_size
            else 0.0
        )
        r_values = [v for v in (_realized_r_multiple(r) for r in mode_rows) if v is not None]
        expectancy_r = (sum(r_values) / len(r_values)) if r_values else 0.0

        active_tags, min_support = _build_tag_stats(
            mode_rows,
            win_rate,
            fallback_vocab=fallback_vocab,
        )
        active_pairs, pair_min_support = _build_pair_stats(
            mode_rows,
            win_rate,
            fallback_vocab=fallback_vocab,
        )
        match_eligible = (
            sample_size >= MIN_MODE_SAMPLE_FOR_MODE_MATCH
            and (bool(active_tags) or bool(active_pairs))
        )

        out[mode] = {
            "mode": mode,
            "sample_size": int(sample_size),
            "wins": int(len(wins)),
            "losses": int(len(losses)),
            "rolling_win_rate": round(win_rate, 6),
            "rolling_expectancy_pnl": round(expectancy_pnl, 6),
            "rolling_expectancy_r": round(expectancy_r, 6),
            "valid_r_sample_size": int(len(r_values)),
            "active_tags": active_tags,
            "active_tag_names": [str(t.get("tag")) for t in active_tags],
            "active_pairs": active_pairs,
            "active_pair_keys": [str(p.get("key")) for p in active_pairs],
            "min_support": int(min_support),
            "pair_min_support": int(pair_min_support),
            "match_eligible": bool(match_eligible),
        }
    return out


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _normalize_base_risk_pct(raw: Any) -> float:
    return _clamp(_as_float(raw, default=1.0), BASE_RISK_MIN_PCT, BASE_RISK_MAX_PCT)


def _compute_guardrails(
    sample_size: int,
    rolling_win_rate: float,
    rolling_expectancy_r: float,
    valid_r_sample_size: int,
) -> bool:
    if sample_size < MIN_SAMPLE_FOR_GUARDRAILS:
        return False
    if valid_r_sample_size < MIN_VALID_R_SAMPLE_FOR_GUARDRAILS:
        return False
    return rolling_win_rate >= WIN_RATE_FLOOR and rolling_expectancy_r > EXPECTANCY_R_FLOOR


def _score_from_block(
    reason_tags: Iterable[str],
    reason_pair_keys: Iterable[str],
    *,
    active_tags: Sequence[Dict[str, Any]],
    active_pairs: Sequence[Dict[str, Any]],
) -> Tuple[float, List[str], List[str]]:
    tags = set(str(t) for t in (reason_tags or []))
    pairs = set(str(p) for p in (reason_pair_keys or []))
    if not tags and not pairs:
        return 0.0, [], []

    tag_weights = {
        str(t.get("tag")): _as_float(t.get("weight"), 0.0)
        for t in (active_tags or [])
    }
    pair_weights = {
        str(p.get("key")): _as_float(p.get("weight"), 0.0)
        for p in (active_pairs or [])
    }
    total_weight = sum(tag_weights.values()) + sum(pair_weights.values())
    if total_weight <= 0:
        return 0.0, [], []

    matched_tags = [tag for tag in tag_weights.keys() if tag in tags]
    matched_pairs = [pair_key for pair_key in pair_weights.keys() if pair_key in pairs]
    matched_weight = (
        sum(tag_weights.get(tag, 0.0) for tag in matched_tags)
        + sum(pair_weights.get(pair_key, 0.0) for pair_key in matched_pairs)
    )
    score = matched_weight / total_weight if total_weight > 0 else 0.0
    return round(score, 3), matched_tags, matched_pairs


def _select_match_patterns(
    snapshot: Dict[str, Any],
    *,
    mode: str,
) -> Tuple[str, Sequence[Dict[str, Any]], Sequence[Dict[str, Any]]]:
    mode_stats = snapshot.get("mode_stats", {}) or {}
    mode_block = mode_stats.get(mode) if isinstance(mode_stats, dict) else None
    if isinstance(mode_block, dict):
        if bool(mode_block.get("match_eligible")):
            return (
                mode,
                list(mode_block.get("active_tags", []) or []),
                list(mode_block.get("active_pairs", []) or []),
            )
    return (
        "global",
        list(snapshot.get("active_tags", []) or []),
        list(snapshot.get("active_pairs", []) or []),
    )


def is_strong_playbook_match(
    match_score: float,
    matched_tags: List[str],
    matched_pairs: Optional[List[str]] = None,
) -> bool:
    return bool(matched_tags or (matched_pairs or [])) and float(match_score) >= STRONG_MATCH_THRESHOLD


def compute_playbook_match_from_reasons(
    raw_reasons: Any,
    snapshot: Optional[Dict[str, Any]] = None,
    trade_type: Optional[str] = None,
    timeframe: Optional[str] = None,
    mode_hint: Optional[str] = None,
) -> Dict[str, Any]:
    snap = snapshot or get_win_playbook_snapshot()
    fallback_vocab = list(snap.get("historical_vocab_tags", []) or [])
    reason_tags = extract_reason_tags(
        raw_reasons,
        fallback_vocab=fallback_vocab,
        allow_new_fallback=False,
    )
    reason_pairs = _build_pair_keys(reason_tags)
    mode = _resolve_mode_hint(
        trade_type=trade_type,
        timeframe=timeframe,
        mode_hint=mode_hint,
    )
    score_source, source_tags, source_pairs = _select_match_patterns(snap, mode=mode)
    score, matched_single_tags, matched_pair_keys = _score_from_block(
        reason_tags,
        reason_pairs,
        active_tags=source_tags,
        active_pairs=source_pairs,
    )
    matched_display = list(matched_single_tags) + [f"pair:{k}" for k in matched_pair_keys]
    return {
        "playbook_match_score": score,
        "matched_tags": matched_display,
        "matched_single_tags": list(matched_single_tags),
        "matched_pair_tags": list(matched_pair_keys),
        "reason_tags": list(reason_tags),
        "reason_pair_tags": list(reason_pairs),
        "match_mode": mode,
        "score_source": score_source,
        "strong_match": is_strong_playbook_match(score, matched_display, matched_pair_keys),
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
    Rebuild global playbook stats from strategy trades.

    Learning model:
    - Historical winner vocabulary for fallback `reason:*` tags.
    - Live weights from rolling sample (last 300 or 14d, whichever is larger).
    """
    prev = get_win_playbook_snapshot()
    carry_overlay = _clamp(_as_float(prev.get("risk_overlay_pct"), 0.0), 0.0, OVERLAY_MAX_PCT)
    carry_last_overlay_ts = _as_float(prev.get("last_overlay_update_ts"), 0.0)
    carry_last_action = str(prev.get("last_overlay_action") or "hold")

    try:
        closed_rows = fetch_closed_trades(limit=MAX_PLAYBOOK_FETCH_ROWS)
        strategy_rows = _extract_strategy_rows(closed_rows)
        sample = _select_learning_sample(strategy_rows)
        wins = [r for r in sample if str(r.get("outcome_class")) == "strategy_win"]
        losses = [r for r in sample if str(r.get("outcome_class")) == "strategy_loss"]
        sample_size = len(sample)
        baseline_win_rate = (len(wins) / sample_size) if sample_size else 0.0

        rolling_expectancy_pnl = (
            sum(_as_float(r.get("pnl_usdt"), 0.0) for r in sample) / sample_size
            if sample_size
            else 0.0
        )
        r_values = [v for v in (_realized_r_multiple(r) for r in sample) if v is not None]
        rolling_expectancy_r = (sum(r_values) / len(r_values)) if r_values else 0.0
        valid_r_sample_size = len(r_values)

        historical_vocab_tags = _build_historical_reason_vocabulary(strategy_rows)
        active_tags, min_support = _build_tag_stats(
            sample,
            baseline_win_rate,
            fallback_vocab=historical_vocab_tags,
        )
        active_pairs, pair_min_support = _build_pair_stats(
            sample,
            baseline_win_rate,
            fallback_vocab=historical_vocab_tags,
        )
        mode_stats = _build_mode_stats(
            sample,
            fallback_vocab=historical_vocab_tags,
        )
        guardrails = _compute_guardrails(
            sample_size=sample_size,
            rolling_win_rate=baseline_win_rate,
            rolling_expectancy_r=rolling_expectancy_r,
            valid_r_sample_size=valid_r_sample_size,
        )

        next_state = _default_state()
        next_state.update({
            "updated_at": _utc_now().isoformat(),
            "sample_size": sample_size,
            "wins": len(wins),
            "losses": len(losses),
            "rolling_win_rate": round(baseline_win_rate, 6),
            "rolling_expectancy": round(rolling_expectancy_pnl, 6),
            "rolling_expectancy_pnl": round(rolling_expectancy_pnl, 6),
            "rolling_expectancy_r": round(rolling_expectancy_r, 6),
            "valid_r_sample_size": int(valid_r_sample_size),
            "baseline_win_rate": round(baseline_win_rate, 6),
            "active_tags": active_tags,
            "active_tag_names": [str(t.get("tag")) for t in active_tags],
            "active_pairs": active_pairs,
            "active_pair_keys": [str(p.get("key")) for p in active_pairs],
            "historical_vocab_tags": list(historical_vocab_tags),
            "mode_stats": mode_stats,
            "min_support": int(min_support),
            "pair_min_support": int(pair_min_support),
            "risk_overlay_pct": round(carry_overlay, 3),
            "last_overlay_update_ts": carry_last_overlay_ts,
            "last_overlay_action": carry_last_action,
            "guardrails_healthy": bool(guardrails),
            "refresh_error": "",
        })

        with _state_lock:
            _state.clear()
            _state.update(next_state)

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


def evaluate_signal_risk(
    base_risk_pct: float,
    raw_reasons: Any,
    trade_type: Optional[str] = None,
    timeframe: Optional[str] = None,
    mode_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Score signal against active playbook patterns and compute runtime risk overlay.
    """
    base_risk = _normalize_base_risk_pct(base_risk_pct)
    snapshot = get_win_playbook_snapshot()
    match = compute_playbook_match_from_reasons(
        raw_reasons,
        snapshot=snapshot,
        trade_type=trade_type,
        timeframe=timeframe,
        mode_hint=mode_hint,
    )
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
        "playbook_match_pairs": list(match.get("matched_pair_tags", [])),
        "playbook_reason_tags": list(match.get("reason_tags", [])),
        "playbook_reason_pair_tags": list(match.get("reason_pair_tags", [])),
        "playbook_strong_match": strong_match,
        "playbook_match_mode": str(match.get("match_mode") or "swing"),
        "playbook_score_source": str(match.get("score_source") or "global"),
        "guardrails_healthy": guardrails_healthy,
        "overlay_action": action,
        "rolling_win_rate": round(_as_float(snapshot.get("rolling_win_rate"), 0.0), 6),
        "rolling_expectancy": round(_as_float(snapshot.get("rolling_expectancy"), 0.0), 6),
        "rolling_expectancy_pnl": round(_as_float(snapshot.get("rolling_expectancy_pnl"), 0.0), 6),
        "rolling_expectancy_r": round(_as_float(snapshot.get("rolling_expectancy_r"), 0.0), 6),
        "valid_r_sample_size": int(snapshot.get("valid_r_sample_size", 0) or 0),
        "sample_size": int(snapshot.get("sample_size", 0) or 0),
    }
