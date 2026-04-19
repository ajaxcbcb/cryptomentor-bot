from app.core.confidence import calculate_confidence
from app.core.context_builder import build_trade_context


class Cfg:
    min_confidence_score = 0.7


def test_confidence_components(trending_candles):
    tf = {"1m": trending_candles, "5m": trending_candles, "15m": trending_candles, "1h": trending_candles}
    ctx = build_trade_context("BTCUSDT", tf, Cfg())
    c = calculate_confidence(ctx)
    assert 0.0 <= c.score <= 1.0
    assert "market_state" in c.components
