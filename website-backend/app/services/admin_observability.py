from __future__ import annotations

import csv
import importlib.util
import io
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.db.supabase import _client

_ROOT = Path(__file__).resolve().parents[3]
_BISMILLAH = _ROOT / "Bismillah"
_BISMILLAH_APP = _BISMILLAH / "app"

if str(_BISMILLAH) in sys.path:
    sys.path.remove(str(_BISMILLAH))
sys.path.insert(0, str(_BISMILLAH))
if str(_BISMILLAH_APP) not in sys.path:
    sys.path.insert(1, str(_BISMILLAH_APP))


def _load_bismillah_submodule(rel_name: str, alias: str):
    short_key = f"app.{rel_name}"
    if short_key in sys.modules:
        return sys.modules[short_key]

    file_path = _BISMILLAH_APP / f"{rel_name}.py"
    if not file_path.is_file():
        return None

    spec = importlib.util.spec_from_file_location(alias, str(file_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    sys.modules[short_key] = mod
    spec.loader.exec_module(mod)
    return mod


def _get_dashboard_module():
    module_key = "bismillah.app.decision_tree_v2_live_dashboard"
    if module_key in sys.modules:
        return sys.modules[module_key]

    for submod in ("supabase_repo", "volume_pair_selector"):
        _load_bismillah_submodule(submod, f"bismillah.app.{submod}")
    return _load_bismillah_submodule(
        "decision_tree_v2_live_dashboard",
        module_key,
    )


def _get_autosignal_module():
    module_key = "bismillah.app.autosignal_fast"
    if module_key in sys.modules:
        return sys.modules[module_key]

    for submod in ("chat_store", "safe_send"):
        _load_bismillah_submodule(submod, f"bismillah.app.{submod}")
    return _load_bismillah_submodule("autosignal_fast", module_key)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_window_minutes(window: str | None) -> int:
    value = str(window or "30m").strip().lower()
    mapping = {
        "5m": 5,
        "30m": 30,
        "2h": 120,
        "24h": 1440,
    }
    return mapping.get(value, 30)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return float(default)


_VERIFIED_ALIASES = {"approved", "uid_verified", "active", "verified"}


def _fetch_table_rows(
    client,
    table_name: str,
    columns: str,
    *,
    page_size: int = 1000,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    chunk = max(1, int(page_size))
    while True:
        batch = (
            client.table(table_name)
            .select(columns)
            .range(offset, offset + chunk - 1)
            .execute()
            .data
            or []
        )
        rows.extend(batch)
        if len(batch) < chunk:
            break
        offset += chunk
    return rows


def get_decision_tree_snapshot(window: str = "30m", tail: int = 8) -> dict[str, Any]:
    dashboard = _get_dashboard_module()
    minutes = parse_window_minutes(window)
    if dashboard is None:
        return {
            "generated_at": _utc_now().isoformat(),
            "window_minutes": minutes,
            "top_pairs": {"pairs": [], "health": {"error": "dashboard_module_unavailable"}},
            "db": {},
            "journal": {"available": False, "reason": "dashboard_module_unavailable"},
        }
    return dashboard.get_live_dashboard_snapshot(minutes=minutes, tail=tail)


def export_decision_tree_snapshot(window: str = "30m", tail: int = 8) -> str:
    dashboard = _get_dashboard_module()
    snapshot = get_decision_tree_snapshot(window=window, tail=tail)
    if dashboard is None:
        out_dir = _ROOT / "logs" / "decision_tree_v2"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"web_admin_live_dashboard_{_utc_now().strftime('%Y%m%d_%H%M%S')}.json"
        out_path.write_text(str(snapshot), encoding="utf-8")
        return str(out_path)
    return dashboard.write_live_dashboard_snapshot(snapshot)


def get_signal_control_snapshot() -> dict[str, Any]:
    mod = _get_autosignal_module()
    if mod is None:
        return {
            "enabled": None,
            "interval_seconds": None,
            "top_n": None,
            "min_confidence": None,
            "timeframe": None,
            "available": False,
        }
    return {
        "enabled": bool(mod.autosignal_enabled()),
        "interval_seconds": int(getattr(mod, "SCAN_INTERVAL_SEC", 0) or 0),
        "top_n": int(getattr(mod, "TOP_N", 0) or 0),
        "min_confidence": float(getattr(mod, "MIN_CONFIDENCE", 0) or 0),
        "timeframe": str(getattr(mod, "TIMEFRAME", "") or ""),
        "available": True,
    }


def set_signal_control(enabled: bool) -> dict[str, Any]:
    mod = _get_autosignal_module()
    if mod is None:
        raise RuntimeError("autosignal_module_unavailable")
    mod.set_autosignal_enabled(bool(enabled))
    return get_signal_control_snapshot()


def get_user_stats_summary() -> dict[str, int]:
    s = _client()

    user_rows = _fetch_table_rows(
        s,
        "users",
        "telegram_id, is_premium, is_lifetime",
    )
    user_ids = {
        int(row["telegram_id"])
        for row in user_rows
        if row.get("telegram_id") is not None
    }
    premium_ids = {
        int(row["telegram_id"])
        for row in user_rows
        if row.get("telegram_id") is not None and bool(row.get("is_premium"))
    }
    lifetime_ids = {
        int(row["telegram_id"])
        for row in user_rows
        if row.get("telegram_id") is not None and bool(row.get("is_lifetime"))
    }

    verification_rows = _fetch_table_rows(
        s,
        "user_verifications",
        "telegram_id, status",
    )
    verified_ids = {
        int(row["telegram_id"])
        for row in verification_rows
        if row.get("telegram_id") is not None and str(row.get("status") or "").strip().lower() in _VERIFIED_ALIASES
    }
    verified_count = len(user_ids & verified_ids)

    session_rows = _fetch_table_rows(
        s,
        "autotrade_sessions",
        "telegram_id, engine_active",
    )
    engine_active_ids = {
        int(row["telegram_id"])
        for row in session_rows
        if row.get("telegram_id") is not None and bool(row.get("engine_active"))
    }
    engine_stopped_ids = {
        int(row["telegram_id"])
        for row in session_rows
        if row.get("telegram_id") is not None and not bool(row.get("engine_active"))
    }
    # If duplicate rows exist, prioritize active state for the user to avoid double counting.
    engine_stopped_ids -= engine_active_ids

    total = len(user_ids)
    premium = len(premium_ids)
    lifetime = len(lifetime_ids)
    unverified_count = max(int(total) - int(verified_count), 0)
    new_today = (
        s.table("users")
        .select("telegram_id", count="exact")
        .gte("created_at", _utc_now().strftime("%Y-%m-%d"))
        .execute()
        .count
        or 0
    )
    return {
        "total_users": int(total),
        "premium_users": int(premium),
        "lifetime_users": int(lifetime),
        "verified_users": int(verified_count),
        "unverified_users": int(unverified_count),
        "engine_active_users": int(len(engine_active_ids)),
        "engine_stopped_users": int(len(engine_stopped_ids)),
        "free_users": max(int(total) - int(premium), 0),
        "new_today": int(new_today),
    }


def _load_candidate_rows(minutes: int) -> list[dict[str, Any]]:
    cutoff = (_utc_now() - timedelta(minutes=int(minutes))).isoformat()
    client = _client()
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        batch = (
            client.table("trade_candidates_log")
            .select("*")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .range(offset, offset + 999)
            .execute()
            .data
            or []
        )
        rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return rows


def _norm_str(value: Any) -> str:
    return str(value or "").strip()


def _candidate_matches_filters(
    row: dict[str, Any],
    *,
    symbol: str | None = None,
    reject_reason: str | None = None,
    status: str | None = None,
    tier: str | None = None,
    engine: str | None = None,
    regime: str | None = None,
) -> bool:
    metadata = row.get("metadata") or {}
    execution_mode = _norm_str(metadata.get("execution_mode")).lower()
    if execution_mode and execution_mode != "live":
        return False
    if symbol and _norm_str(row.get("symbol")).upper() != symbol.strip().upper():
        return False
    if reject_reason and _norm_str(row.get("reject_reason")).lower() != reject_reason.strip().lower():
        return False
    if tier and _norm_str(row.get("user_equity_tier")).lower() != tier.strip().lower():
        return False
    if engine and _norm_str(row.get("engine")).lower() != engine.strip().lower():
        return False
    if regime and _norm_str(row.get("regime")).lower() != regime.strip().lower():
        return False
    normalized_status = _norm_str(status).lower()
    if normalized_status == "approved" and row.get("approved") is not True:
        return False
    if normalized_status == "rejected" and row.get("approved") is not False:
        return False
    return True


def list_trade_candidates(
    *,
    window: str = "30m",
    symbol: str | None = None,
    reject_reason: str | None = None,
    status: str | None = None,
    tier: str | None = None,
    engine: str | None = None,
    regime: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    minutes = parse_window_minutes(window)
    rows = [
        row
        for row in _load_candidate_rows(minutes)
        if _candidate_matches_filters(
            row,
            symbol=symbol,
            reject_reason=reject_reason,
            status=status,
            tier=tier,
            engine=engine,
            regime=regime,
        )
    ]
    total = len(rows)
    start = max(int(page) - 1, 0) * max(int(page_size), 1)
    end = start + max(int(page_size), 1)
    page_rows = rows[start:end]
    normalized_rows = []
    for row in page_rows:
        normalized_rows.append(
            {
                "id": row.get("id"),
                "created_at": row.get("created_at"),
                "symbol": row.get("symbol"),
                "engine": row.get("engine"),
                "side": row.get("side"),
                "regime": row.get("regime"),
                "setup_name": row.get("setup_name"),
                "user_equity_tier": row.get("user_equity_tier"),
                "approved": row.get("approved"),
                "reject_reason": row.get("reject_reason"),
                "display_reason": row.get("display_reason"),
                "signal_confidence": _safe_float(row.get("signal_confidence")),
                "tradeability_score": _safe_float(row.get("tradeability_score")),
                "approval_score": _safe_float(row.get("approval_score")),
                "community_score": _safe_float(row.get("community_score")),
                "user_segment_score": _safe_float(row.get("user_segment_score")),
                "portfolio_penalty": _safe_float(row.get("portfolio_penalty")),
                "final_score": _safe_float(row.get("final_score")),
                "recommended_risk_pct": _safe_float(row.get("recommended_risk_pct")),
                "quality_bucket": row.get("quality_bucket"),
                "participation_bucket": row.get("participation_bucket"),
                "approval_audit": row.get("approval_audit") or {},
                "metadata": row.get("metadata") or {},
            }
        )
    return {
        "window": window,
        "window_minutes": minutes,
        "page": int(page),
        "page_size": int(page_size),
        "total": total,
        "rows": normalized_rows,
    }


def export_trade_candidates(payload: dict[str, Any], fmt: str = "json") -> tuple[str, str]:
    rows = payload.get("rows") or []
    normalized_format = str(fmt or "json").strip().lower()
    if normalized_format == "csv":
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "created_at",
                "symbol",
                "engine",
                "side",
                "regime",
                "setup_name",
                "user_equity_tier",
                "approved",
                "reject_reason",
                "display_reason",
                "signal_confidence",
                "tradeability_score",
                "approval_score",
                "community_score",
                "user_segment_score",
                "portfolio_penalty",
                "final_score",
                "recommended_risk_pct",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in writer.fieldnames})
        return "text/csv", buffer.getvalue()

    import json

    return "application/json", json.dumps(payload, indent=2)


def get_one_click_push_fomo_metrics(window_minutes: int = 1440) -> dict[str, Any]:
    cutoff = (_utc_now() - timedelta(minutes=max(1, int(window_minutes)))).isoformat()
    client = _client()
    try:
        event_rows = (
            client.table("one_click_signal_events")
            .select(
                "signal_id,push_started_at,push_completed_at,outcome_status,outcome_level,generated_at"
            )
            .gte("generated_at", cutoff)
            .execute()
            .data
            or []
        )
        receipt_rows = (
            client.table("one_click_signal_receipts")
            .select(
                "signal_id,delivery_status,delivery_error,eligible,missed_alert_status,example_used,created_at"
            )
            .gte("created_at", cutoff)
            .execute()
            .data
            or []
        )
    except Exception as exc:
        return {
            "available": False,
            "window_minutes": int(window_minutes),
            "error": str(exc),
            "generated_at": _utc_now().isoformat(),
        }

    blocked_like = {
        row.get("signal_id")
        for row in receipt_rows
        if any(
            token in str(row.get("delivery_error") or "").lower()
            for token in ("blocked", "forbidden", "chat not found", "deactivated")
        )
    }
    sent_receipts = [row for row in receipt_rows if str(row.get("delivery_status") or "").lower() == "sent"]
    failed_receipts = [row for row in receipt_rows if str(row.get("delivery_status") or "").lower() == "failed"]
    fomo_sent = [row for row in receipt_rows if str(row.get("missed_alert_status") or "").lower() == "sent"]
    fomo_failed = [row for row in receipt_rows if str(row.get("missed_alert_status") or "").lower() == "failed"]

    return {
        "available": True,
        "generated_at": _utc_now().isoformat(),
        "window_minutes": int(window_minutes),
        "events": {
            "TOTAL_EVENTS": len(event_rows),
            "PUSH_STARTED": sum(1 for row in event_rows if row.get("push_started_at")),
            "PUSH_COMPLETED": sum(1 for row in event_rows if row.get("push_completed_at")),
            "TP_HIT_EVENTS": sum(1 for row in event_rows if str(row.get("outcome_status") or "").lower() == "tp_hit"),
            "EXPIRED_EVENTS": sum(1 for row in event_rows if str(row.get("outcome_status") or "").lower() == "expired"),
        },
        "deliveries": {
            "TOTAL_TARGET": len(receipt_rows),
            "SENT": len(sent_receipts),
            "FAILED": len(failed_receipts),
            "BLOCKED_OR_FORBIDDEN": len(blocked_like),
            "ELIGIBLE": sum(1 for row in receipt_rows if bool(row.get("eligible"))),
        },
        "missed_fomo": {
            "MISSED_ALERTS_SENT": len(fomo_sent),
            "MISSED_ALERTS_FAILED": len(fomo_failed),
            "ZERO_EQUITY_EXAMPLE_ALERTS": sum(
                1 for row in fomo_sent if bool(row.get("example_used"))
            ),
        },
    }
