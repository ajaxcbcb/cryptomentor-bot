import importlib
import os
import sys


_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WEB_BACKEND = os.path.join(_ROOT, "website-backend")
if _WEB_BACKEND in sys.path:
    sys.path.remove(_WEB_BACKEND)
sys.path.insert(0, _WEB_BACKEND)

for _name in list(sys.modules.keys()):
    if _name == "app" or _name.startswith("app."):
        del sys.modules[_name]

observability = importlib.import_module("app.services.admin_observability")


class _CountResult:
    def __init__(self, count: int):
        self.count = int(count)
        self.data = []


class _UsersCountQuery:
    def __init__(self, count: int):
        self._count = int(count)

    def select(self, *_args, **_kwargs):
        return self

    def gte(self, *_args, **_kwargs):
        return self

    def execute(self):
        return _CountResult(self._count)


class _FakeClient:
    def __init__(self, new_today_count: int):
        self._new_today_count = int(new_today_count)

    def table(self, name: str):
        assert name == "users"
        return _UsersCountQuery(self._new_today_count)


def test_get_user_stats_summary_includes_engine_and_unverified_counts(monkeypatch):
    def _rows(_client, table_name: str, _columns: str, page_size: int = 1000):
        _ = page_size
        if table_name == "users":
            return [
                {"telegram_id": 1, "is_premium": False, "is_lifetime": False},
                {"telegram_id": 2, "is_premium": True, "is_lifetime": False},
                {"telegram_id": 3, "is_premium": False, "is_lifetime": True},
                {"telegram_id": 3, "is_premium": False, "is_lifetime": True},
            ]
        if table_name == "user_verifications":
            return [
                {"telegram_id": 1, "status": "approved"},
                {"telegram_id": 1, "status": "active"},
                {"telegram_id": 4, "status": "approved"},
            ]
        if table_name == "autotrade_sessions":
            return [
                {"telegram_id": 1, "engine_active": True},
                {"telegram_id": 2, "engine_active": False},
                {"telegram_id": 2, "engine_active": True},
                {"telegram_id": 3, "engine_active": False},
            ]
        return []

    monkeypatch.setattr(observability, "_client", lambda: _FakeClient(new_today_count=2))
    monkeypatch.setattr(observability, "_fetch_table_rows", _rows)

    stats = observability.get_user_stats_summary()

    assert stats["total_users"] == 3
    assert stats["premium_users"] == 1
    assert stats["lifetime_users"] == 1
    assert stats["verified_users"] == 1
    assert stats["unverified_users"] == 2
    assert stats["engine_active_users"] == 2
    assert stats["engine_stopped_users"] == 1
    assert stats["free_users"] == 2
    assert stats["new_today"] == 2
