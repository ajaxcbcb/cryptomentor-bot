"""
Advisory position-state labeling for Decision Tree V2.
"""

from __future__ import annotations

import time
from typing import Any, Dict


def label_position_state(
    *,
    position: Any,
    user_profile: Any = None,
    current_price: float | None = None,
    elapsed_seconds: float | None = None,
) -> Dict[str, Any]:
    entry = float(getattr(position, "entry_price", 0.0) or 0.0)
    tp = float(getattr(position, "tp_price", getattr(position, "tp1_price", 0.0)) or 0.0)
    sl = float(getattr(position, "sl_price", 0.0) or 0.0)
    side = str(getattr(position, "side", "BUY") or "BUY").upper()
    px = float(current_price if current_price is not None else entry)
    now_elapsed = float(elapsed_seconds if elapsed_seconds is not None else max(0.0, time.time() - float(getattr(position, "opened_at", time.time()) or time.time())))
    risk = abs(entry - sl)
    progress_r = 0.0
    if risk > 0:
        if side in {"BUY", "LONG"}:
            progress_r = (px - entry) / risk
        else:
            progress_r = (entry - px) / risk
    state = "fresh_entry"
    if progress_r >= 1.0:
        state = "expanding"
    elif progress_r >= 0.25:
        state = "validated"
    elif progress_r <= -0.5:
        state = "at_risk"
    elif now_elapsed > 0.75 * float(getattr(position, "max_hold_until", now_elapsed + 1) - float(getattr(position, "opened_at", 0.0) or 0.0)):
        state = "stalling"
    if progress_r >= 3.0:
        state = "runner"
    runner_allowed = bool(getattr(user_profile, "allow_runner_mode", False)) and state in {"validated", "expanding", "runner"}
    return {
        "state": state,
        "progress_r": round(progress_r, 4),
        "runner_allowed": runner_allowed,
        "notes": ["advisory_only"],
    }

