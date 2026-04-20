import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

try:
    import Bismillah.app.volume_pair_selector as selector
except ImportError:
    import app.volume_pair_selector as selector  # type: ignore


class _Resp:
    def __init__(self, payload, code=200):
        self._payload = payload
        self.status_code = code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self):
        return self._payload


def _reset_state():
    selector._state["pairs"] = []
    selector._state["last_refresh_ts"] = 0.0
    selector._state["source"] = "bootstrap"
    selector._state["error"] = None
    selector._state["requested_limit"] = selector.DEFAULT_LIMIT
    selector._state["runtime_untradable_until"] = {}
    selector._state["tradable_symbol_count"] = 0
    selector._state["dynamic_quarantine"] = {}
    selector._state["dynamic_quarantine_last_refresh_ts"] = 0.0
    selector._state["dynamic_quarantine_error"] = None


def test_selector_sorts_quote_volume_desc_and_filters_usdt(monkeypatch):
    _reset_state()

    tickers_payload = {
        "code": 0,
        "msg": "Success",
        "data": [
            {"symbol": "AAAUSDT", "quoteVol": "50"},
            {"symbol": "BBBUSDT", "quoteVol": "200"},
            {"symbol": "CCCUSDT", "quoteVol": "120"},
            {"symbol": "BTCUSD", "quoteVol": "999"},  # ignored (not USDT futures pair)
            {"symbol": "DDDUSDT", "quoteVol": "0"},   # ignored (no volume)
        ],
    }
    trading_pairs_payload = {
        "code": 0,
        "msg": "Success",
        "data": [
            {"symbol": "AAAUSDT", "quote": "USDT", "symbolStatus": "OPEN"},
            {"symbol": "BBBUSDT", "quote": "USDT", "symbolStatus": "OPEN"},
            {"symbol": "CCCUSDT", "quote": "USDT", "symbolStatus": "OPEN"},
        ],
    }

    def _fake_get(url, *args, **kwargs):
        if str(url).endswith(selector.TRADING_PAIRS_PATH):
            return _Resp(trading_pairs_payload)
        if str(url).endswith(selector.TICKERS_PATH):
            return _Resp(tickers_payload)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(selector.requests, "get", _fake_get)
    pairs = selector.get_ranked_top_volume_pairs(limit=3)
    assert pairs == ["BBBUSDT", "CCCUSDT", "AAAUSDT"]


def test_selector_uses_cache_fallback_when_refresh_fails(monkeypatch):
    _reset_state()
    selector._state["pairs"] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    selector._state["last_refresh_ts"] = 0.0  # force refresh path

    def _boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(selector.requests, "get", _boom)
    pairs = selector.get_ranked_top_volume_pairs(limit=2)
    assert pairs == ["BTCUSDT", "ETHUSDT"]
    assert selector.get_selector_health()["source"] == "cache_fallback"


def test_selector_bootstrap_fallback_when_no_cache_and_refresh_fails(monkeypatch):
    _reset_state()

    def _boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(selector.requests, "get", _boom)
    pairs = selector.get_ranked_top_volume_pairs(limit=4)
    assert pairs == selector.DEFAULT_BOOTSTRAP_PAIRS[:4]
    assert selector.get_selector_health()["source"] == "bootstrap_fallback"


def test_selector_filters_by_trading_pairs_open_status(monkeypatch):
    _reset_state()

    trading_pairs_payload = {
        "code": 0,
        "msg": "Success",
        "data": [
            {"symbol": "AAAUSDT", "quote": "USDT", "symbolStatus": "OPEN"},
            {"symbol": "BBBUSDT", "quote": "USDT", "symbolStatus": "PREVIEW"},  # should be filtered
            {"symbol": "CCCUSDT", "quote": "USDT", "symbolStatus": "OPEN"},
        ],
    }
    tickers_payload = {
        "code": 0,
        "msg": "Success",
        "data": [
            {"symbol": "DDDUSDT", "quoteVol": "500"},   # missing from trading_pairs
            {"symbol": "BBBUSDT", "quoteVol": "400"},   # not OPEN
            {"symbol": "CCCUSDT", "quoteVol": "300"},
            {"symbol": "AAAUSDT", "quoteVol": "200"},
        ],
    }

    def _fake_get(url, *args, **kwargs):
        if str(url).endswith(selector.TRADING_PAIRS_PATH):
            return _Resp(trading_pairs_payload)
        if str(url).endswith(selector.TICKERS_PATH):
            return _Resp(tickers_payload)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(selector.requests, "get", _fake_get)
    pairs = selector.get_ranked_top_volume_pairs(limit=5)
    assert pairs == ["CCCUSDT", "AAAUSDT"]


def test_runtime_untradable_quarantine_excludes_then_expires(monkeypatch):
    _reset_state()
    selector._state["pairs"] = ["ETHUSDT", "BTCUSDT", "SOLUSDT"]
    selector._state["last_refresh_ts"] = 1000.0

    now = {"ts": 1000.0}
    monkeypatch.setattr(selector.time, "time", lambda: float(now["ts"]))

    expiry = selector.mark_runtime_untradable_symbol("ETHUSDT", ttl_sec=10.0)
    assert expiry == 1010.0

    now["ts"] = 1001.0
    pairs_live = selector.get_ranked_top_volume_pairs(limit=2)
    assert pairs_live == ["BTCUSDT", "SOLUSDT"]

    now["ts"] = 1012.0
    pairs_after_expiry = selector.get_ranked_top_volume_pairs(limit=2)
    assert pairs_after_expiry == ["ETHUSDT", "BTCUSDT"]


def test_dynamic_quarantine_state_triggers_on_negative_expectancy_and_timeout_rates():
    prev = {}
    metrics = {
        "LINKUSDT": {
            "symbol": "LINKUSDT",
            "sample_size": 24,
            "avg_pnl": -0.12,
            "net_pnl": -2.88,
            "timeout_rate": 0.83,
            "negative_timeout_rate": 0.58,
        }
    }

    nxt = selector.compute_dynamic_quarantine_state(prev, metrics, now_ts=1000.0)
    assert "LINKUSDT" in nxt
    assert nxt["LINKUSDT"]["state"] == "quarantined"
    assert nxt["LINKUSDT"]["recovery_windows"] == 0
    assert nxt["LINKUSDT"]["quarantine_until_ts"] == 1000.0 + selector.DYNAMIC_QUARANTINE_TTL_SECONDS
    assert "negative_expectancy" in nxt["LINKUSDT"]["reason"]


def test_dynamic_quarantine_requires_two_healthy_windows_after_ttl():
    prev = {
        "XRPUSDT": {
            "symbol": "XRPUSDT",
            "sample_size": 25,
            "avg_pnl": -0.08,
            "net_pnl": -2.0,
            "timeout_rate": 0.88,
            "negative_timeout_rate": 0.60,
            "reason": "negative_expectancy+timeout_rate",
            "recovery_windows": 0,
            "quarantine_until_ts": 100.0,
            "state": "quarantined",
        }
    }
    healthy_metrics = {
        "XRPUSDT": {
            "symbol": "XRPUSDT",
            "sample_size": 25,
            "avg_pnl": 0.03,
            "net_pnl": 0.75,
            "timeout_rate": 0.40,
            "negative_timeout_rate": 0.12,
        }
    }

    mid = selector.compute_dynamic_quarantine_state(prev, healthy_metrics, now_ts=100.0)
    assert "XRPUSDT" in mid
    assert mid["XRPUSDT"]["state"] == "recovery_observation"
    assert mid["XRPUSDT"]["recovery_windows"] == 1

    nxt = selector.compute_dynamic_quarantine_state(mid, healthy_metrics, now_ts=200.0)
    assert "XRPUSDT" not in nxt


def test_selector_excludes_dynamic_quarantine_symbols_preserving_rank_order(monkeypatch):
    _reset_state()

    tickers_payload = {
        "code": 0,
        "msg": "Success",
        "data": [
            {"symbol": "AAAUSDT", "quoteVol": "500"},
            {"symbol": "BBBUSDT", "quoteVol": "400"},
            {"symbol": "CCCUSDT", "quoteVol": "300"},
        ],
    }
    trading_pairs_payload = {
        "code": 0,
        "msg": "Success",
        "data": [
            {"symbol": "AAAUSDT", "quote": "USDT", "symbolStatus": "OPEN"},
            {"symbol": "BBBUSDT", "quote": "USDT", "symbolStatus": "OPEN"},
            {"symbol": "CCCUSDT", "quote": "USDT", "symbolStatus": "OPEN"},
        ],
    }

    def _fake_get(url, *args, **kwargs):
        if str(url).endswith(selector.TRADING_PAIRS_PATH):
            return _Resp(trading_pairs_payload)
        if str(url).endswith(selector.TICKERS_PATH):
            return _Resp(tickers_payload)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(selector.requests, "get", _fake_get)
    monkeypatch.setattr(
        selector,
        "refresh_dynamic_symbol_quarantine",
        lambda now_ts=None: {
            "BBBUSDT": {
                "symbol": "BBBUSDT",
                "sample_size": 24,
                "avg_pnl": -0.10,
                "net_pnl": -2.4,
                "timeout_rate": 0.82,
                "negative_timeout_rate": 0.56,
                "reason": "negative_expectancy+timeout_rate",
                "recovery_windows": 0,
                "quarantine_until_ts": 2000.0,
                "state": "quarantined",
            }
        },
    )

    pairs = selector.get_ranked_top_volume_pairs(limit=3)
    assert pairs == ["AAAUSDT", "CCCUSDT"]


def test_selector_health_exposes_dynamic_quarantine_details():
    _reset_state()
    selector._state["dynamic_quarantine"] = {
        "SOLUSDT": {
            "symbol": "SOLUSDT",
            "reason": "negative_expectancy+negative_timeout_rate",
            "sample_size": 22,
            "avg_pnl": -0.22,
            "net_pnl": -4.84,
            "timeout_rate": 0.81,
            "negative_timeout_rate": 0.59,
            "recovery_windows": 0,
            "quarantine_until_ts": 5000.0,
            "state": "quarantined",
        }
    }

    health = selector.get_selector_health()
    assert health["quarantined_symbol_count"] == 1
    assert health["quarantined_symbols"][0]["symbol"] == "SOLUSDT"
    assert health["quarantined_symbols"][0]["sample_size"] == 22
