"""
Canonical one-click signal hub shared by dashboard and Telegram push workers.

Responsibilities:
- Build strict-gated dynamic top-volume one-click signals.
- Persist signal/receipt lifecycle for push + missed-TP FOMO.
- Provide risk/equity-based projected PnL helpers.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlencode

from app.autotrade_engine import _compute_signal_pro, _get_btc_bias
from app.candidate_approver import approve_candidate
from app.confidence_adaptation import get_confidence_adaptation
from app.engine_execution_shared import evaluate_and_apply_playbook_risk
from app.exchange_registry import get_client
from app.market_context_provider import get_market_context
from app.pair_strategy_router import get_mixed_pair_assignments
from app.supabase_repo import _client, get_user_api_key
from app.symbol_memory import get_symbol_memory
from app.trade_candidate import TradeCandidate
from app.tradeability import score_tradeability
from app.user_segmentation import get_profile
from app.volume_pair_selector import get_ranked_top_volume_pairs
from app.lib.auth import create_access_token

logger = logging.getLogger(__name__)

VERIFIED_ALIASES = {"approved", "uid_verified", "active", "verified"}
DEFAULT_RISK_PCT = 3.0
STRICT_MIN_CONFIDENCE = 90.0
PUSH_THRESHOLD = 90.0


def _env_flag(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, "true" if default else "false") or "").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


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


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _now_utc().isoformat()


def _parse_iso(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        raw = str(value)
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _norm_symbol(symbol: Any) -> str:
    return str(symbol or "").strip().upper().replace("/", "")


def _pair_label(symbol: str) -> str:
    sym = _norm_symbol(symbol)
    if sym.endswith("USDT"):
        return f"{sym[:-4]}/USDT"
    return sym


def _clamp_risk_pct(raw: Any, default: float = DEFAULT_RISK_PCT) -> float:
    risk = _as_float(raw, default)
    return max(0.25, min(10.0, risk))


def _entry_band(entry: float) -> tuple[float, float]:
    band = abs(float(entry)) * 0.001
    return float(entry - band), float(entry + band)


def _front_url() -> str:
    return (
        os.getenv("FRONTEND_URL")
        or os.getenv("WEB_DASHBOARD_URL")
        or "https://cryptomentor.id"
    ).rstrip("/")


def build_dashboard_signal_url(
    telegram_id: int,
    *,
    username: str = "",
    first_name: str = "",
    signal_id: str = "",
    instant: bool = False,
) -> str:
    token = create_access_token(int(telegram_id), str(username or ""), str(first_name or ""))
    params = {
        "t": token,
        "tab": "signals",
    }
    if signal_id:
        params["signal_id"] = str(signal_id)
    if instant:
        params["action"] = "instant_1click"
    return f"{_front_url()}/?{urlencode(params)}"


def build_signal_id(symbol: str, generated_at: datetime, model_source: str = "canonical_pro_v1") -> str:
    base = f"{_norm_symbol(symbol)}|{generated_at.isoformat()}|{model_source}|v1"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]
    return f"ocs_{digest}"


def build_signal_fingerprint(signal: Dict[str, Any]) -> str:
    symbol = _norm_symbol(signal.get("symbol"))
    direction = str(signal.get("direction") or "").upper()
    entry = round(_as_float(signal.get("entry_price"), 0.0), 4)
    sl = round(_as_float(signal.get("stop_loss"), 0.0), 4)
    tp1 = round(_as_float(signal.get("tp1"), 0.0), 4)
    sig_type = str(signal.get("type") or "Scalp")
    raw = f"{symbol}|{direction}|{entry}|{sl}|{tp1}|{sig_type}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def strict_gate_enabled() -> bool:
    return _env_flag("ONE_CLICK_STRICT_GATE_ENABLED", False)


def telegram_push_enabled() -> bool:
    return _env_flag("ONE_CLICK_TELEGRAM_PUSH_ENABLED", False)


def missed_fomo_enabled() -> bool:
    return _env_flag("ONE_CLICK_MISSED_FOMO_ENABLED", False)


def push_threshold() -> float:
    return max(50.0, min(99.0, _as_float(os.getenv("ONE_CLICK_PUSH_MIN_CONFIDENCE"), PUSH_THRESHOLD)))


def _compute_tp3(side: str, entry: float, tp2: float) -> float:
    dist = abs(tp2 - entry)
    if dist <= 0:
        dist = abs(entry) * 0.012
    return float(tp2 + dist * 0.75) if side == "LONG" else float(tp2 - dist * 0.75)


async def _resolve_type_map(user_id: int, ranked_pairs: List[str]) -> Dict[str, str]:
    try:
        assign = await get_mixed_pair_assignments(
            user_id=int(user_id),
            limit=max(1, len(ranked_pairs)),
            fallback_pairs=ranked_pairs,
            label=f"[OneClickHub:{user_id}]",
        )
        swing = {_norm_symbol(s) for s in (assign.get("swing") or [])}
    except Exception:
        swing = set()
    out: Dict[str, str] = {}
    for sym in ranked_pairs:
        out[_norm_symbol(sym)] = "Swing" if _norm_symbol(sym) in swing else "Scalp"
    return out


async def _quality_gate_for_signal(
    *,
    signal: Dict[str, Any],
    signal_type: str,
    user_id: int,
    base_risk_pct: float,
    strict_gate: bool,
) -> Dict[str, Any]:
    symbol = _norm_symbol(signal.get("symbol"))
    side = str(signal.get("direction") or "LONG").upper()
    trade_type = "scalping" if str(signal_type).lower() == "scalp" else "swing"
    timeframe = "5m" if trade_type == "scalping" else "15m"

    market_context = get_market_context(symbols=[symbol], limit=10)
    try:
        profile = get_profile(int(user_id))
    except Exception:
        # Conservative fallback profile behavior through user_id=0 lookup.
        profile = get_profile(0)
    symbol_memory = get_symbol_memory(symbol)

    candidate = TradeCandidate(
        user_id=int(user_id),
        symbol=symbol,
        engine=trade_type,
        side=side,
        regime=str(signal.get("market_structure") or "unknown"),
        setup_name=str(signal.get("setup_name") or "canonical_one_click"),
        entry_price=_as_float(signal.get("entry_price"), 0.0),
        stop_loss=_as_float(signal.get("stop_loss"), 0.0),
        take_profit_hint=_as_float(signal.get("tp1"), 0.0),
        rr_estimate=_as_float(signal.get("rr_ratio"), 0.0),
        signal_confidence=_as_float(signal.get("confidence"), 0.0),
        source_signal_payload=dict(signal),
        metadata={"preferred_engine": trade_type},
    )

    tradeability = score_tradeability(candidate, market_context, symbol_memory)
    candidate.tradeability_score = _as_float(tradeability.get("tradeability_score"), 0.0)

    approval = approve_candidate(candidate, user_profile=profile, market_context=market_context, symbol_memory=symbol_memory)
    candidate.approval_score = _as_float(approval.get("approval_score"), 0.0)

    sig_mut = {
        "reasons": list(signal.get("reasons") or []),
        "trade_type": trade_type,
        "timeframe": timeframe,
    }
    playbook_eval = await evaluate_and_apply_playbook_risk(
        signal=sig_mut,
        base_risk_pct=float(base_risk_pct),
        raw_reasons=list(signal.get("reasons") or []),
        logger=logger,
        label=f"[OneClickHub:{symbol}]",
    )

    conf_adapt = get_confidence_adaptation(trade_type, _as_float(signal.get("confidence"), 0.0), is_emergency=False)
    conf_penalty = int(conf_adapt.get("bucket_penalty", 0) or 0)
    conf_effective = max(0.0, _as_float(signal.get("confidence"), 0.0) - float(conf_penalty))

    reasons: List[str] = []
    hard_reject = str(tradeability.get("hard_reject_reason") or "").strip()
    reject_reason = str(approval.get("reject_reason") or "").strip()

    if hard_reject:
        reasons.append(hard_reject)
    if reject_reason:
        reasons.append(reject_reason)
    if conf_effective < STRICT_MIN_CONFIDENCE:
        reasons.append(f"confidence_below_{int(STRICT_MIN_CONFIDENCE)}")

    approved = bool(approval.get("approved", False)) and not hard_reject
    if strict_gate and conf_effective < STRICT_MIN_CONFIDENCE:
        approved = False

    return {
        "approved": bool(approved),
        "gate_status": "approved" if approved else "blocked",
        "gate_reasons": reasons,
        "push_eligible": bool(approved and conf_effective >= push_threshold()),
        "confidence_effective": round(conf_effective, 2),
        "tradeability_score": round(candidate.tradeability_score, 4),
        "approval_score": round(candidate.approval_score, 4),
        "playbook_match_score": round(_as_float(playbook_eval.get("playbook_match_score"), 0.0), 4),
        "playbook_match_tags": list(playbook_eval.get("playbook_match_tags") or []),
        "risk_overlay_pct": round(_as_float(playbook_eval.get("risk_overlay_pct"), 0.0), 4),
        "effective_risk_pct": round(_as_float(playbook_eval.get("effective_risk_pct"), base_risk_pct), 4),
        "confidence_bucket": str(conf_adapt.get("bucket") or ""),
        "confidence_bucket_penalty": int(conf_penalty),
        "confidence_bucket_risk_scale": round(_as_float(conf_adapt.get("bucket_risk_scale"), 1.0), 4),
    }


async def generate_canonical_signals(
    *,
    user_id: Optional[int],
    user_risk_pct: float,
    limit: int = 10,
    include_blocked: bool = True,
    strict_gate: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    strict = strict_gate_enabled() if strict_gate is None else bool(strict_gate)
    uid = int(user_id or 0)
    risk = _clamp_risk_pct(user_risk_pct, default=DEFAULT_RISK_PCT)

    ranked_pairs = list(get_ranked_top_volume_pairs(limit=max(1, int(limit or 10))))
    type_map = await _resolve_type_map(uid, ranked_pairs)
    btc_bias = await asyncio.to_thread(_get_btc_bias)
    now_utc = _now_utc()

    out: List[Dict[str, Any]] = []
    for rank, symbol in enumerate(ranked_pairs, start=1):
        base_symbol = _norm_symbol(symbol).replace("USDT", "")
        try:
            raw = await asyncio.to_thread(
                _compute_signal_pro,
                base_symbol,
                btc_bias,
                float(risk),
                None,
                uid if uid > 0 else None,
            )
        except Exception as exc:
            logger.warning("[OneClickHub] signal compute failed for %s: %s", symbol, exc)
            continue

        if not raw:
            continue

        side = str(raw.get("side") or "LONG").upper()
        entry_price = _as_float(raw.get("entry_price"), 0.0)
        sl_price = _as_float(raw.get("sl"), 0.0)
        tp1 = _as_float(raw.get("tp1"), 0.0)
        tp2 = _as_float(raw.get("tp2"), tp1)
        tp3 = _as_float(raw.get("tp3"), 0.0)
        if tp3 <= 0:
            tp3 = _compute_tp3(side, entry_price, tp2)
        entry_low, entry_high = _entry_band(entry_price)

        signal_type = type_map.get(_norm_symbol(symbol), "Scalp")
        confidence = _as_float(raw.get("confidence"), 0.0)
        reasons = [str(r) for r in list(raw.get("reasons") or []) if str(r).strip()]
        generated_at = now_utc
        expiry_seconds = _env_int("ONE_CLICK_SIGNAL_ENTRY_WINDOW_SECONDS", 300)
        expires_at = generated_at + timedelta(seconds=max(60, expiry_seconds))
        signal_payload = {
            "symbol": _norm_symbol(symbol),
            "pair": _pair_label(symbol),
            "type": signal_type,
            "direction": side,
            "entry_price": entry_price,
            "entry_zone_low": entry_low,
            "entry_zone_high": entry_high,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "stop_loss": sl_price,
            "confidence": confidence,
            "rr_ratio": _as_float(raw.get("rr_ratio"), 0.0),
            "market_structure": str(raw.get("market_structure") or ""),
            "reasons": reasons,
            "volume_rank": rank,
            "generated_at": generated_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "model_source": "canonical_pro_v1",
        }

        quality = await _quality_gate_for_signal(
            signal=signal_payload,
            signal_type=signal_type,
            user_id=uid,
            base_risk_pct=float(risk),
            strict_gate=strict,
        )
        signal_payload.update(quality)
        signal_payload["signal_id"] = build_signal_id(signal_payload["symbol"], generated_at, signal_payload["model_source"])
        signal_payload["signal_fingerprint"] = build_signal_fingerprint(signal_payload)

        if not include_blocked and signal_payload.get("gate_status") != "approved":
            continue
        out.append(signal_payload)

    out.sort(
        key=lambda s: (
            int(s.get("volume_rank", 9999)),
            -_as_float(s.get("confidence_effective", s.get("confidence")), 0.0),
        )
    )
    return out


def _fetch_table_rows(table_name: str, columns: str, page_size: int = 1000) -> List[Dict[str, Any]]:
    s = _client()
    rows: List[Dict[str, Any]] = []
    offset = 0
    while True:
        batch = (
            s.table(table_name)
            .select(columns)
            .range(offset, offset + page_size - 1)
            .execute()
            .data
            or []
        )
        rows.extend([dict(r) for r in batch])
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def fetch_verified_recipients() -> List[Dict[str, Any]]:
    users = _fetch_table_rows("users", "telegram_id,first_name,username")
    ver_rows = _fetch_table_rows("user_verifications", "telegram_id,status")
    approved = {
        int(r["telegram_id"])
        for r in ver_rows
        if r.get("telegram_id") is not None and str(r.get("status") or "").strip().lower() in VERIFIED_ALIASES
    }
    out: List[Dict[str, Any]] = []
    seen = set()
    for row in users:
        raw_uid = row.get("telegram_id")
        if raw_uid is None:
            continue
        uid = int(raw_uid)
        if uid in seen or uid not in approved:
            continue
        seen.add(uid)
        out.append(
            {
                "telegram_id": uid,
                "first_name": str(row.get("first_name") or ""),
                "username": str(row.get("username") or ""),
            }
        )
    return out


def find_recent_event_by_fingerprint(signal_fingerprint: str, within_minutes: int = 20) -> Optional[Dict[str, Any]]:
    since = (_now_utc() - timedelta(minutes=max(1, int(within_minutes)))).isoformat()
    try:
        res = (
            _client()
            .table("one_click_signal_events")
            .select("*")
            .eq("signal_fingerprint", str(signal_fingerprint))
            .gte("generated_at", since)
            .order("generated_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        return dict(rows[0]) if rows else None
    except Exception as exc:
        logger.warning("[OneClickHub] find_recent_event_by_fingerprint failed: %s", exc)
        return None


def upsert_signal_event(signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    signal_id = str(signal.get("signal_id") or "").strip()
    if not signal_id:
        return None
    signal_type = str(signal.get("type") or "Scalp")
    generated_at = _parse_iso(signal.get("generated_at")) or _now_utc()
    deadline_hours = (
        _env_int("ONE_CLICK_OUTCOME_WINDOW_SWING_HOURS", 24)
        if signal_type.lower() == "swing"
        else _env_int("ONE_CLICK_OUTCOME_WINDOW_SCALP_HOURS", 6)
    )
    payload = {
        "signal_id": signal_id,
        "signal_fingerprint": str(signal.get("signal_fingerprint") or build_signal_fingerprint(signal)),
        "symbol": _norm_symbol(signal.get("symbol")),
        "pair": str(signal.get("pair") or _pair_label(signal.get("symbol"))),
        "signal_type": signal_type,
        "direction": str(signal.get("direction") or "LONG").upper(),
        "confidence": _as_float(signal.get("confidence_effective", signal.get("confidence")), 0.0),
        "gate_status": str(signal.get("gate_status") or "approved"),
        "gate_reasons": list(signal.get("gate_reasons") or []),
        "model_source": str(signal.get("model_source") or "canonical_pro_v1"),
        "quality_meta": {
            "volume_rank": int(signal.get("volume_rank", 0) or 0),
            "tradeability_score": _as_float(signal.get("tradeability_score"), 0.0),
            "approval_score": _as_float(signal.get("approval_score"), 0.0),
            "playbook_match_score": _as_float(signal.get("playbook_match_score"), 0.0),
            "confidence_bucket": str(signal.get("confidence_bucket") or ""),
            "confidence_bucket_penalty": int(signal.get("confidence_bucket_penalty", 0) or 0),
            "push_eligible": bool(signal.get("push_eligible")),
        },
        "entry_price": _as_float(signal.get("entry_price"), 0.0),
        "sl_price": _as_float(signal.get("stop_loss"), 0.0),
        "tp1_price": _as_float(signal.get("tp1"), 0.0),
        "tp2_price": _as_float(signal.get("tp2"), 0.0),
        "tp3_price": _as_float(signal.get("tp3"), 0.0),
        "generated_at": generated_at.isoformat(),
        "expires_at": (_parse_iso(signal.get("expires_at")) or (generated_at + timedelta(minutes=5))).isoformat(),
        "outcome_deadline_at": (generated_at + timedelta(hours=max(1, int(deadline_hours)))).isoformat(),
        "updated_at": _iso_now(),
    }
    try:
        res = (
            _client()
            .table("one_click_signal_events")
            .upsert(payload, on_conflict="signal_id")
            .execute()
        )
        rows = res.data or []
        return dict(rows[0]) if rows else payload
    except Exception as exc:
        logger.warning("[OneClickHub] upsert_signal_event failed: %s", exc)
        return None


def mark_event_push_window(signal_id: str, *, started: bool) -> None:
    if not signal_id:
        return
    fields = {"updated_at": _iso_now()}
    if started:
        fields["push_started_at"] = _iso_now()
    else:
        fields["push_completed_at"] = _iso_now()
    try:
        _client().table("one_click_signal_events").update(fields).eq("signal_id", str(signal_id)).execute()
    except Exception as exc:
        logger.warning("[OneClickHub] mark_event_push_window failed: %s", exc)


def upsert_signal_receipt(
    *,
    signal_id: str,
    telegram_id: int,
    audience_status: str,
    eligible: bool,
    eligibility_reason: str,
    delivery_status: str,
    delivery_error: str = "",
) -> Optional[Dict[str, Any]]:
    payload = {
        "signal_id": str(signal_id),
        "telegram_id": int(telegram_id),
        "audience_status": str(audience_status or "verified"),
        "eligible": bool(eligible),
        "eligibility_reason": str(eligibility_reason or ""),
        "delivery_status": str(delivery_status or "pending"),
        "delivery_error": str(delivery_error or ""),
        "delivered_at": _iso_now() if str(delivery_status or "").lower() == "sent" else None,
        "updated_at": _iso_now(),
    }
    try:
        res = (
            _client()
            .table("one_click_signal_receipts")
            .upsert(payload, on_conflict="signal_id,telegram_id")
            .execute()
        )
        rows = res.data or []
        return dict(rows[0]) if rows else payload
    except Exception as exc:
        logger.warning("[OneClickHub] upsert_signal_receipt failed: %s", exc)
        return None


def mark_receipt_opened_for_signal(signal_id: str, telegram_id: int, trade_id: Optional[int] = None) -> None:
    if not signal_id or not telegram_id:
        return
    fields = {
        "opened_at": _iso_now(),
        "opened_trade_id": int(trade_id) if trade_id else None,
        "updated_at": _iso_now(),
    }
    try:
        _client().table("one_click_signal_receipts").update(fields).eq("signal_id", str(signal_id)).eq(
            "telegram_id", int(telegram_id)
        ).execute()
    except Exception as exc:
        logger.warning("[OneClickHub] mark_receipt_opened_for_signal failed: %s", exc)


def list_pending_outcome_events(limit: int = 100) -> List[Dict[str, Any]]:
    try:
        res = (
            _client()
            .table("one_click_signal_events")
            .select("*")
            .eq("outcome_status", "pending")
            .not_.is_("push_started_at", "null")
            .order("generated_at", desc=False)
            .limit(max(1, int(limit)))
            .execute()
        )
        return [dict(r) for r in (res.data or [])]
    except Exception as exc:
        logger.warning("[OneClickHub] list_pending_outcome_events failed: %s", exc)
        return []


def update_event_outcome(
    signal_id: str,
    *,
    outcome_status: str,
    outcome_level: str = "",
    outcome_price: float = 0.0,
) -> None:
    if not signal_id:
        return
    fields = {
        "outcome_status": str(outcome_status or "pending"),
        "outcome_level": str(outcome_level or None) if outcome_level else None,
        "outcome_price": float(outcome_price) if outcome_price else None,
        "outcome_at": _iso_now() if outcome_status != "pending" else None,
        "updated_at": _iso_now(),
    }
    try:
        _client().table("one_click_signal_events").update(fields).eq("signal_id", str(signal_id)).execute()
    except Exception as exc:
        logger.warning("[OneClickHub] update_event_outcome failed: %s", exc)


def list_pending_missed_receipts(signal_id: str) -> List[Dict[str, Any]]:
    try:
        res = (
            _client()
            .table("one_click_signal_receipts")
            .select("*")
            .eq("signal_id", str(signal_id))
            .eq("eligible", True)
            .eq("delivery_status", "sent")
            .is_("opened_at", "null")
            .is_("missed_alert_sent_at", "null")
            .execute()
        )
        return [dict(r) for r in (res.data or [])]
    except Exception as exc:
        logger.warning("[OneClickHub] list_pending_missed_receipts failed: %s", exc)
        return []


def mark_missed_alert_result(
    *,
    signal_id: str,
    telegram_id: int,
    status: str,
    error: str = "",
    tp_level_hit: str = "",
    projected_pnl_usdt: float = 0.0,
    projected_rr: float = 0.0,
    risk_pct_used: float = 0.0,
    equity_used_usdt: float = 0.0,
    example_used: bool = False,
) -> None:
    fields = {
        "missed_alert_status": str(status or "failed"),
        "missed_alert_error": str(error or ""),
        "missed_alert_sent_at": _iso_now(),
        "tp_level_hit": str(tp_level_hit or None) if tp_level_hit else None,
        "projected_pnl_usdt": float(projected_pnl_usdt),
        "projected_rr": float(projected_rr),
        "risk_pct_used": float(risk_pct_used),
        "equity_used_usdt": float(equity_used_usdt),
        "example_used": bool(example_used),
        "updated_at": _iso_now(),
    }
    try:
        _client().table("one_click_signal_receipts").update(fields).eq("signal_id", str(signal_id)).eq(
            "telegram_id", int(telegram_id)
        ).execute()
    except Exception as exc:
        logger.warning("[OneClickHub] mark_missed_alert_result failed: %s", exc)


def get_user_risk_pct(telegram_id: int) -> float:
    try:
        res = (
            _client()
            .table("autotrade_sessions")
            .select("risk_per_trade")
            .eq("telegram_id", int(telegram_id))
            .limit(1)
            .execute()
        )
        row = (res.data or [{}])[0]
        return _clamp_risk_pct(row.get("risk_per_trade"), default=DEFAULT_RISK_PCT)
    except Exception:
        return float(DEFAULT_RISK_PCT)


def get_user_equity_snapshot(telegram_id: int) -> Dict[str, Any]:
    # 1) Live equity from exchange (preferred)
    try:
        keys = get_user_api_key(int(telegram_id))
        if keys:
            exchange_id = str(keys.get("exchange") or "bitunix")
            client = get_client(exchange_id, keys["api_key"], keys["api_secret"])
            acc = client.get_account_info()
            if acc.get("success"):
                available = _as_float(acc.get("available"), 0.0)
                frozen = _as_float(acc.get("frozen"), 0.0)
                unrealized = _as_float(acc.get("total_unrealized_pnl"), 0.0)
                equity = available + frozen + unrealized
                if equity > 0:
                    return {"equity": float(equity), "source": "live_exchange"}
    except Exception:
        pass

    # 2) Session snapshot fallback
    try:
        res = (
            _client()
            .table("autotrade_sessions")
            .select("current_balance,initial_deposit")
            .eq("telegram_id", int(telegram_id))
            .limit(1)
            .execute()
        )
        row = (res.data or [{}])[0]
        current = _as_float(row.get("current_balance"), 0.0)
        if current > 0:
            return {"equity": current, "source": "session_current_balance"}
        initial = _as_float(row.get("initial_deposit"), 0.0)
        if initial > 0:
            return {"equity": initial, "source": "session_initial_deposit"}
    except Exception:
        pass
    return {"equity": 0.0, "source": "none"}


def projected_missed_pnl(telegram_id: int, rr_hit: float) -> Dict[str, Any]:
    rr = max(0.0, _as_float(rr_hit, 0.0))
    risk_pct = get_user_risk_pct(int(telegram_id))
    eq_snap = get_user_equity_snapshot(int(telegram_id))
    equity = _as_float(eq_snap.get("equity"), 0.0)
    risk_amount = max(0.0, equity * (risk_pct / 100.0))
    if equity > 0:
        return {
            "projected_pnl_usdt": round(risk_amount * rr, 4),
            "risk_pct_used": round(risk_pct, 4),
            "equity_used_usdt": round(equity, 4),
            "trade_value_usdt": round(risk_amount, 4),
            "example_used": False,
            "equity_source": str(eq_snap.get("source") or "live_exchange"),
            "example_note": "",
        }

    # Zero-equity fallback example (as requested): $100 deposit with 10% risk.
    example_equity = 100.0
    example_risk_pct = 10.0
    example_risk_amount = example_equity * (example_risk_pct / 100.0)
    return {
        # Keep real account-context lines visible even when equity is zero.
        "projected_pnl_usdt": round(risk_amount * rr, 4),
        "risk_pct_used": round(risk_pct, 4),
        "equity_used_usdt": round(equity, 4),
        "trade_value_usdt": round(risk_amount, 4),
        "example_used": True,
        "equity_source": "example_zero_equity",
        "example_equity_usdt": round(example_equity, 4),
        "example_risk_pct": round(example_risk_pct, 4),
        "example_trade_value_usdt": round(example_risk_amount, 4),
        "example_projected_pnl_usdt": round(example_risk_amount * rr, 4),
        "example_note": "If you deposit $100 and use 10% risk/trade, this setup could have returned this amount.",
    }


def detect_tp_hit(event_row: Dict[str, Any], mark_price: float) -> Dict[str, Any]:
    side = str(event_row.get("direction") or "LONG").upper()
    tp1 = _as_float(event_row.get("tp1_price"), 0.0)
    tp2 = _as_float(event_row.get("tp2_price"), tp1)
    tp3 = _as_float(event_row.get("tp3_price"), tp2)
    if mark_price <= 0:
        return {"hit": False, "level": "", "tp_price": 0.0, "rr_hit": 0.0}

    if side == "LONG":
        if tp3 > 0 and mark_price >= tp3:
            lvl, tp_price = "TP3", tp3
        elif tp2 > 0 and mark_price >= tp2:
            lvl, tp_price = "TP2", tp2
        elif tp1 > 0 and mark_price >= tp1:
            lvl, tp_price = "TP1", tp1
        else:
            return {"hit": False, "level": "", "tp_price": 0.0, "rr_hit": 0.0}
    else:
        if tp3 > 0 and mark_price <= tp3:
            lvl, tp_price = "TP3", tp3
        elif tp2 > 0 and mark_price <= tp2:
            lvl, tp_price = "TP2", tp2
        elif tp1 > 0 and mark_price <= tp1:
            lvl, tp_price = "TP1", tp1
        else:
            return {"hit": False, "level": "", "tp_price": 0.0, "rr_hit": 0.0}

    entry = _as_float(event_row.get("entry_price"), 0.0)
    sl = _as_float(event_row.get("sl_price"), 0.0)
    denom = abs(entry - sl)
    rr_hit = abs(tp_price - entry) / denom if denom > 0 else 0.0
    return {"hit": True, "level": lvl, "tp_price": float(tp_price), "rr_hit": float(rr_hit)}
