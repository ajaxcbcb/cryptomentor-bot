"""
Shared execution/persistence helpers for swing + scalping engines.

This module keeps shared pre-entry and post-close behavior aligned while
preserving strategy-specific decision logic in each engine.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Tuple

from app.risk_audit import emit_order_open_risk_audit, format_risk_audit_line
from app.win_playbook import compute_playbook_match_from_reasons, evaluate_signal_risk


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _signal_reasons(raw_reasons: Any) -> list[str]:
    if isinstance(raw_reasons, list):
        return [str(x) for x in raw_reasons if str(x).strip()]
    if raw_reasons is None:
        return []
    txt = str(raw_reasons).strip()
    return [txt] if txt else []


def _set_signal_field(signal: Any, key: str, value: Any) -> None:
    if isinstance(signal, dict):
        signal[key] = value
    else:
        setattr(signal, key, value)


def _get_signal_field(signal: Any, key: str, default: Any = None) -> Any:
    if isinstance(signal, dict):
        return signal.get(key, default)
    return getattr(signal, key, default)


async def evaluate_and_apply_playbook_risk(
    *,
    signal: Any,
    base_risk_pct: float,
    raw_reasons: Optional[Iterable[Any]] = None,
    logger: Optional[logging.Logger] = None,
    label: str = "",
) -> Dict[str, Any]:
    """
    Evaluate win-playbook runtime risk overlay and apply fields onto a signal.

    Applied fields:
      - playbook_match_score
      - playbook_match_tags
      - effective_risk_pct
      - risk_overlay_pct
    """
    reasons = _signal_reasons(list(raw_reasons) if raw_reasons is not None else _get_signal_field(signal, "reasons", []))
    fallback_score = _as_float(_get_signal_field(signal, "playbook_match_score", 0.0), 0.0)
    fallback_tags = list(_get_signal_field(signal, "playbook_match_tags", []) or [])

    try:
        risk_eval = await asyncio.to_thread(
            evaluate_signal_risk,
            float(base_risk_pct),
            reasons,
        )
    except Exception as exc:
        if logger is not None:
            logger.warning(f"{label} Win playbook eval failed, fallback to base risk: {exc}")
        risk_eval = {
            "effective_risk_pct": float(base_risk_pct),
            "risk_overlay_pct": 0.0,
            "playbook_match_score": float(fallback_score),
            "playbook_match_tags": list(fallback_tags),
            "guardrails_healthy": False,
            "overlay_action": "fallback_base_risk",
        }

    effective_risk_pct = _as_float(risk_eval.get("effective_risk_pct", base_risk_pct), float(base_risk_pct))
    risk_overlay_pct = _as_float(risk_eval.get("risk_overlay_pct", 0.0), 0.0)
    playbook_match_score = _as_float(risk_eval.get("playbook_match_score", fallback_score), fallback_score)
    playbook_match_tags = list(risk_eval.get("playbook_match_tags", fallback_tags) or [])

    _set_signal_field(signal, "playbook_match_score", playbook_match_score)
    _set_signal_field(signal, "playbook_match_tags", playbook_match_tags)
    _set_signal_field(signal, "effective_risk_pct", effective_risk_pct)
    _set_signal_field(signal, "risk_overlay_pct", risk_overlay_pct)

    return {
        "effective_risk_pct": effective_risk_pct,
        "risk_overlay_pct": risk_overlay_pct,
        "playbook_match_score": playbook_match_score,
        "playbook_match_tags": playbook_match_tags,
        "guardrails_healthy": bool(risk_eval.get("guardrails_healthy", False)),
        "overlay_action": risk_eval.get("overlay_action"),
    }


def format_and_emit_order_open_risk_audit(
    *,
    logger: logging.Logger,
    user_id: int,
    symbol: str,
    side: str,
    order_id: str,
    base_risk_pct: float,
    overlay_pct: float,
    effective_risk_pct: float,
    implied_risk_usdt: float,
) -> str:
    """
    Shared risk-audit formatting + structured emission.

    Returns:
        Human-readable risk audit line for user notification.
    """
    line = format_risk_audit_line(
        base_risk_pct=float(base_risk_pct),
        overlay_pct=float(overlay_pct),
        effective_risk_pct=float(effective_risk_pct),
        implied_risk_usdt=float(implied_risk_usdt),
    )
    emit_order_open_risk_audit(
        logger,
        user_id=int(user_id),
        symbol=str(symbol),
        side=str(side),
        order_id=str(order_id or "-"),
        base_risk_pct=float(base_risk_pct),
        overlay_pct=float(overlay_pct),
        effective_risk_pct=float(effective_risk_pct),
        implied_risk_usdt=float(implied_risk_usdt),
    )
    return line


async def coordinator_set_pending(coordinator: Any, user_id: int, symbol: str, strategy: Any) -> None:
    await coordinator.set_pending(int(user_id), str(symbol), strategy)


async def coordinator_clear_pending(
    coordinator: Any,
    user_id: int,
    symbol: str,
    reason: str = "explicit_clear",
) -> None:
    await coordinator.clear_pending(int(user_id), str(symbol), reason=reason)


async def coordinator_confirm_open(
    coordinator: Any,
    *,
    user_id: int,
    symbol: str,
    strategy: Any,
    side: Any,
    size: float,
    entry_price: float,
    exchange_position_id: Optional[str] = None,
) -> None:
    await coordinator.confirm_open(
        user_id=int(user_id),
        symbol=str(symbol),
        strategy=strategy,
        side=side,
        size=float(size),
        entry_price=float(entry_price),
        exchange_position_id=exchange_position_id,
    )


async def coordinator_confirm_closed(
    coordinator: Any,
    *,
    user_id: int,
    symbol: str,
    now_ts: Optional[float] = None,
) -> None:
    await coordinator.confirm_closed(
        user_id=int(user_id),
        symbol=str(symbol),
        now_ts=float(now_ts if now_ts is not None else datetime.utcnow().timestamp()),
    )


def build_cumulative_close_update_payload(
    *,
    open_row: Dict[str, Any],
    position: Any,
    close_price: float,
    pnl: float,
    close_reason: str,
    loss_reasoning: str = "",
    win_metadata: Optional[Dict[str, Any]] = None,
    playbook_snapshot: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], float, float]:
    """
    Build close-update payload with cumulative PnL and win/loss metadata.

    Returns:
        (payload, cumulative_pnl, partial_realized)
    """
    partial_realized = _as_float(open_row.get("profit_tp1"), 0.0) + _as_float(open_row.get("profit_tp2"), 0.0) + _as_float(open_row.get("profit_tp3"), 0.0)
    final_leg_pnl = _as_float(pnl, 0.0)
    cumulative_pnl = float(final_leg_pnl + partial_realized)

    base_playbook_score = _as_float(
        open_row.get("playbook_match_score", _get_signal_field(position, "playbook_match_score", 0.0)),
        0.0,
    )
    base_effective_risk = _as_float(
        open_row.get("effective_risk_pct", _get_signal_field(position, "effective_risk_pct", 0.0)),
        0.0,
    )
    base_overlay = _as_float(
        open_row.get("risk_overlay_pct", _get_signal_field(position, "risk_overlay_pct", 0.0)),
        0.0,
    )

    payload: Dict[str, Any] = {
        "close_price": float(close_price),
        "exit_price": float(close_price),
        "pnl_usdt": cumulative_pnl,
        "close_reason": str(close_reason),
        "status": str(close_reason),
        "qty": 0.0,
        "quantity": 0.0,
        "remaining_quantity": 0.0,
        "closed_at": datetime.now(timezone.utc).isoformat(),
        "playbook_match_score": base_playbook_score,
        "effective_risk_pct": base_effective_risk,
        "risk_overlay_pct": base_overlay,
    }

    if loss_reasoning:
        payload["loss_reasoning"] = str(loss_reasoning)
    elif cumulative_pnl < 0:
        payload["loss_reasoning"] = (
            f"auto_loss_reason: close_reason={close_reason}; pnl={cumulative_pnl:+.6f}"
        )

    if win_metadata:
        if win_metadata.get("playbook_match_score") is not None:
            payload["playbook_match_score"] = _as_float(win_metadata.get("playbook_match_score"), payload["playbook_match_score"])
        if win_metadata.get("effective_risk_pct") is not None:
            payload["effective_risk_pct"] = _as_float(win_metadata.get("effective_risk_pct"), payload["effective_risk_pct"])
        if win_metadata.get("risk_overlay_pct") is not None:
            payload["risk_overlay_pct"] = _as_float(win_metadata.get("risk_overlay_pct"), payload["risk_overlay_pct"])
        if win_metadata.get("win_reason_tags") is not None:
            payload["win_reason_tags"] = list(win_metadata.get("win_reason_tags") or [])
        if win_metadata.get("win_reasoning"):
            payload["win_reasoning"] = str(win_metadata.get("win_reasoning"))

    is_win_close = cumulative_pnl > 0 and close_reason in {"closed_tp", "closed_tp3", "closed_flip"}
    if cumulative_pnl > 0 and not payload.get("win_reasoning"):
        from app.trade_history import build_win_reasoning

        entry_reasons = list(
            _get_signal_field(position, "entry_reasons", open_row.get("entry_reasons", [])) or []
        )
        trade_ctx = {
            "symbol": open_row.get("symbol", _get_signal_field(position, "symbol", "")),
            "side": "LONG" if str(_get_signal_field(position, "side", open_row.get("side", "LONG"))).upper() in {"BUY", "LONG"} else "SHORT",
            "entry_price": _as_float(open_row.get("entry_price", _get_signal_field(position, "entry_price", 0.0)), 0.0),
            "exit_price": float(close_price),
            "pnl_usdt": cumulative_pnl,
            "close_reason": str(close_reason),
            "entry_reasons": entry_reasons,
            "confidence": _as_float(open_row.get("confidence", 0), 0.0),
            "rr_ratio": _as_float(open_row.get("rr_ratio", 0), 0.0),
        }

        if is_win_close and playbook_snapshot is not None:
            match_meta = compute_playbook_match_from_reasons(entry_reasons, playbook_snapshot)
            payload["win_reasoning"] = build_win_reasoning(
                trade_ctx,
                playbook_tags=match_meta.get("matched_tags", []),
                playbook_score=match_meta.get("playbook_match_score"),
            )
            payload["win_reason_tags"] = list(match_meta.get("matched_tags", []))
            payload["playbook_match_score"] = _as_float(
                match_meta.get("playbook_match_score", payload["playbook_match_score"]),
                payload["playbook_match_score"],
            )
            payload["effective_risk_pct"] = _as_float(
                _get_signal_field(position, "effective_risk_pct", payload["effective_risk_pct"]),
                payload["effective_risk_pct"],
            )
            payload["risk_overlay_pct"] = _as_float(
                _get_signal_field(position, "risk_overlay_pct", payload["risk_overlay_pct"]),
                payload["risk_overlay_pct"],
            )
        else:
            payload["win_reasoning"] = build_win_reasoning(trade_ctx)

    return payload, cumulative_pnl, partial_realized
