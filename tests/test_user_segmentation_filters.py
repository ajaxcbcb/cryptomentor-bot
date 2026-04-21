import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

import app.user_segmentation as seg  # type: ignore


class _Result:
    def __init__(self, data):
        self.data = data


class _Table:
    def __init__(self, db, name):
        self._db = db
        self._name = name
        self._filters = {}
        self._limit = None
        self._order = None

    def select(self, _fields="*"):
        return self

    def eq(self, key, value):
        self._filters[key] = value
        return self

    def gte(self, key, value):
        self._filters[f"gte:{key}"] = value
        return self

    def order(self, key, desc=False):
        self._order = (key, desc)
        return self

    def limit(self, n):
        self._limit = int(n)
        return self

    def execute(self):
        rows = list(self._db.get(self._name, []))
        for key, value in self._filters.items():
            if key.startswith("gte:"):
                real = key.split(":", 1)[1]
                rows = [r for r in rows if str(r.get(real) or "") >= str(value)]
            else:
                rows = [r for r in rows if r.get(key) == value]
        if self._order:
            key, desc = self._order
            rows = sorted(rows, key=lambda r: str(r.get(key) or ""), reverse=desc)
        if self._limit is not None:
            rows = rows[: self._limit]
        return _Result(rows)


class _DB:
    def __init__(self):
        self._db = {
            "autotrade_sessions": [{"telegram_id": 7, "initial_deposit": 500.0, "current_balance": 420.0, "total_profit": -80.0}],
            "autotrade_trades": [{"telegram_id": 7, "symbol": "BTCUSDT", "status": "open", "opened_at": "2026-04-21T00:00:00+00:00"}],
        }

    def table(self, name):
        return _Table(self._db, name)


def test_get_profile_applies_drawdown_tightening(monkeypatch):
    monkeypatch.setattr(seg, "_client", lambda: _DB())
    profile = seg.get_profile(7, client=None)
    assert profile.tier == "micro"
    assert profile.tightened is True
    assert profile.max_daily_new_entries == 1
    assert profile.max_effective_risk_pct < 0.75
