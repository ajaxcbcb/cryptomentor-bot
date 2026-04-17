from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib
import pathlib
import sys

import pytest
from fastapi import HTTPException


def _load_signals_module(monkeypatch, signing_key: str = "unit-test-signing-key"):
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    backend_root = repo_root / "website-backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    monkeypatch.setenv("ONE_CLICK_SIGNAL_SIGNING_KEY", signing_key)
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key")
    monkeypatch.setenv("JWT_SECRET", "jwt-secret")

    if "config" in sys.modules:
        importlib.reload(sys.modules["config"])
    if "app.routes.signals" in sys.modules:
        del sys.modules["app.routes.signals"]

    return importlib.import_module("app.routes.signals")


def _base_payload():
    now = datetime.now(timezone.utc)
    return {
        "v": 1,
        "signal_id": "sig_unit_test_01",
        "symbol": "BTCUSDT",
        "pair": "BTC/USDT",
        "direction": "LONG",
        "stop_loss": 62000.0,
        "targets": [64000.0, 65000.0, 66000.0],
        "generated_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=5)).isoformat(),
        "model_source": "confluence_v1",
    }


def test_signal_token_roundtrip_valid(monkeypatch):
    signals = _load_signals_module(monkeypatch)
    payload = _base_payload()
    token = signals._sign_signal_payload(payload)
    decoded = signals._decode_signal_token(token)
    assert decoded["signal_id"] == payload["signal_id"]
    assert decoded["symbol"] == "BTCUSDT"
    assert decoded["side"] == "BUY"
    assert decoded["stop_loss"] == pytest.approx(62000.0)


def test_signal_token_rejects_expired(monkeypatch):
    signals = _load_signals_module(monkeypatch)
    payload = _base_payload()
    payload["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    token = signals._sign_signal_payload(payload)
    with pytest.raises(HTTPException) as err:
        signals._decode_signal_token(token)
    assert err.value.status_code == 410


def test_signal_token_rejects_tampered_signature(monkeypatch):
    signals = _load_signals_module(monkeypatch)
    payload = _base_payload()
    token = signals._sign_signal_payload(payload)
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(HTTPException) as err:
        signals._decode_signal_token(tampered)
    assert err.value.status_code == 400
    assert "signature" in str(err.value.detail).lower()


def test_compute_sizing_reports_effective_risk_after_cap(monkeypatch):
    signals = _load_signals_module(monkeypatch)
    sizing = signals._compute_sizing(
        symbol="BTCUSDT",
        entry_price=100000.0,
        sl_price=99000.0,
        tp_price=101200.0,
        leverage=10,
        balance=100.0,
        equity=1000.0,
        requested_risk_pct=50.0,
        accepted_risk_pct=50.0,
        all_in=False,
    )
    assert sizing["cap_applied"] is True
    assert sizing["cap_reason"] == "balance_margin_cap_95pct"
    assert sizing["risk_amount"] < 500.0  # capped below requested 50% of 1000
    assert sizing["effective_risk_pct"] < 50.0


def test_replay_open_response_preserves_long_direction(monkeypatch):
    signals = _load_signals_module(monkeypatch)
    row = {
        "signal_id": "sig_replay_long",
        "symbol": "BTCUSDT",
        "side": "LONG",
        "qty": 0.01,
        "entry_price": 65000.0,
        "tp_price": 66000.0,
        "sl_price": 64000.0,
        "margin_required_usdt": 65.0,
        "risk_amount_usdt": 10.0,
        "requested_risk_pct": 5.0,
        "accepted_risk_pct": 5.0,
        "leverage": 10,
        "cap_applied": False,
        "cap_reason": "",
        "exchange_order_id": "ord-1",
        "exchange_position_id": "pos-1",
    }
    replay = signals._replay_open_response(row)
    assert replay["direction"] == "LONG"
    assert replay["idempotency_status"] == "replayed"
