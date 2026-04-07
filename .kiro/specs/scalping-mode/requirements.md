# Requirements Document: Scalping Mode

## Introduction

This document defines the requirements for implementing a Scalping Mode feature in the crypto trading bot. The scalping mode is designed to increase trading volume by 50-80% through high-frequency trading on 5-minute timeframes, targeting quick in-and-out trades with lower risk-reward ratios and shorter hold times compared to the existing swing trading mode.

The scalping mode will operate alongside the existing 15-minute swing trading system, focusing on BTC and ETH pairs with the highest liquidity. This feature is based on the TIER 1 quick wins recommendation #2 from the volume growth strategy analysis.

## Glossary

- **Scalping_Mode**: A high-frequency trading mode that executes 10-20 trades per day on 5-minute timeframes with quick profit targets
- **Swing_Mode**: The existing trading mode that operates on 15-minute timeframes with 2-3 trades per day
- **Trading_Engine**: The autotrade_engine.py module responsible for executing trading strategies
- **Signal_Generator**: The autosignal_fast.py module that generates trading signals using technical analysis
- **StackMentor**: The 3-tier take-profit system (50%/40%/10% at R:R 1:2/1:3/1:10)
- **Confidence_Threshold**: The minimum confidence percentage required for a signal to trigger a trade
- **R:R**: Risk-to-Reward ratio, expressed as 1:X format
- **Max_Hold_Time**: Maximum duration a position can remain open before forced closure
- **Scan_Interval**: Time between market scans for new trading opportunities
- **Circuit_Breaker**: Risk management system that stops trading after reaching daily loss limit
- **ATR**: Average True Range, a volatility indicator used for stop-loss and take-profit calculations
- **Order_Block**: Smart Money Concepts (SMC) structure indicating institutional buying/selling zones
- **FVG**: Fair Value Gap, a price imbalance indicating potential support/resistance
- **CHoCH**: Change of Character, a market structure shift indicating trend reversal

## Requirements

### Requirement 1: Scalping Mode Configuration

**User Story:** As a trader, I want a dedicated scalping mode with optimized parameters for high-frequency trading, so that I can increase my trading volume and capture more market opportunities.

#### Acceptance Criteria

1. THE Trading_Engine SHALL support a scalping mode configuration separate from swing mode
2. WHEN scalping mode is enabled, THE Trading_Engine SHALL use 5-minute timeframe for signal generation
3. THE Scalping_Mode SHALL limit trading pairs to BTCUSDT and ETHUSDT
4. THE Scalping_Mode SHALL set minimum R:R to 1:1.5
5. THE Scalping_Mode SHALL set scan interval to 15 seconds
6. THE Scalping_Mode SHALL set maximum hold time to 30 minutes
7. THE Scalping_Mode SHALL require minimum confidence threshold of 80%
8. WHERE scalping mode is active, THE Trading_Engine SHALL execute 10-20 trades per day per user

### Requirement 2: Scalping Signal Generation

**User Story:** As a trader, I want scalping signals based on strong 15M trends with 5M pullback entries, so that I can enter trades at optimal prices with high probability of success.

#### Acceptance Criteria

1. WHEN generating scalping signals, THE Signal_Generator SHALL analyze 15-minute timeframe for trend direction
2. WHEN 15M trend is identified, THE Signal_Generator SHALL detect pullback entries on 5-minute timeframe
3. WHEN RSI on 5M exceeds 70, THE Signal_Generator SHALL generate SHORT signal
4. WHEN RSI on 5M falls below 30, THE Signal_Generator SHALL generate LONG signal
5. WHEN volume spike exceeds 2x average, THE Signal_Generator SHALL increase signal confidence by 10%
6. THE Signal_Generator SHALL validate signals against 15M trend direction before execution
7. IF 5M signal contradicts 15M trend, THEN THE Signal_Generator SHALL reject the signal

### Requirement 3: Scalping Take-Profit Strategy

**User Story:** As a trader, I want a single take-profit target at 1.5R for scalping trades, so that I can quickly lock in profits and move to the next opportunity.

#### Acceptance Criteria

1. WHEN scalping mode executes a trade, THE Trading_Engine SHALL set single take-profit at 1.5x stop-loss distance
2. WHEN take-profit is hit, THE Trading_Engine SHALL close 100% of the position
3. THE Scalping_Mode SHALL NOT use StackMentor 3-tier system
4. WHEN calculating take-profit, THE Trading_Engine SHALL use ATR-based distance calculation
5. FOR LONG positions, THE Trading_Engine SHALL set TP at entry_price + (1.5 × stop_loss_distance)
6. FOR SHORT positions, THE Trading_Engine SHALL set TP at entry_price - (1.5 × stop_loss_distance)

### Requirement 4: Scalping Stop-Loss Management

**User Story:** As a trader, I want tight stop-losses for scalping trades, so that I can minimize losses on failed setups while maintaining acceptable risk-reward ratios.

#### Acceptance Criteria

1. WHEN placing scalping trades, THE Trading_Engine SHALL calculate stop-loss using 1.5x ATR on 5-minute timeframe
2. FOR LONG positions, THE Trading_Engine SHALL place stop-loss at entry_price - (1.5 × ATR_5M)
3. FOR SHORT positions, THE Trading_Engine SHALL place stop-loss at entry_price + (1.5 × ATR_5M)
4. THE Scalping_Mode SHALL NOT move stop-loss to breakeven
5. WHEN stop-loss is hit, THE Trading_Engine SHALL close 100% of the position
6. THE Trading_Engine SHALL validate stop-loss price against exchange minimum tick size

### Requirement 5: Maximum Hold Time Enforcement

**User Story:** As a trader, I want positions automatically closed after 30 minutes, so that I don't hold scalping positions too long and miss other opportunities.

#### Acceptance Criteria

1. WHEN a scalping position is opened, THE Trading_Engine SHALL record the entry timestamp
2. WHILE a scalping position is open, THE Trading_Engine SHALL monitor elapsed time every scan interval
3. WHEN elapsed time exceeds 30 minutes, THE Trading_Engine SHALL close the position at market price
4. WHEN max hold time is reached, THE Trading_Engine SHALL log the closure reason as "max_hold_time_exceeded"
5. WHEN closing due to max hold time, THE Trading_Engine SHALL calculate and record final PnL
6. THE Trading_Engine SHALL notify the user when a position is closed due to max hold time

### Requirement 6: Trading Mode Selection

**User Story:** As a trader, I want to choose between scalping mode or swing mode from the dashboard, so that I can select the trading style that fits my risk tolerance and time availability.

#### Acceptance Criteria

1. THE Trading_Engine SHALL support two mutually exclusive trading modes: "scalping" and "swing"
2. THE AutoTrade Dashboard SHALL display a "⚙️ Trading Mode" button in the main menu
3. WHEN user clicks "Trading Mode" button, THE Bot SHALL show mode selection menu with:
   - "⚡ Scalping Mode (5M)" option with description
   - "📊 Swing Mode (15M)" option with description
   - Current active mode indicator (✅ checkmark)
4. WHEN user selects scalping mode, THE Trading_Engine SHALL:
   - Disable swing mode
   - Start scanning 5M timeframes
   - Use scalping parameters (1.5R TP, 30min max hold, 80% confidence)
   - Send confirmation: "✅ Trading mode changed to Scalping (5M)"
5. WHEN user selects swing mode, THE Trading_Engine SHALL:
   - Disable scalping mode
   - Start scanning 15M timeframes
   - Use swing parameters (StackMentor 3-tier TP, 68% confidence)
   - Send confirmation: "✅ Trading mode changed to Swing (15M)"
6. THE Trading_Engine SHALL NOT allow both scalping and swing modes to run simultaneously
7. WHEN switching modes, THE Trading_Engine SHALL allow existing positions to close naturally before starting new mode
8. THE Trading_Engine SHALL persist the selected trading mode in database (autotrade_sessions.trading_mode column)
9. THE Trading_Engine SHALL load selected trading mode from database on bot restart
10. THE Dashboard SHALL display current trading mode status: "⚡ Mode: Scalping (5M)" or "📊 Mode: Swing (15M)"
11. WHEN user first registers, THE Trading_Engine SHALL default to swing mode
12. THE mode selection menu SHALL include brief descriptions:
    - Scalping: "⚡ Fast trades, 5M chart, 10-20 trades/day, 1.5R profit target"
    - Swing: "📊 Swing trades, 15M chart, 2-3 trades/day, 3-tier profit targets"

### Requirement 7: Confidence Threshold Validation

**User Story:** As a trader, I want only high-confidence scalping signals (≥80%), so that I avoid low-quality setups and maintain a high win rate.

#### Acceptance Criteria

1. WHEN Signal_Generator produces a scalping signal, THE Trading_Engine SHALL validate confidence level
2. IF signal confidence is below 80%, THEN THE Trading_Engine SHALL reject the signal
3. WHEN strong 15M trend aligns with 5M pullback, THE Signal_Generator SHALL assign confidence ≥ 80%
4. WHEN RSI extreme (>70 or <30) occurs with volume spike, THE Signal_Generator SHALL assign confidence ≥ 85%
5. WHEN Order_Block or FVG confluence exists, THE Signal_Generator SHALL add 5% to confidence
6. THE Signal_Generator SHALL cap maximum confidence at 95%

### Requirement 8: Scalping Risk Management

**User Story:** As a trader, I want scalping mode to respect the same circuit breaker and risk limits as swing mode, so that I don't exceed my daily loss tolerance.

#### Acceptance Criteria

1. WHEN scalping mode is active, THE Circuit_Breaker SHALL monitor combined PnL from both scalping and swing trades
2. WHEN daily loss reaches 5% of account balance, THE Circuit_Breaker SHALL stop both scalping and swing trading
3. THE Scalping_Mode SHALL respect the maximum 4 concurrent positions limit across both modes
4. WHEN 4 positions are open, THE Trading_Engine SHALL queue new scalping signals until a position closes
5. THE Scalping_Mode SHALL use the same position sizing calculation as swing mode
6. THE Trading_Engine SHALL prevent opening scalping and swing positions on the same symbol simultaneously

### Requirement 9: Scalping Performance Tracking

**User Story:** As a trader, I want to see separate statistics for scalping vs swing trades, so that I can evaluate which strategy performs better for me.

#### Acceptance Criteria

1. WHEN a scalping trade is executed, THE Trading_Engine SHALL tag it with trade_type="scalping"
2. WHEN a swing trade is executed, THE Trading_Engine SHALL tag it with trade_type="swing"
3. THE Trading_Engine SHALL calculate and store separate win rates for scalping and swing modes
4. THE Trading_Engine SHALL calculate and store separate average R:R for scalping and swing modes
5. THE Trading_Engine SHALL calculate and store separate total PnL for scalping and swing modes
6. THE Trading_Engine SHALL provide a command to display scalping vs swing performance comparison

### Requirement 10: Scalping Signal Cooldown

**User Story:** As a trader, I want a cooldown period between scalping signals on the same pair, so that I don't overtrade and accumulate excessive fees.

#### Acceptance Criteria

1. WHEN a scalping signal is executed, THE Trading_Engine SHALL record the symbol and timestamp
2. WHEN a new scalping signal is generated for the same symbol, THE Trading_Engine SHALL check elapsed time since last trade
3. IF elapsed time is less than 5 minutes, THEN THE Trading_Engine SHALL reject the new signal
4. WHEN cooldown period expires, THE Trading_Engine SHALL allow new signals for that symbol
5. THE Trading_Engine SHALL maintain separate cooldown tracking for scalping and swing modes
6. THE Trading_Engine SHALL log rejected signals with reason "scalping_cooldown_active"

### Requirement 11: Multi-Exchange Scalping Support

**User Story:** As a trader, I want scalping mode to work across all supported exchanges (Bitunix, Binance, BingX, Bybit), so that I can use my preferred exchange.

#### Acceptance Criteria

1. WHEN scalping mode is enabled, THE Trading_Engine SHALL support Bitunix exchange
2. WHEN scalping mode is enabled, THE Trading_Engine SHALL support Binance exchange
3. WHEN scalping mode is enabled, THE Trading_Engine SHALL support BingX exchange
4. WHEN scalping mode is enabled, THE Trading_Engine SHALL support Bybit exchange
5. THE Trading_Engine SHALL validate that BTCUSDT and ETHUSDT are available on the selected exchange
6. IF a symbol is not available on the exchange, THEN THE Trading_Engine SHALL skip that symbol for scalping

### Requirement 12: Scalping Mode Notifications

**User Story:** As a trader, I want to receive notifications for scalping trade entries and exits, so that I can monitor my high-frequency trading activity.

#### Acceptance Criteria

1. WHEN a scalping position is opened, THE Trading_Engine SHALL send a notification with entry price, TP, and SL
2. WHEN a scalping position hits take-profit, THE Trading_Engine SHALL send a notification with profit amount and percentage
3. WHEN a scalping position hits stop-loss, THE Trading_Engine SHALL send a notification with loss amount and percentage
4. WHEN a scalping position is closed due to max hold time, THE Trading_Engine SHALL send a notification with final PnL
5. THE Trading_Engine SHALL include "SCALP" tag in all scalping notifications to distinguish from swing trades
6. THE Trading_Engine SHALL format scalping notifications with emoji indicators for quick visual recognition

### Requirement 13: Scalping Volume Spike Detection

**User Story:** As a trader, I want scalping signals to prioritize volume spikes above 2x average, so that I enter trades with strong momentum and liquidity.

#### Acceptance Criteria

1. WHEN analyzing 5M candles, THE Signal_Generator SHALL calculate 20-period volume moving average
2. WHEN current volume exceeds 2x the moving average, THE Signal_Generator SHALL flag as volume spike
3. WHEN volume spike is detected, THE Signal_Generator SHALL increase signal confidence by 10%
4. WHEN volume spike occurs with RSI extreme, THE Signal_Generator SHALL increase confidence by additional 5%
5. IF volume is below 1.5x average, THEN THE Signal_Generator SHALL decrease confidence by 5%
6. THE Signal_Generator SHALL log volume ratio for each scalping signal

### Requirement 14: Scalping Trend Validation

**User Story:** As a trader, I want scalping entries to align with 15M trend direction, so that I trade with the momentum rather than against it.

#### Acceptance Criteria

1. WHEN generating scalping signals, THE Signal_Generator SHALL analyze 15M EMA21 and EMA50
2. WHEN 15M price is above EMA21 and EMA21 is above EMA50, THE Signal_Generator SHALL identify uptrend
3. WHEN 15M price is below EMA21 and EMA21 is below EMA50, THE Signal_Generator SHALL identify downtrend
4. WHEN 15M trend is uptrend, THE Signal_Generator SHALL only generate LONG scalping signals
5. WHEN 15M trend is downtrend, THE Signal_Generator SHALL only generate SHORT scalping signals
6. IF 15M trend is neutral, THEN THE Signal_Generator SHALL skip scalping signal generation

### Requirement 15: Scalping Position Sizing

**User Story:** As a trader, I want scalping positions to use the same position sizing as swing trades, so that I maintain consistent risk per trade.

#### Acceptance Criteria

1. WHEN calculating scalping position size, THE Trading_Engine SHALL use the configured amount per trade
2. WHEN leverage is set, THE Trading_Engine SHALL apply the same leverage to scalping trades
3. THE Trading_Engine SHALL validate position size against exchange minimum order size
4. THE Trading_Engine SHALL validate position size against available account balance
5. IF position size is below minimum, THEN THE Trading_Engine SHALL reject the scalping signal
6. THE Trading_Engine SHALL round position size to exchange-specific precision (3 decimals for BTC, 2 for ETH)

### Requirement 16: Scalping Mode Database Schema

**User Story:** As a developer, I want scalping trades and mode selection stored with proper metadata, so that I can analyze performance and debug issues.

#### Acceptance Criteria

1. THE autotrade_sessions table SHALL include a "trading_mode" column (VARCHAR, default: "swing")
2. THE trading_mode column SHALL accept values: "scalping" or "swing"
3. WHEN user selects a trading mode, THE Trading_Engine SHALL update autotrade_sessions.trading_mode
4. WHEN a scalping trade is opened, THE Trading_Engine SHALL insert a record in autotrade_trades table
5. THE Trading_Engine SHALL set trade_type column to "scalping"
6. THE Trading_Engine SHALL set timeframe column to "5m"
7. THE Trading_Engine SHALL set max_hold_time column to 1800 seconds (30 minutes)
8. THE Trading_Engine SHALL set tp_strategy column to "single_tp_1.5R"
9. WHEN a scalping trade is closed, THE Trading_Engine SHALL update the record with close_reason and final_pnl
10. WHEN a swing trade is opened, THE Trading_Engine SHALL set trade_type to "swing" and timeframe to "15m"

### Requirement 17: Trading Mode Configuration Persistence

**User Story:** As a trader, I want my trading mode selection to persist across bot restarts, so that I don't have to reconfigure every time.

#### Acceptance Criteria

1. WHEN user selects scalping mode, THE Trading_Engine SHALL save "scalping" to autotrade_sessions.trading_mode
2. WHEN user selects swing mode, THE Trading_Engine SHALL save "swing" to autotrade_sessions.trading_mode
3. WHEN bot restarts, THE Trading_Engine SHALL load trading_mode from autotrade_sessions table
4. WHEN bot restarts with trading_mode="scalping", THE Trading_Engine SHALL start in scalping mode
5. WHEN bot restarts with trading_mode="swing", THE Trading_Engine SHALL start in swing mode
6. THE Trading_Engine SHALL persist trading mode selection per user (by telegram_id)
7. WHEN new user registers, THE Trading_Engine SHALL default trading_mode to "swing"

### Requirement 18: Trading Mode Dashboard UI

**User Story:** As a trader, I want an intuitive dashboard interface to switch between trading modes, so that I can easily change my strategy without using commands.

#### Acceptance Criteria

1. THE AutoTrade Dashboard SHALL display current trading mode in the status section
2. THE status display SHALL show: "⚡ Mode: Scalping (5M)" when scalping is active
3. THE status display SHALL show: "📊 Mode: Swing (15M)" when swing is active
4. THE Dashboard main menu SHALL include "⚙️ Trading Mode" button
5. WHEN user clicks "Trading Mode" button, THE Bot SHALL display mode selection menu with:
   - Title: "⚙️ Select Trading Mode"
   - Description of each mode
   - Current active mode marked with ✅
6. THE mode selection menu SHALL show:
   - "⚡ Scalping Mode" button with description: "Fast trades • 5M chart • 10-20 trades/day • 1.5R target"
   - "📊 Swing Mode" button with description: "Swing trades • 15M chart • 2-3 trades/day • 3-tier targets"
   - "🔙 Back to Dashboard" button
7. WHEN user selects a mode, THE Bot SHALL:
   - Update database immediately
   - Send confirmation message with mode details
   - Return to dashboard showing new mode
8. THE confirmation message SHALL include:
   - Mode name and emoji
   - Timeframe
   - Expected trades per day
   - Profit target strategy
9. THE Dashboard SHALL update mode display without requiring /autotrade command again
10. THE mode selection SHALL be accessible from Settings menu as well

### Requirement 19: Scalping Mode Error Handling

**User Story:** As a trader, I want scalping mode to handle errors gracefully without crashing the entire trading engine, so that my swing trades continue even if scalping fails.

#### Acceptance Criteria

1. WHEN scalping signal generation fails, THE Trading_Engine SHALL log the error and continue
2. WHEN scalping order placement fails, THE Trading_Engine SHALL retry up to 3 times with exponential backoff
3. IF scalping order fails after 3 retries, THEN THE Trading_Engine SHALL skip the signal and notify the user
4. WHEN exchange API rate limit is hit, THE Trading_Engine SHALL pause scalping for 60 seconds
5. WHEN scalping position monitoring fails, THE Trading_Engine SHALL log the error and retry on next scan
6. THE Trading_Engine SHALL isolate scalping errors from swing mode errors

### Requirement 20: Scalping Mode Testing Support

**User Story:** As a developer, I want to test scalping mode with demo users, so that I can validate the feature before production deployment.

#### Acceptance Criteria

1. THE Trading_Engine SHALL support enabling scalping mode for demo users
2. WHEN demo user enables scalping mode, THE Trading_Engine SHALL use paper trading (no real orders)
3. THE Trading_Engine SHALL log all scalping signals and simulated trades for demo users
4. THE Trading_Engine SHALL calculate simulated PnL for demo scalping trades
5. THE Trading_Engine SHALL provide a command to view demo scalping performance
6. THE Trading_Engine SHALL allow toggling between demo and live scalping mode

### Requirement 21: Scalping Mode Documentation

**User Story:** As a trader, I want clear documentation on how scalping mode works, so that I understand the risks and benefits before enabling it.

#### Acceptance Criteria

1. THE Trading_Engine SHALL provide a /scalping_help command that explains scalping mode
2. THE help text SHALL describe the 5M timeframe and 30-minute max hold time
3. THE help text SHALL explain the single TP at 1.5R strategy
4. THE help text SHALL warn about higher trading frequency and fee accumulation
5. THE help text SHALL list the supported pairs (BTC, ETH)
6. THE help text SHALL explain the 80% minimum confidence requirement

