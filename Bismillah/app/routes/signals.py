"""Compatibility helpers for one-click signal security tests.

This module intentionally mirrors the security/sizing helpers used by the
website backend, but stays dependency-light so importing ``app.routes.signals``
from the bot package is stable in mixed test runs.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import HTTPException


SIGNAL_TOKEN_VERSION = 1
ONE_CLICK_RISK_MAX_PCT = 10.0

# Keep parity with core pair set used across runtime paths.
_WATCHLIST_SYMBOLS = {
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "AVAXUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "ADAUSDT",
    "DOTUSDT",
    "MATICUSDT",
    "LTCUSDT",
}

_QTY_PRECISION = {
    "BTCUSDT": 3,
    "ETHUSDT": 2,
    "AVAXUSDT": 2,
    "SOLUSDT": 1,
    "BNBUSDT": 2,
    "XRPUSDT": 0,
    "DOGEUSDT": 0,
    "LINKUSDT": 1,
    "ADAUSDT": 0,
    "DOTUSDT": 1,
    "MATICUSDT": 0,
    "LTCUSDT": 2,
}


def _signing_key() -> str:
    key = os.getenv("ONE_CLICK_SIGNAL_SIGNING_KEY", "").strip()
    return key or "dev-insecure-signing-key"


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _norm_symbol(symbol: Any) -> str:
    return str(symbol or "").upper().replace("/", "").strip()


def _norm_side(side: Any) -> str:
    normalized = str(side or "").upper().strip()
    if normalized in {"BUY", "LONG"}:
        return "BUY"
    if normalized in {"SELL", "SHORT"}:
        return "SELL"
    return normalized


def _iso_to_dt(value: str) -> datetime:
    raw = str(value).replace("Z", "+00:00")
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _b64u_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64u_decode(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _sign_signal_payload(payload: Dict[str, Any]) -> str:
    message = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(_signing_key().encode("utf-8"), message, digestmod=hashlib.sha256).digest()
    return f"{_b64u_encode(message)}.{_b64u_encode(sig)}"


def _decode_signal_token(token: str) -> Dict[str, Any]:
    raw = str(token or "").strip()
    if not raw or "." not in raw:
        raise HTTPException(status_code=400, detail="Invalid signal token")
    encoded_payload, encoded_sig = raw.split(".", 1)
    try:
        payload_bytes = _b64u_decode(encoded_payload)
        supplied_sig = _b64u_decode(encoded_sig)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Malformed signal token") from exc

    expected_sig = hmac.new(
        _signing_key().encode("utf-8"),
        payload_bytes,
        digestmod=hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(supplied_sig, expected_sig):
        raise HTTPException(status_code=400, detail="Signal token signature mismatch")

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Signal token payload invalid") from exc

    required = (
        "v",
        "signal_id",
        "symbol",
        "pair",
        "direction",
        "stop_loss",
        "targets",
        "generated_at",
        "expires_at",
        "model_source",
    )
    missing = [key for key in required if key not in payload]
    if missing:
        raise HTTPException(status_code=400, detail=f"Signal token missing fields: {','.join(missing)}")
    if int(payload.get("v", 0)) != SIGNAL_TOKEN_VERSION:
        raise HTTPException(status_code=400, detail="Signal token version mismatch")

    try:
        expires_at = _iso_to_dt(str(payload["expires_at"]))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Signal token expires_at invalid") from exc
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=410, detail="Signal token expired")

    symbol = _norm_symbol(payload.get("symbol"))
    if symbol not in _WATCHLIST_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Token symbol {symbol} not in watchlist")

    payload["symbol"] = symbol
    payload["side"] = "BUY" if str(payload.get("direction")).upper() == "LONG" else "SELL"
    payload["stop_loss"] = _as_float(payload.get("stop_loss"), 0.0)
    payload["targets"] = [_as_float(value, 0.0) for value in (payload.get("targets") or [])]
    if payload["stop_loss"] <= 0:
        raise HTTPException(status_code=400, detail="Signal token stop_loss invalid")
    return payload


def _compute_sizing(
    *,
    symbol: str,
    entry_price: float,
    sl_price: float,
    tp_price: float,
    leverage: int,
    balance: float,
    equity: float,
    requested_risk_pct: float,
    accepted_risk_pct: float,
    all_in: bool,
) -> Dict[str, Any]:
    del all_in  # Compatibility signature; sizing math does not need this value.

    sl_distance = abs(entry_price - sl_price)
    if sl_distance <= 0:
        raise HTTPException(status_code=400, detail="Invalid SL distance")
    sl_distance_pct = sl_distance / entry_price
    if sl_distance_pct < 0.001:
        raise HTTPException(status_code=400, detail="Stop loss too tight (<0.1%)")
    if sl_distance_pct > 0.15:
        raise HTTPException(status_code=400, detail="Stop loss too wide (>15%)")

    desired_risk_amount = equity * (accepted_risk_pct / 100.0)
    position_size_usdt = desired_risk_amount / sl_distance_pct
    margin_required = position_size_usdt / max(1, int(leverage))

    cap_applied = False
    cap_reason = ""
    if margin_required > balance * 0.95:
        cap_applied = True
        cap_reason = "balance_margin_cap_95pct"
        margin_required = balance * 0.95
        position_size_usdt = margin_required * max(1, int(leverage))

    effective_risk_amount = position_size_usdt * sl_distance_pct
    effective_risk_pct = (effective_risk_amount / equity * 100.0) if equity > 0 else 0.0

    qty = position_size_usdt / entry_price
    precision = _QTY_PRECISION.get(_norm_symbol(symbol), 3)
    qty = round(qty, precision)
    min_qty = 10 ** (-precision) if precision > 0 else 1
    if qty < min_qty:
        raise HTTPException(
            status_code=400,
            detail=f"Computed qty {qty} below exchange minimum {min_qty}",
        )

    return {
        "qty": qty,
        "entry_price": round(entry_price, 6),
        "tp_price": round(tp_price, 6),
        "sl_price": round(sl_price, 6),
        "position_size_usdt": round(position_size_usdt, 2),
        "margin_required": round(margin_required, 2),
        "risk_amount": round(effective_risk_amount, 2),
        "requested_risk_pct": round(float(requested_risk_pct), 4),
        "risk_pct": round(float(accepted_risk_pct), 4),
        "effective_risk_pct": round(float(effective_risk_pct), 4),
        "all_in": accepted_risk_pct >= ONE_CLICK_RISK_MAX_PCT,
        "corrected": abs(float(requested_risk_pct) - float(accepted_risk_pct)) > 1e-9,
        "sl_distance_pct": round(sl_distance_pct * 100, 3),
        "leverage": int(leverage),
        "leverage_mode": "auto_max_pair",
        "cap_applied": cap_applied,
        "cap_reason": cap_reason,
    }


def _replay_open_response(row: Dict[str, Any]) -> Dict[str, Any]:
    requested = _as_float(row.get("requested_risk_pct"), 0.0)
    accepted = _as_float(row.get("accepted_risk_pct"), requested)
    side = _norm_side(row.get("side"))

    sizing = {
        "qty": _as_float(row.get("qty"), 0.0),
        "entry_price": _as_float(row.get("entry_price"), 0.0),
        "tp_price": _as_float(row.get("tp_price"), 0.0),
        "sl_price": _as_float(row.get("sl_price"), 0.0),
        "position_size_usdt": 0.0,
        "margin_required": _as_float(row.get("margin_required_usdt"), 0.0),
        "risk_amount": _as_float(row.get("risk_amount_usdt"), 0.0),
        "requested_risk_pct": round(requested, 4),
        "risk_pct": round(accepted, 4),
        "effective_risk_pct": round(accepted, 4),
        "all_in": accepted >= ONE_CLICK_RISK_MAX_PCT,
        "corrected": abs(requested - accepted) > 1e-9,
        "sl_distance_pct": 0.0,
        "leverage": int(_as_float(row.get("leverage"), 10)),
        "leverage_mode": "auto_max_pair",
        "cap_applied": bool(row.get("cap_applied")),
        "cap_reason": str(row.get("cap_reason") or ""),
    }

    return {
        "success": True,
        "signal_id": row.get("signal_id"),
        "symbol": row.get("symbol"),
        "direction": "LONG" if side == "BUY" else "SHORT",
        "idempotency_status": "replayed",
        "order": {
            "success": True,
            "order_id": row.get("exchange_order_id"),
            "position_id": row.get("exchange_position_id"),
        },
        "conflict_gate": {
            "allowed": True,
            "reason_code": "idempotent_replay",
            "reason": "Replayed prior successful request",
            "symbol": row.get("symbol"),
        },
        "account": {},
        "sizing": sizing,
        "warnings": [],
    }

