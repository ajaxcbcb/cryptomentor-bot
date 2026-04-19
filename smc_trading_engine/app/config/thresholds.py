from __future__ import annotations

ATR_LOOKBACK = 14
ATR_MIN_THRESHOLD = 0.001
RANGE_LOOKBACK = 20
RANGE_MIN_MULTIPLIER = 1.2
TREND_LOOKBACK = 20
TREND_STRENGTH_THRESHOLD = 0.55

SWING_LOOKBACK = 30
SWEEP_MIN_PENETRATION_MULT = 0.25
BOS_DISPLACEMENT_MIN = 0.5
ZONE_NEAR_PCT = 0.003

CONFIDENCE_WEIGHTS = {
    "market_state": 0.25,
    "liquidity_sweep": 0.2,
    "bos": 0.25,
    "entry_zone": 0.2,
    "higher_timeframe_bias": 0.1,
}
