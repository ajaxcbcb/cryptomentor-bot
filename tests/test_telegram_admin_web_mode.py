import os
import sys


_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

for _name in list(sys.modules.keys()):
    if _name == "app" or _name.startswith("app."):
        del sys.modules[_name]

from Bismillah.bot import get_telegram_admin_panel_mode  # type: ignore
from app.lib.auth import generate_dashboard_url  # type: ignore


def test_admin_panel_mode_defaults_to_web(monkeypatch):
    monkeypatch.delenv("TELEGRAM_ADMIN_PANEL_MODE", raising=False)
    assert get_telegram_admin_panel_mode() == "web"


def test_admin_panel_mode_accepts_legacy(monkeypatch):
    monkeypatch.setenv("TELEGRAM_ADMIN_PANEL_MODE", "legacy")
    assert get_telegram_admin_panel_mode() == "legacy"


def test_generate_dashboard_url_supports_admin_path(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://cryptomentor.id")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    url = generate_dashboard_url(12345, "admin", "Alice", path="/admin")
    assert url.startswith("https://cryptomentor.id/admin?t=")
