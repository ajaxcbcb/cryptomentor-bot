from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional

from app.db.supabase import _client


logger = logging.getLogger(__name__)


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
    return str(symbol or "").upper().replace("/", "").strip()


def _norm_side(side: Any) -> str:
    s = str(side or "").upper().strip()
    if s in ("BUY", "LONG"):
        return "LONG"
    if s in ("SELL", "SHORT"):
        return "SHORT"
    return s


def find_by_client_request_id(tg_id: int, client_request_id: str) -> Optional[Dict[str, Any]]:
    req_id = str(client_request_id or "").strip()
    if not req_id:
        return None
    try:
        res = (
            _client()
            .table("one_click_trades")
            .select("*")
            .eq("telegram_id", int(tg_id))
            .eq("client_request_id", req_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        return dict(rows[0]) if rows else None
    except Exception as e:
        logger.warning("[OneClickRepo] find_by_client_request_id failed: %s", e)
        return None


def find_recent_by_client_request_id(
    tg_id: int,
    client_request_id: str,
    within_seconds: int = 600,
) -> Optional[Dict[str, Any]]:
    row = find_by_client_request_id(tg_id, client_request_id)
    if not row:
        return None
    created_at = _parse_iso(row.get("created_at"))
    if not created_at:
        return None
    age = (_now_utc() - created_at).total_seconds()
    if age <= max(1, int(within_seconds)):
        return row
    return None


def create_attempt(
    tg_id: int,
    signal_id: str,
    client_request_id: str,
    symbol: str,
    side: str,
    requested_risk_pct: float,
    accepted_risk_pct: float,
    leverage: int,
    sl_price: float,
    tp_price: float,
) -> Optional[Dict[str, Any]]:
    payload = {
        "telegram_id": int(tg_id),
        "signal_id": str(signal_id),
        "client_request_id": str(client_request_id),
        "symbol": _norm_symbol(symbol),
        "side": _norm_side(side),
        "status": "pending_submit",
        "requested_risk_pct": float(requested_risk_pct),
        "accepted_risk_pct": float(accepted_risk_pct),
        "leverage": int(leverage),
        "sl_price": float(sl_price),
        "tp_price": float(tp_price),
        "created_at": _iso_now(),
        "updated_at": _iso_now(),
    }
    try:
        res = _client().table("one_click_trades").insert(payload).execute()
        rows = res.data or []
        return dict(rows[0]) if rows else payload
    except Exception as e:
        logger.warning("[OneClickRepo] create_attempt failed: %s", e)
        return None


def update_trade(trade_id: Any, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not trade_id:
        return None
    payload = dict(fields or {})
    payload["updated_at"] = _iso_now()
    try:
        res = _client().table("one_click_trades").update(payload).eq("id", trade_id).execute()
        rows = res.data or []
        return dict(rows[0]) if rows else None
    except Exception as e:
        logger.warning("[OneClickRepo] update_trade failed: %s", e)
        return None


def mark_rejected(
    trade_id: Any,
    reason_code: str,
    reason_message: str,
) -> Optional[Dict[str, Any]]:
    return update_trade(
        trade_id,
        {
            "status": "rejected",
            "reason_code": str(reason_code or "rejected"),
            "reason_message": str(reason_message or ""),
        },
    )


def mark_open(
    trade_id: Any,
    *,
    entry_price: float,
    qty: float,
    margin_required_usdt: float,
    risk_amount_usdt: float,
    cap_applied: bool,
    cap_reason: str,
    exchange_order_id: str,
    exchange_position_id: str,
) -> Optional[Dict[str, Any]]:
    return update_trade(
        trade_id,
        {
            "status": "open",
            "entry_price": float(entry_price),
            "qty": float(qty),
            "margin_required_usdt": float(margin_required_usdt),
            "risk_amount_usdt": float(risk_amount_usdt),
            "cap_applied": bool(cap_applied),
            "cap_reason": str(cap_reason or ""),
            "exchange_order_id": str(exchange_order_id or ""),
            "exchange_position_id": str(exchange_position_id or ""),
            "opened_at": _iso_now(),
            "reason_code": "executed",
            "reason_message": "order accepted by exchange",
        },
    )


def mark_closed_manual(
    tg_id: int,
    symbol: str,
    side: str,
) -> Optional[Dict[str, Any]]:
    sym = _norm_symbol(symbol)
    sd = _norm_side(side)
    try:
        res = (
            _client()
            .table("one_click_trades")
            .select("*")
            .eq("telegram_id", int(tg_id))
            .eq("symbol", sym)
            .eq("status", "open")
            .order("opened_at", desc=True)
            .limit(10)
            .execute()
        )
        rows = [dict(r) for r in (res.data or [])]
        if not rows:
            return None
        target = None
        for row in rows:
            if sd and _norm_side(row.get("side")) != sd:
                continue
            target = row
            break
        if not target:
            target = rows[0]
        return update_trade(
            target.get("id"),
            {
                "status": "closed_manual",
                "closed_at": _iso_now(),
                "reason_code": "manual_close",
                "reason_message": "closed manually from dashboard",
            },
        )
    except Exception as e:
        logger.warning("[OneClickRepo] mark_closed_manual failed: %s", e)
        return None


def get_open_trades(tg_id: int) -> List[Dict[str, Any]]:
    try:
        res = (
            _client()
            .table("one_click_trades")
            .select("*")
            .eq("telegram_id", int(tg_id))
            .eq("status", "open")
            .order("opened_at", desc=True)
            .execute()
        )
        return [dict(r) for r in (res.data or [])]
    except Exception as e:
        logger.warning("[OneClickRepo] get_open_trades failed: %s", e)
        return []


def recent_symbol_states(
    tg_id: int,
    lookback_hours: int = 24,
) -> Dict[str, Dict[str, Any]]:
    since = (_now_utc() - timedelta(hours=max(1, int(lookback_hours)))).isoformat()
    out: Dict[str, Dict[str, Any]] = {}
    try:
        res = (
            _client()
            .table("one_click_trades")
            .select(
                "id,symbol,side,status,reason_code,reason_message,entry_price,qty,"
                "opened_at,closed_at,created_at,updated_at"
            )
            .eq("telegram_id", int(tg_id))
            .gte("created_at", since)
            .order("created_at", desc=True)
            .execute()
        )
        for row in (res.data or []):
            item = dict(row)
            sym = _norm_symbol(item.get("symbol"))
            if not sym or sym in out:
                continue
            out[sym] = item
    except Exception as e:
        logger.warning("[OneClickRepo] recent_symbol_states failed: %s", e)
    return out
