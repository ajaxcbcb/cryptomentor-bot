from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from telegram import Bot

from app.auth.admin import require_admin_user
from app.db.supabase import _client, get_user_by_tid
from app.services.admin_observability import (
    export_decision_tree_snapshot,
    export_trade_candidates,
    get_decision_tree_snapshot,
    get_signal_control_snapshot,
    get_user_stats_summary,
    list_trade_candidates,
    set_signal_control,
)

router = APIRouter(prefix="/dashboard/admin", tags=["admin"])


class SignalControlPayload(BaseModel):
    enabled: bool


class PremiumPayload(BaseModel):
    user_id: int
    action: Literal["add", "remove", "lifetime"]
    days: int | None = Field(default=None, ge=1, le=3650)


class CreditsPayload(BaseModel):
    user_id: int
    amount: int = Field(ge=1, le=1000000)


class BroadcastPayload(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    audience: str = "all"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_window(window: str | None) -> str:
    value = str(window or "30m").strip().lower()
    return value if value in {"5m", "30m", "2h", "24h"} else "30m"


def _action_result(message: str, **extra):
    return {"ok": True, "message": message, **extra}


def _load_bot_token() -> str:
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        raise HTTPException(status_code=503, detail="TELEGRAM_BOT_TOKEN not configured")
    return token


async def _notify_user_best_effort(chat_id: int, text: str) -> bool:
    try:
        bot = Bot(token=_load_bot_token())
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", disable_web_page_preview=True)
        return True
    except Exception:
        return False


async def _send_telegram_html(client: httpx.AsyncClient, bot_token: str, chat_id: int, text: str) -> tuple[bool, str | None]:
    try:
        resp = await client.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": int(chat_id),
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )
        if resp.status_code >= 400:
            return False, f"http_{resp.status_code}"
        body = resp.json() if resp.text else {}
        if not body.get("ok", False):
            return False, str(body.get("description") or "telegram_api_error")
        return True, None
    except Exception as exc:
        return False, str(exc)


def _fetch_all_user_ids(audience: str = "all") -> list[int]:
    s = _client()
    audience_key = str(audience or "all").strip().lower()
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        res = s.table("users").select("telegram_id, is_premium, is_lifetime").range(offset, offset + 999).execute()
        batch = res.data or []
        rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000

    if audience_key == "all":
        return sorted({int(row["telegram_id"]) for row in rows if row.get("telegram_id")})

    if audience_key == "premium":
        return sorted(
            {
                int(row["telegram_id"])
                for row in rows
                if row.get("telegram_id") and (row.get("is_premium") or row.get("is_lifetime"))
            }
        )

    if audience_key in {"verified", "non-verified", "non_verified"}:
        ver_rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            res = (
                s.table("user_verifications")
                .select("telegram_id, status")
                .range(offset, offset + 999)
                .execute()
            )
            batch = res.data or []
            ver_rows.extend(batch)
            if len(batch) < 1000:
                break
            offset += 1000
        approved_aliases = {"approved", "uid_verified", "active", "verified"}
        approved = {
            int(row["telegram_id"])
            for row in ver_rows
            if row.get("telegram_id") and str(row.get("status") or "").strip().lower() in approved_aliases
        }
        all_ids = {int(row["telegram_id"]) for row in rows if row.get("telegram_id")}
        if audience_key == "verified":
            return sorted(approved)
        return sorted(all_ids - approved)

    raise HTTPException(status_code=400, detail=f"Unsupported audience: {audience}")


def _set_premium_normalized(tg_id: int, action: str, days: int | None = None) -> dict[str, Any]:
    from app.services import bitunix as _bitunix  # ensures Bismillah path prep exists
    import importlib.util
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    bismillah = root / "Bismillah"
    app_dir = bismillah / "app"
    if str(bismillah) not in sys.path:
        sys.path.insert(0, str(bismillah))
    if str(app_dir) not in sys.path:
        sys.path.insert(1, str(app_dir))

    mod_key = "app.supabase_repo"
    if mod_key not in sys.modules:
        spec = importlib.util.spec_from_file_location("bismillah.app.supabase_repo", str(app_dir / "supabase_repo.py"))
        mod = importlib.util.module_from_spec(spec)
        sys.modules["bismillah.app.supabase_repo"] = mod
        sys.modules[mod_key] = mod
        spec.loader.exec_module(mod)
    repo = sys.modules[mod_key]

    if action == "remove":
        repo.revoke_premium(int(tg_id))
    elif action == "lifetime":
        repo.set_premium_normalized(int(tg_id), "lifetime")
    else:
        repo.set_premium_normalized(int(tg_id), f"{int(days or 30)}d")
    return get_user_by_tid(int(tg_id)) or {"telegram_id": int(tg_id)}


@router.get("/bootstrap")
async def admin_bootstrap(requester: int = Depends(require_admin_user)):
    window = "30m"
    snapshot = get_decision_tree_snapshot(window=window, tail=6)
    user_stats = get_user_stats_summary()
    signal = get_signal_control_snapshot()
    db = snapshot.get("db") or {}
    return {
        "is_admin": True,
        "requester_telegram_id": int(requester),
        "capabilities": [
            "decision_tree_dashboard",
            "trade_candidates",
            "user_stats",
            "signal_control",
            "premium_control",
            "credits_control",
            "broadcast",
            "daily_report",
        ],
        "summary_cards": {
            "users": user_stats,
            "signals": signal,
            "candidates": {
                "live_candidate_count": int(db.get("live_candidate_count") or 0),
                "approved_count": int(db.get("approved_count") or 0),
                "rejected_count": int(db.get("rejected_count") or 0),
            },
        },
    }


@router.get("/decision-tree")
async def admin_decision_tree(
    window: str = Query("30m"),
    requester: int = Depends(require_admin_user),
):
    _ = requester
    normalized = _normalize_window(window)
    snapshot = get_decision_tree_snapshot(window=normalized, tail=8)
    snapshot["snapshot_export_path"] = export_decision_tree_snapshot(window=normalized, tail=8)
    return snapshot


@router.get("/decision-tree/symbols")
async def admin_decision_tree_symbols(
    window: str = Query("30m"),
    requester: int = Depends(require_admin_user),
):
    _ = requester
    snapshot = get_decision_tree_snapshot(window=_normalize_window(window), tail=8)
    journal = snapshot.get("journal") or {}
    return {
        "generated_at": snapshot.get("generated_at"),
        "window_minutes": snapshot.get("window_minutes"),
        "metrics": journal.get("metrics") or {},
        "symbols": journal.get("symbol_stats") or {},
    }


@router.get("/trade-candidates")
async def admin_trade_candidates(
    window: str = Query("30m"),
    symbol: str | None = Query(default=None),
    reject_reason: str | None = Query(default=None),
    status: str | None = Query(default=None),
    tier: str | None = Query(default=None),
    engine: str | None = Query(default=None),
    regime: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    requester: int = Depends(require_admin_user),
):
    _ = requester
    return list_trade_candidates(
        window=_normalize_window(window),
        symbol=symbol,
        reject_reason=reject_reason,
        status=status,
        tier=tier,
        engine=engine,
        regime=regime,
        page=page,
        page_size=page_size,
    )


@router.get("/trade-candidates/export")
async def admin_trade_candidates_export(
    window: str = Query("30m"),
    symbol: str | None = Query(default=None),
    reject_reason: str | None = Query(default=None),
    status: str | None = Query(default=None),
    tier: str | None = Query(default=None),
    engine: str | None = Query(default=None),
    regime: str | None = Query(default=None),
    fmt: str = Query(default="json"),
    requester: int = Depends(require_admin_user),
):
    _ = requester
    payload = list_trade_candidates(
        window=_normalize_window(window),
        symbol=symbol,
        reject_reason=reject_reason,
        status=status,
        tier=tier,
        engine=engine,
        regime=regime,
        page=1,
        page_size=5000,
    )
    media_type, body = export_trade_candidates(payload, fmt=fmt)
    extension = "csv" if media_type == "text/csv" else "json"
    filename = f"trade_candidates_{_normalize_window(window)}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.{extension}"
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/user-stats")
async def admin_user_stats(requester: int = Depends(require_admin_user)):
    _ = requester
    return get_user_stats_summary()


@router.post("/signal-control")
async def admin_signal_control(
    payload: SignalControlPayload,
    requester: int = Depends(require_admin_user),
):
    snapshot = set_signal_control(payload.enabled)
    return _action_result(
        f"AutoSignal {'enabled' if snapshot.get('enabled') else 'disabled'} by admin {requester}.",
        signal=snapshot,
        requested_enabled=bool(payload.enabled),
    )


@router.post("/premium")
async def admin_premium(
    payload: PremiumPayload,
    requester: int = Depends(require_admin_user),
):
    if payload.action == "add" and not payload.days:
        raise HTTPException(status_code=400, detail="days is required when action=add")
    user = _set_premium_normalized(payload.user_id, payload.action, payload.days)
    notice = (
        "Your CryptoMentor premium status was updated by admin."
        if payload.action == "remove"
        else "Your CryptoMentor premium access was activated by admin."
    )
    delivered = await _notify_user_best_effort(int(payload.user_id), notice)
    return _action_result(
        f"Premium action '{payload.action}' applied to {payload.user_id}.",
        target_user=user,
        delivered_notice=delivered,
        audit={
            "requester": int(requester),
            "target_user_id": int(payload.user_id),
            "action": payload.action,
            "days": payload.days,
            "applied_at": _utc_now_iso(),
        },
    )


@router.post("/credits")
async def admin_credits(
    payload: CreditsPayload,
    requester: int = Depends(require_admin_user),
):
    s = _client()
    existing = get_user_by_tid(int(payload.user_id))
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    current = int(existing.get("credits") or 0)
    updated_credits = current + int(payload.amount)
    s.table("users").update(
        {
            "credits": updated_credits,
            "updated_at": _utc_now_iso(),
        }
    ).eq("telegram_id", int(payload.user_id)).execute()
    delivered = await _notify_user_best_effort(
        int(payload.user_id),
        f"Your CryptoMentor balance received <b>{int(payload.amount)}</b> credits from admin.",
    )
    return _action_result(
        f"Added {int(payload.amount)} credits to {payload.user_id}.",
        credits={"before": current, "after": updated_credits},
        delivered_notice=delivered,
        audit={
            "requester": int(requester),
            "target_user_id": int(payload.user_id),
            "amount": int(payload.amount),
            "applied_at": _utc_now_iso(),
        },
    )


@router.post("/broadcast")
async def admin_broadcast(
    payload: BroadcastPayload,
    requester: int = Depends(require_admin_user),
):
    audience = str(payload.audience or "all").strip().lower()
    target_ids = _fetch_all_user_ids(audience=audience)
    if not target_ids:
        return _action_result(
            "No users found for the selected audience.",
            metrics={"TOTAL_TARGET": 0, "SENT": 0, "FAILED": 0, "BLOCKED_OR_FORBIDDEN": 0},
        )

    bot_token = _load_bot_token()
    sent = 0
    failed = 0
    blocked = 0
    async with httpx.AsyncClient(timeout=20.0) as client:
        for idx, tid in enumerate(target_ids, start=1):
            ok, error = await _send_telegram_html(client, bot_token, tid, payload.message)
            if ok:
                sent += 1
            else:
                error_text = str(error or "").lower()
                if any(token in error_text for token in ("blocked", "forbidden", "chat not found", "deactivated")):
                    blocked += 1
                else:
                    failed += 1
            if idx % 30 == 0:
                await asyncio.sleep(1)

    return _action_result(
        f"Broadcast sent to audience '{audience}'.",
        metrics={
            "TOTAL_TARGET": len(target_ids),
            "SENT": sent,
            "FAILED": failed,
            "BLOCKED_OR_FORBIDDEN": blocked,
        },
        audit={
            "requester": int(requester),
            "audience": audience,
            "sent_at": _utc_now_iso(),
        },
    )


@router.post("/daily-report-now")
async def admin_daily_report_now(requester: int = Depends(require_admin_user)):
    try:
        from app.services import bitunix as _bitunix  # ensure Bismillah import path is ready
        import importlib.util
        import sys
        from pathlib import Path

        root = Path(__file__).resolve().parents[3]
        bismillah = root / "Bismillah"
        app_dir = bismillah / "app"
        if str(bismillah) not in sys.path:
            sys.path.insert(0, str(bismillah))
        if str(app_dir) not in sys.path:
            sys.path.insert(1, str(app_dir))
        key = "app.admin_daily_report"
        if key not in sys.modules:
            spec = importlib.util.spec_from_file_location("bismillah.app.admin_daily_report", str(app_dir / "admin_daily_report.py"))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["bismillah.app.admin_daily_report"] = mod
            sys.modules[key] = mod
            spec.loader.exec_module(mod)
        report_mod = sys.modules[key]
        bot = Bot(token=_load_bot_token())
        await report_mod.send_daily_report(bot)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to send daily report: {exc}")

    return _action_result(
        "Daily report sent to admin targets.",
        audit={"requester": int(requester), "sent_at": _utc_now_iso()},
    )
