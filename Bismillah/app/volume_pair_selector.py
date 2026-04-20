"""
Global volume-ranked pair selector for Bitunix futures.

Provides a cached top-volume symbol list (USDT pairs) used by both
autotrade (swing) and scalping engines.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Set, Tuple

import requests

logger = logging.getLogger(__name__)

BITUNIX_BASE_URL = (
    os.getenv("BITUNIX_GATEWAY_URL", "").rstrip("/")
    or os.getenv("BITUNIX_BASE_URL", "https://fapi.bitunix.com").rstrip("/")
)
TICKERS_PATH = "/api/v1/futures/market/tickers"
TRADING_PAIRS_PATH = "/api/v1/futures/market/trading_pairs"
REFRESH_TTL_SECONDS = 300
DEFAULT_LIMIT = 10
RUNTIME_UNTRADABLE_TTL_SECONDS = 21600.0  # 6 hours
DYNAMIC_QUARANTINE_TTL_SECONDS = 21600.0
DYNAMIC_QUARANTINE_LOOKBACK_DAYS = 14
DYNAMIC_QUARANTINE_MIN_SAMPLE = 20
DYNAMIC_QUARANTINE_FALLBACK_LAST_N = 30
TIMEOUT_CLOSE_STATUSES = {"max_hold_time_exceeded", "sideways_max_hold_exceeded"}

# Legacy fallback universe (stable, known tradable set in current engines).
DEFAULT_BOOTSTRAP_PAIRS: List[str] = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "DOTUSDT",
    "LINKUSDT",
]

_lock = threading.Lock()
_state: Dict[str, object] = {
    "pairs": [],
    "last_refresh_ts": 0.0,
    "source": "bootstrap",
    "error": None,
    "requested_limit": DEFAULT_LIMIT,
    "runtime_untradable_until": {},
    "tradable_symbol_count": 0,
    "dynamic_quarantine": {},
    "dynamic_quarantine_last_refresh_ts": 0.0,
    "dynamic_quarantine_error": None,
}


def _safe_float(v) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _normalize_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(raw: object) -> datetime | None:
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


def _prune_runtime_untradable_locked(now_ts: float) -> Dict[str, float]:
    runtime_untradable = _state.get("runtime_untradable_until")
    if not isinstance(runtime_untradable, dict):
        runtime_untradable = {}
        _state["runtime_untradable_until"] = runtime_untradable

    expired = [sym for sym, exp in runtime_untradable.items() if _safe_float(exp) <= float(now_ts)]
    for sym in expired:
        runtime_untradable.pop(sym, None)
    return runtime_untradable


def _is_scalping_trade(row: Dict[str, object]) -> bool:
    trade_type = _normalize_symbol(str(row.get("trade_type") or "")).lower()
    timeframe = str(row.get("timeframe") or "").strip().lower()
    return trade_type == "scalping" or timeframe == "5m"


def _select_symbol_quarantine_sample(rows: List[Dict[str, object]], now_utc: datetime) -> List[Dict[str, object]]:
    sorted_rows = sorted(
        rows,
        key=lambda r: _parse_iso(r.get("closed_at")) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    since = now_utc - timedelta(days=DYNAMIC_QUARANTINE_LOOKBACK_DAYS)
    lookback_rows = [
        row
        for row in sorted_rows
        if (_parse_iso(row.get("closed_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= since
    ]
    if len(lookback_rows) >= DYNAMIC_QUARANTINE_FALLBACK_LAST_N:
        return lookback_rows
    return sorted_rows[:DYNAMIC_QUARANTINE_FALLBACK_LAST_N]


def build_dynamic_symbol_quarantine_metrics(
    closed_rows: List[Dict[str, object]],
    *,
    now_utc: datetime | None = None,
) -> Dict[str, Dict[str, object]]:
    now = now_utc or _utc_now()
    per_symbol: Dict[str, List[Dict[str, object]]] = {}
    for row in closed_rows or []:
        if not _is_scalping_trade(row):
            continue
        symbol = _normalize_symbol(row.get("symbol"))
        if not symbol:
            continue
        per_symbol.setdefault(symbol, []).append(dict(row))

    out: Dict[str, Dict[str, object]] = {}
    for symbol, rows in per_symbol.items():
        sample = _select_symbol_quarantine_sample(rows, now_utc=now)
        if not sample:
            continue
        pnl_values = [_safe_float(row.get("pnl_usdt")) for row in sample]
        timeout_count = 0
        negative_timeout_count = 0
        for row in sample:
            reason = str(row.get("close_reason") or row.get("status") or "").strip().lower()
            if reason not in TIMEOUT_CLOSE_STATUSES:
                continue
            timeout_count += 1
            if _safe_float(row.get("pnl_usdt")) < 0.0:
                negative_timeout_count += 1

        sample_size = len(sample)
        net_pnl = float(sum(pnl_values))
        avg_pnl = float(net_pnl / sample_size) if sample_size else 0.0
        timeout_rate = float(timeout_count / sample_size) if sample_size else 0.0
        negative_timeout_rate = float(negative_timeout_count / sample_size) if sample_size else 0.0
        out[symbol] = {
            "symbol": symbol,
            "sample_size": int(sample_size),
            "avg_pnl": round(avg_pnl, 6),
            "net_pnl": round(net_pnl, 6),
            "timeout_rate": round(timeout_rate, 6),
            "negative_timeout_rate": round(negative_timeout_rate, 6),
            "timeout_count": int(timeout_count),
            "negative_timeout_count": int(negative_timeout_count),
            "window": (
                f"{DYNAMIC_QUARANTINE_LOOKBACK_DAYS}d"
                if len(sample) >= DYNAMIC_QUARANTINE_FALLBACK_LAST_N
                else f"last_{len(sample)}"
            ),
        }
    return out


def _should_quarantine_symbol(metrics: Dict[str, object]) -> bool:
    sample_size = int(metrics.get("sample_size", 0) or 0)
    avg_pnl = _safe_float(metrics.get("avg_pnl"))
    negative_timeout_rate = _safe_float(metrics.get("negative_timeout_rate"))
    timeout_rate = _safe_float(metrics.get("timeout_rate"))
    return bool(
        sample_size >= DYNAMIC_QUARANTINE_MIN_SAMPLE
        and avg_pnl < 0.0
        and (negative_timeout_rate >= 0.55 or timeout_rate >= 0.80)
    )


def _is_symbol_recovered(metrics: Dict[str, object]) -> bool:
    sample_size = int(metrics.get("sample_size", 0) or 0)
    avg_pnl = _safe_float(metrics.get("avg_pnl"))
    negative_timeout_rate = _safe_float(metrics.get("negative_timeout_rate"))
    timeout_rate = _safe_float(metrics.get("timeout_rate"))
    return bool(
        sample_size >= DYNAMIC_QUARANTINE_MIN_SAMPLE
        and avg_pnl >= 0.0
        and negative_timeout_rate < 0.55
        and timeout_rate < 0.80
    )


def _build_quarantine_reason(metrics: Dict[str, object]) -> str:
    parts = ["negative_expectancy"]
    if _safe_float(metrics.get("negative_timeout_rate")) >= 0.55:
        parts.append("negative_timeout_rate")
    if _safe_float(metrics.get("timeout_rate")) >= 0.80:
        parts.append("timeout_rate")
    return "+".join(parts)


def compute_dynamic_quarantine_state(
    prev_state: Dict[str, Dict[str, object]],
    symbol_metrics: Dict[str, Dict[str, object]],
    *,
    now_ts: float,
) -> Dict[str, Dict[str, object]]:
    next_state: Dict[str, Dict[str, object]] = {}
    symbols = set(prev_state.keys()) | set(symbol_metrics.keys())
    for symbol in sorted(symbols):
        metrics = dict(symbol_metrics.get(symbol) or {})
        prev = dict(prev_state.get(symbol) or {})

        if _should_quarantine_symbol(metrics):
            next_state[symbol] = {
                **metrics,
                "reason": _build_quarantine_reason(metrics),
                "recovery_windows": 0,
                "quarantine_until_ts": float(now_ts + DYNAMIC_QUARANTINE_TTL_SECONDS),
                "state": "quarantined",
                "updated_at_ts": float(now_ts),
            }
            continue

        if not prev:
            continue

        recovery_windows = int(prev.get("recovery_windows", 0) or 0)
        quarantine_until_ts = float(prev.get("quarantine_until_ts", now_ts) or now_ts)
        recovered = _is_symbol_recovered(metrics)
        if recovered:
            recovery_windows += 1
        else:
            recovery_windows = 0

        if recovered and now_ts >= quarantine_until_ts and recovery_windows >= 2:
            continue

        if not recovered and now_ts >= quarantine_until_ts:
            quarantine_until_ts = float(now_ts + DYNAMIC_QUARANTINE_TTL_SECONDS)

        payload = dict(prev)
        payload.update(metrics or {})
        payload.update({
            "reason": _build_quarantine_reason(metrics or prev),
            "recovery_windows": int(recovery_windows),
            "quarantine_until_ts": float(quarantine_until_ts),
            "state": "recovery_observation" if recovered else "quarantined",
            "updated_at_ts": float(now_ts),
        })
        next_state[symbol] = payload

    return next_state


def _fetch_recent_scalping_closed_rows(limit: int = 4000) -> List[Dict[str, object]]:
    from app.supabase_repo import _client

    s = _client()
    since = (_utc_now() - timedelta(days=DYNAMIC_QUARANTINE_LOOKBACK_DAYS)).isoformat()
    collected: List[Dict[str, object]] = []
    page_size = min(1000, max(200, int(limit)))
    page = 0
    while len(collected) < limit:
        frm = page * page_size
        to = frm + page_size - 1
        res = (
            s.table("autotrade_trades")
            .select("symbol,status,close_reason,pnl_usdt,closed_at,trade_type,timeframe")
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


def refresh_dynamic_symbol_quarantine(now_ts: float | None = None) -> Dict[str, Dict[str, object]]:
    now = float(time.time() if now_ts is None else now_ts)
    try:
        rows = _fetch_recent_scalping_closed_rows(limit=4000)
        metrics = build_dynamic_symbol_quarantine_metrics(
            rows,
            now_utc=datetime.fromtimestamp(now, tz=timezone.utc),
        )
        with _lock:
            prev = dict(_state.get("dynamic_quarantine") or {})
            nxt = compute_dynamic_quarantine_state(prev, metrics, now_ts=now)
            _state["dynamic_quarantine"] = nxt
            _state["dynamic_quarantine_last_refresh_ts"] = now
            _state["dynamic_quarantine_error"] = None
            return dict(nxt)
    except Exception as exc:
        logger.warning("[VolumeSelector] dynamic quarantine refresh failed: %s", exc)
        with _lock:
            _state["dynamic_quarantine_last_refresh_ts"] = now
            _state["dynamic_quarantine_error"] = str(exc)
            return dict(_state.get("dynamic_quarantine") or {})


def _fetch_open_tradable_symbols() -> Set[str]:
    url = f"{BITUNIX_BASE_URL}{TRADING_PAIRS_PATH}"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    payload = resp.json() or {}

    if int(payload.get("code", -1)) != 0:
        raise RuntimeError(f"Bitunix trading_pairs error: code={payload.get('code')} msg={payload.get('msg')}")

    rows = payload.get("data") or []
    tradable: Set[str] = set()
    for row in rows:
        symbol = _normalize_symbol(row.get("symbol"))
        if not symbol.endswith("USDT"):
            continue
        quote = _normalize_symbol(row.get("quote"))
        if quote and quote != "USDT":
            continue
        status = _normalize_symbol(row.get("symbolStatus"))
        if status != "OPEN":
            continue
        tradable.add(symbol)

    if not tradable:
        raise RuntimeError("Bitunix trading_pairs returned empty tradable symbol set")
    return tradable


def _fetch_ranked_pairs(limit: int, quarantined_symbols: Set[str] | None = None) -> Tuple[List[str], int]:
    tradable_symbols = _fetch_open_tradable_symbols()
    quarantined_symbols = set(quarantined_symbols or set())

    url = f"{BITUNIX_BASE_URL}{TICKERS_PATH}"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    payload = resp.json() or {}

    if int(payload.get("code", -1)) != 0:
        raise RuntimeError(f"Bitunix ticker error: code={payload.get('code')} msg={payload.get('msg')}")

    rows = payload.get("data") or []
    ranked = []
    for row in rows:
        symbol = _normalize_symbol(row.get("symbol"))
        if not symbol.endswith("USDT"):
            continue
        if symbol not in tradable_symbols:
            continue
        if symbol in quarantined_symbols:
            continue
        vol = _safe_float(row.get("quoteVol"))
        if vol <= 0:
            continue
        ranked.append((symbol, vol))

    if not ranked:
        raise RuntimeError("Bitunix ticker returned no ranked symbols after tradability filters")

    ranked.sort(key=lambda x: x[1], reverse=True)
    top = []
    seen = set()
    for symbol, _ in ranked:
        if symbol in seen:
            continue
        seen.add(symbol)
        top.append(symbol)
        if len(top) >= limit:
            break
    return top, len(tradable_symbols)


def mark_runtime_untradable_symbol(symbol: str, ttl_sec: float = RUNTIME_UNTRADABLE_TTL_SECONDS) -> float:
    """
    Quarantine a symbol from the dynamic volume universe for a runtime TTL.

    Returns the quarantine expiry timestamp.
    """
    norm = _normalize_symbol(symbol)
    if not norm:
        return time.time()
    now_ts = time.time()
    expires_at = float(now_ts + max(0.0, float(ttl_sec)))
    with _lock:
        runtime_untradable = _prune_runtime_untradable_locked(now_ts)
        runtime_untradable[norm] = expires_at
    return expires_at


def get_ranked_top_volume_pairs(limit: int = DEFAULT_LIMIT) -> List[str]:
    limit = max(1, int(limit or DEFAULT_LIMIT))
    now = time.time()

    with _lock:
        runtime_untradable = _prune_runtime_untradable_locked(now)
        dynamic_quarantine = dict(_state.get("dynamic_quarantine") or {})
        quarantined_symbols = set(runtime_untradable.keys()) | set(dynamic_quarantine.keys())
        cached_pairs = [
            _normalize_symbol(sym)
            for sym in list(_state.get("pairs") or [])
            if _normalize_symbol(sym) and _normalize_symbol(sym) not in quarantined_symbols
        ]
        cache_age = now - float(_state.get("last_refresh_ts", 0.0) or 0.0)
        if cached_pairs and cache_age < REFRESH_TTL_SECONDS and len(cached_pairs) >= limit:
            return cached_pairs[:limit]

    dynamic_quarantine = refresh_dynamic_symbol_quarantine(now_ts=now)
    quarantined_symbols = set(dynamic_quarantine.keys())

    try:
        top, tradable_symbol_count = _fetch_ranked_pairs(
            limit,
            quarantined_symbols=quarantined_symbols | set((_state.get("runtime_untradable_until") or {}).keys()),
        )
        with _lock:
            _state["pairs"] = top
            _state["last_refresh_ts"] = now
            _state["source"] = "fresh"
            _state["error"] = None
            _state["requested_limit"] = limit
            _state["tradable_symbol_count"] = int(tradable_symbol_count)

        logger.info(
            "[VolumeSelector] refresh_success ts=%s source=fresh pair_count=%s pairs=%s",
            int(now),
            len(top),
            ",".join(top),
        )
        return top
    except Exception as e:
        with _lock:
            runtime_untradable = _prune_runtime_untradable_locked(now)
            dynamic_quarantine = dict(_state.get("dynamic_quarantine") or {})
            quarantined_symbols = set(runtime_untradable.keys()) | set(dynamic_quarantine.keys())
            cached_pairs = [
                _normalize_symbol(sym)
                for sym in list(_state.get("pairs") or [])
                if _normalize_symbol(sym) and _normalize_symbol(sym) not in quarantined_symbols
            ]
            if cached_pairs:
                _state["source"] = "cache_fallback"
                _state["error"] = str(e)
                logger.warning(
                    "[VolumeSelector] refresh_failed ts=%s source=cache_fallback pair_count=%s error=%s",
                    int(now),
                    len(cached_pairs),
                    e,
                )
                return cached_pairs[:limit]

            bootstrap = [
                sym for sym in DEFAULT_BOOTSTRAP_PAIRS
                if _normalize_symbol(sym) not in quarantined_symbols
            ][:limit]
            _state["pairs"] = bootstrap
            _state["last_refresh_ts"] = now
            _state["source"] = "bootstrap_fallback"
            _state["error"] = str(e)
            _state["requested_limit"] = limit

            logger.warning(
                "[VolumeSelector] refresh_failed ts=%s source=bootstrap_fallback pair_count=%s error=%s",
                int(now),
                len(bootstrap),
                e,
            )
            return bootstrap


def get_selector_health() -> Dict[str, object]:
    with _lock:
        dynamic_quarantine = dict(_state.get("dynamic_quarantine") or {})
        return {
            "last_refresh_ts": _state.get("last_refresh_ts"),
            "source": _state.get("source"),
            "pair_count": len(_state.get("pairs") or []),
            "pairs": list(_state.get("pairs") or []),
            "error": _state.get("error"),
            "requested_limit": _state.get("requested_limit"),
            "refresh_ttl_seconds": REFRESH_TTL_SECONDS,
            "runtime_untradable_count": len(_prune_runtime_untradable_locked(time.time())),
            "runtime_untradable_symbols": sorted(list((_state.get("runtime_untradable_until") or {}).keys())),
            "tradable_symbol_count": int(_state.get("tradable_symbol_count") or 0),
            "dynamic_quarantine_last_refresh_ts": _state.get("dynamic_quarantine_last_refresh_ts"),
            "dynamic_quarantine_error": _state.get("dynamic_quarantine_error"),
            "quarantined_symbol_count": len(dynamic_quarantine),
            "quarantined_symbols": [
                {
                    "symbol": symbol,
                    "reason": str(payload.get("reason") or ""),
                    "sample_size": int(payload.get("sample_size", 0) or 0),
                    "avg_pnl": float(payload.get("avg_pnl", 0.0) or 0.0),
                    "net_pnl": float(payload.get("net_pnl", 0.0) or 0.0),
                    "timeout_rate": float(payload.get("timeout_rate", 0.0) or 0.0),
                    "negative_timeout_rate": float(payload.get("negative_timeout_rate", 0.0) or 0.0),
                    "recovery_windows": int(payload.get("recovery_windows", 0) or 0),
                    "quarantine_until_ts": float(payload.get("quarantine_until_ts", 0.0) or 0.0),
                    "state": str(payload.get("state") or "quarantined"),
                }
                for symbol, payload in sorted(dynamic_quarantine.items())
            ],
        }
