"""
Decision Tree V2 configuration and feature flags.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Dict


def _env_bool(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, "true" if default else "false") or "").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def _env_str(name: str, default: str) -> str:
    return str(os.getenv(name, default) or default).strip()


def _deep_update(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in (src or {}).items():
        if isinstance(value, dict) and isinstance(dst.get(key), dict):
            _deep_update(dst[key], value)
        else:
            dst[key] = value
    return dst


BASE_CONFIG: Dict[str, Any] = {
    "mode": _env_str("DECISION_TREE_V2_MODE", "legacy").lower(),
    "apply_to": {
        "swing": _env_bool("DECISION_TREE_V2_APPLY_TO_SWING", True),
        "scalping": _env_bool("DECISION_TREE_V2_APPLY_TO_SCALPING", True),
        "mixed": _env_bool("DECISION_TREE_V2_APPLY_TO_MIXED", True),
    },
    "failopen_to_legacy": _env_bool("DECISION_TREE_V2_FAILOPEN_TO_LEGACY", True),
    "log_all_candidates": _env_bool("DECISION_TREE_V2_LOG_ALL_CANDIDATES", True),
    "position_state_mode": _env_str("DECISION_TREE_V2_POSITION_STATE_MODE", "advisory").lower(),
    "scoring": {
        "quality_signal_confidence": 0.40,
        "quality_tradeability": 0.25,
        "quality_approval": 0.20,
        "quality_user_segment": 0.15,
        "community_weight": 0.05,
        "portfolio_penalty_max": 0.35,
    },
    "tiers": {
        "nano": {
            "min_equity": 0.0,
            "max_equity": 99.99,
            "max_positions": 1,
            "max_cluster_exposure": 0.25,
            "max_effective_risk_pct": 0.50,
            "min_quality_score": 0.82,
            "min_tradeability_score": 0.78,
            "max_daily_new_entries": 1,
            "frequency_throttle_minutes": 180,
            "allow_runner_mode": False,
            "allow_fragile_setups": False,
            "allow_expert_only": False,
        },
        "micro": {
            "min_equity": 100.0,
            "max_equity": 499.99,
            "max_positions": 1,
            "max_cluster_exposure": 0.30,
            "max_effective_risk_pct": 0.75,
            "min_quality_score": 0.78,
            "min_tradeability_score": 0.74,
            "max_daily_new_entries": 2,
            "frequency_throttle_minutes": 120,
            "allow_runner_mode": False,
            "allow_fragile_setups": False,
            "allow_expert_only": False,
        },
        "small": {
            "min_equity": 500.0,
            "max_equity": 1999.99,
            "max_positions": 2,
            "max_cluster_exposure": 0.40,
            "max_effective_risk_pct": 1.25,
            "min_quality_score": 0.74,
            "min_tradeability_score": 0.70,
            "max_daily_new_entries": 4,
            "frequency_throttle_minutes": 90,
            "allow_runner_mode": False,
            "allow_fragile_setups": False,
            "allow_expert_only": False,
        },
        "medium": {
            "min_equity": 2000.0,
            "max_equity": 9999.99,
            "max_positions": 3,
            "max_cluster_exposure": 0.50,
            "max_effective_risk_pct": 2.00,
            "min_quality_score": 0.70,
            "min_tradeability_score": 0.66,
            "max_daily_new_entries": 6,
            "frequency_throttle_minutes": 60,
            "allow_runner_mode": False,
            "allow_fragile_setups": False,
            "allow_expert_only": True,
            "expert_only_min_quality": 0.85,
        },
        "large": {
            "min_equity": 10000.0,
            "max_equity": 49999.99,
            "max_positions": 4,
            "max_cluster_exposure": 0.60,
            "max_effective_risk_pct": 3.00,
            "min_quality_score": 0.66,
            "min_tradeability_score": 0.62,
            "max_daily_new_entries": 8,
            "frequency_throttle_minutes": 30,
            "allow_runner_mode": True,
            "allow_fragile_setups": True,
            "allow_expert_only": True,
        },
        "whale": {
            "min_equity": 50000.0,
            "max_equity": 1_000_000_000.0,
            "max_positions": 4,
            "max_cluster_exposure": 0.60,
            "max_effective_risk_pct": 5.00,
            "min_quality_score": 0.62,
            "min_tradeability_score": 0.58,
            "max_daily_new_entries": 10,
            "frequency_throttle_minutes": 15,
            "allow_runner_mode": True,
            "allow_fragile_setups": True,
            "allow_expert_only": True,
        },
    },
    "drawdown_tightening": {
        "nano": 0.08,
        "micro": 0.08,
        "small": 0.10,
        "medium": 0.10,
        "large": 0.12,
        "whale": 0.12,
        "quality_bump": 0.04,
        "tradeability_bump": 0.04,
        "daily_entries_multiplier": 0.50,
        "risk_multiplier": 0.75,
    },
    "rr_thresholds": {
        "swing": {
            "trend_continuation": 1.6,
            "breakout_expansion": 1.8,
            "range_mean_reversion": 999.0,
            "high_volatility_unstable": 999.0,
            "no_trade": 999.0,
        },
        "scalping": {
            "trend_continuation": 1.5,
            "breakout_expansion": 1.5,
            "range_mean_reversion": 1.1,
            "high_volatility_unstable": 999.0,
            "no_trade": 999.0,
        },
    },
}


def get_config() -> Dict[str, Any]:
    config = deepcopy(BASE_CONFIG)
    config["mode"] = _env_str("DECISION_TREE_V2_MODE", str(config.get("mode", "legacy"))).lower()
    config["apply_to"] = {
        "swing": _env_bool("DECISION_TREE_V2_APPLY_TO_SWING", bool((config.get("apply_to") or {}).get("swing", True))),
        "scalping": _env_bool("DECISION_TREE_V2_APPLY_TO_SCALPING", bool((config.get("apply_to") or {}).get("scalping", True))),
        "mixed": _env_bool("DECISION_TREE_V2_APPLY_TO_MIXED", bool((config.get("apply_to") or {}).get("mixed", True))),
    }
    config["failopen_to_legacy"] = _env_bool("DECISION_TREE_V2_FAILOPEN_TO_LEGACY", bool(config.get("failopen_to_legacy", True)))
    config["log_all_candidates"] = _env_bool("DECISION_TREE_V2_LOG_ALL_CANDIDATES", bool(config.get("log_all_candidates", True)))
    config["position_state_mode"] = _env_str("DECISION_TREE_V2_POSITION_STATE_MODE", str(config.get("position_state_mode", "advisory"))).lower()
    raw_override = str(os.getenv("DECISION_TREE_V2_CONFIG_JSON", "") or "").strip()
    if raw_override:
        try:
            parsed = json.loads(raw_override)
            if isinstance(parsed, dict):
                _deep_update(config, parsed)
        except Exception:
            pass
    config["mode"] = str(config.get("mode", "legacy") or "legacy").strip().lower()
    if config["mode"] not in {"legacy", "shadow", "live"}:
        config["mode"] = "legacy"
    return config


def get_v2_mode() -> str:
    return str(get_config().get("mode", "legacy"))


def is_v2_enabled() -> bool:
    return get_v2_mode() in {"shadow", "live"}


def is_live_mode() -> bool:
    return get_v2_mode() == "live"


def should_apply(engine: str, *, mixed_mode: bool = False) -> bool:
    cfg = get_config()
    if cfg.get("mode") == "legacy":
        return False
    apply_to = dict(cfg.get("apply_to") or {})
    if mixed_mode and not bool(apply_to.get("mixed", True)):
        return False
    key = "scalping" if str(engine).strip().lower() in {"scalp", "scalping"} else "swing"
    return bool(apply_to.get(key, True))
