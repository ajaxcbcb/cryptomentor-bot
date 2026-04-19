from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Candle(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class Position(BaseModel):
    symbol: str
    side: Literal["LONG", "SHORT"]
    entry_price: float
    size: float
    leverage: int
    unrealized_pnl: float = 0.0
    opened_at: datetime


class OrderRequest(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT"] = "MARKET"
    size: float
    leverage: int
    reduce_only: bool = False
    take_profit: float | None = None
    stop_loss: float | None = None


class OrderResult(BaseModel):
    success: bool
    order_id: str | None = None
    symbol: str
    status: str
    message: str = ""
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class AccountInfo(BaseModel):
    equity: float
    available_balance: float
    used_margin: float
    unrealized_pnl: float


class MarketStateResult(BaseModel):
    state: Literal["TRENDING", "SIDEWAYS", "LOW_VOLATILITY", "UNCLEAR"]
    reasons: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)


class LiquiditySweepResult(BaseModel):
    has_sweep: bool
    sweep_side: Literal["BUY_SIDE", "SELL_SIDE", "NONE"] = "NONE"
    strength: float = 0.0
    level: float | None = None
    reasons: list[str] = Field(default_factory=list)


class BOSResult(BaseModel):
    confirmed: bool
    direction: Literal["LONG", "SHORT", "NONE"] = "NONE"
    displacement: float = 0.0
    level_broken: float | None = None
    reasons: list[str] = Field(default_factory=list)


class EntryZone(BaseModel):
    zone_type: Literal["OB", "FVG", "NONE"] = "NONE"
    low: float | None = None
    high: float | None = None


class EntryZoneResult(BaseModel):
    exists: bool
    preferred_zone: EntryZone = Field(default_factory=EntryZone)
    tapped: bool = False
    near_tap: bool = False
    distance_pct: float | None = None
    reasons: list[str] = Field(default_factory=list)


class ConfidenceResult(BaseModel):
    score: float
    components: dict[str, float] = Field(default_factory=dict)


class EarlyExitResult(BaseModel):
    should_exit: bool
    reason: str = ""
    metrics: dict[str, float] = Field(default_factory=dict)


class TradeContext(BaseModel):
    symbol: str
    market_state: MarketStateResult
    liquidity_sweep: LiquiditySweepResult
    bos: BOSResult
    entry_zone: EntryZoneResult
    confidence: ConfidenceResult
    higher_timeframe_bias: Literal["LONG", "SHORT", "NEUTRAL"] = "NEUTRAL"
    rsi_divergence: Literal["BULLISH", "BEARISH", "NONE"] = "NONE"
    current_price: float
    missing_conditions: list[str] = Field(default_factory=list)
    debug: dict[str, Any] = Field(default_factory=dict)


class TradeDecision(BaseModel):
    action: Literal["TRADE", "SKIP"]
    direction: Literal["LONG", "SHORT", "NONE"] = "NONE"
    confidence: float
    reason: str
    invalidation_level: float | None = None
    proposed_entry_zone: EntryZone | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
