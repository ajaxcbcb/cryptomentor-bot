from __future__ import annotations

import pathlib
import sys


_ROOT = pathlib.Path(__file__).resolve().parents[1]
_WEB_BACKEND = _ROOT / "website-backend"
if str(_WEB_BACKEND) not in sys.path:
    sys.path.insert(0, str(_WEB_BACKEND))

from app.services import verification_status as vs  # noqa: E402


class _ExecResult:
    def __init__(self, data):
        self.data = data


class _TableQuery:
    def __init__(self, table_name: str, store: dict[str, list[dict]]):
        self.table_name = table_name
        self.store = store
        self.filters = {}

    def select(self, _fields: str):
        return self

    def eq(self, key: str, value):
        self.filters[key] = value
        return self

    def limit(self, _n: int):
        return self

    def execute(self):
        rows = self.store.get(self.table_name, [])
        filtered = []
        for row in rows:
            ok = True
            for key, value in self.filters.items():
                if row.get(key) != value:
                    ok = False
                    break
            if ok:
                filtered.append(row)
        return _ExecResult(filtered[:1])


class _FakeClient:
    def __init__(self, store: dict[str, list[dict]]):
        self.store = store

    def table(self, name: str):
        return _TableQuery(name, self.store)


def test_session_legacy_status_maps_to_approved_only_when_uid_present():
    assert vs.normalize_session_verification_status("stopped", "197832121") == vs.VER_APPROVED
    assert vs.normalize_session_verification_status("stopped", "") != vs.VER_APPROVED


def test_shared_resolver_applies_pending_to_session_final_compat(monkeypatch):
    store = {
        "user_verifications": [
            {
                "telegram_id": 42,
                "status": "pending",
                "bitunix_uid": "12345",
                "submitted_via": "telegram",
                "reviewed_at": None,
                "reviewed_by_admin_id": None,
                "community_code": None,
            }
        ],
        "autotrade_sessions": [
            {
                "telegram_id": 42,
                "status": "stopped",  # legacy approved-compatible
                "bitunix_uid": "12345",
            }
        ],
    }
    monkeypatch.setattr(vs, "_client", lambda: _FakeClient(store))

    snap = vs.load_verification_snapshot(42)

    assert snap["status"] == vs.VER_APPROVED
    assert snap["source"] == "compat_session_override"
    assert snap["decision_reason"] == "uv_pending_session_final_uid_compatible"
    assert snap["mismatch_detected"] is True


def test_shared_resolver_parity_fields_present_for_route_and_guard(monkeypatch):
    store = {
        "user_verifications": [
            {
                "telegram_id": 99,
                "status": "approved",
                "bitunix_uid": "8888",
                "submitted_via": "web",
                "reviewed_at": "2026-04-22T00:00:00+00:00",
                "reviewed_by_admin_id": 1,
                "community_code": "abc",
            }
        ],
        "autotrade_sessions": [
            {
                "telegram_id": 99,
                "status": "active",
                "bitunix_uid": "8888",
            }
        ],
    }
    monkeypatch.setattr(vs, "_client", lambda: _FakeClient(store))

    snap = vs.load_verification_snapshot(99)
    required_keys = {
        "status",
        "raw_status",
        "source",
        "decision_reason",
        "mismatch_detected",
    }
    assert required_keys.issubset(set(snap.keys()))
    assert snap["status"] == vs.VER_APPROVED
