from app.core.liquidity import detect_liquidity_sweep


def test_liquidity_detects_sweep(sweep_candles):
    r = detect_liquidity_sweep(sweep_candles)
    assert r.has_sweep is True
    assert r.sweep_side in {"BUY_SIDE", "SELL_SIDE"}
