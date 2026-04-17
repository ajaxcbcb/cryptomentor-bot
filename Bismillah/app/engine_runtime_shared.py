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
import logging
import time
from typing import Any, Callable, Dict, MutableMapping, Optional, Sequence, Tuple

from app.supabase_repo import _client
from app.volume_pair_selector import get_ranked_top_volume_pairs


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
