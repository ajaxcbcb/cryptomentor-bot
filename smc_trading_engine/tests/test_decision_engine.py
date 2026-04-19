from app.core.context_builder import build_trade_context
from app.core.decision_engine import evaluate_trade


class Cfg:
    min_confidence_score = 0.2


def test_decision_engine_returns_trade_or_skip(trending_candles):
    tf = {"1m": trending_candles, "5m": trending_candles, "15m": trending_candles, "1h": trending_candles}
    ctx = build_trade_context("BTCUSDT", tf, Cfg())
    d = evaluate_trade(ctx, Cfg())
    assert d.action in {"TRADE", "SKIP"}
