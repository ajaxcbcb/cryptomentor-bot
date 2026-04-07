# Design Document: Scalping Mode

## 1. High-Level Architecture

### 1.1 System Overview

The Scalping Mode feature extends the existing autotrade system to support high-frequency trading on 5-minute timeframes alongside the existing 15-minute swing trading mode. The architecture follows a modular design pattern that integrates seamlessly with the current `autotrade_engine.py` and `autosignal_fast.py` modules.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Telegram Bot Interface                       │
│                    (handlers_autotrade.py)                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Trading Mode Manager                           │
│              (New: trading_mode_manager.py)                      │
│  • Mode selection (scalping ↔ swing)                            │
│  • Mode persistence (database)                                   │
│  • Mutual exclusivity enforcement                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│  Scalping Engine │      │   Swing Engine   │
│  (New Module)    │      │   (Existing)     │
│  • 5M signals    │      │   • 15M signals  │
│  • 1.5R TP       │      │   • StackMentor  │
│  • 30min hold    │      │   • Multi-tier   │
└────────┬─────────┘      └────────┬─────────┘
         │                         │
         └────────────┬────────────┘
                      ▼
         ┌────────────────────────┐
         │   Exchange Clients     │
         │  (Bitunix, Binance,    │
         │   BingX, Bybit)        │
         └────────────────────────┘
```

### 1.2 Data Flow


**Signal Generation Flow:**
```
1. User selects Scalping Mode from dashboard
2. TradingModeManager updates database (trading_mode = "scalping")
3. AutoTrade Engine restarts with scalping configuration
4. ScalpingEngine scans BTCUSDT/ETHUSDT every 15 seconds
5. Signal generated → 15M trend validation → 5M entry trigger
6. Order placed → Position monitored → Max hold time enforced
7. TP/SL hit → Position closed → Next scan cycle
```

**Mode Selection Flow:**
```
Dashboard → "⚙️ Trading Mode" button
         → Mode selection menu (Scalping / Swing)
         → User selects mode
         → Database update (autotrade_sessions.trading_mode)
         → Engine restart with new mode
         → Confirmation message sent
         → Dashboard updated with new mode indicator
```

### 1.3 Integration Points

**With autotrade_engine.py:**
- Conditional mode check: `if trading_mode == "scalping": use ScalpingEngine`
- Shared position monitoring loop
- Shared circuit breaker and risk management
- Shared exchange client interface

**With autosignal_fast.py:**
- Extended to support 5M timeframe analysis
- 15M trend validation for scalping entries
- Volume spike detection (>2x average)
- RSI extreme detection for scalping signals

**With handlers_autotrade.py:**
- New callback: `callback_trading_mode_menu()`
- New callback: `callback_select_scalping()`
- New callback: `callback_select_swing()`
- Dashboard display updated with mode indicator



## 2. Component Design

### 2.1 ScalpingEngine Module (New)

**File:** `Bismillah/app/scalping_engine.py`

**Purpose:** Dedicated module for scalping-specific trading logic, separate from swing trading to maintain clean separation of concerns.

**Class Structure:**

```python
class ScalpingEngine:
    """
    High-frequency trading engine for 5-minute scalping
    
    Attributes:
        config: ScalpingConfig dataclass
        user_id: Telegram user ID
        client: Exchange client instance
        bot: Telegram bot instance
        notify_chat_id: Chat ID for notifications
        positions: Dict of open scalping positions
        last_scan: Timestamp of last market scan
        cooldown_tracker: Dict tracking symbol cooldowns
    """
    
    def __init__(self, user_id, client, bot, notify_chat_id, config=None):
        self.config = config or ScalpingConfig()
        self.user_id = user_id
        self.client = client
        self.bot = bot
        self.notify_chat_id = notify_chat_id
        self.positions = {}
        self.last_scan = 0
        self.cooldown_tracker = {}
    
    async def run(self):
        """Main trading loop - scans every 15 seconds"""
        pass
    
    def generate_scalping_signal(self, symbol: str) -> Optional[Signal]:
        """Generate 5M scalping signal with 15M trend validation"""
        pass
    
    def validate_scalping_entry(self, signal: Signal) -> bool:
        """Validate signal meets scalping criteria (80% confidence, 1.5R)"""
        pass
    
    def calculate_scalping_tp_sl(self, entry: float, direction: str, atr: float) -> Tuple[float, float]:
        """Calculate single TP at 1.5R and SL using ATR"""
        pass
    
    async def monitor_positions(self):
        """Check open positions for TP/SL/max hold time"""
        pass
    
    def check_max_hold_time(self, position: Position) -> bool:
        """Check if position exceeded 30-minute max hold"""
        pass
    
    async def close_position_max_hold(self, position: Position):
        """Force close position at market price after 30 minutes"""
        pass
    
    def check_cooldown(self, symbol: str) -> bool:
        """Check if symbol is in 5-minute cooldown period"""
        pass
```



**Key Methods:**

#### `generate_scalping_signal(symbol: str) -> Optional[Signal]`

```python
def generate_scalping_signal(self, symbol: str) -> Optional[Signal]:
    """
    Generate scalping signal using multi-timeframe analysis
    
    Algorithm:
    1. Fetch 15M klines (trend direction)
    2. Fetch 5M klines (entry trigger)
    3. Calculate 15M EMA21, EMA50 for trend
    4. Calculate 5M RSI, volume ratio
    5. Validate trend alignment (15M uptrend → LONG only)
    6. Check RSI extreme (>70 SHORT, <30 LONG)
    7. Check volume spike (>2x average)
    8. Calculate confidence score
    9. If confidence >= 80%, return signal
    
    Returns:
        Signal object with entry, TP, SL, confidence
        None if no valid signal
    """
    # Implementation uses existing alternative_klines_provider
    # Similar to _compute_signal_pro() but optimized for 5M
```

#### `validate_scalping_entry(signal: Signal) -> bool`

```python
def validate_scalping_entry(self, signal: Signal) -> bool:
    """
    Validate signal meets scalping requirements
    
    Checks:
    - Confidence >= 80%
    - R:R >= 1.5
    - Symbol in allowed list (BTC, ETH)
    - No existing position on symbol
    - Not in cooldown period
    - Circuit breaker not triggered
    
    Returns:
        True if signal is valid for entry
    """
```

#### `calculate_scalping_tp_sl(entry, direction, atr) -> Tuple[float, float]`

```python
def calculate_scalping_tp_sl(self, entry: float, direction: str, atr: float) -> Tuple[float, float]:
    """
    Calculate single TP at 1.5R and SL using ATR
    
    Formula:
    - SL distance = 1.5 * ATR (5M)
    - TP distance = 1.5 * SL distance (R:R 1:1.5)
    
    For LONG:
    - SL = entry - (1.5 * ATR)
    - TP = entry + (1.5 * SL_distance)
    
    For SHORT:
    - SL = entry + (1.5 * ATR)
    - TP = entry - (1.5 * SL_distance)
    
    Returns:
        (tp_price, sl_price)
    """
```



### 2.2 TradingModeManager (New)

**File:** `Bismillah/app/trading_mode_manager.py`

**Purpose:** Centralized manager for trading mode selection, persistence, and enforcement of mutual exclusivity.

**Class Structure:**

```python
class TradingModeManager:
    """
    Manages trading mode selection and persistence
    
    Responsibilities:
    - Load mode from database on startup
    - Switch between scalping and swing modes
    - Ensure only one mode active at a time
    - Persist mode selection to database
    """
    
    @staticmethod
    def get_mode(user_id: int) -> TradingMode:
        """
        Load trading mode from database
        
        Query: SELECT trading_mode FROM autotrade_sessions WHERE telegram_id = ?
        Default: TradingMode.SWING (for new users)
        
        Returns:
            TradingMode enum (SCALPING or SWING)
        """
        pass
    
    @staticmethod
    def set_mode(user_id: int, mode: TradingMode) -> bool:
        """
        Update trading mode in database
        
        Query: UPDATE autotrade_sessions 
               SET trading_mode = ?, updated_at = NOW()
               WHERE telegram_id = ?
        
        Returns:
            True if update successful
        """
        pass
    
    @staticmethod
    async def switch_mode(user_id: int, new_mode: TradingMode, bot, context) -> Dict:
        """
        Switch trading mode with engine restart
        
        Algorithm:
        1. Validate no open positions (or allow to close naturally)
        2. Stop current engine (scalping or swing)
        3. Update database with new mode
        4. Start new engine with new mode config
        5. Send confirmation to user
        6. Return status dict
        
        Returns:
            {"success": bool, "message": str, "mode": TradingMode}
        """
        pass
```

**Integration with autotrade_engine.py:**

```python
# In start_engine() function
from app.trading_mode_manager import TradingModeManager, TradingMode

def start_engine(bot, user_id, api_key, api_secret, amount, leverage, 
                 notify_chat_id, is_premium=False, silent=False, exchange_id="bitunix"):
    
    # Load trading mode from database
    trading_mode = TradingModeManager.get_mode(user_id)
    
    if trading_mode == TradingMode.SCALPING:
        # Start scalping engine
        from app.scalping_engine import ScalpingEngine
        engine = ScalpingEngine(user_id, client, bot, notify_chat_id)
        task = asyncio.create_task(engine.run())
    else:
        # Start swing engine (existing logic)
        task = asyncio.create_task(_trade_loop(...))
    
    _running_tasks[user_id] = task
```



### 2.3 Dashboard UI Updates

**File:** `Bismillah/app/handlers_autotrade.py`

**New Callback Handlers:**

#### `callback_trading_mode_menu(update, context)`

```python
async def callback_trading_mode_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display trading mode selection menu
    
    Shows:
    - Current active mode (✅ indicator)
    - Scalping mode option with description
    - Swing mode option with description
    - Back to dashboard button
    """
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    current_mode = TradingModeManager.get_mode(user_id)
    
    scalping_check = "✅ " if current_mode == TradingMode.SCALPING else ""
    swing_check = "✅ " if current_mode == TradingMode.SWING else ""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{scalping_check}⚡ Scalping Mode (5M)",
            callback_data="mode_select_scalping"
        )],
        [InlineKeyboardButton(
            f"{swing_check}📊 Swing Mode (15M)",
            callback_data="mode_select_swing"
        )],
        [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="at_dashboard")],
    ])
    
    await query.edit_message_text(
        "⚙️ <b>Select Trading Mode</b>\n\n"
        "⚡ <b>Scalping Mode (5M):</b>\n"
        "• Fast trades on 5-minute chart\n"
        "• 10-20 trades per day\n"
        "• Single TP at 1.5R\n"
        "• 30-minute max hold time\n"
        "• Pairs: BTC, ETH\n\n"
        "📊 <b>Swing Mode (15M):</b>\n"
        "• Swing trades on 15-minute chart\n"
        "• 2-3 trades per day\n"
        "• 3-tier TP (StackMentor)\n"
        "• No max hold time\n"
        "• Pairs: BTC, ETH, SOL, BNB\n\n"
        f"Current mode: <b>{current_mode.value.upper()}</b>",
        parse_mode='HTML',
        reply_markup=keyboard
    )
```



#### `callback_select_scalping(update, context)`

```python
async def callback_select_scalping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle scalping mode selection
    
    Flow:
    1. Check if already in scalping mode
    2. Validate no open positions (or warn user)
    3. Call TradingModeManager.switch_mode()
    4. Send confirmation message
    5. Return to dashboard
    """
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    current_mode = TradingModeManager.get_mode(user_id)
    
    if current_mode == TradingMode.SCALPING:
        await query.edit_message_text(
            "⚡ You're already in Scalping Mode!",
            parse_mode='HTML'
        )
        return
    
    # Switch mode
    result = await TradingModeManager.switch_mode(
        user_id, TradingMode.SCALPING, context.application.bot, context
    )
    
    if result["success"]:
        await query.edit_message_text(
            "✅ <b>Trading Mode Changed</b>\n\n"
            "⚡ <b>Scalping Mode Activated</b>\n\n"
            "📊 Configuration:\n"
            "• Timeframe: 5 minutes\n"
            "• Scan interval: 15 seconds\n"
            "• Profit target: 1.5R (single TP)\n"
            "• Max hold time: 30 minutes\n"
            "• Trading pairs: BTCUSDT, ETHUSDT\n"
            "• Min confidence: 80%\n\n"
            "🚀 Engine restarted with scalping parameters.\n"
            "You'll receive signals when high-probability setups appear.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 View Dashboard", callback_data="at_dashboard")]
            ])
        )
    else:
        await query.edit_message_text(
            f"❌ Failed to switch mode: {result['message']}",
            parse_mode='HTML'
        )
```

#### `callback_select_swing(update, context)`

Similar implementation for swing mode selection.



**Dashboard Display Update:**

```python
async def cmd_autotrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... existing code ...
    
    # Get trading mode
    trading_mode = TradingModeManager.get_mode(user_id)
    mode_emoji = "⚡" if trading_mode == TradingMode.SCALPING else "📊"
    mode_label = "Scalping (5M)" if trading_mode == TradingMode.SCALPING else "Swing (15M)"
    
    # Add mode to dashboard display
    dashboard_text = (
        "🤖 <b>Auto Trade Dashboard</b>\n\n"
        "✅ Status: <b>ACTIVE</b>\n"
        f"{mode_emoji} Mode: <b>{mode_label}</b>\n\n"
        # ... rest of dashboard ...
    )
    
    # Add Trading Mode button to keyboard
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Status Portfolio", callback_data="at_status")],
        [InlineKeyboardButton("📈 Trade History", callback_data="at_history")],
        [InlineKeyboardButton("⚙️ Trading Mode", callback_data="trading_mode_menu")],  # NEW
        # ... rest of buttons ...
    ])
```

### 2.4 Database Schema Changes

**Migration Script:** `db/add_trading_mode.sql`

```sql
-- Add trading_mode column to autotrade_sessions
ALTER TABLE autotrade_sessions 
ADD COLUMN IF NOT EXISTS trading_mode VARCHAR(20) DEFAULT 'swing';

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_autotrade_sessions_trading_mode 
ON autotrade_sessions(telegram_id, trading_mode);

-- Add comment
COMMENT ON COLUMN autotrade_sessions.trading_mode IS 
'Trading mode: scalping (5M) or swing (15M)';

-- Update existing rows to default swing mode
UPDATE autotrade_sessions 
SET trading_mode = 'swing' 
WHERE trading_mode IS NULL;
```

**Existing autotrade_trades table already supports:**
- `trade_type` column (can store "scalping" or "swing")
- `timeframe` column (can store "5m" or "15m")
- `tp_strategy` column (can store "single_tp_1.5R" or "stackmentor_3tier")

No changes needed to autotrade_trades table.



## 3. Data Models

### 3.1 ScalpingConfig

```python
from dataclasses import dataclass
from typing import List

@dataclass
class ScalpingConfig:
    """Configuration for scalping mode"""
    
    # Timeframe and scanning
    timeframe: str = "5m"
    scan_interval: int = 15  # seconds between scans
    
    # Signal requirements
    min_confidence: float = 0.80  # 80% minimum
    min_rr: float = 1.5  # Minimum risk-reward ratio
    
    # Position management
    max_hold_time: int = 1800  # 30 minutes in seconds
    single_tp_multiplier: float = 1.5  # TP at 1.5R
    
    # Risk management
    max_concurrent_positions: int = 4  # Shared with swing mode
    daily_loss_limit: float = 0.05  # 5% circuit breaker
    
    # Trading pairs
    pairs: List[str] = None
    
    def __post_init__(self):
        if self.pairs is None:
            self.pairs = ["BTCUSDT", "ETHUSDT"]
    
    # ATR multipliers
    atr_sl_multiplier: float = 1.5  # SL = 1.5 * ATR (5M)
    
    # Cooldown
    cooldown_seconds: int = 300  # 5 minutes between signals on same pair
    
    # Volume and volatility filters
    min_volume_ratio: float = 2.0  # Volume must be >2x average
    min_atr_pct: float = 0.3  # Skip if ATR < 0.3% (too flat)
    max_atr_pct: float = 10.0  # Skip if ATR > 10% (too volatile)
```

### 3.2 TradingMode Enum

```python
from enum import Enum

class TradingMode(Enum):
    """Trading mode enumeration"""
    SCALPING = "scalping"
    SWING = "swing"
    
    @classmethod
    def from_string(cls, mode_str: str):
        """Convert string to TradingMode enum"""
        mode_str = mode_str.lower().strip()
        if mode_str == "scalping":
            return cls.SCALPING
        elif mode_str == "swing":
            return cls.SWING
        else:
            return cls.SWING  # Default to swing
    
    def __str__(self):
        return self.value
```



### 3.3 ScalpingSignal

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ScalpingSignal:
    """Scalping signal data structure"""
    
    symbol: str
    side: str  # "LONG" or "SHORT"
    confidence: float  # 0-100
    
    # Price levels
    entry_price: float
    tp_price: float
    sl_price: float
    
    # Technical indicators
    rr_ratio: float
    atr_pct: float
    volume_ratio: float
    rsi_5m: float
    rsi_15m: float
    
    # Trend context
    trend_15m: str  # "LONG", "SHORT", "NEUTRAL"
    market_structure: str  # "uptrend", "downtrend", "ranging"
    
    # Signal metadata
    reasons: List[str]
    timestamp: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "tp_price": self.tp_price,
            "sl_price": self.sl_price,
            "rr_ratio": self.rr_ratio,
            "atr_pct": self.atr_pct,
            "volume_ratio": self.volume_ratio,
            "rsi_5m": self.rsi_5m,
            "rsi_15m": self.rsi_15m,
            "trend_15m": self.trend_15m,
            "market_structure": self.market_structure,
            "reasons": ",".join(self.reasons),
            "timestamp": self.timestamp,
        }
```

### 3.4 ScalpingPosition

```python
@dataclass
class ScalpingPosition:
    """Active scalping position tracking"""
    
    user_id: int
    symbol: str
    side: str  # "BUY" or "SELL"
    
    # Position details
    entry_price: float
    quantity: float
    leverage: int
    
    # Exit levels
    tp_price: float
    sl_price: float
    
    # Timing
    opened_at: float  # Unix timestamp
    max_hold_until: float  # opened_at + 1800 seconds
    
    # Status
    status: str  # "open", "closed_tp", "closed_sl", "closed_max_hold"
    
    def time_remaining(self) -> int:
        """Calculate seconds remaining before max hold time"""
        import time
        return max(0, int(self.max_hold_until - time.time()))
    
    def is_expired(self) -> bool:
        """Check if position exceeded max hold time"""
        import time
        return time.time() >= self.max_hold_until
```



## 4. API Design

### 4.1 ScalpingEngine Methods

#### Core Trading Methods

```python
class ScalpingEngine:
    
    async def run(self):
        """
        Main trading loop
        
        Pseudocode:
        WHILE engine is running:
            WAIT scan_interval seconds
            
            FOR each symbol in config.pairs:
                IF symbol in cooldown:
                    CONTINUE
                
                signal = generate_scalping_signal(symbol)
                
                IF signal is None:
                    CONTINUE
                
                IF NOT validate_scalping_entry(signal):
                    CONTINUE
                
                success = await place_scalping_order(signal)
                
                IF success:
                    mark_cooldown(symbol)
                    register_position(signal)
            
            await monitor_positions()
        """
    
    def generate_scalping_signal(self, symbol: str) -> Optional[ScalpingSignal]:
        """
        Generate 5M scalping signal with 15M trend validation
        
        Pseudocode:
        1. FETCH 15M klines (last 100 candles)
        2. FETCH 5M klines (last 60 candles)
        
        3. CALCULATE 15M indicators:
           - EMA21, EMA50
           - RSI(14)
           - ATR(14)
        
        4. DETERMINE 15M trend:
           IF price > EMA21 > EMA50:
               trend_15m = "LONG"
           ELSE IF price < EMA21 < EMA50:
               trend_15m = "SHORT"
           ELSE:
               trend_15m = "NEUTRAL"
        
        5. IF trend_15m == "NEUTRAL":
               RETURN None  # No clear trend
        
        6. CALCULATE 5M indicators:
           - RSI(14)
           - Volume ratio (current / 20-period MA)
           - ATR(14)
        
        7. GENERATE signal based on trend:
           IF trend_15m == "LONG":
               IF RSI_5m < 30 AND volume_ratio > 2.0:
                   side = "LONG"
                   confidence = 80 + volume_bonus
           
           IF trend_15m == "SHORT":
               IF RSI_5m > 70 AND volume_ratio > 2.0:
                   side = "SHORT"
                   confidence = 80 + volume_bonus
        
        8. IF no signal generated:
               RETURN None
        
        9. CALCULATE TP/SL:
           sl_distance = ATR_5m * 1.5
           tp_distance = sl_distance * 1.5  # R:R 1:1.5
           
           IF side == "LONG":
               sl = entry - sl_distance
               tp = entry + tp_distance
           ELSE:
               sl = entry + sl_distance
               tp = entry - tp_distance
        
        10. RETURN ScalpingSignal(...)
        
        Returns:
            ScalpingSignal object or None
        """
```



#### Validation and Risk Management

```python
    def validate_scalping_entry(self, signal: ScalpingSignal) -> bool:
        """
        Validate signal meets all scalping requirements
        
        Pseudocode:
        1. IF signal.confidence < config.min_confidence:
               LOG "Confidence too low"
               RETURN False
        
        2. IF signal.rr_ratio < config.min_rr:
               LOG "R:R too low"
               RETURN False
        
        3. IF signal.symbol NOT IN config.pairs:
               LOG "Symbol not allowed"
               RETURN False
        
        4. IF has_open_position(signal.symbol):
               LOG "Position already open"
               RETURN False
        
        5. IF is_in_cooldown(signal.symbol):
               LOG "Symbol in cooldown"
               RETURN False
        
        6. IF circuit_breaker_triggered():
               LOG "Daily loss limit reached"
               RETURN False
        
        7. IF count_open_positions() >= config.max_concurrent_positions:
               LOG "Max concurrent positions reached"
               RETURN False
        
        8. IF signal.atr_pct < config.min_atr_pct:
               LOG "ATR too low (market flat)"
               RETURN False
        
        9. IF signal.atr_pct > config.max_atr_pct:
               LOG "ATR too high (too volatile)"
               RETURN False
        
        10. RETURN True
        
        Returns:
            True if signal passes all validation checks
        """
    
    def calculate_scalping_tp_sl(self, entry: float, direction: str, atr: float) -> Tuple[float, float]:
        """
        Calculate single TP at 1.5R and SL using ATR
        
        Pseudocode:
        1. sl_distance = atr * config.atr_sl_multiplier  # 1.5 * ATR
        2. tp_distance = sl_distance * config.single_tp_multiplier  # 1.5 * SL
        
        3. IF direction == "LONG":
               sl = entry - sl_distance
               tp = entry + tp_distance
           ELSE:  # SHORT
               sl = entry + sl_distance
               tp = entry - tp_distance
        
        4. ROUND tp and sl to exchange precision
        
        5. RETURN (tp, sl)
        
        Returns:
            Tuple of (tp_price, sl_price)
        """
```



#### Position Monitoring

```python
    async def monitor_positions(self):
        """
        Monitor open scalping positions for TP/SL/max hold time
        
        Pseudocode:
        FOR each position in self.positions:
            1. FETCH current mark price from exchange
            
            2. CHECK TP hit:
               IF (position.side == "BUY" AND mark_price >= position.tp_price) OR
                  (position.side == "SELL" AND mark_price <= position.tp_price):
                   await close_position_tp(position)
                   CONTINUE
            
            3. CHECK SL hit:
               IF (position.side == "BUY" AND mark_price <= position.sl_price) OR
                  (position.side == "SELL" AND mark_price >= position.sl_price):
                   await close_position_sl(position)
                   CONTINUE
            
            4. CHECK max hold time:
               IF position.is_expired():
                   await close_position_max_hold(position)
                   CONTINUE
        """
    
    def check_max_hold_time(self, position: ScalpingPosition) -> bool:
        """
        Check if position exceeded 30-minute max hold
        
        Pseudocode:
        1. current_time = time.time()
        2. elapsed = current_time - position.opened_at
        3. RETURN elapsed >= config.max_hold_time
        
        Returns:
            True if position exceeded max hold time
        """
    
    async def close_position_max_hold(self, position: ScalpingPosition):
        """
        Force close position at market price after 30 minutes
        
        Pseudocode:
        1. LOG "Max hold time exceeded for {position.symbol}"
        
        2. close_side = "SELL" if position.side == "BUY" else "BUY"
        
        3. result = await client.place_order(
               symbol=position.symbol,
               side=close_side,
               quantity=position.quantity,
               order_type='market',
               reduce_only=True
           )
        
        4. IF result.success:
               final_price = result.fill_price
               pnl = calculate_pnl(position, final_price)
               
               update_database(position, status="closed_max_hold", pnl=pnl)
               
               await notify_user(
                   "⏰ Position closed (max hold time)\n"
                   f"Symbol: {position.symbol}\n"
                   f"PnL: {pnl:+.2f} USDT"
               )
               
               remove_position(position.symbol)
           ELSE:
               LOG "Failed to close position: {result.error}"
        """
```



### 4.2 TradingModeManager Methods

```python
class TradingModeManager:
    
    @staticmethod
    def get_mode(user_id: int) -> TradingMode:
        """
        Load trading mode from database
        
        Pseudocode:
        1. QUERY database:
           SELECT trading_mode FROM autotrade_sessions 
           WHERE telegram_id = user_id
        
        2. IF no result:
               RETURN TradingMode.SWING  # Default for new users
        
        3. mode_str = result['trading_mode']
        4. RETURN TradingMode.from_string(mode_str)
        
        Returns:
            TradingMode enum (SCALPING or SWING)
        """
    
    @staticmethod
    def set_mode(user_id: int, mode: TradingMode) -> bool:
        """
        Update trading mode in database
        
        Pseudocode:
        1. TRY:
               UPDATE autotrade_sessions
               SET trading_mode = mode.value,
                   updated_at = NOW()
               WHERE telegram_id = user_id
               
               RETURN True
           EXCEPT Exception as e:
               LOG "Failed to update mode: {e}"
               RETURN False
        
        Returns:
            True if update successful
        """
    
    @staticmethod
    async def switch_mode(user_id: int, new_mode: TradingMode, bot, context) -> Dict:
        """
        Switch trading mode with engine restart
        
        Pseudocode:
        1. current_mode = get_mode(user_id)
        
        2. IF current_mode == new_mode:
               RETURN {"success": False, "message": "Already in this mode"}
        
        3. # Check for open positions
           open_positions = get_open_positions(user_id)
           IF open_positions:
               # Option 1: Block switch
               RETURN {"success": False, "message": "Close open positions first"}
               
               # Option 2: Allow switch, positions will close naturally
               # (Implementation choice based on requirements)
        
        4. # Stop current engine
           from app.autotrade_engine import stop_engine
           stop_engine(user_id)
        
        5. # Update database
           success = set_mode(user_id, new_mode)
           IF NOT success:
               RETURN {"success": False, "message": "Database update failed"}
        
        6. # Restart engine with new mode
           from app.autotrade_engine import start_engine
           # Get user's API keys and settings
           keys = get_user_api_keys(user_id)
           session = get_autotrade_session(user_id)
           
           start_engine(
               bot=bot,
               user_id=user_id,
               api_key=keys['api_key'],
               api_secret=keys['api_secret'],
               amount=session['initial_deposit'],
               leverage=session['leverage'],
               notify_chat_id=user_id,
               exchange_id=keys.get('exchange', 'bitunix')
           )
        
        7. RETURN {
               "success": True,
               "message": f"Switched to {new_mode.value} mode",
               "mode": new_mode
           }
        
        Returns:
            Dict with success status and message
        """
```



### 4.3 Dashboard Handler Methods

```python
async def callback_trading_mode_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display trading mode selection menu
    
    Pseudocode:
    1. GET user_id from update
    2. current_mode = TradingModeManager.get_mode(user_id)
    
    3. BUILD keyboard with checkmarks:
       - Scalping option (✅ if current)
       - Swing option (✅ if current)
       - Back button
    
    4. SEND message with:
       - Mode descriptions
       - Current mode indicator
       - Selection keyboard
    """

async def callback_select_scalping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle scalping mode selection
    
    Pseudocode:
    1. GET user_id from update
    2. current_mode = TradingModeManager.get_mode(user_id)
    
    3. IF current_mode == TradingMode.SCALPING:
           SEND "Already in scalping mode"
           RETURN
    
    4. result = await TradingModeManager.switch_mode(
           user_id, TradingMode.SCALPING, bot, context
       )
    
    5. IF result['success']:
           SEND confirmation message with:
           - Mode details
           - Configuration summary
           - Dashboard button
       ELSE:
           SEND error message with result['message']
    """

async def callback_select_swing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle swing mode selection
    
    Similar to callback_select_scalping but for swing mode
    """
```



## 5. Integration Points

### 5.1 With Existing autotrade_engine.py

**Conditional Mode Logic:**

```python
# In start_engine() function
def start_engine(bot, user_id: int, api_key: str, api_secret: str,
                 amount: float, leverage: int, notify_chat_id: int,
                 is_premium: bool = False, silent: bool = False, 
                 exchange_id: str = "bitunix"):
    
    stop_engine(user_id)
    
    # Load trading mode
    from app.trading_mode_manager import TradingModeManager, TradingMode
    trading_mode = TradingModeManager.get_mode(user_id)
    
    # Get exchange client
    from app.exchange_registry import get_client
    client = get_client(exchange_id, api_key, api_secret)
    
    # Start appropriate engine based on mode
    if trading_mode == TradingMode.SCALPING:
        from app.scalping_engine import ScalpingEngine
        engine = ScalpingEngine(
            user_id=user_id,
            client=client,
            bot=bot,
            notify_chat_id=notify_chat_id
        )
        task = asyncio.create_task(engine.run())
        logger.info(f"[AutoTrade:{user_id}] Started SCALPING engine")
    else:
        # Existing swing trading logic
        task = asyncio.create_task(_trade_loop(
            bot, user_id, client, amount, leverage, 
            notify_chat_id, is_premium, exchange_id
        ))
        logger.info(f"[AutoTrade:{user_id}] Started SWING engine")
    
    _running_tasks[user_id] = task
    
    def _done_cb(t):
        if t.cancelled():
            logger.info(f"[AutoTrade:{user_id}] Engine cancelled")
        elif t.exception():
            logger.error(f"[AutoTrade:{user_id}] Engine error: {t.exception()}")
    
    task.add_done_callback(_done_cb)
```

**Shared Position Monitoring:**

Both scalping and swing engines use the same position monitoring infrastructure:
- Circuit breaker (5% daily loss limit)
- Max concurrent positions (4 total across both modes)
- Exchange client interface
- Database logging

**Risk Management Integration:**

```python
# Shared circuit breaker check
def circuit_breaker_triggered(user_id: int) -> bool:
    """
    Check if daily loss limit reached (applies to both modes)
    
    Query:
    SELECT SUM(pnl_usdt) as daily_pnl
    FROM autotrade_trades
    WHERE telegram_id = user_id
      AND DATE(opened_at) = CURRENT_DATE
      AND status IN ('closed_tp', 'closed_sl', 'closed_max_hold')
    
    Returns:
        True if daily_pnl <= -5% of account balance
    """
```



### 5.2 With autosignal_fast.py

**Extended Signal Generation:**

```python
# In autosignal_fast.py - add scalping signal support

def compute_signal_scalping(base_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Generate scalping signal for 5M timeframe
    
    Similar to compute_signal_fast() but optimized for scalping:
    - Uses 5M klines for entry
    - Validates against 15M trend
    - Higher confidence threshold (80% vs 75%)
    - Volume spike requirement (>2x vs >1.1x)
    """
    try:
        from app.providers.alternative_klines_provider import alternative_klines_provider
        
        symbol = base_symbol.upper()
        full_symbol = f"{symbol}USDT"
        
        # Get 15M trend
        klines_15m = alternative_klines_provider.get_klines(symbol, interval='15m', limit=100)
        if not klines_15m or len(klines_15m) < 50:
            return None
        
        c15 = [float(k[4]) for k in klines_15m]
        ema21_15 = _calc_ema(c15, 21)
        ema50_15 = _calc_ema(c15, 50)
        price = c15[-1]
        
        # Determine 15M trend
        if price > ema21_15 > ema50_15:
            trend_15m = "LONG"
        elif price < ema21_15 < ema50_15:
            trend_15m = "SHORT"
        else:
            return None  # No clear trend
        
        # Get 5M entry trigger
        klines_5m = alternative_klines_provider.get_klines(symbol, interval='5m', limit=60)
        if not klines_5m or len(klines_5m) < 30:
            return None
        
        c5 = [float(k[4]) for k in klines_5m]
        h5 = [float(k[2]) for k in klines_5m]
        l5 = [float(k[3]) for k in klines_5m]
        v5 = [float(k[5]) for k in klines_5m]
        
        rsi_5m = _calc_rsi(c5)
        atr_5m = _calc_atr(h5, l5, c5, 14)
        vol_ratio = _calc_volume_ratio(v5, 20)
        
        # Signal logic
        side = None
        confidence = 80
        
        if trend_15m == "LONG" and rsi_5m < 30 and vol_ratio > 2.0:
            side = "LONG"
            confidence += 5 if vol_ratio > 3.0 else 0
        elif trend_15m == "SHORT" and rsi_5m > 70 and vol_ratio > 2.0:
            side = "SHORT"
            confidence += 5 if vol_ratio > 3.0 else 0
        
        if side is None:
            return None
        
        # Calculate TP/SL
        sl_distance = atr_5m * 1.5
        tp_distance = sl_distance * 1.5
        
        if side == "LONG":
            sl = price - sl_distance
            tp = price + tp_distance
        else:
            sl = price + sl_distance
            tp = price - tp_distance
        
        return {
            "symbol": full_symbol,
            "timeframe": "5m",
            "side": side,
            "confidence": int(confidence),
            "entry_price": price,
            "tp": tp,
            "sl": sl,
            "rr_ratio": 1.5,
            "atr_pct": (atr_5m / price) * 100,
            "vol_ratio": vol_ratio,
            "rsi_5m": rsi_5m,
            "trend_15m": trend_15m,
            "reasons": [
                f"15M {trend_15m} trend",
                f"5M RSI {rsi_5m:.0f}",
                f"Volume {vol_ratio:.1f}x"
            ]
        }
    
    except Exception as e:
        print(f"Error computing scalping signal for {base_symbol}: {e}")
        return None
```



### 5.3 With handlers_autotrade.py

**Registration of New Handlers:**

```python
# In bot.py or handlers registration
from app.handlers_autotrade import (
    callback_trading_mode_menu,
    callback_select_scalping,
    callback_select_swing,
)

application.add_handler(CallbackQueryHandler(
    callback_trading_mode_menu, 
    pattern="^trading_mode_menu$"
))

application.add_handler(CallbackQueryHandler(
    callback_select_scalping, 
    pattern="^mode_select_scalping$"
))

application.add_handler(CallbackQueryHandler(
    callback_select_swing, 
    pattern="^mode_select_swing$"
))
```

**Dashboard Integration:**

The existing `cmd_autotrade()` function is extended to:
1. Load trading mode from database
2. Display mode indicator in dashboard
3. Add "⚙️ Trading Mode" button to keyboard

No breaking changes to existing functionality.



## 6. Algorithms

### 6.1 Scalping Signal Generation Algorithm

```
ALGORITHM: generate_scalping_signal(symbol)

INPUT: symbol (e.g., "BTCUSDT")
OUTPUT: ScalpingSignal object or None

STEP 1: Fetch Market Data
    klines_15m ← GET klines(symbol, "15m", limit=100)
    klines_5m ← GET klines(symbol, "5m", limit=60)
    
    IF insufficient data:
        RETURN None

STEP 2: Analyze 15M Trend (Higher Timeframe)
    closes_15m ← EXTRACT close prices from klines_15m
    ema21_15m ← CALCULATE EMA(closes_15m, 21)
    ema50_15m ← CALCULATE EMA(closes_15m, 50)
    current_price ← closes_15m[LAST]
    
    IF current_price > ema21_15m > ema50_15m:
        trend_15m ← "LONG"
    ELSE IF current_price < ema21_15m < ema50_15m:
        trend_15m ← "SHORT"
    ELSE:
        trend_15m ← "NEUTRAL"
        RETURN None  // No clear trend, skip signal

STEP 3: Analyze 5M Entry Trigger (Lower Timeframe)
    closes_5m ← EXTRACT close prices from klines_5m
    highs_5m ← EXTRACT high prices from klines_5m
    lows_5m ← EXTRACT low prices from klines_5m
    volumes_5m ← EXTRACT volumes from klines_5m
    
    rsi_5m ← CALCULATE RSI(closes_5m, 14)
    atr_5m ← CALCULATE ATR(highs_5m, lows_5m, closes_5m, 14)
    volume_ma_20 ← CALCULATE MA(volumes_5m, 20)
    volume_ratio ← volumes_5m[LAST] / volume_ma_20

STEP 4: Generate Signal Based on Trend + RSI + Volume
    side ← None
    confidence ← 80  // Base confidence for scalping
    reasons ← []
    
    IF trend_15m == "LONG":
        IF rsi_5m < 30:  // Oversold on 5M
            IF volume_ratio > 2.0:  // Strong volume
                side ← "LONG"
                reasons.APPEND("15M uptrend + 5M oversold + volume spike")
                
                IF volume_ratio > 3.0:
                    confidence ← confidence + 5
                    reasons.APPEND("Exceptional volume")
    
    ELSE IF trend_15m == "SHORT":
        IF rsi_5m > 70:  // Overbought on 5M
            IF volume_ratio > 2.0:  // Strong volume
                side ← "SHORT"
                reasons.APPEND("15M downtrend + 5M overbought + volume spike")
                
                IF volume_ratio > 3.0:
                    confidence ← confidence + 5
                    reasons.APPEND("Exceptional volume")
    
    IF side == None:
        RETURN None  // No valid entry trigger

STEP 5: Calculate TP/SL Using ATR
    sl_distance ← atr_5m × 1.5  // SL at 1.5 ATR
    tp_distance ← sl_distance × 1.5  // TP at 1.5R (R:R 1:1.5)
    
    IF side == "LONG":
        sl_price ← current_price - sl_distance
        tp_price ← current_price + tp_distance
    ELSE:  // SHORT
        sl_price ← current_price + sl_distance
        tp_price ← current_price - tp_distance
    
    rr_ratio ← tp_distance / sl_distance  // Should be 1.5

STEP 6: Validate Signal Quality
    atr_pct ← (atr_5m / current_price) × 100
    
    IF atr_pct < 0.3:  // Market too flat
        RETURN None
    
    IF atr_pct > 10.0:  // Market too volatile
        RETURN None
    
    IF confidence < 80:  // Below minimum threshold
        RETURN None

STEP 7: Create and Return Signal
    signal ← ScalpingSignal(
        symbol=symbol,
        side=side,
        confidence=confidence,
        entry_price=current_price,
        tp_price=tp_price,
        sl_price=sl_price,
        rr_ratio=rr_ratio,
        atr_pct=atr_pct,
        volume_ratio=volume_ratio,
        rsi_5m=rsi_5m,
        trend_15m=trend_15m,
        reasons=reasons,
        timestamp=CURRENT_TIME
    )
    
    RETURN signal

END ALGORITHM
```



### 6.2 Max Hold Time Enforcement Algorithm

```
ALGORITHM: enforce_max_hold_time()

INPUT: List of open scalping positions
OUTPUT: Positions closed if max hold time exceeded

STEP 1: Get Current Time
    current_time ← GET current Unix timestamp

STEP 2: Iterate Through Open Positions
    FOR EACH position IN open_positions:
        
        STEP 2.1: Calculate Elapsed Time
            elapsed_seconds ← current_time - position.opened_at
        
        STEP 2.2: Check Max Hold Time
            IF elapsed_seconds >= 1800:  // 30 minutes = 1800 seconds
                
                STEP 2.2.1: Log Event
                    LOG "Max hold time exceeded for {position.symbol}"
                    LOG "Elapsed: {elapsed_seconds}s, Max: 1800s"
                
                STEP 2.2.2: Close Position at Market
                    close_side ← "SELL" IF position.side == "BUY" ELSE "BUY"
                    
                    result ← PLACE_ORDER(
                        symbol=position.symbol,
                        side=close_side,
                        quantity=position.quantity,
                        order_type="market",
                        reduce_only=True
                    )
                
                STEP 2.2.3: Handle Close Result
                    IF result.success:
                        fill_price ← result.fill_price
                        
                        // Calculate PnL
                        IF position.side == "BUY":
                            pnl ← (fill_price - position.entry_price) × position.quantity
                        ELSE:
                            pnl ← (position.entry_price - fill_price) × position.quantity
                        
                        pnl_with_leverage ← pnl × position.leverage
                        
                        // Update database
                        UPDATE autotrade_trades
                        SET status = "closed_max_hold",
                            close_price = fill_price,
                            pnl_usdt = pnl_with_leverage,
                            close_reason = "max_hold_time_exceeded",
                            closed_at = current_time
                        WHERE telegram_id = position.user_id
                          AND symbol = position.symbol
                          AND status = "open"
                        
                        // Notify user
                        SEND_MESSAGE(
                            user_id=position.user_id,
                            text="⏰ Position closed (30min max hold)\n"
                                 f"Symbol: {position.symbol}\n"
                                 f"Entry: {position.entry_price}\n"
                                 f"Exit: {fill_price}\n"
                                 f"PnL: {pnl_with_leverage:+.2f} USDT"
                        )
                        
                        // Remove from tracking
                        REMOVE position FROM open_positions
                    
                    ELSE:
                        LOG "Failed to close position: {result.error}"
                        // Retry on next scan cycle

END ALGORITHM
```



### 6.3 Mode Switching Algorithm

```
ALGORITHM: switch_trading_mode(user_id, new_mode)

INPUT: user_id (int), new_mode (TradingMode enum)
OUTPUT: Success/failure status with message

STEP 1: Validate Mode Change
    current_mode ← GET_MODE(user_id)
    
    IF current_mode == new_mode:
        RETURN {
            "success": False,
            "message": "Already in {new_mode} mode"
        }

STEP 2: Check Open Positions
    open_positions ← QUERY database:
        SELECT * FROM autotrade_trades
        WHERE telegram_id = user_id
          AND status = 'open'
    
    IF open_positions.COUNT > 0:
        // Option A: Block mode switch
        RETURN {
            "success": False,
            "message": "Please close {open_positions.COUNT} open position(s) first"
        }
        
        // Option B: Allow switch, positions close naturally
        // (Choose based on requirements)

STEP 3: Stop Current Engine
    TRY:
        CALL stop_engine(user_id)
        LOG "Stopped {current_mode} engine for user {user_id}"
    CATCH Exception as e:
        LOG "Warning: Failed to stop engine: {e}"
        // Continue anyway - engine may not be running

STEP 4: Update Database
    TRY:
        UPDATE autotrade_sessions
        SET trading_mode = new_mode.value,
            updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = user_id
        
        IF rows_affected == 0:
            RETURN {
                "success": False,
                "message": "Database update failed - no session found"
            }
    
    CATCH Exception as e:
        LOG "Database update error: {e}"
        RETURN {
            "success": False,
            "message": "Database error: {e}"
        }

STEP 5: Load User Configuration
    keys ← GET_USER_API_KEYS(user_id)
    session ← GET_AUTOTRADE_SESSION(user_id)
    
    IF keys == None OR session == None:
        RETURN {
            "success": False,
            "message": "User configuration not found"
        }

STEP 6: Start New Engine
    TRY:
        CALL start_engine(
            bot=bot,
            user_id=user_id,
            api_key=keys.api_key,
            api_secret=keys.api_secret,
            amount=session.initial_deposit,
            leverage=session.leverage,
            notify_chat_id=user_id,
            exchange_id=keys.exchange
        )
        
        LOG "Started {new_mode} engine for user {user_id}"
    
    CATCH Exception as e:
        LOG "Failed to start engine: {e}"
        
        // Rollback: restore previous mode
        UPDATE autotrade_sessions
        SET trading_mode = current_mode.value
        WHERE telegram_id = user_id
        
        RETURN {
            "success": False,
            "message": "Failed to start engine: {e}"
        }

STEP 7: Return Success
    RETURN {
        "success": True,
        "message": "Switched to {new_mode} mode",
        "mode": new_mode,
        "previous_mode": current_mode
    }

END ALGORITHM
```



## 7. Database Schema

### 7.1 Migration Script

**File:** `db/add_trading_mode.sql`

```sql
-- ============================================================
-- Migration: Add Trading Mode Support
-- Description: Add trading_mode column to autotrade_sessions
-- Date: 2024
-- ============================================================

-- Add trading_mode column
ALTER TABLE autotrade_sessions 
ADD COLUMN IF NOT EXISTS trading_mode VARCHAR(20) DEFAULT 'swing';

-- Add comment for documentation
COMMENT ON COLUMN autotrade_sessions.trading_mode IS 
'Trading mode: scalping (5M high-frequency) or swing (15M multi-tier)';

-- Create index for faster mode queries
CREATE INDEX IF NOT EXISTS idx_autotrade_sessions_trading_mode 
ON autotrade_sessions(telegram_id, trading_mode);

-- Update existing rows to default swing mode
UPDATE autotrade_sessions 
SET trading_mode = 'swing' 
WHERE trading_mode IS NULL;

-- Add constraint to ensure valid values
ALTER TABLE autotrade_sessions
ADD CONSTRAINT chk_trading_mode 
CHECK (trading_mode IN ('scalping', 'swing'));

-- ============================================================
-- Verification Queries
-- ============================================================

-- Check column exists
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'autotrade_sessions'
  AND column_name = 'trading_mode';

-- Check index exists
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'autotrade_sessions'
  AND indexname = 'idx_autotrade_sessions_trading_mode';

-- Check data distribution
SELECT trading_mode, COUNT(*) as user_count
FROM autotrade_sessions
GROUP BY trading_mode;
```

### 7.2 Query Patterns

**Get User Trading Mode:**

```sql
-- Get current trading mode for user
SELECT trading_mode 
FROM autotrade_sessions 
WHERE telegram_id = $1;

-- Expected result: 'scalping' or 'swing'
-- Default: 'swing' for new users
```

**Update Trading Mode:**

```sql
-- Update user's trading mode
UPDATE autotrade_sessions 
SET trading_mode = $2,
    updated_at = NOW()
WHERE telegram_id = $1
RETURNING trading_mode, updated_at;

-- Parameters:
-- $1: user telegram_id (int)
-- $2: new mode ('scalping' or 'swing')
```

**Get Scalping Trades:**

```sql
-- Get all scalping trades for user
SELECT *
FROM autotrade_trades
WHERE telegram_id = $1
  AND trade_type = 'scalping'
ORDER BY opened_at DESC
LIMIT 50;

-- Get scalping performance stats
SELECT 
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN pnl_usdt < 0 THEN 1 ELSE 0 END) as losses,
    AVG(pnl_usdt) as avg_pnl,
    SUM(pnl_usdt) as total_pnl,
    AVG(EXTRACT(EPOCH FROM (closed_at - opened_at))) as avg_hold_time_seconds
FROM autotrade_trades
WHERE telegram_id = $1
  AND trade_type = 'scalping'
  AND status IN ('closed_tp', 'closed_sl', 'closed_max_hold');
```

**Get Swing Trades:**

```sql
-- Get all swing trades for user
SELECT *
FROM autotrade_trades
WHERE telegram_id = $1
  AND trade_type = 'swing'
ORDER BY opened_at DESC
LIMIT 50;

-- Get swing performance stats
SELECT 
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN pnl_usdt < 0 THEN 1 ELSE 0 END) as losses,
    AVG(pnl_usdt) as avg_pnl,
    SUM(pnl_usdt) as total_pnl,
    SUM(CASE WHEN tp1_hit THEN 1 ELSE 0 END) as tp1_hits,
    SUM(CASE WHEN tp2_hit THEN 1 ELSE 0 END) as tp2_hits,
    SUM(CASE WHEN tp3_hit THEN 1 ELSE 0 END) as tp3_hits
FROM autotrade_trades
WHERE telegram_id = $1
  AND trade_type = 'swing'
  AND status IN ('closed_tp', 'closed_sl', 'closed_tp1', 'closed_tp2', 'closed_tp3');
```

**Compare Mode Performance:**

```sql
-- Compare scalping vs swing performance
SELECT 
    trade_type,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(100.0 * SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate_pct,
    ROUND(AVG(pnl_usdt), 2) as avg_pnl,
    ROUND(SUM(pnl_usdt), 2) as total_pnl,
    ROUND(AVG(EXTRACT(EPOCH FROM (closed_at - opened_at)) / 60), 1) as avg_hold_time_minutes
FROM autotrade_trades
WHERE telegram_id = $1
  AND status IN ('closed_tp', 'closed_sl', 'closed_max_hold', 'closed_tp1', 'closed_tp2', 'closed_tp3')
GROUP BY trade_type
ORDER BY trade_type;
```



## 8. Error Handling

### 8.1 Signal Generation Errors

**Strategy:** Graceful degradation - log error and continue to next symbol

```python
def generate_scalping_signal(self, symbol: str) -> Optional[ScalpingSignal]:
    try:
        # Signal generation logic
        pass
    except requests.exceptions.Timeout as e:
        logger.warning(f"[Scalping:{self.user_id}] Timeout fetching data for {symbol}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"[Scalping:{self.user_id}] Network error for {symbol}: {e}")
        return None
    except KeyError as e:
        logger.error(f"[Scalping:{self.user_id}] Missing data field for {symbol}: {e}")
        return None
    except Exception as e:
        logger.error(f"[Scalping:{self.user_id}] Unexpected error for {symbol}: {e}", exc_info=True)
        return None
```

**Error Recovery:**
- Skip current symbol and continue to next
- Log error details for debugging
- Don't crash entire engine
- Retry on next scan cycle (15 seconds later)

### 8.2 Order Placement Errors

**Strategy:** Exponential backoff retry with user notification

```python
async def place_scalping_order(self, signal: ScalpingSignal) -> bool:
    max_retries = 3
    base_delay = 1.0  # seconds
    
    for attempt in range(max_retries):
        try:
            result = await asyncio.to_thread(
                self.client.place_order,
                symbol=signal.symbol,
                side="BUY" if signal.side == "LONG" else "SELL",
                quantity=self.calculate_position_size(signal),
                order_type='market'
            )
            
            if result.get('success'):
                logger.info(f"[Scalping:{self.user_id}] Order placed: {signal.symbol} {signal.side}")
                return True
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.warning(f"[Scalping:{self.user_id}] Order failed (attempt {attempt+1}): {error_msg}")
                
                # Check if error is retryable
                if 'insufficient balance' in error_msg.lower():
                    await self.notify_user(f"❌ Order failed: Insufficient balance")
                    return False
                
                if 'invalid symbol' in error_msg.lower():
                    await self.notify_user(f"❌ Order failed: Invalid symbol {signal.symbol}")
                    return False
                
                # Retryable error - wait and retry
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    await asyncio.sleep(delay)
        
        except asyncio.TimeoutError:
            logger.warning(f"[Scalping:{self.user_id}] Order timeout (attempt {attempt+1})")
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2 ** attempt))
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Order exception (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2 ** attempt))
    
    # All retries failed
    await self.notify_user(
        f"❌ Failed to place order for {signal.symbol} after {max_retries} attempts.\n"
        f"Signal skipped. Engine continues monitoring."
    )
    return False
```



### 8.3 Mode Switching Errors

**Strategy:** Rollback on failure, maintain system consistency

```python
async def switch_mode(user_id: int, new_mode: TradingMode, bot, context) -> Dict:
    current_mode = None
    engine_stopped = False
    db_updated = False
    
    try:
        # Step 1: Get current mode
        current_mode = TradingModeManager.get_mode(user_id)
        
        # Step 2: Stop engine
        try:
            stop_engine(user_id)
            engine_stopped = True
        except Exception as e:
            logger.warning(f"[ModeSwitch:{user_id}] Engine stop warning: {e}")
            # Continue - engine may not be running
        
        # Step 3: Update database
        try:
            success = TradingModeManager.set_mode(user_id, new_mode)
            if not success:
                raise Exception("Database update returned False")
            db_updated = True
        except Exception as e:
            logger.error(f"[ModeSwitch:{user_id}] Database update failed: {e}")
            
            # Rollback: restart old engine
            if engine_stopped and current_mode:
                try:
                    await restart_engine_with_mode(user_id, current_mode, bot, context)
                except Exception as restart_err:
                    logger.error(f"[ModeSwitch:{user_id}] Rollback failed: {restart_err}")
            
            return {
                "success": False,
                "message": f"Database update failed: {str(e)[:100]}"
            }
        
        # Step 4: Start new engine
        try:
            await restart_engine_with_mode(user_id, new_mode, bot, context)
        except Exception as e:
            logger.error(f"[ModeSwitch:{user_id}] Engine start failed: {e}")
            
            # Rollback: restore old mode in database
            if db_updated and current_mode:
                try:
                    TradingModeManager.set_mode(user_id, current_mode)
                    await restart_engine_with_mode(user_id, current_mode, bot, context)
                except Exception as rollback_err:
                    logger.critical(f"[ModeSwitch:{user_id}] CRITICAL: Rollback failed: {rollback_err}")
            
            return {
                "success": False,
                "message": f"Engine start failed: {str(e)[:100]}"
            }
        
        # Success
        logger.info(f"[ModeSwitch:{user_id}] Successfully switched from {current_mode} to {new_mode}")
        return {
            "success": True,
            "message": f"Switched to {new_mode.value} mode",
            "mode": new_mode,
            "previous_mode": current_mode
        }
    
    except Exception as e:
        logger.error(f"[ModeSwitch:{user_id}] Unexpected error: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)[:100]}"
        }
```

**Error Scenarios:**

1. **Database update fails:** Restart old engine, notify user
2. **Engine start fails:** Rollback database, restart old engine
3. **Rollback fails:** Log critical error, notify admin, manual intervention required



## 9. Performance Considerations

### 9.1 Scan Interval Optimization

**Challenge:** Scalping mode scans every 15 seconds (4x faster than swing's 60 seconds)

**Optimizations:**

1. **Async/Await for Non-Blocking I/O:**
```python
async def run(self):
    while self.running:
        # Non-blocking sleep
        await asyncio.sleep(self.config.scan_interval)
        
        # Parallel symbol scanning
        tasks = [
            self.scan_symbol(symbol) 
            for symbol in self.config.pairs
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
```

2. **Batch API Calls:**
```python
# Instead of sequential calls:
# for symbol in symbols:
#     klines = get_klines(symbol)

# Use batch fetching:
async def fetch_all_klines(symbols):
    tasks = [
        asyncio.to_thread(get_klines, symbol)
        for symbol in symbols
    ]
    return await asyncio.gather(*tasks)
```

3. **Caching Market Data:**
```python
# Cache 15M trend data (changes slowly)
_trend_cache = {}
_trend_cache_ttl = 300  # 5 minutes

def get_15m_trend(symbol):
    if symbol in _trend_cache:
        cached_time, trend = _trend_cache[symbol]
        if time.time() - cached_time < _trend_cache_ttl:
            return trend
    
    # Fetch fresh data
    trend = calculate_15m_trend(symbol)
    _trend_cache[symbol] = (time.time(), trend)
    return trend
```

### 9.2 Database Query Optimization

**Challenge:** Frequent database reads/writes for position tracking

**Optimizations:**

1. **In-Memory Position Tracking:**
```python
# Keep positions in memory, sync to DB periodically
class ScalpingEngine:
    def __init__(self):
        self.positions = {}  # In-memory cache
        self.db_sync_interval = 30  # Sync every 30 seconds
    
    async def sync_positions_to_db(self):
        """Batch update positions to database"""
        if not self.positions:
            return
        
        # Batch update instead of individual updates
        updates = [
            {
                "telegram_id": self.user_id,
                "symbol": pos.symbol,
                "status": pos.status,
                "updated_at": datetime.utcnow().isoformat()
            }
            for pos in self.positions.values()
        ]
        
        # Single batch upsert
        _client().table("autotrade_trades").upsert(updates).execute()
```

2. **Connection Pooling:**
```python
# Supabase client already uses connection pooling
# Ensure we reuse the same client instance
_supabase_client = None

def _client():
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supabase_client
```

3. **Index Optimization:**
```sql
-- Composite index for fast position lookups
CREATE INDEX idx_autotrade_trades_user_status 
ON autotrade_trades(telegram_id, status, symbol);

-- Index for mode queries
CREATE INDEX idx_autotrade_sessions_mode 
ON autotrade_sessions(telegram_id, trading_mode);
```



### 9.3 API Rate Limits

**Challenge:** Exchange APIs have rate limits (e.g., Binance: 1200 requests/minute)

**Rate Limit Management:**

```python
class RateLimiter:
    """Token bucket rate limiter for exchange API calls"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window  # seconds
        self.tokens = max_requests
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until a token is available"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Refill tokens based on elapsed time
            self.tokens = min(
                self.max_requests,
                self.tokens + (elapsed * self.max_requests / self.time_window)
            )
            self.last_update = now
            
            if self.tokens < 1:
                # Wait until next token available
                wait_time = (1 - self.tokens) * self.time_window / self.max_requests
                await asyncio.sleep(wait_time)
                self.tokens = 1
            
            self.tokens -= 1

# Usage in ScalpingEngine
class ScalpingEngine:
    def __init__(self):
        # Binance: 1200 req/min = 20 req/sec
        # Conservative: 10 req/sec for scalping
        self.rate_limiter = RateLimiter(max_requests=10, time_window=1)
    
    async def fetch_klines(self, symbol, interval):
        await self.rate_limiter.acquire()
        return await asyncio.to_thread(
            self.provider.get_klines, symbol, interval
        )
```

**Backoff Strategy:**

```python
async def handle_rate_limit_error(self, error):
    """Handle 429 Too Many Requests error"""
    if '429' in str(error) or 'rate limit' in str(error).lower():
        logger.warning(f"[Scalping:{self.user_id}] Rate limit hit, pausing for 60s")
        
        # Pause scalping for 60 seconds
        await asyncio.sleep(60)
        
        # Notify user
        await self.notify_user(
            "⚠️ Exchange rate limit reached. Scalping paused for 1 minute."
        )
        
        return True
    return False
```

**Priority System:**

```python
# Prioritize position monitoring over signal generation
async def run(self):
    while self.running:
        # PRIORITY 1: Monitor existing positions (critical)
        await self.monitor_positions()
        
        # PRIORITY 2: Generate new signals (can skip if rate limited)
        try:
            await self.scan_for_signals()
        except RateLimitError:
            logger.info("Rate limit - skipping signal scan this cycle")
            # Continue to next cycle, positions still monitored
        
        await asyncio.sleep(self.config.scan_interval)
```



## 10. Testing Strategy

### 10.1 Unit Tests

**File:** `tests/test_scalping_engine.py`

```python
import pytest
from app.scalping_engine import ScalpingEngine, ScalpingConfig
from app.trading_mode_manager import TradingMode, TradingModeManager

class TestScalpingSignalGeneration:
    """Test signal generation logic"""
    
    def test_generate_signal_uptrend_oversold(self):
        """Test LONG signal on 15M uptrend + 5M oversold"""
        # Mock 15M data: uptrend (price > EMA21 > EMA50)
        # Mock 5M data: RSI < 30, volume > 2x
        # Expected: LONG signal with confidence >= 80%
        pass
    
    def test_generate_signal_downtrend_overbought(self):
        """Test SHORT signal on 15M downtrend + 5M overbought"""
        # Mock 15M data: downtrend (price < EMA21 < EMA50)
        # Mock 5M data: RSI > 70, volume > 2x
        # Expected: SHORT signal with confidence >= 80%
        pass
    
    def test_generate_signal_no_trend(self):
        """Test no signal when 15M trend is neutral"""
        # Mock 15M data: neutral (EMA21 ≈ EMA50)
        # Expected: None (no signal)
        pass
    
    def test_generate_signal_low_volume(self):
        """Test no signal when volume < 2x average"""
        # Mock data with volume ratio < 2.0
        # Expected: None (no signal)
        pass

class TestScalpingValidation:
    """Test signal validation logic"""
    
    def test_validate_confidence_threshold(self):
        """Test signal rejected if confidence < 80%"""
        signal = create_mock_signal(confidence=75)
        engine = ScalpingEngine(...)
        assert engine.validate_scalping_entry(signal) == False
    
    def test_validate_rr_ratio(self):
        """Test signal rejected if R:R < 1.5"""
        signal = create_mock_signal(rr_ratio=1.2)
        engine = ScalpingEngine(...)
        assert engine.validate_scalping_entry(signal) == False
    
    def test_validate_cooldown(self):
        """Test signal rejected if symbol in cooldown"""
        engine = ScalpingEngine(...)
        engine.mark_cooldown("BTCUSDT")
        signal = create_mock_signal(symbol="BTCUSDT")
        assert engine.validate_scalping_entry(signal) == False

class TestMaxHoldTime:
    """Test max hold time enforcement"""
    
    def test_position_expired(self):
        """Test position marked as expired after 30 minutes"""
        position = create_mock_position(opened_at=time.time() - 1801)
        assert position.is_expired() == True
    
    def test_position_not_expired(self):
        """Test position not expired before 30 minutes"""
        position = create_mock_position(opened_at=time.time() - 1799)
        assert position.is_expired() == False
    
    @pytest.mark.asyncio
    async def test_close_position_max_hold(self):
        """Test position closed at market when max hold time reached"""
        # Mock exchange client
        # Create expired position
        # Call close_position_max_hold()
        # Assert order placed with reduce_only=True
        # Assert position removed from tracking
        pass

class TestTradingModeManager:
    """Test mode management"""
    
    def test_get_mode_default(self):
        """Test default mode is SWING for new users"""
        mode = TradingModeManager.get_mode(user_id=99999)
        assert mode == TradingMode.SWING
    
    def test_set_mode(self):
        """Test mode update in database"""
        success = TradingModeManager.set_mode(user_id=12345, mode=TradingMode.SCALPING)
        assert success == True
        
        mode = TradingModeManager.get_mode(user_id=12345)
        assert mode == TradingMode.SCALPING
    
    @pytest.mark.asyncio
    async def test_switch_mode_success(self):
        """Test successful mode switch"""
        result = await TradingModeManager.switch_mode(
            user_id=12345,
            new_mode=TradingMode.SCALPING,
            bot=mock_bot,
            context=mock_context
        )
        assert result["success"] == True
        assert result["mode"] == TradingMode.SCALPING
```



### 10.2 Integration Tests

**File:** `tests/test_scalping_integration.py`

```python
import pytest
from app.autotrade_engine import start_engine, stop_engine
from app.trading_mode_manager import TradingMode, TradingModeManager

class TestScalpingIntegration:
    """Test full scalping flow"""
    
    @pytest.mark.asyncio
    async def test_full_scalping_flow(self):
        """
        Test complete scalping flow:
        1. User selects scalping mode
        2. Engine starts with scalping config
        3. Signal generated
        4. Order placed
        5. Position monitored
        6. TP hit → position closed
        """
        # Setup test user
        user_id = 12345
        
        # Step 1: Switch to scalping mode
        result = await TradingModeManager.switch_mode(
            user_id, TradingMode.SCALPING, mock_bot, mock_context
        )
        assert result["success"] == True
        
        # Step 2: Verify engine started
        from app.autotrade_engine import is_running
        assert is_running(user_id) == True
        
        # Step 3: Mock signal generation
        # (Use test exchange with mock data)
        
        # Step 4: Wait for signal and order
        await asyncio.sleep(20)  # Wait for scan cycle
        
        # Step 5: Verify position opened
        positions = get_open_positions(user_id)
        assert len(positions) == 1
        
        # Step 6: Mock TP hit
        # Verify position closed
        # Verify database updated
        pass
    
    @pytest.mark.asyncio
    async def test_mode_switch_with_open_positions(self):
        """Test mode switch behavior with open positions"""
        user_id = 12345
        
        # Open a scalping position
        # Attempt to switch to swing mode
        # Verify: either blocked or positions close naturally
        pass
    
    @pytest.mark.asyncio
    async def test_max_hold_time_enforcement(self):
        """Test position closed after 30 minutes"""
        user_id = 12345
        
        # Open scalping position
        # Fast-forward time by 30 minutes (mock)
        # Verify position closed with reason "max_hold_time_exceeded"
        pass
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_scalping(self):
        """Test circuit breaker stops scalping after 5% loss"""
        user_id = 12345
        
        # Simulate multiple losing scalping trades
        # Verify engine stops when -5% reached
        # Verify no new signals generated
        pass

class TestDashboardIntegration:
    """Test dashboard UI integration"""
    
    @pytest.mark.asyncio
    async def test_trading_mode_menu_display(self):
        """Test mode selection menu shows correctly"""
        # Simulate /autotrade command
        # Click "Trading Mode" button
        # Verify menu shows both modes with current mode marked
        pass
    
    @pytest.mark.asyncio
    async def test_mode_selection_callback(self):
        """Test mode selection updates dashboard"""
        # Click "Scalping Mode" button
        # Verify confirmation message
        # Return to dashboard
        # Verify dashboard shows "⚡ Mode: Scalping (5M)"
        pass
```



### 10.3 Demo User Testing

**Strategy:** Enable scalping mode for demo users with paper trading

**Implementation:**

```python
# In scalping_engine.py
class ScalpingEngine:
    def __init__(self, user_id, client, bot, notify_chat_id, config=None, demo_mode=False):
        self.demo_mode = demo_mode or is_demo_user(user_id)
        # ... rest of init
    
    async def place_scalping_order(self, signal: ScalpingSignal) -> bool:
        if self.demo_mode:
            # Paper trading - simulate order
            logger.info(f"[DEMO] Simulated order: {signal.symbol} {signal.side}")
            
            # Store simulated position
            self.positions[signal.symbol] = ScalpingPosition(
                user_id=self.user_id,
                symbol=signal.symbol,
                side="BUY" if signal.side == "LONG" else "SELL",
                entry_price=signal.entry_price,
                quantity=self.calculate_position_size(signal),
                leverage=10,
                tp_price=signal.tp_price,
                sl_price=signal.sl_price,
                opened_at=time.time(),
                max_hold_until=time.time() + 1800,
                status="open"
            )
            
            await self.notify_user(
                f"📝 <b>DEMO Trade Opened</b>\n\n"
                f"Symbol: {signal.symbol}\n"
                f"Side: {signal.side}\n"
                f"Entry: {signal.entry_price:.4f}\n"
                f"TP: {signal.tp_price:.4f}\n"
                f"SL: {signal.sl_price:.4f}\n\n"
                f"⚠️ This is a simulated trade (demo mode)"
            )
            
            return True
        else:
            # Real trading
            return await self._place_real_order(signal)
```

**Demo User Test Plan:**

1. **Setup:**
   - Add test user to demo_users list
   - Enable scalping mode for demo user
   - Monitor logs for signal generation

2. **Signal Quality Test:**
   - Run for 24 hours
   - Log all generated signals
   - Verify confidence >= 80%
   - Verify R:R >= 1.5
   - Verify volume spike > 2x

3. **Performance Test:**
   - Track simulated trades
   - Calculate win rate
   - Calculate average hold time
   - Verify max hold time enforcement

4. **Validation Criteria:**
   - Win rate >= 60%
   - Average R:R >= 1.5
   - Max hold time never exceeded
   - No crashes or errors
   - Scan interval consistent (15s ± 2s)

**Test Script:**

```python
# test_scalping_demo.py
import asyncio
from app.demo_users import add_demo_user
from app.trading_mode_manager import TradingModeManager, TradingMode
from app.autotrade_engine import start_engine

async def test_scalping_demo():
    """Test scalping mode with demo user"""
    
    # Setup demo user
    demo_user_id = 999999
    add_demo_user(demo_user_id)
    
    # Switch to scalping mode
    result = await TradingModeManager.switch_mode(
        demo_user_id,
        TradingMode.SCALPING,
        bot,
        context
    )
    
    print(f"Mode switch result: {result}")
    
    # Let it run for 1 hour
    print("Running scalping engine for 1 hour...")
    await asyncio.sleep(3600)
    
    # Check results
    trades = get_demo_trades(demo_user_id)
    print(f"\nDemo Results:")
    print(f"Total signals: {len(trades)}")
    print(f"Win rate: {calculate_win_rate(trades):.1f}%")
    print(f"Avg hold time: {calculate_avg_hold_time(trades):.1f} minutes")
    
    # Stop engine
    stop_engine(demo_user_id)

if __name__ == "__main__":
    asyncio.run(test_scalping_demo())
```



## 11. Deployment Plan

### 11.1 Phased Rollout

**Phase 1: Development & Testing (Week 1-2)**
- Implement ScalpingEngine module
- Implement TradingModeManager
- Add database migration
- Unit tests
- Integration tests

**Phase 2: Demo User Testing (Week 3)**
- Deploy to VPS with demo users only
- Monitor for 7 days
- Collect performance metrics
- Fix bugs and optimize

**Phase 3: Limited Beta (Week 4)**
- Enable for 10-20 beta users
- Monitor closely for issues
- Gather user feedback
- Optimize based on feedback

**Phase 4: General Availability (Week 5+)**
- Enable for all users
- Announce feature in community
- Monitor performance and stability
- Iterate based on user feedback

### 11.2 Monitoring & Metrics

**Key Metrics to Track:**

```python
# Scalping performance metrics
SCALPING_METRICS = {
    "signals_generated_per_day": 0,
    "signals_executed_per_day": 0,
    "avg_confidence": 0.0,
    "avg_rr_ratio": 0.0,
    "win_rate": 0.0,
    "avg_hold_time_minutes": 0.0,
    "max_hold_time_violations": 0,
    "circuit_breaker_triggers": 0,
    "api_rate_limit_hits": 0,
    "order_placement_failures": 0,
    "mode_switches_per_day": 0,
}

# Log metrics every hour
async def log_scalping_metrics():
    metrics = calculate_scalping_metrics()
    logger.info(f"[ScalpingMetrics] {metrics}")
    
    # Send to monitoring service (e.g., Datadog, Prometheus)
    # send_metrics_to_monitoring(metrics)
```

**Alerts:**

```python
# Alert conditions
ALERTS = {
    "high_failure_rate": {
        "condition": "order_placement_failures > 10 per hour",
        "action": "Notify admin, investigate exchange issues"
    },
    "low_win_rate": {
        "condition": "win_rate < 50% over 24 hours",
        "action": "Review signal quality, adjust parameters"
    },
    "rate_limit_exceeded": {
        "condition": "api_rate_limit_hits > 5 per hour",
        "action": "Reduce scan frequency, optimize API calls"
    },
    "circuit_breaker_frequent": {
        "condition": "circuit_breaker_triggers > 3 per day",
        "action": "Review risk management, adjust loss limits"
    }
}
```

### 11.3 Rollback Plan

**If critical issues arise:**

1. **Disable scalping mode for all users:**
```sql
-- Emergency: disable scalping mode
UPDATE autotrade_sessions 
SET trading_mode = 'swing' 
WHERE trading_mode = 'scalping';
```

2. **Stop all scalping engines:**
```python
# In bot admin command
async def cmd_emergency_stop_scalping(update, context):
    """Admin command to stop all scalping engines"""
    from app.autotrade_engine import _running_tasks
    
    stopped_count = 0
    for user_id, task in _running_tasks.items():
        mode = TradingModeManager.get_mode(user_id)
        if mode == TradingMode.SCALPING:
            task.cancel()
            stopped_count += 1
    
    await update.message.reply_text(
        f"🛑 Emergency stop: {stopped_count} scalping engines stopped"
    )
```

3. **Notify affected users:**
```python
async def notify_scalping_users_rollback(bot):
    """Notify users that scalping mode is temporarily disabled"""
    users = get_scalping_users()
    
    for user_id in users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    "⚠️ <b>Scalping Mode Temporarily Disabled</b>\n\n"
                    "We've detected an issue with scalping mode and have "
                    "temporarily disabled it for all users.\n\n"
                    "Your account has been switched to Swing Mode.\n\n"
                    "We're working to resolve the issue and will notify you "
                    "when scalping mode is available again.\n\n"
                    "Apologies for the inconvenience."
                ),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
```



## 12. Future Enhancements

### 12.1 Advanced Scalping Features (Post-MVP)

**Dynamic TP Adjustment:**
- Adjust TP based on market volatility
- Higher TP in trending markets (2R instead of 1.5R)
- Lower TP in ranging markets (1.2R for quick exits)

**Trailing Stop for Scalping:**
- After TP is 50% reached, activate trailing stop
- Trail by 0.5 ATR to capture extended moves
- Maximize profit on strong momentum trades

**Multi-Pair Scalping:**
- Expand beyond BTC/ETH to top 10 pairs
- Dynamic pair selection based on volatility
- Rotate pairs based on performance

**Adaptive Confidence Threshold:**
- Lower threshold (75%) during high-volatility periods
- Higher threshold (85%) during low-volatility periods
- Machine learning to optimize threshold

### 12.2 Performance Optimization

**Signal Caching:**
- Cache 15M trend analysis for 5 minutes
- Reduce redundant calculations
- Improve scan speed

**WebSocket Integration:**
- Use WebSocket for real-time price updates
- Reduce API calls by 80%
- Faster signal generation

**Distributed Scalping:**
- Run scalping engine on separate process
- Isolate from swing trading engine
- Better resource utilization

### 12.3 User Experience Improvements

**Scalping Dashboard:**
- Dedicated dashboard for scalping stats
- Real-time position tracking
- Performance charts (win rate, PnL over time)

**Customizable Parameters:**
- Allow users to adjust confidence threshold
- Adjust max hold time (15-60 minutes)
- Select specific pairs to trade

**Scalping Leaderboard:**
- Show top scalping performers
- Gamification to encourage engagement
- Social proof for feature adoption

### 12.4 Risk Management Enhancements

**Per-Mode Circuit Breaker:**
- Separate loss limits for scalping vs swing
- Scalping: -3% daily limit
- Swing: -5% daily limit

**Position Correlation:**
- Avoid opening correlated positions
- If long BTC, don't long ETH (high correlation)
- Diversify risk across uncorrelated pairs

**Volatility-Based Position Sizing:**
- Reduce position size in high volatility
- Increase position size in low volatility
- Maintain consistent risk per trade

---

## Summary

This design document provides a comprehensive blueprint for implementing the Scalping Mode feature. The architecture follows a modular design pattern that integrates seamlessly with the existing autotrade system while maintaining clean separation of concerns.

**Key Design Principles:**
1. **Modularity:** Separate ScalpingEngine from swing trading logic
2. **Persistence:** Trading mode stored in database, survives restarts
3. **Safety:** Circuit breaker, max hold time, cooldown periods
4. **Performance:** Async/await, caching, rate limiting
5. **Testability:** Unit tests, integration tests, demo user testing
6. **Maintainability:** Clear error handling, logging, monitoring

**Next Steps:**
1. Review and approve design document
2. Create implementation tasks from design
3. Begin Phase 1 development
4. Set up monitoring and metrics
5. Prepare demo user test environment

