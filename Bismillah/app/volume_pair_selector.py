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
}


def _safe_float(v) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _normalize_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper()


def _prune_runtime_untradable_locked(now_ts: float) -> Dict[str, float]:
    runtime_untradable = _state.get("runtime_untradable_until")
    if not isinstance(runtime_untradable, dict):
        runtime_untradable = {}
        _state["runtime_untradable_until"] = runtime_untradable

    expired = [sym for sym, exp in runtime_untradable.items() if _safe_float(exp) <= float(now_ts)]
    for sym in expired:
        runtime_untradable.pop(sym, None)
    return runtime_untradable


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
        quarantined_symbols = set(runtime_untradable.keys())
        cached_pairs = [
            _normalize_symbol(sym)
            for sym in list(_state.get("pairs") or [])
            if _normalize_symbol(sym) and _normalize_symbol(sym) not in quarantined_symbols
        ]
        cache_age = now - float(_state.get("last_refresh_ts", 0.0) or 0.0)
        if cached_pairs and cache_age < REFRESH_TTL_SECONDS and len(cached_pairs) >= limit:
            return cached_pairs[:limit]

    try:
        top, tradable_symbol_count = _fetch_ranked_pairs(limit, quarantined_symbols=quarantined_symbols)
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
            quarantined_symbols = set(runtime_untradable.keys())
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
        }
