"""
Pair Strategy Router
--------------------
Assigns dynamic top-volume pairs to swing vs scalping strategy owners.

Policy:
- Universe source: dynamic top-volume pairs (default top 10)
- Classifier: market sentiment detector per symbol
- Stickiness: assignments stay fixed for 10 minutes per user
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from app.engine_runtime_shared import get_top_volume_pairs
from app.market_sentiment_detector import detect_market_condition

logger = logging.getLogger(__name__)

ROUTER_STICKY_SECONDS = 600.0

_router_cache: Dict[int, Dict[str, Any]] = {}
_router_locks: Dict[int, asyncio.Lock] = {}


def _get_lock(user_id: int) -> asyncio.Lock:
    uid = int(user_id)
    if uid not in _router_locks:
        _router_locks[uid] = asyncio.Lock()
    return _router_locks[uid]


def _normalize_pair(symbol: str) -> str:
    pair = str(symbol or "").strip().upper().replace("/", "")
    if not pair:
        return ""
    if pair.endswith("USDT"):
        return pair
    return f"{pair}USDT"


def _pair_base(symbol: str) -> str:
    pair = _normalize_pair(symbol)
    if pair.endswith("USDT"):
        return pair[:-4]
    return pair


async def _classify_symbol_mode(symbol: str) -> str:
    """
    Return classifier recommendation for one symbol as 'scalping' or 'swing'.
    Defaults to swing on any failure/unknown.
    """
    base = _pair_base(symbol)
    if not base:
        return "swing"
    try:
        result = await asyncio.to_thread(detect_market_condition, base)
        mode = str((result or {}).get("recommended_mode") or "").strip().lower()
        if mode in ("scalping", "swing"):
            return mode
    except Exception as exc:
        logger.debug("[PairRouter] classifier failed for %s: %s", symbol, exc)
    return "swing"


def _is_cache_fresh(payload: Optional[Dict[str, Any]], now_ts: float, limit: int) -> bool:
    if not payload:
        return False
    as_of_ts = float(payload.get("as_of_ts", 0.0) or 0.0)
    cached_limit = int(payload.get("limit", 0) or 0)
    if cached_limit != int(limit):
        return False
    return (now_ts - as_of_ts) < ROUTER_STICKY_SECONDS


async def get_mixed_pair_assignments(
    user_id: int,
    *,
    limit: int = 10,
    fallback_pairs: Optional[Sequence[str]] = None,
    logger_override: Optional[logging.Logger] = None,
    label: str = "",
) -> Dict[str, Any]:
    """
    Return per-user pair assignments for mixed mode.

    Shape:
    {
      "swing": ["BTCUSDT", ...],
      "scalp": ["ETHUSDT", ...],
      "ranked_pairs": [...],
      "as_of_ts": 1710000000.0,
      "as_of_iso": "...",
      "limit": 10,
      "sticky_seconds": 600
    }
    """
    uid = int(user_id)
    log = logger_override or logger
    lock = _get_lock(uid)
    limit = max(1, int(limit or 10))

    async with lock:
        now_ts = time.time()
        cached = _router_cache.get(uid)
        if _is_cache_fresh(cached, now_ts, limit=limit):
            return {
                **cached,
                "swing": list(cached.get("swing") or []),
                "scalp": list(cached.get("scalp") or []),
                "ranked_pairs": list(cached.get("ranked_pairs") or []),
            }

        ranked_pairs = await get_top_volume_pairs(
            limit=limit,
            fallback_pairs=list(fallback_pairs or []),
            logger=log,
            label=label or f"[PairRouter:{uid}]",
        )
        ranked_pairs = [_normalize_pair(p) for p in (ranked_pairs or []) if _normalize_pair(p)]

        if not ranked_pairs:
            payload = {
                "swing": [],
                "scalp": [],
                "ranked_pairs": [],
                "as_of_ts": now_ts,
                "as_of_iso": datetime.utcnow().isoformat(),
                "limit": limit,
                "sticky_seconds": int(ROUTER_STICKY_SECONDS),
            }
            _router_cache[uid] = payload
            return payload

        modes = await asyncio.gather(
            *[_classify_symbol_mode(pair) for pair in ranked_pairs],
            return_exceptions=True,
        )
        swing: List[str] = []
        scalp: List[str] = []
        for pair, mode in zip(ranked_pairs, modes):
            resolved_mode = "swing"
            if isinstance(mode, Exception):
                resolved_mode = "swing"
            else:
                mode_str = str(mode or "").strip().lower()
                if mode_str in ("scalping", "swing"):
                    resolved_mode = mode_str
            if resolved_mode == "scalping":
                scalp.append(pair)
            else:
                swing.append(pair)

        payload = {
            "swing": swing,
            "scalp": scalp,
            "ranked_pairs": ranked_pairs,
            "as_of_ts": now_ts,
            "as_of_iso": datetime.utcnow().isoformat(),
            "limit": limit,
            "sticky_seconds": int(ROUTER_STICKY_SECONDS),
        }
        _router_cache[uid] = payload
        return {
            **payload,
            "swing": list(swing),
            "scalp": list(scalp),
            "ranked_pairs": list(ranked_pairs),
        }


async def get_mixed_symbols_for_owner(
    user_id: int,
    owner: str,
    *,
    limit: int = 10,
    fallback_pairs: Optional[Sequence[str]] = None,
    logger_override: Optional[logging.Logger] = None,
    label: str = "",
) -> List[str]:
    side = "scalp" if str(owner or "").strip().lower() in {"scalp", "scalping"} else "swing"
    assignments = await get_mixed_pair_assignments(
        user_id=int(user_id),
        limit=limit,
        fallback_pairs=fallback_pairs,
        logger_override=logger_override,
        label=label,
    )
    return list(assignments.get(side) or [])


def reset_pair_strategy_router_for_testing() -> None:
    _router_cache.clear()
    _router_locks.clear()
