# CryptoMentor AI 2.0 - Trading Bot

## Project Overview
Telegram-based crypto signal bot using Supply & Demand (SnD) zone detection based on Binance klines only.

## Current Status
- **Latest Update**: Dec 31, 2025
- **Focus**: Sentiment-Based Entry Recommendations
- **Status**: Futures Analysis fixed with sentiment-based LIMIT order recommendations

## Recent Changes (Dec 31, 2025)
- **ESTIMATED TIME FEATURE**: Added estimated completion time to all loading messages
  - Format: "⏱️ Estimated: ~Xs (selesai 14:30:25 WIB)"
  - Uses user's timezone preference (WIB, WITA, WIT, UTC, etc.)
  - Applied to: Multi-coin signals, Market overview, Spot/Futures analysis, Portfolio, Credits
  - Helper functions: `get_estimated_time_message()` and `get_user_timezone_from_context()`
- **MULTI-COIN SIGNALS FIX**: Fixed callback timeout with async background processing
  - Uses asyncio.create_task() to prevent blocking Telegram's 3-second timeout
  - Fixed invalid symbols: DOL→DOT, MATIC→POL
  - Optimized from 15 to 10 coins for faster ~10s response
- **PERFORMANCE OPTIMIZATION**: Refactored bot.py for faster, lighter operation
  - Lazy loading of heavy modules (menu, AI, crypto API, Supabase)
  - Shared database service with singleton pattern (services.py)
  - Reduced startup time by deferring module imports
  - All handlers now use shared database instance instead of creating new connections
- Fixed "Reset All Credits" button to properly set credits to 200
- Fixed Futures Analysis parsing error (switched from MARKDOWN to plain text)
- Added sentiment-based entry recommendations:
  - BULLISH → LIMIT LONG at Demand Zone
  - BEARISH → LIMIT SHORT at Supply Zone
  - SIDEWAYS → Wait for Breakout
- Updated Auto-Signals to show zone-based LIMIT orders instead of single entry prices
- All signals now emphasize LIMIT orders at zones (no market orders)

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

## Algorithm: S&D Zone Detection v3.0 (Swing-Based)

### NEW Swing-Based Approach (Works for ALL volatility levels)
1. **ATR CALCULATION**: Adaptive thresholds based on Average True Range
2. **SWING DETECTION**: Find pivot highs (supply) and pivot lows (demand) using 3-candle windows
3. **ZONE CLUSTERING**: Group nearby swings within 1.5 ATR into zones
4. **ZONE SCORING**: Weight by freshness, touch count, volume, and move magnitude
5. **ACTIVE ZONE SELECTION**: Find zones closest to current price for entry signals

### Zone Definitions
- **DEMAND ZONE** (Support): Cluster of swing lows where buying pressure emerged
  - Entry: BUY when price revisits demand zone from above
  - Stop Loss: Below zone low - 0.75 ATR

- **SUPPLY ZONE** (Resistance): Cluster of swing highs where selling pressure emerged
  - Entry: SELL when price revisits supply zone from below
  - Stop Loss: Above zone high + 0.75 ATR

### Zone Strength Scoring (0-100)
- **Touch Count** (up to 45 points): More swing touches = stronger zone
- **Freshness** (up to 25 points): Newer zones score higher
- **Volume** (up to 20 points): Higher volume at zone = stronger
- **Move Magnitude** (up to 20 points): Bigger moves from zone = stronger

### Validation Rules
- **Zone is VALID if**: Strength >= 40% and not broken by price
- **Zone is INVALID if**: 
  - Price closes beyond zone boundary (0.5% buffer)
  - Zone completely broken through

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

## UI: Button-Based Menu System

### Files Added
- `menu_handler.py` - InlineKeyboard system mapping ALL commands to buttons
- `MENU_INTEGRATION_GUIDE.md` - Complete integration instructions

### Menu Structure (7 Categories)
1. **📈 Price & Market** → Check Price, Market Overview
2. **🧠 Trading Analysis** → Spot Analysis (SnD), Futures Analysis (SnD)
3. **🚀 Futures Signals** → Multi-Coin Signals, Auto Signals (Lifetime)
4. **💼 Portfolio & Credits** → Portfolio, Add Coin, Credits, Upgrade
5. **👑 Premium & Referral** → Referral Program, Premium Earnings
6. **🤖 Ask AI** → Ask CryptoMentor AI
7. **⚙️ Settings** → Change Language, Back to Main

### Integration Status
- ✅ Menu builder functions created
- ✅ Callback handlers implemented
- ✅ Symbol input flow (step-by-step)
- ✅ Backward compatible (slash commands still work)
- ⏳ Needs: Add to bot.py registration

### Quick Setup
```python
# In bot.py
from menu_handler import register_menu_handlers
register_menu_handlers(application)
```

## Next Steps
1. ✅ Core S&D detection algorithm
2. ✅ Button-based UI menu system
3. ⏳ Integration with bot signal pipeline
4. ⏳ Multi-timeframe analysis (1H + 4H confluence)
5. ⏳ Risk/Reward calculation for entries
