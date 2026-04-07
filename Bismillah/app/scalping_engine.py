"""
Scalping Engine
High-frequency trading engine for 5-minute scalping with 30-minute max hold time
"""

import asyncio
import logging
import time
from typing import Optional, Dict
from datetime import datetime

from app.trading_mode import ScalpingConfig, ScalpingSignal, ScalpingPosition
from app.supabase_repo import _client

logger = logging.getLogger(__name__)


class ScalpingEngine:
    """
    High-frequency trading engine for 5-minute scalping
    
    Features:
    - 5M timeframe with 15M trend validation
    - Single TP at 1.5R
    - 30-minute max hold time
    - 5-minute cooldown between signals
    - 80% minimum confidence
    """
    
    def __init__(self, user_id: int, client, bot, notify_chat_id: int, config: Optional[ScalpingConfig] = None):
        """
        Initialize scalping engine
        
        Args:
            user_id: Telegram user ID
            client: Exchange client instance
            bot: Telegram bot instance
            notify_chat_id: Chat ID for notifications
            config: ScalpingConfig (optional, uses defaults if None)
        """
        self.user_id = user_id
        self.client = client
        self.bot = bot
        self.notify_chat_id = notify_chat_id
        self.config = config or ScalpingConfig()
        
        # Position tracking
        self.positions: Dict[str, ScalpingPosition] = {}
        
        # Cooldown tracking
        self.cooldown_tracker: Dict[str, float] = {}
        
        # Sideways error counter per symbol
        self.sideways_error_counter: Dict[str, int] = {}
        
        # Running state
        self.running = False
        
        logger.info(f"[Scalping:{user_id}] Engine initialized with config: {self.config}")
    
    async def run(self):
        """Main trading loop - scans every 15 seconds"""
        self.running = True
        logger.info(f"[Scalping:{self.user_id}] Engine started")
        
        # Send startup notification
        try:
            await self.bot.send_message(
                chat_id=self.notify_chat_id,
                text=(
                    "🤖 <b>Scalping Engine Active!</b>\n\n"
                    "⚡ <b>Mode: Scalping (5M)</b>\n\n"
                    "📊 Configuration:\n"
                    f"• Timeframe: {self.config.timeframe}\n"
                    f"• Scan interval: {self.config.scan_interval}s\n"
                    f"• Min confidence: {self.config.min_confidence * 100:.0f}%\n"
                    f"• Min R:R: 1:{self.config.min_rr}\n"
                    f"• Max hold time: {self.config.max_hold_time // 60} minutes\n"
                    f"• Max concurrent: {self.config.max_concurrent_positions} positions\n"
                    f"• Trading pairs: {len(self.config.pairs)} pairs\n\n"
                    "Bot will scan for high-probability setups every 15 seconds.\n"
                    "Patience = profit. 🎯"
                ),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.warning(f"[Scalping:{self.user_id}] Startup notification failed: {e}")
        
        scan_count = 0
        try:
            while self.running:
                try:
                    scan_count += 1
                    logger.info(f"[Scalping:{self.user_id}] Scan cycle #{scan_count} starting...")
                    
                    # Monitor existing positions first (priority)
                    logger.info(f"[Scalping:{self.user_id}] Monitoring positions...")
                    await self.monitor_positions()
                    
                    # Scan for new signals
                    logger.info(f"[Scalping:{self.user_id}] Scanning {len(self.config.pairs)} pairs for signals...")
                    signals_found = 0
                    signals_validated = 0
                    
                    for symbol in self.config.pairs:
                        if not self.running:
                            break
                        
                        try:
                            # Check cooldown
                            if self.check_cooldown(symbol):
                                logger.debug(f"[Scalping:{self.user_id}] {symbol} in cooldown, skipping")
                                continue
                            
                            # Generate signal
                            signal = await self.generate_scalping_signal(symbol)
                            
                            if signal is None:
                                logger.debug(f"[Scalping:{self.user_id}] {symbol} - No signal generated")
                                continue
                            
                            signals_found += 1
                            logger.info(f"[Scalping:{self.user_id}] {symbol} - Signal found! Validating...")
                            
                            # Validate signal
                            if not self.validate_scalping_entry(signal):
                                logger.info(f"[Scalping:{self.user_id}] {symbol} - Signal validation failed")
                                continue
                            
                            signals_validated += 1
                            logger.info(f"[Scalping:{self.user_id}] {symbol} - Signal validated! Placing order...")
                            
                            # Place order
                            success = await self.place_scalping_order(signal)
                            
                            if success:
                                self.mark_cooldown(symbol)
                                logger.info(f"[Scalping:{self.user_id}] {symbol} - Order placed successfully!")
                            else:
                                logger.warning(f"[Scalping:{self.user_id}] {symbol} - Order placement failed")
                        
                        except Exception as e:
                            logger.error(f"[Scalping:{self.user_id}] Error scanning {symbol}: {e}")
                            import traceback
                            traceback.print_exc()
                            continue
                    
                    logger.info(
                        f"[Scalping:{self.user_id}] Scan #{scan_count} complete: "
                        f"{signals_found} signals found, {signals_validated} validated"
                    )
                    
                    # Wait for next scan
                    logger.debug(f"[Scalping:{self.user_id}] Sleeping for {self.config.scan_interval}s...")
                    await asyncio.sleep(self.config.scan_interval)
                
                except Exception as e:
                    logger.error(f"[Scalping:{self.user_id}] Error in main loop: {e}")
                    import traceback
                    traceback.print_exc()
                    await asyncio.sleep(self.config.scan_interval)
        
        finally:
            self.running = False
            logger.info(f"[Scalping:{self.user_id}] Engine stopped after {scan_count} scan cycles")
    
    def stop(self):
        """Stop the trading loop"""
        self.running = False
        logger.info(f"[Scalping:{self.user_id}] Stop requested")

    
    async def generate_scalping_signal(self, symbol: str) -> Optional[ScalpingSignal]:
        """
        Generate 5M scalping signal with 15M trend validation (ASYNC with caching)
        
        Algorithm:
        1. Check trading mode — sideways pipeline only in SCALPING mode
        2. If SCALPING mode, try sideways signal first
        3. Fall through to trending signal (existing logic unchanged)
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            
        Returns:
            ScalpingSignal or MicroScalpSignal object, or None
        """
        try:
            # Check trading mode — sideways only for scalping mode
            from app.trading_mode_manager import TradingModeManager
            from app.trading_mode import TradingMode
            mode = TradingModeManager.get_mode(self.user_id)

            if mode == TradingMode.SCALPING:
                # Try sideways detection first
                sideways_signal = await self._try_sideways_signal(symbol)
                if sideways_signal is not None:
                    return sideways_signal

            # Fall through to trending signal (existing logic unchanged)
            from app.autosignal_async import compute_signal_scalping_async

            # Generate signal using async version with caching
            signal_dict = await compute_signal_scalping_async(symbol.replace("USDT", ""))
            
            if not signal_dict:
                return None
            
            # Convert dict to ScalpingSignal object
            signal = ScalpingSignal(
                symbol=signal_dict["symbol"],
                side=signal_dict["side"],
                confidence=signal_dict["confidence"],
                entry_price=signal_dict["entry_price"],
                tp_price=signal_dict["tp"],
                sl_price=signal_dict["sl"],
                rr_ratio=signal_dict["rr_ratio"],
                atr_pct=signal_dict["atr_pct"],
                volume_ratio=signal_dict["vol_ratio"],
                rsi_5m=signal_dict["rsi_5m"],
                trend_15m=signal_dict["trend_15m"],
                reasons=signal_dict["reasons"]
            )
            
            logger.info(
                f"[Scalping:{self.user_id}] Signal generated: {symbol} {signal.side} "
                f"@ {signal.entry_price:.4f} (confidence: {signal.confidence}%)"
            )
            
            return signal
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error generating signal for {symbol}: {e}")
            return None

    async def _try_sideways_signal(self, symbol: str):
        """
        Try to generate a sideways micro-scalp signal.
        Returns MicroScalpSignal if valid, None otherwise (fall through to trending).
        """
        try:
            from app.candle_cache import get_candles_cached
            from app.providers.alternative_klines_provider import alternative_klines_provider
            from app.sideways_detector import SidewaysDetector
            from app.range_analyzer import RangeAnalyzer
            from app.bounce_detector import BounceDetector
            from app.rsi_divergence_detector import RSIDivergenceDetector
            from app.trading_mode import MicroScalpSignal

            base_symbol = symbol.replace("USDT", "").upper()

            # Wrap sync get_klines in async with cache
            async def fetch_klines_async(sym, interval, limit):
                return await asyncio.to_thread(
                    alternative_klines_provider.get_klines,
                    sym, interval, limit
                )

            # Fetch klines (list format: [timestamp, open, high, low, close, volume, ...])
            raw_5m = await get_candles_cached(fetch_klines_async, base_symbol, "5m", 50)
            raw_15m = await get_candles_cached(fetch_klines_async, base_symbol, "15m", 60)

            if not raw_5m or not raw_15m:
                return None

            # Convert list format to dict format expected by detectors
            def to_dict_candles(raw):
                result = []
                for k in raw:
                    result.append({
                        'open':   float(k[1]),
                        'high':   float(k[2]),
                        'low':    float(k[3]),
                        'close':  float(k[4]),
                        'volume': float(k[5]),
                    })
                return result

            candles_5m = to_dict_candles(raw_5m)
            candles_15m = to_dict_candles(raw_15m)

            price = candles_5m[-1]['close']
            if price == 0:
                return None

            # Step 1: Detect sideways
            try:
                sideways_result = SidewaysDetector().detect(candles_5m, candles_15m, price)
            except Exception as e:
                self._increment_sideways_error(symbol)
                logger.error(f"[Scalping:{self.user_id}] SidewaysDetector error for {symbol}: {e}")
                return None

            if not sideways_result.is_sideways:
                return None  # Market is trending, use trending logic

            logger.info(f"[Scalping:{self.user_id}] {symbol} SIDEWAYS detected: {sideways_result.reason}")

            # Step 2: Identify range S/R
            try:
                range_result = RangeAnalyzer().analyze(candles_5m, price)
            except Exception as e:
                self._increment_sideways_error(symbol)
                logger.error(f"[Scalping:{self.user_id}] RangeAnalyzer error for {symbol}: {e}")
                return None

            if range_result is None:
                logger.debug(f"[Scalping:{self.user_id}] {symbol} No valid S/R range found")
                return None

            # Step 3: Detect bounce
            try:
                bounce_result = BounceDetector().detect(
                    last_candle=candles_5m[-1],
                    support=range_result.support,
                    resistance=range_result.resistance,
                    price=price,
                )
            except Exception as e:
                self._increment_sideways_error(symbol)
                logger.error(f"[Scalping:{self.user_id}] BounceDetector error for {symbol}: {e}")
                return None

            if bounce_result is None:
                logger.debug(f"[Scalping:{self.user_id}] {symbol} No bounce confirmed")
                return None

            direction = bounce_result.direction  # "LONG" or "SHORT"

            # Step 4: RSI divergence (optional bonus, don't fail if error)
            divergence_bonus = 0
            rsi_divergence_detected = False
            divergence_reason = ""
            try:
                div_result = RSIDivergenceDetector().detect(candles_5m, direction)
                divergence_bonus = div_result.confidence_bonus
                rsi_divergence_detected = div_result.detected
                divergence_reason = div_result.reason
            except Exception as e:
                logger.warning(f"[Scalping:{self.user_id}] RSIDivergenceDetector error (continuing): {e}")

            # Step 5: Calculate confidence
            base_confidence = 70

            # Volume bonus: current volume > 1.5x average of last 20 candles
            volume_bonus = 0
            volume_ratio = 0
            try:
                volumes = [float(c.get('volume', 0)) for c in candles_5m[-21:-1]]
                avg_volume = sum(volumes) / len(volumes) if volumes else 0
                current_volume = float(candles_5m[-1].get('volume', 0))
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
                if volume_ratio > 1.5:
                    volume_bonus = 5
            except Exception:
                volume_ratio = 0

            # Range width bonus: 1.0% - 2.0% is ideal
            range_bonus = 5 if 1.0 <= range_result.range_width_pct <= 2.0 else 0

            confidence = min(95, base_confidence + divergence_bonus + volume_bonus + range_bonus)

            # Relaxed confidence threshold for sideways (70% vs 75%)
            if confidence < 70:
                logger.debug(f"[Scalping:{self.user_id}] {symbol} Sideways confidence too low: {confidence}")
                return None

            # Step 6: Calculate TP/SL
            entry = price
            if direction == "LONG":
                tp = entry + 0.70 * (range_result.resistance - entry)
                sl = range_result.support * (1 - 0.0015)
            else:  # SHORT
                tp = entry - 0.70 * (entry - range_result.support)
                sl = range_result.resistance * (1 + 0.0015)

            # Step 7: Validate R:R
            if direction == "LONG":
                rr = (tp - entry) / (entry - sl) if (entry - sl) > 0 else 0
            else:
                rr = (entry - tp) / (sl - entry) if (sl - entry) > 0 else 0

            if rr < 1.0:
                logger.debug(f"[Scalping:{self.user_id}] {symbol} Sideways R:R too low: {rr:.2f}")
                return None

            # Build reasons
            reasons = [
                f"Sideways market: {sideways_result.reason}",
                f"Range: {range_result.support:.4f} - {range_result.resistance:.4f} ({range_result.range_width_pct:.2f}%)",
                bounce_result.reason,
            ]
            if divergence_reason:
                reasons.append(divergence_reason)

            # Reset error counter on success
            self.sideways_error_counter[symbol] = 0

            return MicroScalpSignal(
                symbol=symbol,
                side=direction,
                entry_price=entry,
                tp_price=round(tp, 6),
                sl_price=round(sl, 6),
                rr_ratio=round(rr, 2),
                range_support=range_result.support,
                range_resistance=range_result.resistance,
                range_width_pct=range_result.range_width_pct,
                confidence=confidence,
                bounce_confirmed=True,
                rsi_divergence_detected=rsi_divergence_detected,
                volume_ratio=volume_ratio,
                reasons=reasons,
            )

        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] _try_sideways_signal error for {symbol}: {e}")
            return None

    def _increment_sideways_error(self, symbol: str):
        """Increment error counter and apply cooldown if threshold reached."""
        self.sideways_error_counter[symbol] = self.sideways_error_counter.get(symbol, 0) + 1
        if self.sideways_error_counter[symbol] >= 3:
            self.cooldown_tracker[symbol] = time.time() + 300  # 5 min cooldown
            self.sideways_error_counter[symbol] = 0
            logger.warning(
                f"[Scalping:{self.user_id}] {symbol} sideways error threshold reached, cooldown 5min"
            )

    def calculate_position_size_pro(self, entry_price: float, sl_price: float, 
                                    capital: float, leverage: int) -> tuple:
        """
        Calculate position size based on risk % per trade (PRO TRADER METHOD)
        
        SCALPING MODE: MAXIMUM 5% RISK PER TRADE (SAFETY FIRST!)
        
        Args:
            entry_price: Entry price
            sl_price: Stop loss price
            capital: Total trading capital
            leverage: Leverage multiplier (will be capped at 10x for scalping)
            
        Returns:
            (position_size, used_risk_sizing): tuple of (quantity, whether risk sizing was used)
        """
        try:
            # CRITICAL: Cap leverage at 10x for scalping (safety)
            leverage = min(leverage, 10)
            
            # Get risk percentage from database
            from app.supabase_repo import get_risk_per_trade
            risk_pct = get_risk_per_trade(self.user_id)
            
            # CRITICAL: Cap risk at 5% maximum for scalping
            risk_pct = min(risk_pct, 5.0)
            
            # Get current balance from exchange
            bal_result = self.client.get_balance()
            if not bal_result.get('success'):
                raise Exception(f"Balance fetch failed: {bal_result.get('error')}")
            
            balance = bal_result.get('balance', 0)
            if balance <= 0:
                raise Exception(f"Invalid balance: {balance}")
            
            # Calculate position size using risk-based formula
            from app.position_sizing import calculate_position_size
            sizing = calculate_position_size(
                balance=balance,
                risk_pct=risk_pct,
                entry_price=entry_price,
                sl_price=sl_price,
                leverage=leverage,
                symbol=f"BTCUSDT"  # Default symbol for precision
            )
            
            if not sizing['valid']:
                raise Exception(f"Position sizing invalid: {sizing['error']}")
            
            qty = sizing['qty']
            
            # SAFETY CHECK: Ensure position size is reasonable
            position_value = qty * entry_price
            max_position_value = balance * 0.5  # Max 50% of balance per trade
            
            if position_value > max_position_value:
                logger.warning(
                    f"[Scalping:{self.user_id}] Position too large! "
                    f"${position_value:.2f} > ${max_position_value:.2f} (50% of balance). "
                    f"Reducing to safe size."
                )
                qty = (max_position_value / entry_price) * 0.9  # 90% of max for safety margin
            
            logger.info(
                f"[Scalping:{self.user_id}] RISK-BASED sizing: "
                f"Balance=${balance:.2f}, Risk={risk_pct}% (capped at 5%), "
                f"Leverage={leverage}x (capped at 10x), "
                f"Entry=${entry_price:.2f}, SL=${sl_price:.2f}, "
                f"SL_Dist={sizing['sl_distance_pct']:.2f}%, "
                f"Position=${sizing['position_size_usdt']:.2f}, "
                f"Margin=${sizing['margin_required']:.2f}, "
                f"Qty={qty}, Risk_Amt=${sizing['risk_amount']:.2f}"
            )
            
            return qty, True  # Success - used risk-based sizing
            
        except Exception as e:
            logger.warning(
                f"[Scalping:{self.user_id}] Risk sizing FAILED: {e} - "
                f"Falling back to ULTRA-SAFE 2% method"
            )
            
            # FALLBACK: Use ULTRA-SAFE 2% risk method
            risk_per_trade_pct = 0.02  # 2% ONLY
            risk_amount = capital * risk_per_trade_pct
            
            # Calculate SL distance in %
            sl_distance_pct = abs(entry_price - sl_price) / entry_price
            
            # Position size = Risk Amount / SL Distance
            position_size_usdt = risk_amount / sl_distance_pct
            
            # SAFETY: Cap at 20% of capital
            max_position_usdt = capital * 0.2
            if position_size_usdt > max_position_usdt:
                logger.warning(
                    f"[Scalping:{self.user_id}] Fallback position too large! "
                    f"${position_size_usdt:.2f} > ${max_position_usdt:.2f}. Capping."
                )
                position_size_usdt = max_position_usdt
            
            # Convert to base currency
            position_size = position_size_usdt / entry_price
            
            logger.info(
                f"[Scalping:{self.user_id}] FALLBACK sizing: "
                f"Capital=${capital:.2f}, Risk=${risk_amount:.2f} (2%), "
                f"SL Distance={sl_distance_pct:.2%}, "
                f"Position=${position_size_usdt:.2f} (capped at 20%), "
                f"Quantity={position_size:.6f}"
            )
            
            return position_size, False  # Fallback used
    
    def is_optimal_trading_time(self) -> tuple:
        """
        Check if current time is optimal for scalping
        
        Crypto has high/low volatility hours:
        - Best: 12:00-20:00 UTC (EU + US overlap) - High volume, clear trends
        - Good: 08:00-12:00 UTC (EU open) - Good volume
        - Avoid: 00:00-06:00 UTC (Asian session) - Low volume, whipsaw
        
        Returns:
            (should_trade: bool, position_size_multiplier: float)
        """
        hour_utc = datetime.utcnow().hour
        
        # Best hours: 12:00-20:00 UTC (EU + US overlap)
        if 12 <= hour_utc < 20:
            return True, 1.0  # Full position size
        
        # Good hours: 08:00-12:00 UTC (EU open)
        elif 8 <= hour_utc < 12:
            return True, 0.7  # 70% position size
        
        # Avoid: 00:00-06:00 UTC (Asian session)
        elif 0 <= hour_utc < 6:
            logger.info(f"[Scalping:{self.user_id}] Skipping trade - Asian session (low volume)")
            return False, 0.0  # Skip trading
        
        # Neutral: Other hours
        else:
            return True, 0.5  # 50% position size
    
    def calculate_scalping_tp_sl(self, entry: float, direction: str, atr: float) -> tuple:
        """
        Calculate single TP at 1.5R and SL using ATR with slippage buffer
        
        Formula:
        - SL distance = 1.5 * ATR (5M)
        - TP distance = 1.5 * SL distance (R:R 1:1.5)
        - Slippage buffer = 0.05% (0.03% slippage + 0.02% spread)
        
        Args:
            entry: Entry price
            direction: "LONG" or "SHORT"
            atr: ATR value (5M timeframe)
            
        Returns:
            Tuple of (tp_price, sl_price)
        """
        sl_distance = atr * self.config.atr_sl_multiplier  # 1.5 * ATR
        tp_distance = sl_distance * self.config.single_tp_multiplier  # 1.5 * SL
        
        # Slippage & spread buffer for realistic fills
        slippage_pct = 0.0003  # 0.03% average slippage
        spread_pct = 0.0002    # 0.02% spread
        buffer_pct = slippage_pct + spread_pct  # 0.05% total
        
        if direction == "LONG":
            # SL: Trigger earlier to avoid worse fill
            sl = entry - sl_distance
            sl_adjusted = sl * (1 + buffer_pct)  # Trigger 0.05% earlier
            
            # TP: Need to go further to account for slippage
            tp = entry + tp_distance
            tp_adjusted = tp * (1 + buffer_pct)  # Go 0.05% further
        else:  # SHORT
            # SL: Trigger earlier
            sl = entry + sl_distance
            sl_adjusted = sl * (1 - buffer_pct)
            
            # TP: Go further
            tp = entry - tp_distance
            tp_adjusted = tp * (1 - buffer_pct)
        
        # Round to 8 decimals (exchange precision)
        tp_final = round(tp_adjusted, 8)
        sl_final = round(sl_adjusted, 8)
        
        logger.debug(
            f"[Scalping:{self.user_id}] TP/SL calculated: "
            f"Entry={entry:.4f}, TP={tp_final:.4f}, SL={sl_final:.4f} "
            f"(buffer={buffer_pct:.2%})"
        )
        
        return (tp_final, sl_final)
    
    def validate_scalping_entry(self, signal) -> bool:
        """
        Validate signal meets all scalping requirements.
        MicroScalpSignal (sideways) bypasses ATR checks — already validated in pipeline.
        """
        from app.trading_mode import MicroScalpSignal as _MicroScalpSignal
        is_sideways = isinstance(signal, _MicroScalpSignal)

        # Check confidence
        if signal.confidence < self.config.min_confidence * 100:
            logger.debug(
                f"[Scalping:{self.user_id}] Signal rejected: "
                f"Confidence {signal.confidence}% < {self.config.min_confidence * 100}%"
            )
            return False
        
        # Check R:R
        if signal.rr_ratio < self.config.min_rr:
            logger.debug(
                f"[Scalping:{self.user_id}] Signal rejected: "
                f"R:R {signal.rr_ratio} < {self.config.min_rr}"
            )
            return False
        
        # Check symbol in allowed list
        if signal.symbol not in [f"{p}" for p in self.config.pairs]:
            logger.debug(f"[Scalping:{self.user_id}] Signal rejected: Symbol {signal.symbol} not allowed")
            return False
        
        # Check no existing position
        if signal.symbol in self.positions:
            logger.debug(f"[Scalping:{self.user_id}] Signal rejected: Position already open on {signal.symbol}")
            return False
        
        # Check max concurrent positions
        if len(self.positions) >= self.config.max_concurrent_positions:
            logger.debug(
                f"[Scalping:{self.user_id}] Signal rejected: "
                f"Max positions reached ({self.config.max_concurrent_positions})"
            )
            return False
        
        # ATR checks — skip for sideways signals (no atr_pct field)
        if not is_sideways:
            if signal.atr_pct < self.config.min_atr_pct:
                logger.debug(
                    f"[Scalping:{self.user_id}] Signal rejected: "
                    f"ATR {signal.atr_pct:.2f}% too low (market flat)"
                )
                return False
            
            if signal.atr_pct > self.config.max_atr_pct:
                logger.debug(
                    f"[Scalping:{self.user_id}] Signal rejected: "
                    f"ATR {signal.atr_pct:.2f}% too high (too volatile)"
                )
                return False
        
        # Check circuit breaker
        if self._circuit_breaker_triggered():
            logger.warning(f"[Scalping:{self.user_id}] Signal rejected: Circuit breaker triggered")
            return False
        
        return True
    
    def _circuit_breaker_triggered(self) -> bool:
        """Check if daily loss limit reached"""
        try:
            s = _client()
            # Get today's PnL
            res = s.table("autotrade_trades").select("pnl_usdt").eq(
                "telegram_id", self.user_id
            ).gte(
                "opened_at", datetime.utcnow().date().isoformat()
            ).execute()
            
            if not res.data:
                return False
            
            total_pnl = sum(float(t.get("pnl_usdt", 0)) for t in res.data)
            
            # Get account balance
            session_res = s.table("autotrade_sessions").select("initial_deposit").eq(
                "telegram_id", self.user_id
            ).limit(1).execute()
            
            if not session_res.data:
                return False
            
            balance = float(session_res.data[0].get("initial_deposit", 100))
            loss_pct = abs(total_pnl / balance) if balance > 0 else 0
            
            if loss_pct >= self.config.daily_loss_limit:
                logger.warning(
                    f"[Scalping:{self.user_id}] Circuit breaker: "
                    f"Daily loss {loss_pct:.2%} >= {self.config.daily_loss_limit:.2%}"
                )
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error checking circuit breaker: {e}")
            return False  # Don't block on error

    
    async def place_scalping_order(self, signal: ScalpingSignal) -> bool:
        """
        Place scalping order with PROPER position sizing and time-of-day filter
        
        Args:
            signal: ScalpingSignal to execute
            
        Returns:
            True if order placed successfully
        """
        # Check optimal trading time
        should_trade, size_multiplier = self.is_optimal_trading_time()
        
        if not should_trade:
            logger.info(
                f"[Scalping:{self.user_id}] Skipping {signal.symbol} - "
                f"Non-optimal trading hours"
            )
            return False
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Get account info
                session = _client().table("autotrade_sessions").select(
                    "initial_deposit", "leverage"
                ).eq("telegram_id", self.user_id).limit(1).execute()
                
                if not session.data:
                    logger.error(f"[Scalping:{self.user_id}] No session found")
                    return False
                
                capital = float(session.data[0].get("initial_deposit", 100))
                leverage = int(session.data[0].get("leverage", 10))
                
                # CRITICAL: Calculate position size based on risk (Phase 2)
                quantity, used_risk_sizing = self.calculate_position_size_pro(
                    entry_price=signal.entry_price,
                    sl_price=signal.sl_price,
                    capital=capital,
                    leverage=leverage
                )
                
                if used_risk_sizing:
                    logger.info(f"[Scalping:{self.user_id}] Using RISK-BASED position sizing for {signal.symbol}")
                else:
                    logger.info(f"[Scalping:{self.user_id}] Using FIXED 2% position sizing for {signal.symbol} (fallback)")
                
                # Apply time-of-day multiplier
                quantity_adjusted = quantity * size_multiplier
                
                if size_multiplier < 1.0:
                    logger.info(
                        f"[Scalping:{self.user_id}] Time-of-day adjustment: "
                        f"{size_multiplier:.0%} position size (hour={datetime.utcnow().hour} UTC)"
                    )
                
                # ── Minimum qty validation (NO AUTO-LEVERAGE for risk management) ──
                # Minimum qty per pair (Bitunix standard minimums)
                MIN_QTY_MAP = {
                    "BTCUSDT": 0.001, "ETHUSDT": 0.01, "SOLUSDT": 0.1,
                    "BNBUSDT": 0.01,  "XRPUSDT": 1.0,  "DOGEUSDT": 10.0,
                    "ADAUSDT": 1.0,   "AVAXUSDT": 0.1, "DOTUSDT": 0.1,
                    "MATICUSDT": 1.0, "LINKUSDT": 0.1, "UNIUSDT": 0.1,
                    "ATOMUSDT": 0.1,
                }
                min_qty = MIN_QTY_MAP.get(signal.symbol, 0.001)
                effective_leverage = leverage
                
                # CRITICAL: Skip trade if qty too small - NEVER auto-raise leverage
                # Auto-raising leverage breaks risk management (user set leverage for specific risk %)
                if quantity_adjusted < min_qty:
                    logger.warning(
                        f"[Scalping:{self.user_id}] {signal.symbol} qty={quantity_adjusted:.6f} "
                        f"< min={min_qty}. Skipping trade to preserve risk management."
                    )
                    await self._notify_user(
                        f"⚠️ <b>Trade Skipped: {signal.symbol}</b>\n\n"
                        f"Quantity too small: {quantity_adjusted:.6f} < {min_qty}\n\n"
                        f"<b>To fix:</b>\n"
                        f"• Increase balance, OR\n"
                        f"• Increase risk % in settings\n\n"
                        f"Risk management preserved ✅"
                    )
                    return False
                
                # ═══════════════════════════════════════════════════════════
                # Unified entry path — see app/trade_execution.py
                # Atomic order with TP1 + SL on exchange + StackMentor register
                # ═══════════════════════════════════════════════════════════
                from app.trade_execution import open_managed_position

                exec_result = await open_managed_position(
                    client=self.client,
                    user_id=self.user_id,
                    symbol=signal.symbol,
                    side=signal.side,                # "LONG" / "SHORT"
                    entry_price=signal.entry_price,
                    sl_price=signal.sl_price,
                    quantity=quantity_adjusted,
                    leverage=effective_leverage,
                )

                if exec_result.success:
                    levels = exec_result.levels
                    side_str = "BUY" if signal.side == "LONG" else "SELL"

                    # Register position for local tracking
                    position = ScalpingPosition(
                        user_id=self.user_id,
                        symbol=signal.symbol,
                        side=side_str,
                        entry_price=signal.entry_price,
                        quantity=quantity_adjusted,
                        leverage=effective_leverage,
                        tp_price=levels.tp1,
                        sl_price=levels.sl,
                        opened_at=time.time(),
                        breakeven_set=False,
                    )
                    self.positions[signal.symbol] = position

                    # Mark as sideways position if signal is MicroScalpSignal
                    from app.trading_mode import MicroScalpSignal as _MicroScalpSignal
                    if isinstance(signal, _MicroScalpSignal):
                        position.is_sideways = True

                    # Save to database + notify user
                    await self._save_position_to_db(position, signal)
                    await self._notify_stackmentor_opened(position, signal, levels)

                    logger.info(
                        f"[Scalping:{self.user_id}] StackMentor position opened: "
                        f"{signal.symbol} {side_str} @ {signal.entry_price:.4f}, "
                        f"Qty: {quantity_adjusted:.6f}, "
                        f"TP1={levels.tp1:.4f} TP2={levels.tp2:.4f} TP3={levels.tp3:.4f}"
                    )
                    return True
                else:
                    error_msg = exec_result.error or "Unknown error"
                    error_code = exec_result.error_code or ""
                    logger.warning(
                        f"[Scalping:{self.user_id}] Order failed (attempt {attempt+1}) "
                        f"[{error_code}]: {error_msg}"
                    )

                    # Non-retryable conditions
                    if error_code == "insufficient_balance":
                        await self._notify_user("❌ Order failed: Insufficient balance")
                        return False
                    if error_code == "invalid_prices":
                        await self._notify_user(
                            f"⚠️ <b>Trade skipped: {signal.symbol}</b>\n\n"
                            f"Market moved before entry: {error_msg}"
                        )
                        return False
                    if error_code in ("auth", "ip_blocked"):
                        await self._notify_user(
                            f"⚠️ Exchange auth/IP error: {error_msg}\n"
                            f"Engine continues; check API key & proxy."
                        )
                        return False
                    if error_code == "reconcile_failed":
                        await self._notify_user(
                            f"🚨 <b>Position auto-closed: {signal.symbol}</b>\n\n"
                            f"Self-healing check found the live position did not match "
                            f"expected qty/TP/SL and could not be repaired. Position was "
                            f"closed to protect your capital.\n\n"
                            f"<code>{error_msg}</code>"
                        )
                        return False
                    if 'invalid symbol' in error_msg.lower():
                        await self._notify_user(f"❌ Order failed: Invalid symbol {signal.symbol}")
                        return False

                    # Retryable error — backoff
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
            
            except asyncio.TimeoutError:
                logger.warning(f"[Scalping:{self.user_id}] Order timeout (attempt {attempt+1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
            
            except Exception as e:
                logger.error(f"[Scalping:{self.user_id}] Order exception (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
        
        # All retries failed — set cooldown to prevent spam
        self.mark_cooldown(signal.symbol)
        await self._notify_user(
            f"❌ Failed to place order for {signal.symbol} after {max_retries} attempts.\n"
            f"Signal skipped. Engine continues monitoring."
        )
        return False
    
    async def monitor_positions(self):
        """
        Monitor open positions using StackMentor system
        StackMentor handles 3-tier TP and auto-breakeven automatically
        """
        if not self.positions:
            return
        
        # Use StackMentor monitoring for all positions
        from app.stackmentor import monitor_stackmentor_positions

        try:
            # monitor_stackmentor_positions is async (bot, user_id, client, chat_id)
            await monitor_stackmentor_positions(
                self.bot,
                self.user_id,
                self.client,
                self.notify_chat_id,
            )
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error in StackMentor monitoring: {e}")
        
        # Check for positions that need to be removed from local tracking
        for symbol in list(self.positions.keys()):
            position = self.positions[symbol]
            
            try:
                # Check sideways max hold (2 minutes) - local check only
                if getattr(position, 'is_sideways', False):
                    elapsed = time.time() - position.opened_at
                    if elapsed > 120:  # 2 minutes
                        await self._close_sideways_max_hold(position)
                        continue
                
                # Check max hold time (30 minutes) - local check only
                if position.is_expired():
                    await self._close_position_max_hold(position)
                    continue
            
            except Exception as e:
                logger.error(f"[Scalping:{self.user_id}] Error checking {symbol}: {e}")
                continue
    
    async def _move_sl_to_breakeven(self, position: ScalpingPosition, current_price: float):
        """Move stop loss to breakeven (entry price) to protect profits"""
        try:
            # Update position SL to entry price
            old_sl = position.sl_price
            position.sl_price = position.entry_price
            
            # Notify user
            await self._notify_user(
                f"🔒 <b>Breakeven Protection Activated</b>\n\n"
                f"Symbol: {position.symbol}\n"
                f"Entry: {position.entry_price:.4f}\n"
                f"Old SL: {old_sl:.4f}\n"
                f"New SL: {position.sl_price:.4f} (Breakeven)\n\n"
                f"Position is now risk-free! 🎉"
            )
            
            logger.info(
                f"[Scalping:{self.user_id}] SL moved to breakeven: "
                f"{position.symbol} @ {position.entry_price:.4f}"
            )
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error moving SL to breakeven: {e}")
    
    async def _close_position_max_hold(self, position: ScalpingPosition):
        """Force close position at market price after 30 minutes (for StackMentor positions)"""
        try:
            logger.info(
                f"[Scalping:{self.user_id}] Max hold time exceeded for {position.symbol} "
                f"(elapsed: {int(time.time() - position.opened_at)}s)"
            )
            
            # Close entire position at market
            close_side = "SELL" if position.side == "BUY" else "BUY"
            
            result = await asyncio.to_thread(
                self.client.place_order,
                symbol=position.symbol,
                side=close_side,
                qty=position.quantity,
                order_type='market',
                reduce_only=True
            )
            
            if result.get('success'):
                fill_price = float(result.get('fill_price', position.entry_price))
                
                # Calculate PnL
                if position.side == "BUY":
                    pnl = (fill_price - position.entry_price) * position.quantity
                else:
                    pnl = (position.entry_price - fill_price) * position.quantity
                
                pnl_with_leverage = pnl * position.leverage
                
                # Update database
                await self._update_position_closed(
                    position, fill_price, pnl_with_leverage, "max_hold_time_exceeded"
                )
                
                # Update StackMentor tracking
                try:
                    from app.stackmentor import remove_stackmentor_position
                    remove_stackmentor_position(self.user_id, position.symbol)
                except Exception as sm_err:
                    logger.warning(f"[Scalping:{self.user_id}] Failed to update StackMentor: {sm_err}")
                
                # Notify user
                await self._notify_user(
                    f"⏰ <b>Position Closed (Max Hold Time)</b>\n\n"
                    f"Symbol: {position.symbol}\n"
                    f"Entry: {position.entry_price:.4f}\n"
                    f"Exit: {fill_price:.4f}\n"
                    f"Hold Time: 30 minutes\n"
                    f"PnL: <b>{pnl_with_leverage:+.2f} USDT</b>"
                )
                
                # Remove from tracking
                del self.positions[position.symbol]
            else:
                logger.error(
                    f"[Scalping:{self.user_id}] Failed to close position: {result.get('error')}"
                )
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error closing max hold position: {e}")
    
    async def _close_sideways_max_hold(self, position: ScalpingPosition):
        """Force close sideways position after 2 minutes max hold"""
        try:
            elapsed = int(time.time() - position.opened_at)
            logger.info(
                f"[Scalping:{self.user_id}] Sideways max hold exceeded for {position.symbol} "
                f"(elapsed: {elapsed}s)"
            )
            
            close_side = "SELL" if position.side == "BUY" else "BUY"
            
            result = await asyncio.to_thread(
                self.client.place_order,
                symbol=position.symbol,
                side=close_side,
                qty=position.quantity,
                order_type='market',
                reduce_only=True
            )
            
            if result.get('success'):
                fill_price = float(result.get('fill_price', position.entry_price))
                
                if position.side == "BUY":
                    pnl = (fill_price - position.entry_price) * position.quantity
                else:
                    pnl = (position.entry_price - fill_price) * position.quantity
                
                pnl_with_leverage = pnl * position.leverage
                
                await self._update_position_closed(
                    position, fill_price, pnl_with_leverage, "sideways_max_hold_exceeded"
                )
                
                await self._notify_user(
                    f"⏰ <b>SIDEWAYS Closed (2min)</b>\n\n"
                    f"Symbol: {position.symbol}\n"
                    f"Entry: {position.entry_price:.4f}\n"
                    f"Exit: {fill_price:.4f}\n"
                    f"Hold Time: {elapsed}s\n"
                    f"PnL: <b>{pnl_with_leverage:+.2f} USDT</b>"
                )
                
                del self.positions[position.symbol]
            else:
                logger.error(
                    f"[Scalping:{self.user_id}] Failed to close sideways position: {result.get('error')}"
                )
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error closing sideways max hold: {e}")
    
    async def _close_position_tp(self, position: ScalpingPosition, fill_price: float):
        """Close position when TP hit"""
        try:
            close_side = "SELL" if position.side == "BUY" else "BUY"
            
            result = await asyncio.to_thread(
                self.client.place_order,
                symbol=position.symbol,
                side=close_side,
                qty=position.quantity,
                order_type='market',
                reduce_only=True
            )
            
            if result.get('success'):
                # Calculate PnL
                if position.side == "BUY":
                    pnl = (fill_price - position.entry_price) * position.quantity
                else:
                    pnl = (position.entry_price - fill_price) * position.quantity
                
                pnl_with_leverage = pnl * position.leverage
                
                await self._update_position_closed(position, fill_price, pnl_with_leverage, "closed_tp")
                
                if position.is_sideways:
                    await self._notify_sideways_closed(position, fill_price, pnl_with_leverage, "closed_tp")
                else:
                    await self._notify_user(
                        f"✅ <b>TP Hit!</b>\n\n"
                        f"Symbol: {position.symbol}\n"
                        f"Entry: {position.entry_price:.4f}\n"
                        f"Exit: {fill_price:.4f}\n"
                        f"PnL: <b>{pnl_with_leverage:+.2f} USDT</b> 🎉"
                    )
                
                del self.positions[position.symbol]
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error closing TP position: {e}")
    
    async def _close_position_sl(self, position: ScalpingPosition, fill_price: float):
        """Close position when SL hit"""
        try:
            close_side = "SELL" if position.side == "BUY" else "BUY"
            
            result = await asyncio.to_thread(
                self.client.place_order,
                symbol=position.symbol,
                side=close_side,
                qty=position.quantity,
                order_type='market',
                reduce_only=True
            )
            
            if result.get('success'):
                # Calculate PnL
                if position.side == "BUY":
                    pnl = (fill_price - position.entry_price) * position.quantity
                else:
                    pnl = (position.entry_price - fill_price) * position.quantity
                
                pnl_with_leverage = pnl * position.leverage
                
                await self._update_position_closed(position, fill_price, pnl_with_leverage, "closed_sl")
                
                if position.is_sideways:
                    await self._notify_sideways_closed(position, fill_price, pnl_with_leverage, "closed_sl")
                else:
                    await self._notify_user(
                        f"🛑 <b>SL Hit</b>\n\n"
                        f"Symbol: {position.symbol}\n"
                        f"Entry: {position.entry_price:.4f}\n"
                        f"Exit: {fill_price:.4f}\n"
                        f"PnL: <b>{pnl_with_leverage:+.2f} USDT</b>"
                    )
                
                del self.positions[position.symbol]
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error closing SL position: {e}")

    
    def check_cooldown(self, symbol: str) -> bool:
        """
        Check if symbol is in cooldown period
        
        Args:
            symbol: Trading pair
            
        Returns:
            True if in cooldown, False otherwise
        """
        if symbol not in self.cooldown_tracker:
            return False
        
        cooldown_until = self.cooldown_tracker[symbol]
        current_time = time.time()
        
        if current_time >= cooldown_until:
            # Cooldown expired, remove from tracker
            del self.cooldown_tracker[symbol]
            return False
        
        return True
    
    def mark_cooldown(self, symbol: str):
        """
        Mark symbol as in cooldown for 2.5 minutes
        
        Args:
            symbol: Trading pair
        """
        self.cooldown_tracker[symbol] = time.time() + self.config.cooldown_seconds
        logger.debug(f"[Scalping:{self.user_id}] Cooldown marked for {symbol} (2.5 minutes)")
    
    async def _save_position_to_db(self, position: ScalpingPosition, signal):
        """Save position to database, including sideways metadata if applicable"""
        try:
            from app.trading_mode import MicroScalpSignal as _MicroScalpSignal
            s = _client()

            row = {
                "telegram_id": self.user_id,
                "symbol": position.symbol,
                "side": position.side,
                "entry_price": position.entry_price,
                "quantity": position.quantity,
                "leverage": position.leverage,
                "tp_price": position.tp_price,
                "sl_price": position.sl_price,
                "trade_type": "scalping",
                "timeframe": "5m",
                "confidence": signal.confidence,
                "status": "open",
                "opened_at": datetime.utcnow().isoformat(),
            }

            if isinstance(signal, _MicroScalpSignal):
                # Sideways scalp metadata
                row.update({
                    "trade_subtype": "sideways_scalp",
                    "tp_strategy": "sideways_range_70pct",
                    "max_hold_time": 120,
                    "range_support": signal.range_support,
                    "range_resistance": signal.range_resistance,
                    "range_width_pct": signal.range_width_pct,
                    "bounce_confirmed": True,
                    "rsi_divergence_detected": signal.rsi_divergence_detected,
                })
            else:
                row.update({
                    "tp_strategy": "single_tp_1.5R",
                    "max_hold_time": 1800,
                })

            s.table("autotrade_trades").insert(row).execute()
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error saving position to DB: {e}")
    
    async def _update_position_closed(self, position: ScalpingPosition, close_price: float, 
                                     pnl: float, close_reason: str):
        """Update position in database when closed"""
        try:
            s = _client()
            s.table("autotrade_trades").update({
                "close_price": close_price,
                "pnl_usdt": pnl,
                "close_reason": close_reason,
                "status": close_reason,
                "closed_at": datetime.utcnow().isoformat(),
            }).eq("telegram_id", self.user_id).eq("symbol", position.symbol).eq("status", "open").execute()
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error updating position in DB: {e}")
    
    async def _notify_sideways_opened(self, position: ScalpingPosition, signal):
        """Notify user when sideways scalp position opened"""
        try:
            reasons_text = "\n".join(f"• {r}" for r in signal.reasons)
            await self.bot.send_message(
                chat_id=self.notify_chat_id,
                text=(
                    f"⚡ <b>SIDEWAYS SCALP Opened</b>\n\n"
                    f"Symbol: {position.symbol}\n"
                    f"Side: {position.side}\n"
                    f"Entry: {position.entry_price:.4f}\n"
                    f"TP: {position.tp_price:.4f}\n"
                    f"SL: {position.sl_price:.4f}\n"
                    f"R:R: 1:{signal.rr_ratio:.2f}\n"
                    f"Confidence: {signal.confidence}%\n"
                    f"Range: {signal.range_support:.4f} - {signal.range_resistance:.4f}\n"
                    f"Max Hold: 2 menit\n\n"
                    f"<b>Reasons:</b>\n{reasons_text}"
                ),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error sending sideways notification: {e}")

    async def _notify_sideways_closed(self, position: ScalpingPosition, fill_price: float, pnl: float, reason: str):
        """Notify user when sideways scalp position closed"""
        try:
            if reason == "closed_tp":
                label = "✅ SIDEWAYS TP Hit"
            elif reason == "closed_sl":
                label = "🛑 SIDEWAYS SL Hit"
            else:
                label = "⏰ SIDEWAYS Closed (2min)"
            
            await self._notify_user(
                f"{label}\n\n"
                f"Symbol: {position.symbol}\n"
                f"Entry: {position.entry_price:.4f}\n"
                f"Exit: {fill_price:.4f}\n"
                f"PnL: <b>{pnl:+.2f} USDT</b>"
            )
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error sending sideways close notification: {e}")

    async def _notify_position_opened(self, position: ScalpingPosition, signal: ScalpingSignal):
        """Notify user when position opened"""
        try:
            reasons_text = "\n".join(f"• {r}" for r in signal.reasons)
            
            await self.bot.send_message(
                chat_id=self.notify_chat_id,
                text=(
                    f"⚡ <b>SCALP Trade Opened</b>\n\n"
                    f"Symbol: {position.symbol}\n"
                    f"Side: {position.side}\n"
                    f"Entry: {position.entry_price:.4f}\n"
                    f"TP: {position.tp_price:.4f} (1.5R)\n"
                    f"SL: {position.sl_price:.4f}\n"
                    f"Confidence: {signal.confidence:.0f}%\n"
                    f"Max Hold: 30 minutes\n\n"
                    f"<b>Reasons:</b>\n{reasons_text}"
                ),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error sending notification: {e}")
    
    async def _notify_stackmentor_opened(self, position: ScalpingPosition, signal, levels):
        """Notify user when StackMentor position opened.

        `levels` is a `StackMentorLevels` dataclass from app.trade_execution.
        """
        try:
            reasons_text = "\n".join(f"• {r}" for r in signal.reasons) if hasattr(signal, 'reasons') else "Signal detected"

            # Calculate R:R ratios
            sl_distance = abs(position.entry_price - levels.sl)
            rr1 = abs(levels.tp1 - position.entry_price) / sl_distance if sl_distance > 0 else 0
            rr2 = abs(levels.tp2 - position.entry_price) / sl_distance if sl_distance > 0 else 0
            rr3 = abs(levels.tp3 - position.entry_price) / sl_distance if sl_distance > 0 else 0

            await self.bot.send_message(
                chat_id=self.notify_chat_id,
                text=(
                    f"⚡ <b>SCALP Trade Opened (StackMentor)</b>\n\n"
                    f"Symbol: {position.symbol}\n"
                    f"Side: {position.side}\n"
                    f"Entry: {position.entry_price:.4f}\n"
                    f"Quantity: {position.quantity:.6f}\n\n"
                    f"🎯 <b>3-Tier Take Profit:</b>\n"
                    f"TP1: {levels.tp1:.4f} ({rr1:.1f}R) - {levels.qty_tp1:.6f} (60%)\n"
                    f"TP2: {levels.tp2:.4f} ({rr2:.1f}R) - {levels.qty_tp2:.6f} (30%)\n"
                    f"TP3: {levels.tp3:.4f} ({rr3:.1f}R) - {levels.qty_tp3:.6f} (10%)\n\n"
                    f"🛡️ <b>Stop Loss:</b> {levels.sl:.4f}\n"
                    f"💡 <b>Auto-Breakeven:</b> SL moves to entry when TP1 hit\n\n"
                    f"<b>Reasons:</b>\n{reasons_text}\n\n"
                    f"✅ TP/SL ter-set dengan StackMentor system!"
                ),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error sending StackMentor notification: {e}")
    
    async def _notify_user(self, message: str):
        """Send notification to user"""
        try:
            await self.bot.send_message(
                chat_id=self.notify_chat_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error sending notification: {e}")

