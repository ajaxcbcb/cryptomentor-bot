import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

import app.scheduler as scheduler  # type: ignore
import app.trade_history as trade_history  # type: ignore
import app.supabase_repo as supabase_repo  # type: ignore
import app.exchange_registry as exchange_registry  # type: ignore
import app.autotrade_engine as autotrade_engine  # type: ignore


@pytest.mark.asyncio
async def test_startup_reconcile_close_alert_send_failure_is_non_fatal(monkeypatch):
    monkeypatch.setattr(
        trade_history,
        "get_all_open_trades",
        lambda: [{"telegram_id": 111, "symbol": "BTCUSDT", "status": "open"}],
    )
    monkeypatch.setattr(
        trade_history,
        "inspect_open_trade_drift",
        lambda _uid, _client, _trade_type=None: {"exchange_fetch_ok": True, "open_trades": []},
    )
    monkeypatch.setattr(
        trade_history,
        "apply_open_trade_reconcile",
        lambda _uid, _client, _trade_type=None, _drift=None: {
            "exchange_fetch_ok": True,
            "exchange_open_count": 0,
            "db_open_count": 1,
            "healed_count": 1,
            "stale_symbols": ["BTCUSDT"],
            "healed_closes": [
                {
                    "trade_id": 901,
                    "symbol": "BTCUSDT",
                    "side": "LONG",
                    "entry_price": 100.0,
                    "exit_price": 99.0,
                    "pnl_usdt": -1.0,
                    "close_reason": "stale_reconcile",
                    "trade_type": "swing",
                }
            ],
            "live_symbols": [],
        },
    )
    monkeypatch.setattr(trade_history, "get_open_trades", lambda _uid, _trade_type=None: [])
    monkeypatch.setattr(
        supabase_repo,
        "get_user_api_key",
        lambda _uid: {"exchange": "bitunix", "api_key": "k", "api_secret": "s"},
    )
    monkeypatch.setattr(exchange_registry, "get_client", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(autotrade_engine, "_compute_signal_pro", lambda *_args, **_kwargs: None)

    send_message = AsyncMock(side_effect=RuntimeError("telegram send failed"))
    app = SimpleNamespace(bot=SimpleNamespace(send_message=send_message))

    await scheduler._check_stale_positions(app)
    send_message.assert_awaited()
