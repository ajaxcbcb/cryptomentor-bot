"""
Short-term symbol behavior memory for Decision Tree V2.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any, Dict, Iterable, List

from app.supabase_repo import _client

logger = logging.getLogger(__name__)

_CACHE: Dict[str, Any] = {"ts": 0.0, "symbols": {}}
_TTL_SECONDS = 600.0


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _fetch_recent_trade_rows(limit: int = 1000) -> List[Dict[str, Any]]:
    s = _client()
    res = (
        s.table("autotrade_trades")
        .select("symbol,status,close_reason,pnl_usdt,opened_at,closed_at")
        .order("opened_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(res.data or [])


def _fetch_recent_candidate_rows(limit: int = 1000) -> List[Dict[str, Any]]:
    s = _client()
    try:
        res = (
            s.table("trade_candidates_log")
            .select("symbol,approved,reject_reason,metadata,created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return list(res.data or [])
    except Exception:
        return []


def refresh_symbol_memory(force: bool = False) -> Dict[str, Dict[str, Any]]:
    now = time.time()
    if not force and (now - float(_CACHE.get("ts", 0.0) or 0.0)) < _TTL_SECONDS:
        return dict(_CACHE.get("symbols") or {})

    trades = _fetch_recent_trade_rows(limit=1500)
    candidates = _fetch_recent_candidate_rows(limit=1500)
    per_symbol: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "sample_size": 0,
            "stopout_count": 0,
            "fakeout_count": 0,
            "negative_timeout_count": 0,
            "followthrough_fail_count": 0,
            "avg_slippage_bps": 0.0,
            "wickiness_score": 0.0,
            "last_trade_at": "",
            "cooldown_recommended": False,
            "unstable": False,
        }
    )

    for row in trades:
        symbol = str(row.get("symbol") or "").upper().strip()
        if not symbol:
            continue
        state = per_symbol[symbol]
        state["sample_size"] += 1
        close_reason = str(row.get("close_reason") or row.get("status") or "").strip().lower()
        pnl = _safe_float(row.get("pnl_usdt"), 0.0)
        state["last_trade_at"] = str(row.get("closed_at") or row.get("opened_at") or state["last_trade_at"])
        if close_reason in {"closed_sl", "stale_reconcile"} or pnl < 0:
            state["stopout_count"] += 1
        if close_reason in {"max_hold_time_exceeded", "sideways_max_hold_exceeded"} and pnl < 0:
            state["negative_timeout_count"] += 1

    for row in candidates:
        symbol = str(row.get("symbol") or "").upper().strip()
        if not symbol:
            continue
        state = per_symbol[symbol]
        reject_reason = str(row.get("reject_reason") or "").strip().lower()
        if reject_reason in {"tradeability_below_threshold", "symbol_memory_unstable"}:
            state["fakeout_count"] += 1
        if reject_reason in {"invalid_candidate", "regime_no_trade"}:
            state["followthrough_fail_count"] += 1

    final: Dict[str, Dict[str, Any]] = {}
    for symbol, state in per_symbol.items():
        sample = max(1, int(state["sample_size"]))
        stopout_density = state["stopout_count"] / sample
        fakeout_density = state["fakeout_count"] / sample
        timeout_density = state["negative_timeout_count"] / sample
        followthrough_density = state["followthrough_fail_count"] / sample
        unstable = bool(stopout_density >= 0.60 or fakeout_density >= 0.50 or timeout_density >= 0.40)
        final[symbol] = {
            **state,
            "stopout_density": round(stopout_density, 4),
            "fakeout_density": round(fakeout_density, 4),
            "negative_timeout_density": round(timeout_density, 4),
            "followthrough_fail_density": round(followthrough_density, 4),
            "cooldown_recommended": unstable,
            "unstable": unstable,
        }

    _CACHE["ts"] = now
    _CACHE["symbols"] = final
    return dict(final)


def get_symbol_memory(symbol: str) -> Dict[str, Any]:
    symbols = refresh_symbol_memory(force=False)
    return dict(symbols.get(str(symbol or "").upper().strip()) or {})


def get_symbol_memory_batch(symbols: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    cached = refresh_symbol_memory(force=False)
    out: Dict[str, Dict[str, Any]] = {}
    for symbol in symbols:
        key = str(symbol or "").upper().strip()
        out[key] = dict(cached.get(key) or {})
    return out

