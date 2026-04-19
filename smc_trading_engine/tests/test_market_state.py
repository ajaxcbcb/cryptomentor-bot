from app.core.market_state import detect_market_state


def test_market_state_trending(trending_candles):
    r = detect_market_state(trending_candles)
    assert r.state in {"TRENDING", "UNCLEAR"}


def test_market_state_sideways(sideways_candles):
    r = detect_market_state(sideways_candles)
    assert r.state in {"SIDEWAYS", "LOW_VOLATILITY", "UNCLEAR"}
