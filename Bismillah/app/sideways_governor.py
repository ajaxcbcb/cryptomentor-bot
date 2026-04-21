"""
Adaptive Sideways Governor (runtime-only)
=========================================

Controls sideways entry strictness and dynamic max-hold windows using
recent closed-trade behavior (last 24h).
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

TIMEOUT_CLOSE_STATUSES = {"max_hold_time_exceeded", "sideways_max_hold_exceeded"}
SIDEWAYS_SUBTYPE = "sideways_scalp"

MODE_NORMAL = "normal"
MODE_STRICT = "strict"
MODE_PAUSE = "pause"

PAUSE_DURATION_SECONDS = 3600
RECOVERY_WINDOWS_REQUIRED = 2
FALLBACK_LOOKBACK_DAYS = 14
MIN_STRICT_SAMPLE = 20

SIDEWAYS_HOLD_MIN = 90
SIDEWAYS_HOLD_MAX = 150
TREND_HOLD_MIN = 1200
TREND_HOLD_MAX = 2400

def _env_flag(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, "true" if default else "false") or "").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


SIDEWAYS_GOVERNOR_PAUSE_FALLBACK_ENABLED = _env_flag(
    "SIDEWAYS_GOVERNOR_PAUSE_FALLBACK_ENABLED",
    False,
)

_state_lock = threading.Lock()
_state: Dict[str, Any] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


STRICT_MIN_RR = min(
    1.35,
    max(1.05, _as_float(os.getenv("SIDEWAYS_GOVERNOR_STRICT_MIN_RR", "1.20"), 1.20)),
)
STRICT_MIN_VOLUME_FLOOR = min(
    1.30,
    max(0.90, _as_float(os.getenv("SIDEWAYS_GOVERNOR_STRICT_MIN_VOLUME_FLOOR", "1.00"), 1.00)),
)
STRICT_CONFIDENCE_BONUS = min(
    5,
    max(0, _as_int(os.getenv("SIDEWAYS_GOVERNOR_STRICT_CONFIDENCE_BONUS", "1"), 1)),
)
STRICT_CONFIRMATIONS_REQUIRED = min(
    3,
    max(1, _as_int(os.getenv("SIDEWAYS_GOVERNOR_STRICT_CONFIRMATIONS_REQUIRED", "1"), 1)),
)


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


def _clamp_int(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, int(value)))


def default_sideways_governor_state() -> Dict[str, Any]:
    return {
        "updated_at": None,
        "mode": MODE_STRICT,  # strict baseline until recent quality recovers
        "decision_reason": "bootstrap",
        "pause_until_ts": 0.0,
        "consecutive_recovery_windows": 0,
        "fallback_recovery_windows": 0,
        "sample_size_24h": 0,
        "non_sideways_sample_size_24h": 0,
        "sideways_expectancy_24h": 0.0,
        "non_sideways_expectancy_24h": 0.0,
        "sideways_timeout_exit_count_24h": 0,
        "sideways_timeout_loss_count_24h": 0,
        "sideways_timeout_loss_rate_24h": 0.0,
        "sample_basis_window": "bootstrap_strict",
        "sample_size_basis": 0,
        "sideways_expectancy_basis": 0.0,
        "sideways_timeout_loss_rate_basis": 0.0,
        "fallback_sample_size_14d": 0,
        "allow_sideways_entries": True,
        "allow_sideways_fallback": False,
        "sideways_min_rr_override": STRICT_MIN_RR,
        "sideways_min_volume_floor": STRICT_MIN_VOLUME_FLOOR,
        "sideways_confidence_bonus": STRICT_CONFIDENCE_BONUS,
        "sideways_confirmations_required": STRICT_CONFIRMATIONS_REQUIRED,
        "dynamic_hold_sideways_seconds": 120,
        "dynamic_hold_non_sideways_seconds": 1800,
        "symbol_sideways_hold_seconds": {},
        "symbol_non_sideways_hold_seconds": {},
    }


def _avg(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _derive_global_sideways_hold(expectancy: float, sample_size: int) -> int:
    if sample_size < 10:
        return 120
    if expectancy <= -0.010:
        return SIDEWAYS_HOLD_MIN
    if expectancy < -0.003:
        return 105
    if expectancy >= 0.010:
        return SIDEWAYS_HOLD_MAX
    if expectancy > 0.003:
        return 135
    return 120


def _derive_global_non_sideways_hold(expectancy: float, sample_size: int) -> int:
    if sample_size < 20:
        return 1800
    if expectancy <= -0.020:
        return TREND_HOLD_MIN
    if expectancy < 0:
        return 1500
    if expectancy >= 0.050:
        return TREND_HOLD_MAX
    if expectancy > 0:
        return 2100
    return 1800


def _build_symbol_hold_map(
    per_symbol: Dict[str, Tuple[int, float]],
    global_hold: int,
    hold_min: int,
    hold_max: int,
) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for symbol, (n, expectancy) in per_symbol.items():
        if n < 5:
            continue
        factor = 1.0
        if expectancy <= -0.010:
            factor = 0.85
        elif expectancy >= 0.010:
            factor = 1.15
        out[symbol] = _clamp_int(int(round(global_hold * factor)), hold_min, hold_max)
    return out


def build_sideways_metrics(closed_trades: List[Dict[str, Any]], now_utc: Optional[datetime] = None) -> Dict[str, Any]:
    now = now_utc or _utc_now()
    since_24h = now - timedelta(hours=24)
    since_14d = now - timedelta(days=FALLBACK_LOOKBACK_DAYS)

    rows_24h: List[Dict[str, Any]] = []
    rows_14d: List[Dict[str, Any]] = []
    for row in closed_trades:
        dt = _parse_iso(row.get("closed_at"))
        if not dt:
            continue
        if dt >= since_24h:
            rows_24h.append(row)
        if dt >= since_14d:
            rows_14d.append(row)

    sideways_rows = [r for r in rows_24h if str(r.get("trade_subtype") or "") == SIDEWAYS_SUBTYPE]
    non_sideways_rows = [r for r in rows_24h if str(r.get("trade_subtype") or "") != SIDEWAYS_SUBTYPE]
    fallback_sideways_rows = [r for r in rows_14d if str(r.get("trade_subtype") or "") == SIDEWAYS_SUBTYPE]

    sideways_pnls = [_as_float(r.get("pnl_usdt"), 0.0) for r in sideways_rows]
    non_sideways_pnls = [_as_float(r.get("pnl_usdt"), 0.0) for r in non_sideways_rows]
    fallback_sideways_pnls = [_as_float(r.get("pnl_usdt"), 0.0) for r in fallback_sideways_rows]

    timeout_rows = [
        r for r in sideways_rows
        if str(r.get("close_reason") or r.get("status") or "").strip().lower() in TIMEOUT_CLOSE_STATUSES
    ]
    timeout_losses = [r for r in timeout_rows if _as_float(r.get("pnl_usdt"), 0.0) < 0]
    fallback_timeout_rows = [
        r for r in fallback_sideways_rows
        if str(r.get("close_reason") or r.get("status") or "").strip().lower() in TIMEOUT_CLOSE_STATUSES
    ]
    fallback_timeout_losses = [r for r in fallback_timeout_rows if _as_float(r.get("pnl_usdt"), 0.0) < 0]

    per_symbol_sideways: Dict[str, List[float]] = {}
    per_symbol_non_sideways: Dict[str, List[float]] = {}
    for row in sideways_rows:
        symbol = str(row.get("symbol") or "").upper()
        if not symbol:
            continue
        per_symbol_sideways.setdefault(symbol, []).append(_as_float(row.get("pnl_usdt"), 0.0))
    for row in non_sideways_rows:
        symbol = str(row.get("symbol") or "").upper()
        if not symbol:
            continue
        per_symbol_non_sideways.setdefault(symbol, []).append(_as_float(row.get("pnl_usdt"), 0.0))

    side_symbol_stats = {
        sym: (len(vals), _avg(vals)) for sym, vals in per_symbol_sideways.items()
    }
    non_side_symbol_stats = {
        sym: (len(vals), _avg(vals)) for sym, vals in per_symbol_non_sideways.items()
    }

    return {
        "sample_size_24h": len(sideways_rows),
        "non_sideways_sample_size_24h": len(non_sideways_rows),
        "sideways_expectancy_24h": _avg(sideways_pnls),
        "non_sideways_expectancy_24h": _avg(non_sideways_pnls),
        "sideways_timeout_exit_count_24h": len(timeout_rows),
        "sideways_timeout_loss_count_24h": len(timeout_losses),
        "sideways_timeout_loss_rate_24h": (
            float(len(timeout_losses) / len(timeout_rows)) if timeout_rows else 0.0
        ),
        "fallback_sample_size_14d": len(fallback_sideways_rows),
        "sideways_expectancy_14d": _avg(fallback_sideways_pnls),
        "sideways_timeout_exit_count_14d": len(fallback_timeout_rows),
        "sideways_timeout_loss_count_14d": len(fallback_timeout_losses),
        "sideways_timeout_loss_rate_14d": (
            float(len(fallback_timeout_losses) / len(fallback_timeout_rows)) if fallback_timeout_rows else 0.0
        ),
        "symbol_sideways_stats": side_symbol_stats,
        "symbol_non_sideways_stats": non_side_symbol_stats,
    }


def compute_next_sideways_governor_state(
    prev_state: Dict[str, Any],
    metrics: Dict[str, Any],
    now_utc: Optional[datetime] = None,
) -> Dict[str, Any]:
    now = now_utc or _utc_now()
    now_ts = now.timestamp()

    out = dict(default_sideways_governor_state())
    out.update(prev_state or {})
    out.update({
        "sample_size_24h": _as_int(metrics.get("sample_size_24h"), 0),
        "non_sideways_sample_size_24h": _as_int(metrics.get("non_sideways_sample_size_24h"), 0),
        "sideways_expectancy_24h": _as_float(metrics.get("sideways_expectancy_24h"), 0.0),
        "non_sideways_expectancy_24h": _as_float(metrics.get("non_sideways_expectancy_24h"), 0.0),
        "sideways_timeout_exit_count_24h": _as_int(metrics.get("sideways_timeout_exit_count_24h"), 0),
        "sideways_timeout_loss_count_24h": _as_int(metrics.get("sideways_timeout_loss_count_24h"), 0),
        "sideways_timeout_loss_rate_24h": _as_float(metrics.get("sideways_timeout_loss_rate_24h"), 0.0),
        "fallback_sample_size_14d": _as_int(metrics.get("fallback_sample_size_14d"), 0),
    })

    sample_24h = int(out["sample_size_24h"])
    sample_fallback = _as_int(metrics.get("fallback_sample_size_14d"), 0)
    if sample_24h >= MIN_STRICT_SAMPLE:
        sample = sample_24h
        expectancy = float(out["sideways_expectancy_24h"])
        timeout_loss_rate = float(out["sideways_timeout_loss_rate_24h"])
        sample_basis_window = "24h"
    else:
        sample = sample_fallback
        expectancy = _as_float(metrics.get("sideways_expectancy_14d"), 0.0)
        timeout_loss_rate = _as_float(metrics.get("sideways_timeout_loss_rate_14d"), 0.0)
        sample_basis_window = "14d_fallback" if sample_fallback > 0 else "bootstrap_strict"

    prev_mode = str(out.get("mode") or MODE_NORMAL)
    pause_until_ts = _as_float(out.get("pause_until_ts"), 0.0)
    recovery_windows = _as_int(out.get("consecutive_recovery_windows"), 0)
    fallback_recovery_windows = _as_int(out.get("fallback_recovery_windows"), 0)

    # Hard pause must be based on fresh 24h damage, not fallback history.
    severe = (
        sample_24h >= 30
        and float(out["sideways_expectancy_24h"]) < -0.005
        and float(out["sideways_timeout_loss_rate_24h"]) >= 0.65
    )
    needs_strict = sample >= 20 and (expectancy < -0.0015 or timeout_loss_rate >= 0.58)
    recovery_good = expectancy >= 0.0 and timeout_loss_rate <= 0.50
    fallback_recovered = expectancy >= 0.0

    mode = prev_mode
    decision_reason = "hold"

    if severe:
        mode = MODE_PAUSE
        pause_until_ts = now_ts + PAUSE_DURATION_SECONDS
        recovery_windows = 0
        decision_reason = "pause_sideways_60m"
    elif prev_mode == MODE_PAUSE and now_ts < pause_until_ts:
        mode = MODE_PAUSE
        decision_reason = "pause_window_active"
        recovery_windows = recovery_windows + 1 if recovery_good else 0
    elif needs_strict:
        mode = MODE_STRICT
        decision_reason = "strict_sideways_quality"
        recovery_windows = 0
    elif sample < MIN_STRICT_SAMPLE:
        mode = MODE_STRICT
        decision_reason = "strict_baseline_sparse_recent_sample"
        recovery_windows = 0
    elif prev_mode in {MODE_STRICT, MODE_PAUSE}:
        recovery_windows = recovery_windows + 1 if recovery_good else 0
        if recovery_windows >= RECOVERY_WINDOWS_REQUIRED:
            mode = MODE_NORMAL
            decision_reason = "recovered_to_normal"
            pause_until_ts = 0.0
            recovery_windows = 0
        else:
            mode = MODE_STRICT
            decision_reason = "recovery_observation"
    else:
        mode = MODE_NORMAL
        decision_reason = "normal_hold"
        recovery_windows = 0

    fallback_recovery_windows = (fallback_recovery_windows + 1) if fallback_recovered else 0

    if mode == MODE_PAUSE:
        allow_sideways_entries = False
        allow_sideways_fallback = False
        min_rr_override = STRICT_MIN_RR
        min_vol_floor = STRICT_MIN_VOLUME_FLOOR
        conf_bonus = STRICT_CONFIDENCE_BONUS
        confirmations = STRICT_CONFIRMATIONS_REQUIRED
    elif mode == MODE_STRICT:
        allow_sideways_entries = True
        allow_sideways_fallback = False
        min_rr_override = STRICT_MIN_RR
        min_vol_floor = STRICT_MIN_VOLUME_FLOOR
        conf_bonus = STRICT_CONFIDENCE_BONUS
        confirmations = STRICT_CONFIRMATIONS_REQUIRED
    else:
        allow_sideways_entries = True
        allow_sideways_fallback = fallback_recovery_windows >= RECOVERY_WINDOWS_REQUIRED
        min_rr_override = None
        min_vol_floor = 0.9
        conf_bonus = 0
        confirmations = 1

    sideways_hold = _derive_global_sideways_hold(expectancy, sample)
    non_side_expectancy = float(out["non_sideways_expectancy_24h"])
    non_side_sample = int(out["non_sideways_sample_size_24h"])
    non_side_hold = _derive_global_non_sideways_hold(non_side_expectancy, non_side_sample)

    symbol_side_map = _build_symbol_hold_map(
        per_symbol=metrics.get("symbol_sideways_stats", {}) or {},
        global_hold=sideways_hold,
        hold_min=SIDEWAYS_HOLD_MIN,
        hold_max=SIDEWAYS_HOLD_MAX,
    )
    symbol_non_side_map = _build_symbol_hold_map(
        per_symbol=metrics.get("symbol_non_sideways_stats", {}) or {},
        global_hold=non_side_hold,
        hold_min=TREND_HOLD_MIN,
        hold_max=TREND_HOLD_MAX,
    )

    out.update({
        "mode": mode,
        "decision_reason": decision_reason,
        "pause_until_ts": pause_until_ts,
        "consecutive_recovery_windows": recovery_windows,
        "fallback_recovery_windows": fallback_recovery_windows,
        "sample_basis_window": sample_basis_window,
        "sample_size_basis": sample,
        "sideways_expectancy_basis": expectancy,
        "sideways_timeout_loss_rate_basis": timeout_loss_rate,
        "allow_sideways_entries": allow_sideways_entries,
        "allow_sideways_fallback": allow_sideways_fallback,
        "sideways_min_rr_override": min_rr_override,
        "sideways_min_volume_floor": min_vol_floor,
        "sideways_confidence_bonus": conf_bonus,
        "sideways_confirmations_required": confirmations,
        "dynamic_hold_sideways_seconds": sideways_hold,
        "dynamic_hold_non_sideways_seconds": non_side_hold,
        "symbol_sideways_hold_seconds": symbol_side_map,
        "symbol_non_sideways_hold_seconds": symbol_non_side_map,
        "updated_at": now.isoformat(),
    })
    return out


def _fetch_closed_trades_recent(limit: int = 4000) -> List[Dict[str, Any]]:
    from app.supabase_repo import _client

    s = _client()
    since = (_utc_now() - timedelta(days=FALLBACK_LOOKBACK_DAYS)).isoformat()
    collected: List[Dict[str, Any]] = []
    page_size = min(1000, max(200, int(limit)))
    page = 0
    while len(collected) < limit:
        frm = page * page_size
        to = frm + page_size - 1
        res = (
            s.table("autotrade_trades")
            .select("id,symbol,status,close_reason,pnl_usdt,trade_subtype,closed_at")
            .neq("status", "open")
            .gte("closed_at", since)
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


def refresh_sideways_governor_state() -> Dict[str, Any]:
    prev = get_sideways_governor_snapshot()
    try:
        closed_rows = _fetch_closed_trades_recent(limit=4000)
        metrics = build_sideways_metrics(closed_rows)
        nxt = compute_next_sideways_governor_state(prev, metrics, now_utc=_utc_now())
    except Exception as e:
        logger.warning(f"[SidewaysGovernor] refresh failed: {e}")
        nxt = dict(default_sideways_governor_state())
        nxt.update(prev or {})
        nxt["updated_at"] = _utc_now().isoformat()
        nxt["decision_reason"] = "refresh_failed"
        nxt["refresh_error"] = str(e)

    with _state_lock:
        _state.clear()
        _state.update(nxt)
    return get_sideways_governor_snapshot()


def get_sideways_governor_snapshot() -> Dict[str, Any]:
    with _state_lock:
        if not _state:
            _state.update(default_sideways_governor_state())
        return dict(_state)


def get_sideways_entry_overrides(snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    st = snapshot or get_sideways_governor_snapshot()
    mode = str(st.get("mode") or MODE_NORMAL)
    if mode not in {MODE_NORMAL, MODE_STRICT, MODE_PAUSE}:
        mode = MODE_NORMAL
    allow_sideways_entries = bool(st.get("allow_sideways_entries", True))
    allow_sideways_fallback = bool(st.get("allow_sideways_fallback", True))
    decision_reason = str(st.get("decision_reason") or "")

    if mode == MODE_PAUSE and SIDEWAYS_GOVERNOR_PAUSE_FALLBACK_ENABLED:
        # Hotfix path: keep pause telemetry but avoid full sideways-entry freeze.
        allow_sideways_entries = True
        allow_sideways_fallback = False
        decision_reason = (
            f"{decision_reason}|pause_fallback_strict_override"
            if decision_reason
            else "pause_fallback_strict_override"
        )

    return {
        "mode": mode,
        "allow_sideways_entries": allow_sideways_entries,
        "allow_sideways_fallback": allow_sideways_fallback,
        "sideways_min_rr_override": st.get("sideways_min_rr_override"),
        "sideways_min_volume_floor": float(st.get("sideways_min_volume_floor", 0.9) or 0.9),
        "sideways_confidence_bonus": int(st.get("sideways_confidence_bonus", 0) or 0),
        "sideways_confirmations_required": int(st.get("sideways_confirmations_required", 1) or 1),
        "sideways_expectancy_24h": float(st.get("sideways_expectancy_24h", 0.0) or 0.0),
        "sideways_timeout_loss_rate_24h": float(st.get("sideways_timeout_loss_rate_24h", 0.0) or 0.0),
        "sample_size_24h": int(st.get("sample_size_24h", 0) or 0),
        "sample_basis_window": str(st.get("sample_basis_window", "bootstrap_strict") or "bootstrap_strict"),
        "sample_size_basis": int(st.get("sample_size_basis", 0) or 0),
        "sideways_expectancy_basis": float(st.get("sideways_expectancy_basis", 0.0) or 0.0),
        "sideways_timeout_loss_rate_basis": float(st.get("sideways_timeout_loss_rate_basis", 0.0) or 0.0),
        "fallback_recovery_windows": int(st.get("fallback_recovery_windows", 0) or 0),
        "fallback_sample_size_14d": int(st.get("fallback_sample_size_14d", 0) or 0),
        "decision_reason": decision_reason,
    }


def resolve_dynamic_max_hold_seconds(
    symbol: str,
    is_sideways: bool,
    snapshot: Optional[Dict[str, Any]] = None,
    default_non_sideways: int = 1800,
) -> int:
    st = snapshot or get_sideways_governor_snapshot()
    sym = str(symbol or "").upper()
    if is_sideways:
        sym_map = st.get("symbol_sideways_hold_seconds") or {}
        if sym and sym in sym_map:
            return _clamp_int(_as_int(sym_map.get(sym), 120), SIDEWAYS_HOLD_MIN, SIDEWAYS_HOLD_MAX)
        return _clamp_int(_as_int(st.get("dynamic_hold_sideways_seconds"), 120), SIDEWAYS_HOLD_MIN, SIDEWAYS_HOLD_MAX)

    sym_map = st.get("symbol_non_sideways_hold_seconds") or {}
    if sym and sym in sym_map:
        return _clamp_int(_as_int(sym_map.get(sym), default_non_sideways), TREND_HOLD_MIN, TREND_HOLD_MAX)
    return _clamp_int(_as_int(st.get("dynamic_hold_non_sideways_seconds"), default_non_sideways), TREND_HOLD_MIN, TREND_HOLD_MAX)
