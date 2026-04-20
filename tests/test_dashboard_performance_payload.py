import importlib
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WEB_BACKEND = os.path.join(_ROOT, "website-backend")
if _WEB_BACKEND not in sys.path:
    sys.path.insert(0, _WEB_BACKEND)

for _name in list(sys.modules.keys()):
    if _name == "app" or _name.startswith("app."):
        del sys.modules[_name]

performance = importlib.import_module("app.routes.performance")


class _Result:
    def __init__(self, data):
        self.data = data


class _FakeTable:
    def __init__(self, db, table_name: str):
        self._db = db
        self._table_name = table_name
        self._filters = {}
        self._in_filters = {}
        self._gte_filters = {}
        self._order_col = None
        self._limit = None

    def select(self, _fields="*"):
        return self

    def eq(self, key, value):
        self._filters[key] = value
        return self

    def in_(self, key, values):
        self._in_filters[key] = set(values)
        return self

    def gte(self, key, value):
        self._gte_filters[key] = value
        return self

    def order(self, col, desc=False):
        self._order_col = (col, bool(desc))
        return self

    def limit(self, n):
        self._limit = int(n)
        return self

    def execute(self):
        rows = list(self._db.get(self._table_name, []))
        for key, value in self._filters.items():
            rows = [r for r in rows if r.get(key) == value]
        for key, allowed in self._in_filters.items():
            rows = [r for r in rows if r.get(key) in allowed]
        for key, floor in self._gte_filters.items():
            rows = [r for r in rows if str(r.get(key) or "") >= str(floor)]
        if self._order_col:
            col, desc = self._order_col
            rows = sorted(rows, key=lambda r: str(r.get(col) or ""), reverse=desc)
        if self._limit is not None:
            rows = rows[: self._limit]
        return _Result(rows)


class _FakeSupabase:
    def __init__(self, trades, sessions):
        self._db = {
            "autotrade_trades": list(trades),
            "autotrade_sessions": list(sessions),
        }

    def table(self, name):
        return _FakeTable(self._db, name)


@pytest.mark.asyncio
async def test_build_performance_payload_keeps_legacy_keys_and_adds_playbook_analysis(monkeypatch):
    trades = [
        {
            "symbol": "BTCUSDT",
            "pnl_usdt": 10.0,
            "status": "closed_tp",
            "close_reason": "closed_tp",
            "opened_at": "2026-04-18T10:00:00+00:00",
            "closed_at": "2026-04-18T11:00:00+00:00",
            "entry_reasons": ["Volume confirmation"],
            "trade_type": "swing",
            "timeframe": "15m",
            "confidence": 80,
            "entry_price": 100.0,
            "sl_price": 99.0,
            "qty": 1.0,
            "win_reasoning": "good trade",
            "playbook_match_score": 0.8,
            "telegram_id": 123,
        },
        {
            "symbol": "BTCUSDT",
            "pnl_usdt": -5.0,
            "status": "closed_sl",
            "close_reason": "closed_sl",
            "opened_at": "2026-04-19T10:00:00+00:00",
            "closed_at": "2026-04-19T11:00:00+00:00",
            "entry_reasons": ["RSI overbought"],
            "trade_type": "swing",
            "timeframe": "15m",
            "confidence": 74,
            "entry_price": 100.0,
            "sl_price": 99.0,
            "qty": 1.0,
            "win_reasoning": "",
            "playbook_match_score": 0.1,
            "telegram_id": 123,
        },
    ]
    sessions = [{"telegram_id": 123, "initial_deposit": 1000.0, "current_balance": 995.0}]
    fake = _FakeSupabase(trades, sessions)

    monkeypatch.setattr(performance, "_client", lambda: fake)
    monkeypatch.setattr(
        performance,
        "_PLAYBOOK_ANALYSIS_BUILDER",
        lambda rows, now_utc=None: {
            "window": {},
            "sample_size": len(rows),
            "promote": [{"label": "swing • tag:volume_confirmation", "support": 1, "win_rate": 1.0, "expectancy_usdt": 10.0, "median_r": 10.0, "trade_type": "swing", "symbols": ["BTCUSDT"], "tags": ["volume_confirmation"]}],
            "watch": [],
            "avoid": [],
            "coverage": {"wins_with_reasoning_pct": 100.0, "closed_with_usable_tags_pct": 100.0, "weak_or_missing_playbook_match_wins_pct": 0.0},
            "generated_at": "2026-04-20T00:00:00+00:00",
            "sparse_data": False,
        },
    )

    payload = await performance.build_performance_payload(tg_id=123)
    assert "metrics" in payload
    assert "equity_curve" in payload
    assert "pnl_30d" in payload
    assert "start_equity" in payload
    assert "playbook_analysis" in payload
    assert payload["metrics"]["total_trades"] == 2
    assert payload["playbook_analysis"]["sample_size"] == 2


@pytest.mark.asyncio
async def test_build_performance_payload_zero_trades_has_empty_playbook_analysis(monkeypatch):
    fake = _FakeSupabase(trades=[], sessions=[{"telegram_id": 123, "initial_deposit": 0.0, "current_balance": 0.0}])
    monkeypatch.setattr(performance, "_client", lambda: fake)

    async def _fake_fetch_account(_tg_id):
        return {"success": False}

    monkeypatch.setattr(performance.bsvc, "fetch_account", _fake_fetch_account)
    monkeypatch.setattr(performance, "_PLAYBOOK_ANALYSIS_BUILDER", None)

    payload = await performance.build_performance_payload(tg_id=123)
    assert payload["metrics"]["total_trades"] == 0
    assert payload["equity_curve"] == []
    assert payload["playbook_analysis"]["sample_size"] == 0
    assert payload["playbook_analysis"]["sparse_data"] is True
