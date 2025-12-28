# CryptoMentor AI 2.0 - Trading Bot

## Project Overview
Telegram-based crypto signal bot using Supply & Demand (SnD) zone detection based on Binance klines only.

## Current Status
- **Latest Update**: Dec 28, 2025
- **Focus**: S&D Zone Detection Engine Implementation
- **Status**: Core algorithm implemented and tested

## Key Features
- **SnD Zone Detection** using only Binance Klines (OHLCV)
- **1H and 4H Timeframes** supported
- **Deterministic & Explainable** signals
- **Zone Invalidation Rules** (break detection, close beyond zone)
- **Entry Logic**: Buy at demand revisit, Sell at supply revisit

## Project Structure
```
Bismillah/
├── snd_zone_detector.py      # NEW: Core S&D zone detection engine
├── snd_auto_signals.py        # Auto signal scanner
├── bot.py                     # Telegram bot main
├── main.py                    # Entry point
├── crypto_api.py              # API integration
├── binance_provider.py        # Binance specific endpoints
└── ...other modules
```

## Algorithm: S&D Zone Detection

### Three-Phase Pattern Recognition
1. **IMPULSIVE MOVE**: Large candle (>1.5x avg range) with volume spike
2. **BASE/CONSOLIDATION**: Price consolidates after impulse (low range)
3. **DEPARTURE/BREAKOUT**: Price breaks out from consolidation zone

### Zone Definitions
- **DEMAND ZONE** (Support): Forms after downward impulse → consolidation → upward breakout
  - High: Top of consolidation range
  - Low: Bottom of consolidation range
  - Entry: BUY when price revisits demand from above

- **SUPPLY ZONE** (Resistance): Forms after upward impulse → consolidation → downward breakdown
  - High: Top of consolidation range  
  - Low: Bottom of consolidation range
  - Entry: SELL when price revisits supply from below

### Validation Rules
- **Zone is VALID if**: Pattern complete + volume spike confirmed
- **Zone is INVALID if**: 
  - Price closes beyond zone (not just touches)
  - Zone completely broken through
  - Time decay (too old, market has moved)

## Usage
```python
from snd_zone_detector import detect_snd_zones

# Detect zones for BTC 1H
result = detect_snd_zones("BTCUSDT", "1h", limit=100)

# Returns:
# {
#   'symbol': 'BTCUSDT',
#   'current_price': 42500.50,
#   'demand_zones': [Zone(...), ...],
#   'supply_zones': [Zone(...), ...],
#   'closest_demand': Zone(...),
#   'closest_supply': Zone(...),
#   'entry_signal': 'BUY' | 'SELL' | None,
#   'explanation': '...'
# }
```

## Dependencies
- `requests`: HTTP for Binance API
- `python-dateutil`: Date handling
- `psutil`: System monitoring (existing)

## Key Design Decisions
- **Binance Spot API only** (no futures, no external data)
- **Klines (OHLCV)** as the single source of truth
- **Deterministic output** - same candles → same zones
- **No ML/indicators** - pure price action logic
- **Zone strength 0-100** based on volume consistency
- **Entry proximity**: 0.5% from zone boundary

## Next Steps
1. ✅ Core S&D detection algorithm
2. ⏳ Integration with bot signal pipeline
3. ⏳ Multi-timeframe analysis (1H + 4H confluence)
4. ⏳ Risk/Reward calculation for entries
5. ⏳ Telegram signal formatting
