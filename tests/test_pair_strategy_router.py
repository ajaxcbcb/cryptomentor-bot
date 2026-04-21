import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

import app.pair_strategy_router as pair_router  # type: ignore


@pytest.mark.asyncio
async def test_pair_router_partitions_ranked_pairs_without_overlap(monkeypatch):
    pair_router.reset_pair_strategy_router_for_testing()
    ranked = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
        "ADAUSDT", "AVAXUSDT", "BNBUSDT", "DOTUSDT", "LINKUSDT",
    ]

    async def _fake_get_top_volume_pairs(**_kwargs):
        return list(ranked)

    def _fake_detect_market_condition(base: str):
        if base in {"ETH", "SOL", "DOGE", "AVAX", "LINK"}:
            return {"recommended_mode": "scalping"}
        return {"recommended_mode": "swing"}

    monkeypatch.setattr(pair_router, "get_top_volume_pairs", _fake_get_top_volume_pairs)
    monkeypatch.setattr(pair_router, "detect_market_condition", _fake_detect_market_condition)

    result = await pair_router.get_mixed_pair_assignments(1001, limit=10)
    swing = set(result["swing"])
    scalp = set(result["scalp"])
    union = set(result["ranked_pairs"])

    assert swing.isdisjoint(scalp)
    assert union == set(ranked)
    assert swing | scalp == union


@pytest.mark.asyncio
async def test_pair_router_uses_sticky_cache_for_10_minutes(monkeypatch):
    pair_router.reset_pair_strategy_router_for_testing()
    counters = {"top": 0, "detect": 0}
    ranked = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    async def _fake_get_top_volume_pairs(**_kwargs):
        counters["top"] += 1
        return list(ranked)

    def _fake_detect_market_condition(_base: str):
        counters["detect"] += 1
        return {"recommended_mode": "swing"}

    monkeypatch.setattr(pair_router, "get_top_volume_pairs", _fake_get_top_volume_pairs)
    monkeypatch.setattr(pair_router, "detect_market_condition", _fake_detect_market_condition)

    first = await pair_router.get_mixed_pair_assignments(2002, limit=10)
    second = await pair_router.get_mixed_pair_assignments(2002, limit=10)

    assert first["ranked_pairs"] == second["ranked_pairs"]
    assert counters["top"] == 1
    assert counters["detect"] == len(ranked)


@pytest.mark.asyncio
async def test_pair_router_uses_regime_router_when_live(monkeypatch):
    pair_router.reset_pair_strategy_router_for_testing()

    async def _fake_get_top_volume_pairs(**_kwargs):
        return ["BTCUSDT", "ETHUSDT"]

    async def _fake_classify_regime(symbol, _market_context, _raw_signal=None):
        return {"preferred_engine": "scalping" if symbol == "ETHUSDT" else "swing"}

    monkeypatch.setattr(pair_router, "get_top_volume_pairs", _fake_get_top_volume_pairs)
    monkeypatch.setattr(pair_router, "is_live_mode", lambda: True)
    monkeypatch.setattr(pair_router, "get_market_context", lambda **_kwargs: object())
    monkeypatch.setattr(pair_router, "classify_regime", _fake_classify_regime)

    result = await pair_router.get_mixed_pair_assignments(3003, limit=10)
    assert result["swing"] == ["BTCUSDT"]
    assert result["scalp"] == ["ETHUSDT"]
