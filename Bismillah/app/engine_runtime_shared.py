"""
Shared runtime helpers for swing/scalping engine loops.

This module centralizes small orchestration behaviors that were duplicated
across engine implementations:
  - startup pending-lock sanitation
  - refresh cadence helper (default 10-minute cycles)
  - top-volume pair refresh with fallback
  - blocked-pending notification TTL dedupe
  - stop-signal polling from autotrade_sessions
"""

from __future__ import annotations

import asyncio
import copy
import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, MutableMapping, Optional, Sequence, Tuple

from app.supabase_repo import _client
from app.volume_pair_selector import get_ranked_top_volume_pairs


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return bool(default)
    txt = str(value).strip().lower()
    if txt in {"1", "true", "yes", "y", "on"}:
        return True
    if txt in {"0", "false", "no", "n", "off"}:
        return False
    return bool(default)


def _clamp(value: Any, lo: float, hi: float, default: float) -> float:
    v = _as_float(value, default)
    return max(float(lo), min(float(hi), v))


def _ratio_from_env_pct(raw: Any, default_ratio: float) -> float:
    """
    Parse percent-like env values to ratio.

    Accepts both:
      - percent style: 5.0  -> 0.05
      - ratio style:   0.05 -> 0.05
    """
    v = _as_float(raw, default_ratio)
    if v > 1.0:
        v = v / 100.0
    return max(0.0, float(v))


def _read_adaptive_breaker_cfg(mode: str) -> Dict[str, Any]:
    mode_txt = str(mode or "").strip().lower()
    prefix = "SCALPING" if mode_txt == "scalping" else "SWING"

    enabled = _as_bool(os.getenv(f"{prefix}_ADAPTIVE_CIRCUIT_BREAKER_ENABLED", "true"), True)
    base_ratio = _ratio_from_env_pct(os.getenv(f"{prefix}_DAILY_LOSS_BASE_PCT", "5.0"), 0.05)
    min_ratio = _ratio_from_env_pct(os.getenv(f"{prefix}_DAILY_LOSS_MIN_PCT", "3.0"), 0.03)
    max_ratio = _ratio_from_env_pct(os.getenv(f"{prefix}_DAILY_LOSS_MAX_PCT", "8.0"), 0.08)
    if max_ratio < min_ratio:
        max_ratio = min_ratio
    base_ratio = _clamp(base_ratio, min_ratio, max_ratio, 0.05)

    strong_conf_margin = max(0.0, _as_float(os.getenv(f"{prefix}_BREAKER_STRONG_CONF_MARGIN", "5"), 5.0))
    strong_rr_margin = max(0.0, _as_float(os.getenv(f"{prefix}_BREAKER_STRONG_RR_MARGIN", "0.3"), 0.3))

    return {
        "mode": mode_txt if mode_txt in {"scalping", "swing"} else "swing",
        "enabled": bool(enabled),
        "base_limit_pct": float(base_ratio),
        "min_limit_pct": float(min_ratio),
        "max_limit_pct": float(max_ratio),
        "strong_conf_margin": float(strong_conf_margin),
        "strong_rr_margin": float(strong_rr_margin),
    }


def _signal_field(signal: Any, key: str, default: Any = None) -> Any:
    if isinstance(signal, dict):
        return signal.get(key, default)
    return getattr(signal, key, default)


def compute_adaptive_daily_loss_limit_pct(
    playbook_snapshot: Optional[Dict[str, Any]],
    *,
    base_limit_pct: float = 0.05,
    min_limit_pct: float = 0.03,
    max_limit_pct: float = 0.08,
) -> Dict[str, Any]:
    """
    Compute adaptive daily loss limit using deterministic playbook steps.

    Step mapping (1 step = 1.0% absolute limit shift):
      +2: strong playbook health (high WR + positive expectancy)
      +1: mildly strong playbook health
       0: neutral / insufficient sample
      -1: mildly weak playbook health
      -2: clearly weak playbook health
    """
    snap = dict(playbook_snapshot or {})
    wr = _clamp(snap.get("rolling_win_rate", 0.0), 0.0, 1.0, 0.0)
    exp = _as_float(snap.get("rolling_expectancy", 0.0), 0.0)
    sample = int(_as_float(snap.get("sample_size", 0), 0.0))
    guardrails = bool(snap.get("guardrails_healthy", False))

    base = _clamp(base_limit_pct, min_limit_pct, max_limit_pct, 0.05)
    min_v = _clamp(min_limit_pct, 0.0, 1.0, 0.03)
    max_v = _clamp(max_limit_pct, min_v, 1.0, 0.08)

    step = 0
    reason = "neutral_insufficient_sample"
    if sample >= 40:
        if guardrails and wr >= 0.82 and exp >= 0.05:
            step = 2
            reason = "strong_plus2"
        elif guardrails and wr >= 0.75 and exp > 0.0:
            step = 1
            reason = "strong_plus1"
        elif (not guardrails) or wr < 0.55 or exp <= -0.15:
            step = -2
            reason = "weak_minus2"
        elif wr < 0.70 or exp < 0.0:
            step = -1
            reason = "weak_minus1"
        else:
            step = 0
            reason = "neutral_balanced"

    adaptive = base + (float(step) * 0.01)
    adaptive = _clamp(adaptive, min_v, max_v, base)
    return {
        "adaptive_limit_pct": float(adaptive),
        "step": int(step),
        "step_reason": reason,
        "base_limit_pct": float(base),
        "min_limit_pct": float(min_v),
        "max_limit_pct": float(max_v),
        "rolling_win_rate": float(wr),
        "rolling_expectancy": float(exp),
        "sample_size": int(sample),
        "guardrails_healthy": bool(guardrails),
    }


def compute_daily_loss_pct_utc(supabase_client: Any, user_id: int) -> Dict[str, Any]:
    """
    Compute UTC-day loss ratio from realized trade PnL and session balance basis.
    """
    utc_day = datetime.now(timezone.utc).date().isoformat()
    trades_res = (
        supabase_client.table("autotrade_trades")
        .select("pnl_usdt")
        .eq("telegram_id", int(user_id))
        .gte("opened_at", utc_day)
        .execute()
    )
    trades = getattr(trades_res, "data", None) or []

    total_pnl = 0.0
    for row in trades:
        if not isinstance(row, dict):
            continue
        total_pnl += _as_float(row.get("pnl_usdt"), 0.0)

    session_res = (
        supabase_client.table("autotrade_sessions")
        .select("initial_deposit,current_balance")
        .eq("telegram_id", int(user_id))
        .limit(1)
        .execute()
    )
    session_data = getattr(session_res, "data", None) or []
    first = session_data[0] if session_data and isinstance(session_data[0], dict) else {}

    current_balance = _as_float(first.get("current_balance"), 0.0)
    initial_deposit = _as_float(first.get("initial_deposit"), 0.0)
    balance_basis = current_balance if current_balance > 0.0 else initial_deposit
    if balance_basis <= 0.0:
        balance_basis = 100.0

    daily_loss_usdt = max(0.0, -float(total_pnl))
    daily_loss_pct = float(daily_loss_usdt / balance_basis) if balance_basis > 0.0 else 0.0
    return {
        "utc_day": utc_day,
        "daily_pnl_usdt": float(total_pnl),
        "daily_loss_usdt": float(daily_loss_usdt),
        "balance_basis_usdt": float(balance_basis),
        "loss_pct_today": float(daily_loss_pct),
    }


def is_strong_opportunity(
    *,
    signal: Any,
    min_confidence_pct: float,
    min_rr_ratio: float,
    conf_margin_pct: float = 5.0,
    rr_margin: float = 0.3,
    playbook_strong_match: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Strong opportunity requires:
      - playbook strong match
      - confidence >= (effective_min_conf + margin)
      - rr >= (mode_min_rr + margin)
    """
    conf = _as_float(_signal_field(signal, "confidence", 0.0), 0.0)
    rr = _as_float(_signal_field(signal, "rr_ratio", 0.0), 0.0)
    strong_playbook = bool(
        playbook_strong_match
        if playbook_strong_match is not None
        else _signal_field(signal, "playbook_strong_match", False)
    )
    req_conf = max(0.0, float(min_confidence_pct) + max(0.0, float(conf_margin_pct)))
    req_rr = max(0.0, float(min_rr_ratio) + max(0.0, float(rr_margin)))
    conf_ok = conf >= req_conf
    rr_ok = rr >= req_rr
    is_strong = bool(strong_playbook and conf_ok and rr_ok)
    return {
        "is_strong": bool(is_strong),
        "playbook_strong_match": bool(strong_playbook),
        "confidence_ok": bool(conf_ok),
        "rr_ok": bool(rr_ok),
        "signal_confidence": float(conf),
        "signal_rr_ratio": float(rr),
        "required_confidence": float(req_conf),
        "required_rr_ratio": float(req_rr),
    }


def evaluate_daily_circuit_breaker_action(
    *,
    enabled: bool,
    loss_pct_today: float,
    adaptive_limit_pct: float,
    strong_opportunity: bool,
) -> Dict[str, Any]:
    if not bool(enabled):
        return {
            "blocked": False,
            "override_applied": False,
            "decision_reason": "breaker_disabled",
        }
    if float(loss_pct_today) < float(adaptive_limit_pct):
        return {
            "blocked": False,
            "override_applied": False,
            "decision_reason": "within_adaptive_limit",
        }
    if bool(strong_opportunity):
        return {
            "blocked": False,
            "override_applied": True,
            "decision_reason": "strong_opportunity_full_bypass",
        }
    return {
        "blocked": True,
        "override_applied": False,
        "decision_reason": "adaptive_limit_exceeded_non_strong",
    }


def evaluate_adaptive_daily_circuit_breaker(
    *,
    mode: str,
    user_id: int,
    signal: Any,
    supabase_client: Any,
    playbook_snapshot: Optional[Dict[str, Any]],
    min_confidence_pct: float,
    min_rr_ratio: float,
    playbook_strong_match: Optional[bool] = None,
) -> Dict[str, Any]:
    cfg = _read_adaptive_breaker_cfg(mode)
    try:
        daily = compute_daily_loss_pct_utc(supabase_client, int(user_id))
        adaptive = compute_adaptive_daily_loss_limit_pct(
            playbook_snapshot,
            base_limit_pct=float(cfg["base_limit_pct"]),
            min_limit_pct=float(cfg["min_limit_pct"]),
            max_limit_pct=float(cfg["max_limit_pct"]),
        )
        strong = is_strong_opportunity(
            signal=signal,
            min_confidence_pct=float(min_confidence_pct),
            min_rr_ratio=float(min_rr_ratio),
            conf_margin_pct=float(cfg["strong_conf_margin"]),
            rr_margin=float(cfg["strong_rr_margin"]),
            playbook_strong_match=playbook_strong_match,
        )
        action = evaluate_daily_circuit_breaker_action(
            enabled=bool(cfg["enabled"]),
            loss_pct_today=float(daily["loss_pct_today"]),
            adaptive_limit_pct=float(adaptive["adaptive_limit_pct"]),
            strong_opportunity=bool(strong["is_strong"]),
        )
        return {
            "mode": cfg["mode"],
            "enabled": bool(cfg["enabled"]),
            "threshold_source": "adaptive_win_playbook",
            "strong_conf_margin": float(cfg["strong_conf_margin"]),
            "strong_rr_margin": float(cfg["strong_rr_margin"]),
            "loss_pct_today": float(daily["loss_pct_today"]),
            "daily_loss_usdt": float(daily["daily_loss_usdt"]),
            "daily_pnl_usdt": float(daily["daily_pnl_usdt"]),
            "balance_basis_usdt": float(daily["balance_basis_usdt"]),
            "utc_day": daily["utc_day"],
            "adaptive_limit_pct": float(adaptive["adaptive_limit_pct"]),
            "adaptive_step": int(adaptive["step"]),
            "adaptive_step_reason": str(adaptive["step_reason"]),
            "base_limit_pct": float(adaptive["base_limit_pct"]),
            "min_limit_pct": float(adaptive["min_limit_pct"]),
            "max_limit_pct": float(adaptive["max_limit_pct"]),
            "rolling_win_rate": float(adaptive["rolling_win_rate"]),
            "rolling_expectancy": float(adaptive["rolling_expectancy"]),
            "sample_size": int(adaptive["sample_size"]),
            "guardrails_healthy": bool(adaptive["guardrails_healthy"]),
            "strong_opportunity": bool(strong["is_strong"]),
            "playbook_strong_match": bool(strong["playbook_strong_match"]),
            "confidence_ok": bool(strong["confidence_ok"]),
            "rr_ok": bool(strong["rr_ok"]),
            "signal_confidence": float(strong["signal_confidence"]),
            "signal_rr_ratio": float(strong["signal_rr_ratio"]),
            "required_confidence": float(strong["required_confidence"]),
            "required_rr_ratio": float(strong["required_rr_ratio"]),
            "blocked": bool(action["blocked"]),
            "override_applied": bool(action["override_applied"]),
            "decision_reason": str(action["decision_reason"]),
        }
    except Exception as exc:
        return {
            "mode": cfg["mode"],
            "enabled": bool(cfg["enabled"]),
            "threshold_source": "adaptive_win_playbook",
            "strong_conf_margin": float(cfg["strong_conf_margin"]),
            "strong_rr_margin": float(cfg["strong_rr_margin"]),
            "loss_pct_today": 0.0,
            "daily_loss_usdt": 0.0,
            "daily_pnl_usdt": 0.0,
            "balance_basis_usdt": 0.0,
            "utc_day": datetime.now(timezone.utc).date().isoformat(),
            "adaptive_limit_pct": float(cfg["base_limit_pct"]),
            "adaptive_step": 0,
            "adaptive_step_reason": "evaluation_error",
            "base_limit_pct": float(cfg["base_limit_pct"]),
            "min_limit_pct": float(cfg["min_limit_pct"]),
            "max_limit_pct": float(cfg["max_limit_pct"]),
            "rolling_win_rate": 0.0,
            "rolling_expectancy": 0.0,
            "sample_size": 0,
            "guardrails_healthy": False,
            "strong_opportunity": False,
            "playbook_strong_match": bool(playbook_strong_match),
            "confidence_ok": False,
            "rr_ok": False,
            "signal_confidence": _as_float(_signal_field(signal, "confidence", 0.0), 0.0),
            "signal_rr_ratio": _as_float(_signal_field(signal, "rr_ratio", 0.0), 0.0),
            "required_confidence": float(min_confidence_pct),
            "required_rr_ratio": float(min_rr_ratio),
            "blocked": False,
            "override_applied": False,
            "decision_reason": "evaluation_error_fail_open",
            "evaluation_error": str(exc),
        }


def _normalize_trade_mode(row: Dict[str, Any]) -> str:
    trade_type = str(row.get("trade_type") or "").strip().lower()
    if trade_type in {"swing", "scalping"}:
        return trade_type
    timeframe = str(row.get("timeframe") or "").strip().lower()
    if timeframe == "5m":
        return "scalping"
    if timeframe:
        return "swing"
    return ""


def _read_scalping_risk_parity_cfg() -> Dict[str, Any]:
    target_min = _clamp(os.getenv("SCALP_RISK_PARITY_TARGET_MIN", "0.85"), 0.10, 2.00, 0.85)
    target_max = _clamp(os.getenv("SCALP_RISK_PARITY_TARGET_MAX", "1.00"), 0.10, 2.00, 1.00)
    if target_max < target_min:
        target_max = float(target_min)

    cap_base = _clamp(os.getenv("SCALP_NOTIONAL_CAP_BASE_PCT", "0.50"), 0.10, 1.00, 0.50)
    cap_tight = _clamp(os.getenv("SCALP_NOTIONAL_CAP_TIGHT_PCT", "0.45"), 0.10, 1.00, 0.45)
    cap_tighter = _clamp(os.getenv("SCALP_NOTIONAL_CAP_TIGHTER_PCT", "0.40"), 0.10, 1.00, 0.40)
    cap_tight = min(cap_base, cap_tight)
    cap_tighter = min(cap_tight, cap_tighter)

    return {
        "enabled": _as_bool(os.getenv("SCALP_RISK_PARITY_ENABLED", "true"), True),
        "target_min": float(target_min),
        "target_max": float(target_max),
        "lookback_hours": max(1, int(_as_float(os.getenv("SCALP_RISK_PARITY_LOOKBACK_HOURS", "24"), 24.0))),
        "min_swing_sample": max(1, int(_as_float(os.getenv("SCALP_RISK_PARITY_MIN_SWING_SAMPLE", "20"), 20.0))),
        "dynamic_time_enabled": _as_bool(os.getenv("SCALP_DYNAMIC_TIME_ENABLED", "true"), True),
        "dynamic_cap_enabled": _as_bool(os.getenv("SCALP_DYNAMIC_CAP_ENABLED", "true"), True),
        "dynamic_conf_relief_enabled": _as_bool(os.getenv("SCALP_DYNAMIC_CONF_RELIEF_ENABLED", "true"), True),
        "cap_base_pct": float(cap_base),
        "cap_tight_pct": float(cap_tight),
        "cap_tighter_pct": float(cap_tighter),
    }


def classify_scalping_risk_parity_regime(
    ratio: Any,
    target_min: Any = 0.85,
    target_max: Any = 1.00,
) -> str:
    r = max(0.0, _as_float(ratio, 1.0))
    lo = _clamp(target_min, 0.10, 2.00, 0.85)
    hi = _clamp(target_max, 0.10, 2.00, 1.00)
    if hi < lo:
        hi = lo
    if r < lo:
        return "under_risk"
    if r > hi:
        return "over_risk"
    return "balanced"


def _base_time_profile() -> Dict[str, float]:
    return {"best": 1.0, "good": 0.7, "neutral": 0.5, "avoid": 0.0}


def _under_time_profile() -> Dict[str, float]:
    return {"best": 1.0, "good": 1.0, "neutral": 0.7, "avoid": 0.0}


def _over_time_profile() -> Dict[str, float]:
    return {"best": 1.0, "good": 0.6, "neutral": 0.4, "avoid": 0.0}


def _clamp_time_profile(profile: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for key in ("best", "good", "neutral", "avoid"):
        out[key] = _clamp(profile.get(key, 0.0), 0.0, 1.0, 0.0)
    return out


def build_scalping_risk_parity_state(
    opened_rows: List[Dict[str, Any]],
    session_rows: List[Dict[str, Any]],
    *,
    cfg: Optional[Dict[str, Any]] = None,
    now_utc: Optional[datetime] = None,
) -> Dict[str, Any]:
    cfg_data = dict(cfg or _read_scalping_risk_parity_cfg())
    now = now_utc or datetime.now(timezone.utc)

    scalp_vals: List[float] = []
    swing_vals: List[float] = []
    for row in opened_rows or []:
        mode = _normalize_trade_mode(row)
        if mode not in {"swing", "scalping"}:
            continue
        risk = _as_float(row.get("effective_risk_pct"), 0.0)
        if risk <= 0.0:
            continue
        if mode == "scalping":
            scalp_vals.append(risk)
        else:
            swing_vals.append(risk)

    scalp_sample = len(scalp_vals)
    swing_sample = len(swing_vals)
    scalp_avg = float(sum(scalp_vals) / scalp_sample) if scalp_sample > 0 else 0.0
    swing_avg_opened = float(sum(swing_vals) / swing_sample) if swing_sample > 0 else 0.0

    swing_baseline = swing_avg_opened
    swing_source = "opened_trades"
    if swing_sample < int(cfg_data["min_swing_sample"]):
        session_swing_vals: List[float] = []
        for row in session_rows or []:
            mode = str(row.get("trading_mode") or "").strip().lower()
            if mode != "swing":
                continue
            if not bool(row.get("engine_active")):
                continue
            risk = _clamp(row.get("risk_per_trade"), 0.25, 5.0, 1.0)
            session_swing_vals.append(risk)
        if session_swing_vals:
            swing_baseline = float(sum(session_swing_vals) / len(session_swing_vals))
            swing_source = "active_swing_sessions"
        elif swing_sample > 0:
            swing_baseline = swing_avg_opened
            swing_source = "opened_trades_sparse"
        else:
            synthetic = scalp_avg if scalp_avg > 0 else 1.0
            swing_baseline = _clamp(synthetic, 0.25, 5.0, 1.0)
            swing_source = "synthetic_from_scalping"

    ratio = 1.0
    if scalp_avg > 0.0 and swing_baseline > 0.0:
        ratio = float(scalp_avg / swing_baseline)

    enabled = bool(cfg_data.get("enabled", True))
    regime = classify_scalping_risk_parity_regime(
        ratio=ratio,
        target_min=cfg_data.get("target_min", 0.85),
        target_max=cfg_data.get("target_max", 1.00),
    )
    if not enabled:
        regime = "disabled"

    time_profile = _base_time_profile()
    if enabled and bool(cfg_data.get("dynamic_time_enabled", True)):
        if regime == "under_risk":
            time_profile = _under_time_profile()
        elif regime == "over_risk":
            time_profile = _over_time_profile()
    time_profile = _clamp_time_profile(time_profile)

    cap_pct = float(cfg_data.get("cap_base_pct", 0.50))
    if enabled and bool(cfg_data.get("dynamic_cap_enabled", True)) and regime == "over_risk":
        cap_pct = float(cfg_data.get("cap_tight_pct", 0.45))
        if ratio > 1.10:
            cap_pct = float(cfg_data.get("cap_tighter_pct", 0.40))
    cap_pct = _clamp(cap_pct, 0.10, 1.00, 0.50)

    conf_relief_max_penalty = None
    conf_relief_min_scale = None
    if enabled and bool(cfg_data.get("dynamic_conf_relief_enabled", True)) and regime == "under_risk":
        conf_relief_max_penalty = 2
        conf_relief_min_scale = 0.85

    return {
        "enabled": bool(enabled),
        "updated_at": now.isoformat(),
        "lookback_hours": int(cfg_data.get("lookback_hours", 24)),
        "target_min": float(cfg_data.get("target_min", 0.85)),
        "target_max": float(cfg_data.get("target_max", 1.00)),
        "min_swing_sample": int(cfg_data.get("min_swing_sample", 20)),
        "scalp_avg_effective_risk_pct": round(float(scalp_avg), 6),
        "swing_avg_effective_risk_pct": round(float(swing_avg_opened), 6),
        "swing_baseline_effective_risk_pct": round(float(swing_baseline), 6),
        "scalp_sample_size": int(scalp_sample),
        "swing_sample_size": int(swing_sample),
        "swing_baseline_source": str(swing_source),
        "ratio": round(float(ratio), 6),
        "regime": str(regime),
        "under_target": bool(enabled and regime == "under_risk"),
        "over_target": bool(enabled and regime == "over_risk"),
        "controls": {
            "dynamic_time_enabled": bool(cfg_data.get("dynamic_time_enabled", True)),
            "dynamic_cap_enabled": bool(cfg_data.get("dynamic_cap_enabled", True)),
            "dynamic_conf_relief_enabled": bool(cfg_data.get("dynamic_conf_relief_enabled", True)),
            "time_profile": dict(time_profile),
            "cap_pct": round(float(cap_pct), 6),
            "conf_relief_max_penalty": conf_relief_max_penalty,
            "conf_relief_min_scale": conf_relief_min_scale,
        },
    }


_scalp_risk_parity_state_lock = threading.Lock()
_scalp_risk_parity_state: Dict[str, Any] = build_scalping_risk_parity_state(
    opened_rows=[],
    session_rows=[],
    cfg=_read_scalping_risk_parity_cfg(),
)


def refresh_scalping_risk_parity_state() -> Dict[str, Any]:
    cfg = _read_scalping_risk_parity_cfg()
    lookback_hours = int(cfg.get("lookback_hours", 24))
    since = datetime.now(timezone.utc) - timedelta(hours=max(1, lookback_hours))
    s = _client()
    opened_rows = (
        s.table("autotrade_trades")
        .select("trade_type,timeframe,effective_risk_pct,opened_at")
        .gte("opened_at", since.isoformat())
        .order("opened_at", desc=True)
        .limit(5000)
        .execute()
        .data
        or []
    )
    session_rows = (
        s.table("autotrade_sessions")
        .select("trading_mode,status,engine_active,risk_per_trade")
        .execute()
        .data
        or []
    )
    nxt = build_scalping_risk_parity_state(
        opened_rows=opened_rows,
        session_rows=session_rows,
        cfg=cfg,
    )
    with _scalp_risk_parity_state_lock:
        _scalp_risk_parity_state.clear()
        _scalp_risk_parity_state.update(nxt)
        return copy.deepcopy(_scalp_risk_parity_state)


def get_scalping_risk_parity_snapshot() -> Dict[str, Any]:
    with _scalp_risk_parity_state_lock:
        if not _scalp_risk_parity_state:
            _scalp_risk_parity_state.update(
                build_scalping_risk_parity_state(
                    opened_rows=[],
                    session_rows=[],
                    cfg=_read_scalping_risk_parity_cfg(),
                )
            )
        return copy.deepcopy(_scalp_risk_parity_state)


def get_scalping_risk_parity_controls(snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    st = snapshot or get_scalping_risk_parity_snapshot()
    controls = dict(st.get("controls") or {})
    time_profile = _clamp_time_profile(dict(controls.get("time_profile") or _base_time_profile()))
    return {
        "enabled": bool(st.get("enabled", False)),
        "updated_at": st.get("updated_at"),
        "regime": str(st.get("regime") or "disabled"),
        "ratio": _as_float(st.get("ratio"), 1.0),
        "target_min": _as_float(st.get("target_min"), 0.85),
        "target_max": _as_float(st.get("target_max"), 1.00),
        "under_target": bool(st.get("under_target", False)),
        "over_target": bool(st.get("over_target", False)),
        "scalp_avg_effective_risk_pct": _as_float(st.get("scalp_avg_effective_risk_pct"), 0.0),
        "swing_baseline_effective_risk_pct": _as_float(st.get("swing_baseline_effective_risk_pct"), 0.0),
        "dynamic_time_enabled": bool(controls.get("dynamic_time_enabled", False)),
        "dynamic_cap_enabled": bool(controls.get("dynamic_cap_enabled", False)),
        "dynamic_conf_relief_enabled": bool(controls.get("dynamic_conf_relief_enabled", False)),
        "time_profile": time_profile,
        "cap_pct": _clamp(controls.get("cap_pct", 0.50), 0.10, 1.00, 0.50),
        "conf_relief_max_penalty": controls.get("conf_relief_max_penalty"),
        "conf_relief_min_scale": controls.get("conf_relief_min_scale"),
    }


def apply_scalping_confidence_relief(
    conf_adapt: Dict[str, Any],
    parity_controls: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    out = dict(conf_adapt or {})
    out["parity_conf_relief_applied"] = False
    ctrl = parity_controls or {}
    if not bool(ctrl.get("enabled", False)):
        return out
    if str(ctrl.get("regime") or "") != "under_risk":
        return out
    if not bool(ctrl.get("dynamic_conf_relief_enabled", False)):
        return out

    changed = False
    penalty = int(_as_float(out.get("bucket_penalty", 0), 0.0))
    max_penalty = ctrl.get("conf_relief_max_penalty")
    if isinstance(max_penalty, int) and penalty > int(max_penalty):
        penalty = int(max_penalty)
        changed = True

    scale = _clamp(out.get("bucket_risk_scale", 1.0), 0.0, 1.0, 1.0)
    floor_scale = ctrl.get("conf_relief_min_scale")
    if floor_scale is not None:
        flo = _clamp(floor_scale, 0.0, 1.0, 0.85)
        if scale < flo:
            scale = flo
            changed = True

    out["bucket_penalty"] = int(penalty)
    out["bucket_risk_scale"] = float(scale)
    out["parity_conf_relief_applied"] = bool(changed)
    if changed:
        prev_reason = str(out.get("reason") or "")
        out["reason"] = "parity_relief" if not prev_reason else f"parity_relief_{prev_reason}"
    return out


def should_notify_blocked_pending(
    notify_map: MutableMapping[Any, float],
    key: Any,
    ttl_sec: float = 600.0,
    now_ts: Optional[float] = None,
) -> bool:
    """Return True when a blocked-pending notification is outside TTL."""
    if now_ts is None:
        now_ts = time.time()
    last = float(notify_map.get(key, 0.0) or 0.0)
    if now_ts - last < float(ttl_sec):
        return False
    notify_map[key] = float(now_ts)
    return True


def normalize_pending_lock_context(
    context: Optional[Dict[str, Any]],
    *,
    default_ttl_seconds: float = 90.0,
) -> Dict[str, Any]:
    ctx = dict(context or {})
    age_raw = ctx.get("pending_age_seconds")
    age: Optional[float]
    try:
        age = None if age_raw is None else max(0.0, float(age_raw))
    except Exception:
        age = None
    ttl = _as_float(ctx.get("pending_ttl_seconds"), float(default_ttl_seconds))
    ttl = max(1.0, float(ttl))
    pending_owner = str(ctx.get("pending_owner") or "").strip()
    owner = str(ctx.get("owner") or "none").strip().lower() or "none"
    has_position = bool(ctx.get("has_position", False))
    pending_order = bool(ctx.get("pending_order", False))
    stale_candidate = bool(
        pending_order
        and (not has_position)
        and (age is not None)
        and (age > ttl)
    )
    return {
        "pending_order": pending_order,
        "pending_owner": pending_owner,
        "pending_age_seconds": age,
        "pending_ttl_seconds": ttl,
        "has_position": has_position,
        "owner": owner,
        "last_pending_clear_reason": str(ctx.get("last_pending_clear_reason") or "").strip(),
        "stale_candidate": stale_candidate,
    }


def pending_lock_age_label(age_seconds: Optional[float]) -> str:
    if age_seconds is None:
        return "n/a"
    try:
        return f"{float(age_seconds):.1f}s"
    except Exception:
        return "n/a"


def set_ttl_cooldown(
    cooldown_map: MutableMapping[Any, float],
    key: Any,
    ttl_sec: float,
    now_ts: Optional[float] = None,
) -> float:
    """Set cooldown expiry for key and return the expiry timestamp."""
    if now_ts is None:
        now_ts = time.time()
    expires_at = float(now_ts + max(0.0, float(ttl_sec)))
    cooldown_map[key] = expires_at
    return expires_at


def is_ttl_cooldown_active(
    cooldown_map: MutableMapping[Any, float],
    key: Any,
    now_ts: Optional[float] = None,
) -> bool:
    """
    Return True when cooldown for key is still active.

    Expired entries are cleaned up lazily.
    """
    if now_ts is None:
        now_ts = time.time()
    expires_at = float(cooldown_map.get(key, 0.0) or 0.0)
    if expires_at <= float(now_ts):
        cooldown_map.pop(key, None)
        return False
    return True


async def sanitize_startup_pending_locks(
    coordinator: Any,
    user_id: int,
    logger: logging.Logger,
    label: str,
) -> Tuple[int, int]:
    """
    Clear orphan/stale pending locks for one user at startup.

    Returns:
        tuple: (cleared_any, cleared_stale)
    """
    try:
        cleared_any = int(
            await coordinator.clear_all_pending_without_position_for_user(
                int(user_id), reason="startup_sanitize"
            )
            or 0
        )
        cleared_stale = int(
            await coordinator.clear_stale_pending_for_user(int(user_id), now_ts=time.time())
            or 0
        )
        if cleared_any or cleared_stale:
            logger.warning(
                f"{label} Startup pending cleanup: immediate={cleared_any}, stale={cleared_stale}"
            )
        return cleared_any, cleared_stale
    except Exception as exc:
        logger.warning(f"{label} Startup pending cleanup failed: {exc}")
        return 0, 0


def is_stop_requested_row(row: Optional[Dict[str, Any]]) -> bool:
    """True when session row requests stop (status=stopped and engine_active=false)."""
    if not row:
        return False
    status = str(row.get("status") or "").strip().lower()
    engine_active = bool(row.get("engine_active", True))
    return status == "stopped" and not engine_active


async def fetch_engine_control_row(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch stop-control fields from autotrade_sessions."""
    s = _client()
    res = await asyncio.to_thread(
        lambda: s.table("autotrade_sessions")
        .select("status,engine_active")
        .eq("telegram_id", int(user_id))
        .limit(1)
        .execute()
    )
    data = getattr(res, "data", None) or []
    return dict(data[0]) if data else None


async def should_stop_engine(
    user_id: int,
    logger: Optional[logging.Logger] = None,
    label: str = "",
) -> bool:
    """
    Poll autotrade stop signal from Supabase.

    Returns False on polling errors (non-fatal).
    """
    try:
        row = await fetch_engine_control_row(int(user_id))
        return is_stop_requested_row(row)
    except Exception as exc:
        if logger is not None:
            logger.debug(f"{label} Stop signal check failed (non-fatal): {exc}")
        return False


async def refresh_runtime_snapshot(
    *,
    now_ts: float,
    next_refresh_ts: float,
    refresh_fn: Callable[[], Any],
    snapshot_fn: Callable[[], Any],
    current_snapshot: Any,
    interval_sec: float = 600.0,
) -> Tuple[float, Any, bool, Optional[str]]:
    """
    Refresh shared runtime snapshot on cadence.

    Returns:
        (new_next_refresh_ts, snapshot, refreshed, error_message)
    """
    if float(now_ts) < float(next_refresh_ts):
        return float(next_refresh_ts), current_snapshot, False, None

    try:
        await asyncio.to_thread(refresh_fn)
        snapshot = await asyncio.to_thread(snapshot_fn)
        return float(now_ts + interval_sec), snapshot, True, None
    except Exception as exc:
        return float(now_ts + interval_sec), current_snapshot, False, str(exc)


async def get_top_volume_pairs(
    *,
    limit: int = 10,
    fallback_pairs: Optional[Sequence[str]] = None,
    logger: Optional[logging.Logger] = None,
    label: str = "",
) -> list[str]:
    """
    Resolve dynamic top-volume symbol set with fallback.

    Returns pair strings (e.g. BTCUSDT).
    """
    try:
        pairs = await asyncio.to_thread(get_ranked_top_volume_pairs, int(limit))
        if pairs:
            return list(pairs)
    except Exception as exc:
        if logger is not None:
            logger.warning(f"{label} Top-volume pair refresh failed: {exc}")

    if fallback_pairs:
        return list(fallback_pairs)
    return []
