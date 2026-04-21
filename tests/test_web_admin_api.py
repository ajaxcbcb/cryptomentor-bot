import importlib
import os
import sys

import pytest
from fastapi import HTTPException


_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WEB_BACKEND = os.path.join(_ROOT, "website-backend")
if _WEB_BACKEND not in sys.path:
    sys.path.insert(0, _WEB_BACKEND)

for _name in list(sys.modules.keys()):
    if _name == "app" or _name.startswith("app."):
        del sys.modules[_name]

admin_route = importlib.import_module("app.routes.admin")
admin_auth = importlib.import_module("app.auth.admin")
user_route = importlib.import_module("app.routes.user")


def test_require_admin_user_blocks_non_admin(monkeypatch):
    monkeypatch.setattr(admin_auth, "load_admin_ids", lambda: [111, 222])
    with pytest.raises(HTTPException) as err:
        admin_auth.require_admin_user(999)
    assert err.value.status_code == 403


def test_augment_user_with_admin_flag(monkeypatch):
    monkeypatch.setattr(admin_auth, "load_admin_ids", lambda: [111, 222])
    out = admin_auth.augment_user_with_admin({"telegram_id": 111, "first_name": "Ada"})
    assert out["is_admin"] is True


@pytest.mark.asyncio
async def test_admin_bootstrap_payload(monkeypatch):
    monkeypatch.setattr(
        admin_route,
        "get_decision_tree_snapshot",
        lambda window="30m", tail=6: {
            "db": {"live_candidate_count": 12, "approved_count": 1, "rejected_count": 11}
        },
    )
    monkeypatch.setattr(
        admin_route,
        "get_user_stats_summary",
        lambda: {
            "total_users": 40,
            "premium_users": 5,
            "lifetime_users": 2,
            "verified_users": 12,
            "unverified_users": 28,
            "engine_active_users": 17,
            "engine_stopped_users": 9,
            "free_users": 35,
            "new_today": 3,
        },
    )
    monkeypatch.setattr(
        admin_route,
        "get_signal_control_snapshot",
        lambda: {"enabled": True, "timeframe": "15m", "top_n": 25},
    )

    payload = await admin_route.admin_bootstrap(requester=123)
    assert payload["is_admin"] is True
    assert payload["summary_cards"]["candidates"]["live_candidate_count"] == 12
    assert payload["summary_cards"]["signals"]["enabled"] is True
    assert payload["summary_cards"]["users"]["unverified_users"] == 28
    assert payload["summary_cards"]["users"]["engine_active_users"] == 17


@pytest.mark.asyncio
async def test_trade_candidates_export_returns_csv(monkeypatch):
    monkeypatch.setattr(
        admin_route,
        "list_trade_candidates",
        lambda **kwargs: {
            "rows": [
                {
                    "created_at": "2026-04-21T05:00:00+00:00",
                    "symbol": "BTCUSDT",
                    "engine": "scalping",
                    "side": "LONG",
                    "regime": "trend_continuation",
                    "setup_name": "breakout",
                    "user_equity_tier": "nano",
                    "approved": False,
                    "reject_reason": "tradeability_below_threshold",
                    "display_reason": "Tradeability below threshold",
                    "signal_confidence": 82.0,
                    "tradeability_score": 0.25,
                    "approval_score": 0.0,
                    "community_score": 0.0,
                    "user_segment_score": 0.2,
                    "portfolio_penalty": 0.0,
                    "final_score": 0.33,
                    "recommended_risk_pct": 0.5,
                }
            ],
            "total": 1,
        },
    )

    response = await admin_route.admin_trade_candidates_export(fmt="csv", requester=123)
    assert response.media_type == "text/csv"
    assert "BTCUSDT" in response.body.decode()


@pytest.mark.asyncio
async def test_user_me_exposes_is_admin(monkeypatch):
    monkeypatch.setattr(user_route, "get_user_by_tid", lambda tg_id: {"telegram_id": tg_id, "first_name": "Root"})
    monkeypatch.setattr(user_route, "augment_user_with_admin", lambda user: {**user, "is_admin": True})
    payload = await user_route.get_me(tg_id=555)
    assert payload["is_admin"] is True


def test_fetch_all_user_ids_supports_new_admin_and_partner_audiences(monkeypatch):
    monkeypatch.setattr(
        admin_route,
        "_fetch_table_rows",
        lambda _client, table, _columns: (
            [
                {"telegram_id": 301, "is_premium": False, "is_lifetime": False},
                {"telegram_id": 302, "is_premium": True, "is_lifetime": False},
                {"telegram_id": 303, "is_premium": False, "is_lifetime": False},
            ]
            if table == "users"
            else [
                {"telegram_id": 301, "status": "active"},
                {"telegram_id": 304, "status": "pending"},
                {"telegram_id": 305, "status": "active"},
            ]
        ),
    )
    monkeypatch.setattr(admin_route, "_client", lambda: object())
    monkeypatch.setattr(admin_route, "load_admin_ids", lambda: [999, 888, 999])

    admins = admin_route._fetch_all_user_ids("telegram_admins")
    partners = admin_route._fetch_all_user_ids("community_partners")

    assert admins == [888, 999]
    assert partners == [301, 305]


def test_fetch_all_user_ids_verified_and_non_verified_remain_deduped(monkeypatch):
    def _rows(_client, table, _columns):
        if table == "users":
            return [
                {"telegram_id": 1, "is_premium": False, "is_lifetime": False},
                {"telegram_id": 2, "is_premium": False, "is_lifetime": False},
                {"telegram_id": 3, "is_premium": False, "is_lifetime": False},
            ]
        return [
            {"telegram_id": 1, "status": "approved"},
            {"telegram_id": 4, "status": "active"},  # not in users table, should be excluded
            {"telegram_id": 1, "status": "verified"},
        ]

    monkeypatch.setattr(admin_route, "_fetch_table_rows", _rows)
    monkeypatch.setattr(admin_route, "_client", lambda: object())

    assert admin_route._fetch_all_user_ids("verified") == [1]
    assert admin_route._fetch_all_user_ids("non_verified") == [2, 3]


@pytest.mark.asyncio
async def test_admin_daily_report_now_returns_metrics(monkeypatch):
    monkeypatch.setattr(admin_route, "_load_bot_token", lambda: "token")
    monkeypatch.setattr(
        admin_route,
        "_run_daily_report_isolated",
        lambda _token: {
            "ok": True,
            "metrics": {
                "TOTAL_TARGET": 2,
                "SENT": 2,
                "FAILED": 0,
                "BLOCKED_OR_FORBIDDEN": 0,
            },
        },
    )

    payload = await admin_route.admin_daily_report_now(requester=123)
    assert payload["ok"] is True
    assert payload["metrics"]["SENT"] == 2


@pytest.mark.asyncio
async def test_admin_daily_report_now_raises_on_failure(monkeypatch):
    monkeypatch.setattr(admin_route, "_load_bot_token", lambda: "token")
    monkeypatch.setattr(
        admin_route,
        "_run_daily_report_isolated",
        lambda _token: {
            "ok": False,
            "error": "no_admin_targets",
            "metrics": {
                "TOTAL_TARGET": 0,
                "SENT": 0,
                "FAILED": 0,
                "BLOCKED_OR_FORBIDDEN": 0,
            },
        },
    )

    with pytest.raises(HTTPException) as err:
        await admin_route.admin_daily_report_now(requester=123)
    assert err.value.status_code == 500
