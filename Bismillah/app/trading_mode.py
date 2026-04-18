"""
Trading Mode Data Models and Enums
Defines trading modes (scalping vs swing) and related data structures
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import time
import os


class TradingMode(Enum):
    """Trading mode enumeration"""
    SCALPING = "scalping"
    SWING = "swing"
    MIXED = "mixed"
    
    @classmethod
    def from_string(cls, mode_str: str):
        """
        Convert string to TradingMode enum
        
        Args:
            mode_str: String representation of mode ('scalping' or 'swing')
            
        Returns:
            TradingMode enum value, defaults to SWING if invalid
        """
        mode_str = mode_str.lower().strip() if mode_str else ""
        if mode_str == "scalping":
            return cls.SCALPING
        elif mode_str == "swing":
            return cls.SWING
        elif mode_str == "mixed":
            return cls.MIXED
        else:
            return cls.SWING  # Default to swing
    
    def __str__(self):
        return self.value


@dataclass
class ScalpingConfig:
    """Configuration for scalping mode"""
    
    # Timeframe and scanning
    timeframe: str = "5m"
    scan_interval: int = 15  # seconds between scans (back to 15s with proper async)
    
    # Signal requirements
    min_confidence: float = 0.72  # 72% minimum
    min_rr: float = 1.5  # Minimum risk-reward ratio
    sideways_min_rr: float = float(os.getenv("SCALPING_SIDEWAYS_MIN_RR", "1.1"))  # temporary relax for sideways flow
    emergency_candidate_mode: bool = os.getenv("SCALPING_EMERGENCY_CANDIDATE_MODE", "true").lower() == "true"
    emergency_min_volume_ratio: float = float(os.getenv("SCALPING_EMERGENCY_MIN_VOL_RATIO", "0.9"))
    
    # Position management
    max_hold_time: int = 1800  # 30 minutes in seconds
    single_tp_multiplier: float = 1.5  # TP at 1.5R
    adaptive_timeout_protection_enabled: bool = os.getenv(
        "SCALPING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED",
        os.getenv("SCALPING_TIMEOUT_PROTECTION_ENABLED", "false"),
    ).lower() == "true"
    timeout_be_trigger_pct: float = float(os.getenv("SCALPING_TIMEOUT_BE_TRIGGER_PCT", "0.20"))
    timeout_trailing_trigger_pct: float = float(os.getenv("SCALPING_TIMEOUT_TRAILING_TRIGGER_PCT", "0.35"))
    timeout_late_tighten_multiplier: float = float(os.getenv("SCALPING_TIMEOUT_LATE_TIGHTEN_MULTIPLIER", "1.4"))
    timeout_protection_min_update_seconds: int = int(os.getenv("SCALPING_TIMEOUT_PROTECTION_MIN_UPDATE_SECONDS", "45"))
    timeout_near_flat_usdt_threshold: float = float(os.getenv("SCALPING_TIMEOUT_NEAR_FLAT_USDT_THRESHOLD", "0.02"))
    
    # Risk management
    max_concurrent_positions: int = 4  # Shared with swing mode
    daily_loss_limit: float = 0.05  # 5% circuit breaker
    
    # Trading pairs (expanded for more sideways opportunities)
    pairs: List[str] = field(default_factory=lambda: [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", 
        "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT", 
        "UNIUSDT", "ATOMUSDT", "XAUUSDT", "CLUSDT", "QQQUSDT"
    ])
    
    # ATR multipliers
    atr_sl_multiplier: float = 1.5  # SL = 1.5 * ATR (5M)
    
    # Cooldown (reduced for sideways scalping)
    cooldown_seconds: int = 150  # 2.5 minutes between signals on same pair (was 5min)
    sideways_reentry_cooldown_seconds: int = 420  # 7 minutes after sideways close
    anti_flip_opposite_seconds: int = 600  # 10 minutes block for opposite-direction re-entry
    signal_confirmations_required: int = int(os.getenv("SCALPING_SIGNAL_CONFIRMATIONS_REQUIRED", "1"))  # temporary relax
    signal_confirmation_max_gap_seconds: int = 45  # invalidate stale confirmation chain
    
    # Volume and volatility filters
    min_volume_ratio: float = 2.0  # Volume must be >2x average
    min_atr_pct: float = float(os.getenv("SCALPING_MIN_ATR_PCT", "0.2"))  # relaxed from 0.3%
    max_atr_pct: float = 10.0  # Skip if ATR > 10% (too volatile)


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
    rsi_15m: float = 0.0
    
    # Trend context
    trend_15m: str = ""  # "LONG", "SHORT", "NEUTRAL"
    market_structure: str = ""  # "uptrend", "downtrend", "ranging"
    
    # Signal metadata
    reasons: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
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
    open_order_id: str = ""
    max_hold_until: float = field(init=False)  # opened_at + 1800 seconds
    
    # Status
    status: str = "open"  # "open", "closed_tp", "closed_sl", "closed_max_hold"
    breakeven_set: bool = False  # Track if trailing stop to breakeven activated
    is_sideways: bool = False  # Marker for sideways micro-scalp positions
    
    def __post_init__(self):
        """Calculate max hold until time"""
        self.max_hold_until = self.opened_at + 1800  # 30 minutes
    
    def time_remaining(self) -> int:
        """Calculate seconds remaining before max hold time"""
        return max(0, int(self.max_hold_until - time.time()))
    
    def is_expired(self) -> bool:
        """Check if position exceeded max hold time"""
        return time.time() >= self.max_hold_until
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            "user_id": self.user_id,
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "quantity": self.quantity,
            "leverage": self.leverage,
            "tp_price": self.tp_price,
            "sl_price": self.sl_price,
            "opened_at": self.opened_at,
            "max_hold_until": self.max_hold_until,
            "status": self.status,
        }


@dataclass
class MicroScalpSignal:
    """Signal data structure for sideways micro-scalping strategy"""

    # Identity
    symbol: str
    side: str                       # "LONG" or "SHORT"

    # Price levels
    entry_price: float
    tp_price: float
    sl_price: float
    rr_ratio: float

    # Range metadata
    range_support: float
    range_resistance: float
    range_width_pct: float

    # Analysis metadata
    confidence: int                 # 70-95
    bounce_confirmed: bool          # Always True when signal is generated
    rsi_divergence_detected: bool
    volume_ratio: float

    # Signal reasons
    reasons: List[str] = field(default_factory=list)

    # Markers
    is_sideways: bool = True
    max_hold_time: int = 120        # seconds


@dataclass
class SwingAdaptiveConfig:
    """Configuration surface for swing adaptive parity controls."""

    signal_confirmations_required: int = int(os.getenv("SWING_SIGNAL_CONFIRMATIONS_REQUIRED", "1"))
    signal_confirmation_max_gap_seconds: int = int(os.getenv("SWING_SIGNAL_CONFIRMATION_MAX_GAP_SECONDS", "45"))
    emergency_candidate_mode: bool = os.getenv("SWING_EMERGENCY_CANDIDATE_MODE", "true").lower() == "true"
    emergency_conf_relax: int = int(os.getenv("SWING_EMERGENCY_CONF_RELAX", "8"))
    emergency_min_confidence: int = int(os.getenv("SWING_EMERGENCY_MIN_CONFIDENCE", "50"))

    adaptive_timeout_protection_enabled: bool = os.getenv(
        "SWING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED",
        os.getenv("SWING_TIMEOUT_PROTECTION_ENABLED", "false"),
    ).lower() == "true"
    timeout_be_trigger_pct: float = float(os.getenv("SWING_TIMEOUT_BE_TRIGGER_PCT", "0.20"))
    timeout_trailing_trigger_pct: float = float(os.getenv("SWING_TIMEOUT_TRAILING_TRIGGER_PCT", "0.35"))
    timeout_late_tighten_multiplier: float = float(os.getenv("SWING_TIMEOUT_LATE_TIGHTEN_MULTIPLIER", "1.4"))
    timeout_protection_min_update_seconds: int = int(os.getenv("SWING_TIMEOUT_PROTECTION_MIN_UPDATE_SECONDS", "45"))
    timeout_near_flat_usdt_threshold: float = float(os.getenv("SWING_TIMEOUT_NEAR_FLAT_USDT_THRESHOLD", "0.02"))

    dynamic_max_hold_enabled: bool = os.getenv("SWING_DYNAMIC_MAX_HOLD_ENABLED", "false").lower() == "true"
    max_hold_default_seconds: int = int(os.getenv("SWING_MAX_HOLD_DEFAULT_SECONDS", "1800"))
