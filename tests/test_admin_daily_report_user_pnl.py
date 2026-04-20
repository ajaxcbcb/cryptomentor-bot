import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

from app.admin_daily_report import _build_user_pnl_breakdown_rows  # type: ignore


def test_build_user_pnl_breakdown_includes_all_session_users_and_rolls_up_pnl():
    sessions = [
        {"telegram_id": 111, "status": "active", "trading_mode": "scalping"},
        {"telegram_id": 222, "status": "stopped", "trading_mode": "swing"},
    ]
    trades = [
        {"telegram_id": 111, "status": "closed_tp", "pnl_usdt": 2.5},
        {"telegram_id": 111, "status": "closed_sl", "pnl_usdt": -1.0},
        {"telegram_id": 111, "status": "open", "pnl_usdt": None},
    ]

    rows = _build_user_pnl_breakdown_rows(sessions, trades)
    by_uid = {int(r["telegram_id"]): r for r in rows}

    assert sorted(by_uid.keys()) == [111, 222]
    assert by_uid[111]["opened"] == 3
    assert by_uid[111]["closed"] == 2
    assert by_uid[111]["open_now"] == 1
    assert by_uid[111]["wins"] == 1
    assert by_uid[111]["losses"] == 1
    assert float(by_uid[111]["pnl_usdt"]) == 1.5
    assert by_uid[111]["status"] == "active"
    assert by_uid[111]["trading_mode"] == "scalping"

    # Session user with no trade activity remains visible with zero PnL.
    assert by_uid[222]["opened"] == 0
    assert by_uid[222]["closed"] == 0
    assert by_uid[222]["open_now"] == 0
    assert by_uid[222]["wins"] == 0
    assert by_uid[222]["losses"] == 0
    assert float(by_uid[222]["pnl_usdt"]) == 0.0


def test_build_user_pnl_breakdown_includes_trade_only_users_without_session():
    sessions = [{"telegram_id": 111, "status": "active", "trading_mode": "scalping"}]
    trades = [
        {"telegram_id": 999, "status": "closed_tp", "pnl_usdt": 4.2},
        {"telegram_id": 999, "status": "closed_sl", "pnl_usdt": -1.2},
    ]

    rows = _build_user_pnl_breakdown_rows(sessions, trades)
    by_uid = {int(r["telegram_id"]): r for r in rows}

    assert sorted(by_uid.keys()) == [111, 999]
    assert by_uid[999]["status"] == "no_session"
    assert by_uid[999]["trading_mode"] == "-"
    assert by_uid[999]["opened"] == 2
    assert by_uid[999]["closed"] == 2
    assert by_uid[999]["wins"] == 1
    assert by_uid[999]["losses"] == 1
    assert float(by_uid[999]["pnl_usdt"]) == 3.0
