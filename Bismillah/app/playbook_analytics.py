"""
Playbook Analyzer V2 (analytics-first, read-only)
=================================================

Builds explainable learning snapshots from recent closed strategy trades.
This module does not mutate runtime risk or signal selection behavior.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

TARGET_STRATEGY_SAMPLE = 300
TARGET_LOOKBACK_DAYS = 14
STRONG_MATCH_THRESHOLD = 0.55

try:
    # Keep learning-window and threshold aligned with runtime playbook when available.
    from app.win_playbook import (  # type: ignore
        TARGET_STRATEGY_SAMPLE as _RUNTIME_TARGET_SAMPLE,
        TARGET_LOOKBACK_DAYS as _RUNTIME_LOOKBACK_DAYS,
        STRONG_MATCH_THRESHOLD as _RUNTIME_STRONG_MATCH_THRESHOLD,
        extract_reason_tags as _runtime_extract_reason_tags,
    )

    TARGET_STRATEGY_SAMPLE = int(_RUNTIME_TARGET_SAMPLE)
    TARGET_LOOKBACK_DAYS = int(_RUNTIME_LOOKBACK_DAYS)
    STRONG_MATCH_THRESHOLD = float(_RUNTIME_STRONG_MATCH_THRESHOLD)
except Exception:
    _runtime_extract_reason_tags = None

try:
    from app.adaptive_confluence import classify_outcome_class as _runtime_classify_outcome_class  # type: ignore
except Exception:
    _runtime_classify_outcome_class = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
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


def _fallback_extract_reason_tags(raw_reasons: Any) -> List[str]:
    tags: List[str] = []
    seen = set()
    for reason in _normalize_reason_list(raw_reasons):
        txt = str(reason or "").strip().lower()
        if not txt:
            continue
        candidates = []
        if "btc" in txt:
            candidates.append("btc_alignment")
        if "ob" in txt or "order block" in txt:
            candidates.append("ob_fvg")
        if "fvg" in txt:
            candidates.append("ob_fvg")
        if "volume" in txt:
            candidates.append("volume_confirmation")
        if "trend" in txt:
            candidates.append("trend_alignment")
        if "ema" in txt:
            candidates.append("ema_alignment")
        if "rsi" in txt:
            candidates.append("rsi_context")
        if "support" in txt or "resistance" in txt or "bounce" in txt:
            candidates.append("sr_bounce")
        if "sideways" in txt or "range" in txt or "ranging" in txt:
            candidates.append("range_context")
        if "atr" in txt:
            candidates.append("atr_context")
        if not candidates:
            compact = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in txt)
            compact = "_".join([w for w in compact.split() if len(w) > 2][:5])
            if compact:
                candidates.append(f"reason:{compact}")
        for tag in candidates:
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return tags


def _extract_reason_tags(raw_reasons: Any) -> List[str]:
    if _runtime_extract_reason_tags is not None:
        try:
            return list(_runtime_extract_reason_tags(raw_reasons, allow_new_fallback=True) or [])
        except TypeError:
            try:
                return list(_runtime_extract_reason_tags(raw_reasons) or [])
            except Exception:
                return _fallback_extract_reason_tags(raw_reasons)
        except Exception:
            return _fallback_extract_reason_tags(raw_reasons)
    return _fallback_extract_reason_tags(raw_reasons)


def _fallback_classify_outcome_class(trade: Dict[str, Any]) -> str:
    status = str(trade.get("status") or "").strip().lower()
    close_reason = str(trade.get("close_reason") or "").strip().lower()
    reason_hint = close_reason or status
    pnl = _as_float(trade.get("pnl_usdt"), 0.0)
    loss_reasoning = str(trade.get("loss_reasoning") or "")

    timeout_statuses = {"max_hold_time_exceeded", "sideways_max_hold_exceeded"}
    ops_statuses = {
        "stale_startup_reconcile",
        "legacy_stale_reconcile_backfill",
        "stale_reconcile",
    }
    if reason_hint in timeout_statuses:
        return "timeout_exit"
    if reason_hint in ops_statuses or "reconciled from exchange" in loss_reasoning.lower():
        return "ops_reconcile"
    if reason_hint in {"closed_sl", "sl"}:
        return "strategy_loss"
    if reason_hint.startswith("closed_tp") or reason_hint in {"closed_flip", "closed_manual"}:
        return "strategy_win" if pnl >= 0 else "strategy_loss"
    if status.startswith("closed"):
        return "strategy_loss" if pnl < 0 else "strategy_win"
    return "unknown"


def _classify_outcome_class(trade: Dict[str, Any]) -> str:
    if _runtime_classify_outcome_class is not None:
        try:
            return str(_runtime_classify_outcome_class(trade))
        except Exception:
            return _fallback_classify_outcome_class(trade)
    return _fallback_classify_outcome_class(trade)


def _normalize_symbol(raw: Any) -> str:
    sym = str(raw or "").strip().upper().replace("/", "")
    return sym


def _resolve_trade_type(trade: Dict[str, Any]) -> str:
    trade_type = str(trade.get("trade_type") or "").strip().lower()
    timeframe = str(trade.get("timeframe") or "").strip().lower()
    if trade_type in {"scalp", "scalping"}:
        return "scalping"
    if trade_type == "swing":
        return "swing"
    if timeframe == "5m":
        return "scalping"
    return "swing"


def _resolve_qty_for_r_multiple(trade: Dict[str, Any]) -> Optional[float]:
    for key in ("qty", "quantity", "original_quantity"):
        qty = _as_float(trade.get(key), 0.0)
        if abs(qty) > 0:
            return abs(qty)
    return None


def _realized_r_multiple(trade: Dict[str, Any]) -> Optional[float]:
    pnl = _as_float(trade.get("pnl_usdt"), 0.0)
    entry = _as_float(trade.get("entry_price"), 0.0)
    sl = _as_float(trade.get("sl_price"), 0.0)
    qty = _resolve_qty_for_r_multiple(trade)
    if entry <= 0 or sl <= 0 or qty is None:
        return None
    risk_usdt = abs(entry - sl) * qty
    if risk_usdt <= 0:
        return None
    return float(pnl / risk_usdt)


def _confidence_band(raw_conf: Any) -> str:
    conf = int(_as_float(raw_conf, 0.0))
    if conf < 60:
        return "0-59"
    if conf < 70:
        return "60-69"
    if conf < 80:
        return "70-79"
    if conf < 90:
        return "80-89"
    return "90-100"


def _select_strategy_learning_sample(
    strategy_rows: Sequence[Dict[str, Any]],
    *,
    now_utc: datetime,
) -> List[Dict[str, Any]]:
    rows = list(strategy_rows or [])
    rows.sort(
        key=lambda r: _parse_iso(r.get("closed_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    last_n = rows[:TARGET_STRATEGY_SAMPLE]
    since_lookback = now_utc - timedelta(days=TARGET_LOOKBACK_DAYS)
    lookback_rows = [
        r
        for r in rows
        if (_parse_iso(r.get("closed_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= since_lookback
    ]
    return lookback_rows if len(lookback_rows) >= len(last_n) else last_n


def _default_cluster_item() -> Dict[str, Any]:
    return {
        "label": "",
        "cluster_type": "",
        "trade_type": "swing",
        "tags_counter": Counter(),
        "symbols_counter": Counter(),
        "support": 0,
        "wins": 0,
        "sum_pnl": 0.0,
        "r_values": [],
    }


def _register_cluster_trade(
    acc: Dict[str, Any],
    *,
    label: str,
    cluster_type: str,
    trade_type: str,
    symbol: str,
    tags: Sequence[str],
    pnl: float,
    realized_r: Optional[float],
    is_win: bool,
) -> None:
    acc["label"] = label
    acc["cluster_type"] = cluster_type
    acc["trade_type"] = trade_type
    acc["support"] += 1
    acc["sum_pnl"] += float(pnl)
    if is_win:
        acc["wins"] += 1
    if symbol:
        acc["symbols_counter"][symbol] += 1
    for tag in tags:
        acc["tags_counter"][tag] += 1
    if realized_r is not None:
        acc["r_values"].append(float(realized_r))


def _finalize_cluster_item(
    row: Dict[str, Any],
    *,
    baseline_win_rate: float,
    min_support: int,
) -> Dict[str, Any]:
    support = int(row.get("support", 0) or 0)
    wins = int(row.get("wins", 0) or 0)
    win_rate = (wins / support) if support > 0 else 0.0
    expectancy = (float(row.get("sum_pnl", 0.0) or 0.0) / support) if support > 0 else 0.0
    r_values = list(row.get("r_values") or [])
    median_r = float(median(r_values)) if r_values else 0.0
    lift = float(win_rate - baseline_win_rate)
    symbols = [str(k) for k, _ in Counter(row.get("symbols_counter") or {}).most_common(5)]
    tags = [str(k) for k, _ in Counter(row.get("tags_counter") or {}).most_common(5)]
    bucket = "watch"
    if support >= int(min_support):
        if expectancy > 0 and lift > 0:
            bucket = "promote"
        elif expectancy < 0 and lift < 0:
            bucket = "avoid"

    return {
        "label": str(row.get("label") or "-"),
        "cluster_type": str(row.get("cluster_type") or ""),
        "support": support,
        "win_rate": round(win_rate, 6),
        "expectancy_usdt": round(expectancy, 6),
        "median_r": round(median_r, 6),
        "trade_type": str(row.get("trade_type") or "swing"),
        "symbols": symbols,
        "tags": tags,
        "win_rate_lift": round(lift, 6),
        "bucket": bucket,
    }


def _sort_promote(item: Dict[str, Any]) -> Tuple[float, float, int]:
    return (
        float(item.get("expectancy_usdt", 0.0)),
        float(item.get("win_rate_lift", 0.0)),
        int(item.get("support", 0)),
    )


def _sort_avoid(item: Dict[str, Any]) -> Tuple[float, float, int]:
    return (
        -float(item.get("expectancy_usdt", 0.0)),
        -float(item.get("win_rate_lift", 0.0)),
        int(item.get("support", 0)),
    )


def _sort_watch(item: Dict[str, Any]) -> Tuple[int, float]:
    return (
        int(item.get("support", 0)),
        abs(float(item.get("expectancy_usdt", 0.0))),
    )


def _default_empty_response(*, now_utc: datetime) -> Dict[str, Any]:
    return {
        "window": {
            "policy": f"max(last_{TARGET_STRATEGY_SAMPLE}, last_{TARGET_LOOKBACK_DAYS}d)",
            "target_strategy_sample": int(TARGET_STRATEGY_SAMPLE),
            "target_lookback_days": int(TARGET_LOOKBACK_DAYS),
            "sample_start": None,
            "sample_end": None,
            "strategy_rows_available": 0,
        },
        "sample_size": 0,
        "promote": [],
        "watch": [],
        "avoid": [],
        "coverage": {
            "wins_count": 0,
            "wins_with_reasoning_count": 0,
            "wins_with_reasoning_pct": 100.0,
            "closed_with_usable_tags_count": 0,
            "closed_with_usable_tags_pct": 0.0,
            "weak_or_missing_playbook_match_wins_count": 0,
            "weak_or_missing_playbook_match_wins_pct": 100.0,
            "strong_match_threshold": float(STRONG_MATCH_THRESHOLD),
        },
        "generated_at": now_utc.isoformat(),
        "sparse_data": True,
    }


def build_playbook_analysis(
    closed_trades: Sequence[Dict[str, Any]],
    *,
    now_utc: Optional[datetime] = None,
    max_bucket_items: int = 12,
) -> Dict[str, Any]:
    """
    Build Playbook Analyzer V2 output from closed trades.
    The function is analytics-only and never mutates runtime/system state.
    """
    ref_now = now_utc or _utc_now()
    if ref_now.tzinfo is None:
        ref_now = ref_now.replace(tzinfo=timezone.utc)

    out_empty = _default_empty_response(now_utc=ref_now)
    if not closed_trades:
        return out_empty

    strategy_rows: List[Dict[str, Any]] = []
    for row in closed_trades:
        oc = _classify_outcome_class(dict(row))
        if oc not in {"strategy_win", "strategy_loss"}:
            continue
        entry = dict(row)
        entry["outcome_class"] = oc
        entry["trade_type_resolved"] = _resolve_trade_type(entry)
        strategy_rows.append(entry)

    if not strategy_rows:
        return out_empty

    sample = _select_strategy_learning_sample(strategy_rows, now_utc=ref_now)
    sample_size = len(sample)
    if sample_size <= 0:
        return out_empty

    min_support = max(3, min(15, int(sample_size * 0.04)))
    sparse_data = sample_size < max(20, min_support * 2)

    wins = [r for r in sample if str(r.get("outcome_class")) == "strategy_win"]
    baseline_win_rate = (len(wins) / sample_size) if sample_size else 0.0
    sample_times = [_parse_iso(r.get("closed_at")) for r in sample]
    sample_times = [d for d in sample_times if d is not None]

    coverage_wins_with_reason = sum(1 for r in wins if str(r.get("win_reasoning") or "").strip())
    coverage_usable_tags = 0
    coverage_weak_or_missing = 0
    for row in sample:
        tags = _extract_reason_tags(row.get("entry_reasons", []))
        if tags:
            coverage_usable_tags += 1
        if str(row.get("outcome_class")) == "strategy_win":
            score = _as_float(row.get("playbook_match_score"), 0.0)
            if score < STRONG_MATCH_THRESHOLD:
                coverage_weak_or_missing += 1

    clusters: Dict[str, Dict[str, Any]] = {}
    for row in sample:
        trade_type = str(row.get("trade_type_resolved") or "swing")
        symbol = _normalize_symbol(row.get("symbol"))
        tags = _extract_reason_tags(row.get("entry_reasons", []))
        pnl = _as_float(row.get("pnl_usdt"), 0.0)
        is_win = str(row.get("outcome_class")) == "strategy_win"
        realized_r = _realized_r_multiple(row)
        conf_band = _confidence_band(row.get("confidence"))

        for tag in set(tags):
            key = f"tag|{trade_type}|{tag}"
            acc = clusters.setdefault(key, _default_cluster_item())
            _register_cluster_trade(
                acc,
                label=f"{trade_type} • tag:{tag}",
                cluster_type="tag",
                trade_type=trade_type,
                symbol=symbol,
                tags=[tag],
                pnl=pnl,
                realized_r=realized_r,
                is_win=is_win,
            )

        key_symbol = f"symbol|{trade_type}|{symbol or 'UNKNOWN'}"
        acc_symbol = clusters.setdefault(key_symbol, _default_cluster_item())
        _register_cluster_trade(
            acc_symbol,
            label=f"{trade_type} • symbol:{symbol or 'UNKNOWN'}",
            cluster_type="symbol_mode",
            trade_type=trade_type,
            symbol=symbol,
            tags=tags,
            pnl=pnl,
            realized_r=realized_r,
            is_win=is_win,
        )

        key_conf = f"conf|{trade_type}|{conf_band}"
        acc_conf = clusters.setdefault(key_conf, _default_cluster_item())
        _register_cluster_trade(
            acc_conf,
            label=f"{trade_type} • confidence:{conf_band}",
            cluster_type="confidence_band",
            trade_type=trade_type,
            symbol=symbol,
            tags=tags,
            pnl=pnl,
            realized_r=realized_r,
            is_win=is_win,
        )

    finalized = [
        _finalize_cluster_item(item, baseline_win_rate=baseline_win_rate, min_support=min_support)
        for item in clusters.values()
        if int(item.get("support", 0) or 0) >= 2
    ]

    promote = sorted([c for c in finalized if c.get("bucket") == "promote"], key=_sort_promote, reverse=True)
    avoid = sorted([c for c in finalized if c.get("bucket") == "avoid"], key=_sort_avoid, reverse=True)
    watch = sorted([c for c in finalized if c.get("bucket") == "watch"], key=_sort_watch, reverse=True)

    max_items = max(1, int(max_bucket_items or 12))

    wins_count = len(wins)
    coverage = {
        "wins_count": wins_count,
        "wins_with_reasoning_count": int(coverage_wins_with_reason),
        "wins_with_reasoning_pct": round(
            (coverage_wins_with_reason / wins_count * 100.0) if wins_count else 100.0,
            2,
        ),
        "closed_with_usable_tags_count": int(coverage_usable_tags),
        "closed_with_usable_tags_pct": round((coverage_usable_tags / sample_size * 100.0), 2),
        "weak_or_missing_playbook_match_wins_count": int(coverage_weak_or_missing),
        "weak_or_missing_playbook_match_wins_pct": round(
            (coverage_weak_or_missing / wins_count * 100.0) if wins_count else 100.0,
            2,
        ),
        "strong_match_threshold": float(STRONG_MATCH_THRESHOLD),
    }

    return {
        "window": {
            "policy": f"max(last_{TARGET_STRATEGY_SAMPLE}, last_{TARGET_LOOKBACK_DAYS}d)",
            "target_strategy_sample": int(TARGET_STRATEGY_SAMPLE),
            "target_lookback_days": int(TARGET_LOOKBACK_DAYS),
            "sample_start": min(sample_times).isoformat() if sample_times else None,
            "sample_end": max(sample_times).isoformat() if sample_times else None,
            "strategy_rows_available": len(strategy_rows),
        },
        "sample_size": sample_size,
        "promote": promote[:max_items],
        "watch": watch[:max_items],
        "avoid": avoid[:max_items],
        "coverage": coverage,
        "generated_at": ref_now.isoformat(),
        "sparse_data": bool(sparse_data),
    }


__all__ = ["build_playbook_analysis"]
