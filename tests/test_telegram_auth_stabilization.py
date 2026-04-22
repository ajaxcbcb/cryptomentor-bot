from __future__ import annotations

import hashlib
import hmac
import importlib
import os
import pathlib
import sys
import time
import types

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _load_auth_modules(monkeypatch, *, bot_token: str = "unit-test-bot-token", max_age_seconds: int = 86400):
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    backend_root = repo_root / "website-backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", bot_token)
    monkeypatch.setenv("JWT_SECRET", "unit-test-jwt-secret")
    monkeypatch.setenv("JWT_EXPIRE_HOURS", "24")
    monkeypatch.setenv("TELEGRAM_AUTH_MAX_AGE_SECONDS", str(max_age_seconds))
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key")

    for name in list(sys.modules.keys()):
        if (
            name == "config"
            or name == "app"
            or name.startswith("app.")
        ):
            del sys.modules[name]

    fake_jwt_module = types.ModuleType("app.auth.jwt")
    fake_jwt_module.create_token = lambda telegram_id, extra=None: "stubbed-jwt"
    fake_jwt_module.decode_token = lambda token: {"sub": "1"}
    sys.modules["app.auth.jwt"] = fake_jwt_module

    telegram_auth = importlib.import_module("app.auth.telegram")
    auth_route = importlib.import_module("app.routes.auth")
    return telegram_auth, auth_route


def _build_signed_payload(bot_token: str, *, auth_date: int | None = None, **overrides):
    payload = {
        "id": 123456789,
        "first_name": "Alice",
        "username": "alice",
        "auth_date": int(auth_date if auth_date is not None else time.time()),
    }
    payload.update(overrides)
    signing_fields = {
        k: str(v)
        for k, v in payload.items()
        if k in {"id", "first_name", "last_name", "username", "photo_url", "auth_date"} and v is not None
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(signing_fields.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return payload


def _build_client(auth_route, monkeypatch):
    monkeypatch.setattr(
        auth_route,
        "upsert_web_login",
        lambda tg_id, username, first_name, last_name, referred_by: {
            "telegram_id": tg_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "credits": 0,
            "is_premium": False,
        },
    )
    monkeypatch.setattr(auth_route, "augment_user_with_admin", lambda user: {**user, "is_admin": False})
    monkeypatch.setattr(auth_route, "create_token", lambda telegram_id, extra=None: "mocked-jwt-token")

    app = FastAPI()
    app.include_router(auth_route.router)
    return TestClient(app)


def test_telegram_login_valid_payload_returns_token(monkeypatch):
    bot_token = "unit-test-bot-token-a"
    _telegram_auth, auth_route = _load_auth_modules(monkeypatch, bot_token=bot_token)
    client = _build_client(auth_route, monkeypatch)

    payload = _build_signed_payload(bot_token)
    resp = client.post("/auth/telegram", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "mocked-jwt-token"
    assert data["token_type"] == "bearer"
    assert data["user"]["telegram_id"] == payload["id"]


def test_telegram_login_invalid_hash_returns_explicit_error_code(monkeypatch):
    bot_token = "unit-test-bot-token-b"
    _telegram_auth, auth_route = _load_auth_modules(monkeypatch, bot_token=bot_token)
    client = _build_client(auth_route, monkeypatch)

    payload = _build_signed_payload(bot_token)
    payload["hash"] = "bad-hash"
    resp = client.post("/auth/telegram", json=payload)

    assert resp.status_code == 401
    detail = resp.json()["detail"]
    assert detail["error_code"] == "telegram_auth_invalid"
    assert detail["reason_code"] == "invalid_signature"


def test_telegram_login_expired_returns_explicit_error_code(monkeypatch):
    bot_token = "unit-test-bot-token-c"
    _telegram_auth, auth_route = _load_auth_modules(monkeypatch, bot_token=bot_token, max_age_seconds=120)
    client = _build_client(auth_route, monkeypatch)

    payload = _build_signed_payload(bot_token, auth_date=int(time.time()) - 121)
    resp = client.post("/auth/telegram", json=payload)

    assert resp.status_code == 401
    detail = resp.json()["detail"]
    assert detail["error_code"] == "telegram_auth_expired"
    assert detail["reason_code"] == "auth_data_expired"
    assert detail["max_age_seconds"] == 120


def test_telegram_login_malformed_payload_returns_422(monkeypatch):
    bot_token = "unit-test-bot-token-d"
    _telegram_auth, auth_route = _load_auth_modules(monkeypatch, bot_token=bot_token)
    client = _build_client(auth_route, monkeypatch)

    payload = {
        "id": 123456789,
        "first_name": "Alice",
        "username": "alice",
        "hash": "some-hash",
    }
    resp = client.post("/auth/telegram", json=payload)

    assert resp.status_code == 422


def test_max_auth_age_env_override(monkeypatch):
    _telegram_auth, auth_route = _load_auth_modules(monkeypatch, bot_token="unit-test-bot-token-e", max_age_seconds=999)
    assert auth_route._resolve_max_auth_age_seconds() == 999
    assert auth_route.MAX_AUTH_AGE_SECONDS == 999


def test_invalid_login_logs_redacted_metadata(monkeypatch, caplog):
    bot_token = "unit-test-bot-token-f"
    _telegram_auth, auth_route = _load_auth_modules(monkeypatch, bot_token=bot_token)
    client = _build_client(auth_route, monkeypatch)

    payload = _build_signed_payload(bot_token)
    real_hash = payload["hash"]
    payload["hash"] = "broken-signature"

    with caplog.at_level("WARNING", logger="app.routes.auth"):
        resp = client.post("/auth/telegram", json=payload)

    assert resp.status_code == 401
    logs = caplog.text
    assert "telegram_auth_failure meta=" in logs
    assert "broken-signature" not in logs
    assert real_hash not in logs
