from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.one_click_signal_hub import (
    build_dashboard_signal_url,
    detect_tp_hit,
    fetch_verified_recipients,
    find_recent_event_by_fingerprint,
    generate_canonical_signals,
    list_pending_missed_receipts,
    list_pending_outcome_events,
    mark_event_push_window,
    mark_missed_alert_result,
    projected_missed_pnl,
    push_threshold,
    strict_gate_enabled,
    telegram_push_enabled,
    missed_fomo_enabled,
    update_event_outcome,
    upsert_signal_event,
    upsert_signal_receipt,
)

logger = logging.getLogger(__name__)

_BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/24hr"
_worker_started = False
_worker_tasks: List[asyncio.Task] = []


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)) or default)
    except Exception:
        return int(default)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _fetch_mark_price(symbol: str) -> float:
    params = {"symbol": str(symbol or "").upper().replace("/", "")}
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(_BINANCE_TICKER, params=params)
        resp.raise_for_status()
        payload = resp.json()
    return _as_float(payload.get("lastPrice"), 0.0)


def _signal_keyboard(user_id: int, signal_id: str) -> InlineKeyboardMarkup:
    instant_url = build_dashboard_signal_url(int(user_id), signal_id=signal_id, instant=True)
    dashboard_url = build_dashboard_signal_url(int(user_id), signal_id=signal_id, instant=False)
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⚡ Instant 1-Click Trade", url=instant_url)],
            [InlineKeyboardButton("📊 Dashboard", url=dashboard_url)],
        ]
    )


def _push_message(signal: Dict[str, Any], *, risk_pct: float) -> str:
    direction = str(signal.get("direction") or "LONG").upper()
    reasons = " | ".join([str(r) for r in list(signal.get("reasons") or [])[:3]])
    return (
        "🚨 <b>High-Confidence 1-Click Signal</b>\n\n"
        f"🪙 <b>Pair:</b> {signal.get('pair')}\n"
        f"📈 <b>Direction:</b> {direction}\n"
        f"🎯 <b>Entry:</b> {float(signal.get('entry_zone_low', 0.0)):.4f} - {float(signal.get('entry_zone_high', 0.0)):.4f}\n"
        f"🏁 <b>TP1:</b> {float(signal.get('tp1', 0.0)):.4f}\n"
        f"🛡️ <b>SL:</b> {float(signal.get('stop_loss', 0.0)):.4f}\n"
        f"🤖 <b>AI Confidence:</b> {float(signal.get('confidence_effective', signal.get('confidence', 0.0))):.1f}%\n"
        f"⚙️ <b>Your risk/trade (synced):</b> {float(risk_pct):.2f}%\n"
        f"📌 <b>Type:</b> {signal.get('type')}\n"
        f"🧠 <b>Signal Reason:</b> {reasons or 'Multi-factor confluence'}\n\n"
        "<i>Only high-confidence setups are pushed. Stay disciplined.</i>"
    )


def _fomo_message(event: Dict[str, Any], *, tp_level: str, projection: Dict[str, Any]) -> str:
    pair = str(event.get("pair") or event.get("symbol") or "-")
    direction = str(event.get("direction") or "LONG").upper()
    rr = _as_float(projection.get("projected_rr"), 0.0)
    projected = _as_float(projection.get("projected_pnl_usdt"), 0.0)
    risk_pct = _as_float(projection.get("risk_pct_used"), 0.0)
    equity_used = _as_float(projection.get("equity_used_usdt"), 0.0)
    trade_value = _as_float(projection.get("trade_value_usdt"), 0.0)
    if projection.get("example_used"):
        example_equity = _as_float(projection.get("example_equity_usdt"), 100.0)
        example_risk_pct = _as_float(projection.get("example_risk_pct"), 10.0)
        example_trade_value = _as_float(projection.get("example_trade_value_usdt"), 10.0)
        example_projected = _as_float(projection.get("example_projected_pnl_usdt"), 0.0)
        extra = (
            "🧪 <b>Zero-equity example:</b>\n"
            f"If you deposit <b>${example_equity:.2f}</b> and set <b>{example_risk_pct:.2f}% risk/trade</b>\n"
            f"• Example trade value: <b>${example_trade_value:.2f}</b>\n"
            f"• This move could be: <b>+${example_projected:.2f}</b> (RR {rr:.2f})\n"
        )
    else:
        extra = ""
    return (
        "⚠️ <b>Missed High-Confidence Signal</b>\n\n"
        f"🪙 <b>Pair:</b> {pair}\n"
        f"📈 <b>Direction:</b> {direction}\n"
        f"✅ <b>Outcome:</b> {tp_level} was hit\n\n"
        f"💰 <b>Account equity:</b> ${equity_used:.2f}\n"
        f"⚙️ <b>Risk/trade (synced):</b> {risk_pct:.2f}%\n"
        f"📦 <b>Trade value (risk amount):</b> ${trade_value:.2f}\n"
        f"📊 <b>Potential profit missed:</b> <b>+${projected:.2f}</b> (RR {rr:.2f})\n\n"
        f"{extra}\n"
        "⏳ <b>Stay ready for the next upcoming signal.</b>\n"
        "<i>We’ll continue pushing only strict high-confidence setups.</i>"
    )


async def run_push_cycle(bot) -> Dict[str, int]:
    metrics = {
        "TOTAL_TARGET": 0,
        "SENT": 0,
        "FAILED": 0,
        "BLOCKED_OR_FORBIDDEN": 0,
        "DEDUPE_SKIPPED": 0,
    }
    if not telegram_push_enabled():
        return metrics

    strict = strict_gate_enabled()
    signals = await generate_canonical_signals(
        user_id=0,
        user_risk_pct=3.0,
        strict_gate=strict,
        include_blocked=False,
        limit=max(5, _env_int("ONE_CLICK_PUSH_TOP_LIMIT", 10)),
    )
    approved = [
        s for s in signals
        if str(s.get("gate_status") or "") == "approved"
        and bool(s.get("push_eligible"))
        and _as_float(s.get("confidence_effective", s.get("confidence")), 0.0) >= push_threshold()
    ]
    if not approved:
        return metrics

    recipients = fetch_verified_recipients()
    if not recipients:
        return metrics

    for signal in approved:
        fp = str(signal.get("signal_fingerprint") or "")
        dedupe_minutes = max(1, _env_int("ONE_CLICK_PUSH_DEDUPE_MINUTES", 20))
        recent = find_recent_event_by_fingerprint(fp, within_minutes=dedupe_minutes)
        if recent and recent.get("push_started_at"):
            metrics["DEDUPE_SKIPPED"] += 1
            continue

        event = upsert_signal_event(signal)
        if not event:
            continue
        signal_id = str(event.get("signal_id") or signal.get("signal_id") or "")
        if not signal_id:
            continue
        mark_event_push_window(signal_id, started=True)

        for user in recipients:
            uid = int(user.get("telegram_id") or 0)
            if uid <= 0:
                continue
            metrics["TOTAL_TARGET"] += 1
            risk_pct = 3.0
            try:
                from app.one_click_signal_hub import get_user_risk_pct
                risk_pct = get_user_risk_pct(uid)
            except Exception:
                risk_pct = 3.0

            try:
                await bot.send_message(
                    chat_id=uid,
                    text=_push_message(signal, risk_pct=risk_pct),
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=_signal_keyboard(uid, signal_id),
                )
                metrics["SENT"] += 1
                upsert_signal_receipt(
                    signal_id=signal_id,
                    telegram_id=uid,
                    audience_status="verified",
                    eligible=True,
                    eligibility_reason="verified_high_conf",
                    delivery_status="sent",
                )
            except Exception as exc:
                err = str(exc or "")
                if any(k in err.lower() for k in ("blocked", "forbidden", "chat not found", "deactivated")):
                    metrics["BLOCKED_OR_FORBIDDEN"] += 1
                else:
                    metrics["FAILED"] += 1
                upsert_signal_receipt(
                    signal_id=signal_id,
                    telegram_id=uid,
                    audience_status="verified",
                    eligible=False,
                    eligibility_reason="delivery_failed",
                    delivery_status="failed",
                    delivery_error=err[:500],
                )
            await asyncio.sleep(0.03)
        mark_event_push_window(signal_id, started=False)
    return metrics


async def run_fomo_cycle(bot) -> Dict[str, int]:
    metrics = {"EVENTS_SCANNED": 0, "TP_HIT_EVENTS": 0, "MISSED_ALERTS_SENT": 0, "MISSED_ALERTS_FAILED": 0}
    if not missed_fomo_enabled():
        return metrics

    now_utc = datetime.now(timezone.utc)
    events = list_pending_outcome_events(limit=max(10, _env_int("ONE_CLICK_FOMO_SCAN_LIMIT", 80)))
    metrics["EVENTS_SCANNED"] = len(events)
    for event in events:
        signal_id = str(event.get("signal_id") or "")
        if not signal_id:
            continue
        deadline = event.get("outcome_deadline_at")
        deadline_dt = datetime.fromisoformat(str(deadline).replace("Z", "+00:00")) if deadline else None
        if deadline_dt and now_utc > deadline_dt.astimezone(timezone.utc):
            update_event_outcome(signal_id, outcome_status="expired")
            continue

        symbol = str(event.get("symbol") or "")
        try:
            mark = await _fetch_mark_price(symbol)
        except Exception as exc:
            logger.debug("[OneClickPush] mark fetch failed for %s: %s", symbol, exc)
            continue
        hit = detect_tp_hit(event, mark)
        if not hit.get("hit"):
            continue

        tp_level = str(hit.get("level") or "TP1")
        rr_hit = _as_float(hit.get("rr_hit"), 0.0)
        update_event_outcome(
            signal_id,
            outcome_status="tp_hit",
            outcome_level=tp_level,
            outcome_price=_as_float(hit.get("tp_price"), 0.0),
        )
        metrics["TP_HIT_EVENTS"] += 1

        receipts = list_pending_missed_receipts(signal_id)
        for receipt in receipts:
            uid = int(receipt.get("telegram_id") or 0)
            if uid <= 0:
                continue
            projection = projected_missed_pnl(uid, rr_hit)
            projection["projected_rr"] = rr_hit
            try:
                await bot.send_message(
                    chat_id=uid,
                    text=_fomo_message(event, tp_level=tp_level, projection=projection),
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=_signal_keyboard(uid, signal_id),
                )
                metrics["MISSED_ALERTS_SENT"] += 1
                mark_missed_alert_result(
                    signal_id=signal_id,
                    telegram_id=uid,
                    status="sent",
                    tp_level_hit=tp_level,
                    projected_pnl_usdt=_as_float(projection.get("projected_pnl_usdt"), 0.0),
                    projected_rr=rr_hit,
                    risk_pct_used=_as_float(projection.get("risk_pct_used"), 0.0),
                    equity_used_usdt=_as_float(projection.get("equity_used_usdt"), 0.0),
                    example_used=bool(projection.get("example_used")),
                )
            except Exception as exc:
                metrics["MISSED_ALERTS_FAILED"] += 1
                mark_missed_alert_result(
                    signal_id=signal_id,
                    telegram_id=uid,
                    status="failed",
                    error=str(exc)[:500],
                    tp_level_hit=tp_level,
                    projected_pnl_usdt=_as_float(projection.get("projected_pnl_usdt"), 0.0),
                    projected_rr=rr_hit,
                    risk_pct_used=_as_float(projection.get("risk_pct_used"), 0.0),
                    equity_used_usdt=_as_float(projection.get("equity_used_usdt"), 0.0),
                    example_used=bool(projection.get("example_used")),
                )
            await asyncio.sleep(0.03)
    return metrics


async def _push_loop(application):
    interval = max(60, _env_int("ONE_CLICK_PUSH_INTERVAL_SECONDS", 300))
    await asyncio.sleep(15)
    while True:
        try:
            metrics = await run_push_cycle(application.bot)
            logger.info("[OneClickPush] cycle=%s metrics=%s", _iso_now(), metrics)
        except Exception as exc:
            logger.error("[OneClickPush] push loop error: %s", exc, exc_info=True)
        await asyncio.sleep(interval)


async def _fomo_loop(application):
    interval = max(30, _env_int("ONE_CLICK_FOMO_INTERVAL_SECONDS", 120))
    await asyncio.sleep(30)
    while True:
        try:
            metrics = await run_fomo_cycle(application.bot)
            logger.info("[OneClickPush] fomo_cycle=%s metrics=%s", _iso_now(), metrics)
        except Exception as exc:
            logger.error("[OneClickPush] fomo loop error: %s", exc, exc_info=True)
        await asyncio.sleep(interval)


def start_one_click_signal_workers(application) -> None:
    global _worker_started
    if _worker_started:
        return
    if not telegram_push_enabled() and not missed_fomo_enabled():
        logger.info("[OneClickPush] workers disabled by feature flags")
        return
    _worker_started = True
    if telegram_push_enabled():
        _worker_tasks.append(asyncio.create_task(_push_loop(application)))
    if missed_fomo_enabled():
        _worker_tasks.append(asyncio.create_task(_fomo_loop(application)))
    logger.info(
        "[OneClickPush] workers started push_enabled=%s fomo_enabled=%s task_count=%s",
        telegram_push_enabled(),
        missed_fomo_enabled(),
        len(_worker_tasks),
    )
