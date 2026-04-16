"""
Scalping Engine
High-frequency trading engine for 5-minute scalping with 30-minute max hold time
"""

import asyncio
import logging
import os
import time
from typing import Optional, Dict
from datetime import datetime
from html import escape
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.trading_mode import ScalpingConfig, ScalpingSignal, ScalpingPosition
from app.supabase_repo import _client
from app.symbol_coordinator import (
    get_coordinator,
    StrategyOwner,
    PositionSide,
)

logger = logging.getLogger(__name__)
WEB_DASHBOARD_URL = os.getenv("WEB_DASHBOARD_URL", "https://cryptomentor.id")


def _fmt_price(v: float) -> str:
    s = f"{float(v):,.6f}"
    return s.rstrip("0").rstrip(".")


def _build_trade_url(trade_id: Optional[int] = None, order_id: str = "", symbol: str = "") -> str:
    try:
        parsed = urlsplit(WEB_DASHBOARD_URL)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["tab"] = "portfolio"
        if trade_id:
            query["trade_id"] = str(trade_id)
        if order_id and order_id != "-":
            query["order_id"] = str(order_id)
        if symbol:
            query["symbol"] = symbol
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", urlencode(query), parsed.fragment))
    except Exception:
        return WEB_DASHBOARD_URL


def _trade_detail_keyboard(trade_id: Optional[int] = None, order_id: str = "", symbol: str = "") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 View Trade Details", url=_build_trade_url(trade_id=trade_id, order_id=order_id, symbol=symbol))]
    ])


class ScalpingEngine:
    """
    High-frequency trading engine for 5-minute scalping
    
    Features:
    - 5M timeframe with 15M trend validation
    - Single TP at 1.5R
    - 30-minute max hold time
    - 5-minute cooldown between signals
    - 72% minimum confidence
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
        self._closing_symbols = set()
        self._recent_close_notifications: Dict[str, float] = {}
        
        # Cooldown tracking
        self.cooldown_tracker: Dict[str, float] = {}
        
        # Sideways error counter per symbol
        self.sideways_error_counter: Dict[str, int] = {}
        self.signal_streaks: Dict[str, Dict[str, float]] = {}
        self.last_closed_meta: Dict[str, Dict[str, float]] = {}
        
        # Running state
        self.running = False

        # Multi-user symbol coordinator
        self.coordinator = get_coordinator()

        logger.info(f"[Scalping:{user_id}] Engine initialized with config: {self.config}")

    def _fmt_pnl_usdt(self, pnl: float) -> str:
        """Format PnL with higher precision for tiny values."""
        try:
            p = float(pnl)
        except Exception:
            p = 0.0
        if abs(p) < 0.01:
            return f"{p:+.4f}"
        return f"{p:+.2f}"

    async def _resolve_exit_price(self, symbol: str, fallback: float, order_result: Optional[dict] = None) -> tuple[float, bool]:
        """
        Resolve exit price for PnL calculation.
        Returns (price, is_estimated_from_ticker).
        """
        try:
            if isinstance(order_result, dict):
                fp = order_result.get("fill_price")
                if fp is not None:
                    fpv = float(fp)
                    if fpv > 0:
                        return fpv, False
        except Exception:
            pass

        try:
            ticker = await asyncio.to_thread(self.client.get_ticker, symbol)
            if ticker and ticker.get("success"):
                px = float(
                    ticker.get("mark_price")
                    or ticker.get("last_price")
                    or ticker.get("price")
                    or fallback
                )
                if px > 0:
                    return px, True
        except Exception:
            pass

        return float(fallback), True

    async def _resolve_net_pnl(
        self,
        symbol: str,
        gross_pnl: float,
        open_order_id: str = "",
        close_order_id: str = "",
    ) -> tuple[float, float, float, bool]:
        """
        Best-effort net PnL estimation using exchange order fees/details.
        Returns: (net_pnl, open_fee, close_fee, used_exchange_data)
        """
        open_fee = 0.0
        close_fee = 0.0
        used_exchange_data = False
        close_realized = None

        get_fin = getattr(self.client, "get_order_financials", None)
        if not callable(get_fin):
            return gross_pnl, open_fee, close_fee, used_exchange_data

        try:
            if open_order_id:
                o = await asyncio.to_thread(get_fin, open_order_id, symbol)
                if o.get("success"):
                    open_fee = abs(float(o.get("fee", 0) or 0))
                    used_exchange_data = True
        except Exception:
            pass

        try:
            if close_order_id:
                c = await asyncio.to_thread(get_fin, close_order_id, symbol)
                if c.get("success"):
                    close_fee = abs(float(c.get("fee", 0) or 0))
                    if c.get("realized_pnl") is not None:
                        close_realized = float(c.get("realized_pnl"))
                    used_exchange_data = True
        except Exception:
            pass

        base = close_realized if close_realized is not None else gross_pnl
        net = base - open_fee - close_fee
        return net, open_fee, close_fee, used_exchange_data
    
    async def run(self):
        """Main trading loop - scans every 15 seconds"""
        self.running = True
        logger.info(f"[Scalping:{self.user_id}] Engine started")
        
        # ── Recover existing state ───────────────────────────────────────────
        # 1. Reconcile DB with Exchange (close stale rows if positions closed manually)
        try:
            from app.trade_history import reconcile_open_trades_with_exchange
            reconciled = await asyncio.to_thread(
                reconcile_open_trades_with_exchange, self.user_id, self.client
            )
            if reconciled > 0:
                logger.info(f"[Scalping:{self.user_id}] Reconciled {reconciled} stale positions on startup")
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Reconciliation failed: {e}")

        # 2. Load open positions from DB to resume monitoring
        await self._load_existing_positions()
        
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
                    f"Bot will scan for high-probability setups every {self.config.scan_interval} seconds.\n"
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
                    # ── Check Supabase stop signal ────────────────────────────
                    # Only stop if status is explicitly "stopped" AND engine_active=False
                    # This prevents race conditions where status briefly shows "stopped"
                    # during user restart flow
                    try:
                        from app.supabase_repo import _client as _sc
                        _sr = _sc().table("autotrade_sessions").select("status, engine_active").eq(
                            "telegram_id", self.user_id
                        ).limit(1).execute()
                        if _sr.data:
                            _row = _sr.data[0]
                            _status = _row.get("status")
                            _engine_active = _row.get("engine_active", True)
                            # Only stop if BOTH status=stopped AND engine_active=False
                            # If engine_active=True, user just restarted — keep running
                            if _status == "stopped" and not _engine_active:
                                logger.info(f"[Scalping:{self.user_id}] Stop signal from Supabase (status=stopped, engine_active=False)")
                                self.running = False
                                try:
                                    await self.bot.send_message(
                                        chat_id=self.notify_chat_id,
                                        text="🛑 <b>AutoTrade stopped.</b>\n\nUse /autotrade to restart.",
                                        parse_mode='HTML'
                                    )
                                except Exception:
                                    pass
                                break
                    except Exception:
                        pass

                    scan_count += 1
                    logger.info(f"[Scalping:{self.user_id}] Scan cycle #{scan_count} starting...")
                    
                    # Monitor existing positions first (priority)
                    logger.info(f"[Scalping:{self.user_id}] Monitoring positions...")
                    await self.monitor_positions()
                    
                    # Scan for new signals in PARALLEL
                    logger.info(f"[Scalping:{self.user_id}] Scanning {len(self.config.pairs)} pairs simultaneously...")
                    signals_found = 0
                    signals_validated = 0
                    
                    scan_tasks = []
                    for symbol in self.config.pairs:
                        scan_tasks.append(self._scan_single_symbol(symbol))
                        
                    if scan_tasks and self.running:
                        results = await asyncio.gather(*scan_tasks, return_exceptions=True)
                        
                        candidate_signals = []
                        for r in results:
                            if isinstance(r, Exception):
                                logger.error(f"[Scalping:{self.user_id}] Gathered exception: {r}")
                            elif r is not None:
                                candidate_signals.append(r)

                        normal_signals = [s for s in candidate_signals if not getattr(s, "is_emergency", False)]
                        emergency_signals = [s for s in candidate_signals if getattr(s, "is_emergency", False)]

                        if normal_signals:
                            valid_signals = normal_signals
                        elif emergency_signals:
                            best_emergency = max(
                                emergency_signals,
                                key=lambda s: float(getattr(s, "emergency_score", getattr(s, "confidence", 0)))
                            )
                            valid_signals = [best_emergency]
                            logger.info(
                                f"[Scalping:{self.user_id}] Emergency candidate selected: "
                                f"{best_emergency.symbol} {best_emergency.side} "
                                f"(score={getattr(best_emergency, 'emergency_score', best_emergency.confidence):.2f})"
                            )
                        else:
                            valid_signals = []

                        signals_found += len(valid_signals)
                        
                        # Sequentially process the returned valid signals
                        for signal in valid_signals:
                            if not self.running:
                                break
                                
                            # Re-check concurrent safety limits safely in the sequential block
                            if len(self.positions) >= self.config.max_concurrent_positions:
                                break
                            
                            if signal.symbol in self.positions:
                                continue
                                
                            signals_validated += 1
                            logger.info(f"[Scalping:{self.user_id}] {signal.symbol} - Signal validated! Placing order...")
                            
                            success = await self.place_scalping_order(signal)
                            
                            if success:
                                self.mark_cooldown(signal.symbol)
                                logger.info(f"[Scalping:{self.user_id}] {signal.symbol} - Order placed successfully!")
                            else:
                                # Avoid hammering non-executable symbols in emergency mode.
                                self.cooldown_tracker[signal.symbol] = time.time() + 300
                                logger.warning(f"[Scalping:{self.user_id}] {signal.symbol} - Order placement failed")
                    
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

    
    async def _scan_single_symbol(self, symbol: str) -> Optional[ScalpingSignal]:
        try:
            if self.check_cooldown(symbol):
                return None
                
            signal = await self.generate_scalping_signal(symbol)
            if signal is not None:
                if not self.validate_scalping_entry(signal):
                    signal = None
                elif not self._passes_anti_flip_filters(signal):
                    signal = None
                else:
                    setattr(signal, "is_emergency", False)
                    return signal

            if not getattr(self.config, "emergency_candidate_mode", False):
                return None

            emergency_signal = await self._generate_emergency_candidate(symbol)
            if emergency_signal is None:
                return None
            if not self.validate_scalping_entry(emergency_signal):
                return None
            if not self._passes_anti_flip_filters(emergency_signal):
                return None

            setattr(emergency_signal, "is_emergency", True)
            setattr(
                emergency_signal,
                "emergency_score",
                float(emergency_signal.confidence) + (float(emergency_signal.rr_ratio) * 8.0) + (float(getattr(emergency_signal, "volume_ratio", 1.0)) * 4.0),
            )
            return emergency_signal
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error in _scan_single_symbol for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
            
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

    async def _generate_emergency_candidate(self, symbol: str) -> Optional[ScalpingSignal]:
        """
        Emergency candidate mode:
        Build a conservative fallback candidate when normal logic produces nothing.
        Safety checks are still enforced by validate_scalping_entry().
        """
        try:
            from app.candle_cache import get_candles_cached
            from app.providers.alternative_klines_provider import alternative_klines_provider

            base_symbol = symbol.replace("USDT", "").upper()

            async def fetch_klines_async(sym, interval, limit):
                source_orders = [
                    ["bitunix", "binance", "cryptocompare", "coingecko"],
                    ["binance", "bitunix", "cryptocompare", "coingecko"],
                ]
                for order in source_orders:
                    data = await asyncio.to_thread(
                        alternative_klines_provider.get_klines,
                        sym, interval, limit, order
                    )
                    if data:
                        return data
                return []

            raw_5m = await get_candles_cached(fetch_klines_async, base_symbol, "5m", 80)
            if not raw_5m or len(raw_5m) < 40:
                return None

            closes = [float(k[4]) for k in raw_5m]
            highs = [float(k[2]) for k in raw_5m]
            lows = [float(k[3]) for k in raw_5m]
            vols = [float(k[5]) for k in raw_5m]
            price = closes[-1]
            if price <= 0:
                return None

            def _ema(values, period):
                if len(values) < period:
                    return values[-1]
                k = 2 / (period + 1)
                e = sum(values[:period]) / period
                for v in values[period:]:
                    e = v * k + e * (1 - k)
                return e

            def _rsi(values, period=14):
                if len(values) < period + 1:
                    return 50.0
                gains = []
                losses = []
                for i in range(1, len(values)):
                    d = values[i] - values[i - 1]
                    gains.append(max(d, 0.0))
                    losses.append(max(-d, 0.0))
                avg_gain = sum(gains[-period:]) / period
                avg_loss = sum(losses[-period:]) / period
                if avg_loss == 0:
                    return 100.0
                rs = avg_gain / avg_loss
                return 100 - (100 / (1 + rs))

            ema21 = _ema(closes, 21)
            ema50 = _ema(closes, 50)
            rsi_5m = _rsi(closes, 14)

            tr = []
            for i in range(1, len(closes)):
                tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
            atr = (sum(tr[-14:]) / 14) if len(tr) >= 14 else 0.0
            atr_pct = (atr / price) * 100 if price > 0 else 0.0
            if atr_pct < max(0.08, self.config.min_atr_pct * 0.6):
                return None

            avg_vol = sum(vols[-21:-1]) / 20 if len(vols) >= 21 else (sum(vols[:-1]) / max(1, len(vols) - 1))
            vol_ratio = (vols[-1] / avg_vol) if avg_vol > 0 else 0.0
            if vol_ratio < getattr(self.config, "emergency_min_volume_ratio", 0.9):
                return None

            side = None
            if ema21 >= ema50 and rsi_5m <= 62:
                side = "LONG"
            elif ema21 <= ema50 and rsi_5m >= 38:
                side = "SHORT"
            if side is None:
                return None

            sl_distance = max(atr * 1.15, price * 0.0025)
            tp_distance = sl_distance * 1.6
            if side == "LONG":
                sl = price - sl_distance
                tp = price + tp_distance
                trend_15m = "LONG"
            else:
                sl = price + sl_distance
                tp = price - tp_distance
                trend_15m = "SHORT"

            rr = tp_distance / sl_distance if sl_distance > 0 else 0.0
            confidence = min(82, max(72, int(72 + max(0.0, (vol_ratio - 1.0) * 8.0) + (2 if atr_pct > 0.4 else 0))))

            signal = ScalpingSignal(
                symbol=symbol,
                side=side,
                confidence=confidence,
                entry_price=price,
                tp_price=tp,
                sl_price=sl,
                rr_ratio=rr,
                atr_pct=atr_pct,
                volume_ratio=vol_ratio,
                rsi_5m=rsi_5m,
                trend_15m=trend_15m,
                reasons=[
                    "Emergency candidate mode (top-ranked fallback)",
                    f"EMA21/50={ema21:.4f}/{ema50:.4f}, RSI={rsi_5m:.1f}",
                    f"ATR={atr_pct:.2f}%, Volume={vol_ratio:.2f}x",
                ],
            )
            return signal
        except Exception as e:
            logger.debug(f"[Scalping:{self.user_id}] Emergency candidate error for {symbol}: {e}")
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
                source_orders = [
                    ["bitunix", "binance", "cryptocompare", "coingecko"],
                    ["binance", "bitunix", "cryptocompare", "coingecko"],
                    ["binance", "cryptocompare", "bitunix", "coingecko"],
                ]
                for order in source_orders:
                    data = await asyncio.to_thread(
                        alternative_klines_provider.get_klines,
                        sym, interval, limit, order
                    )
                    if data:
                        return data
                return []

            # Fetch klines (list format: [timestamp, open, high, low, close, volume, ...])
            raw_5m = await get_candles_cached(fetch_klines_async, base_symbol, "5m", 50)
            raw_15m = await get_candles_cached(fetch_klines_async, base_symbol, "15m", 60)

            if not raw_5m or not raw_15m:
                logger.warning(
                    f"[Scalping:{self.user_id}] {symbol} partial feed outage in sideways path "
                    f"(5m={len(raw_5m) if raw_5m else 0}, 15m={len(raw_15m) if raw_15m else 0})"
                )
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

            # Step 2: Identify range S/R (optional — used for room check)
            try:
                range_result = RangeAnalyzer().analyze(candles_5m, price)
            except Exception as e:
                self._increment_sideways_error(symbol)
                logger.error(f"[Scalping:{self.user_id}] RangeAnalyzer error for {symbol}: {e}")
                range_result = None

            support = range_result.support if range_result else None
            resistance = range_result.resistance if range_result else None

            # Step 3: Try bounce signal first (classic S/R bounce)
            bounce_result = None
            if range_result:
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

            # Step 3b: If no bounce, try micro momentum (1M/3M EMA crossover)
            if bounce_result is None:
                try:
                    from app.micro_momentum_detector import MicroMomentumDetector
                    raw_1m = await get_candles_cached(fetch_klines_async, base_symbol, "1m", 30)
                    raw_3m = await get_candles_cached(fetch_klines_async, base_symbol, "3m", 15)

                    if raw_1m and raw_3m:
                        candles_1m = to_dict_candles(raw_1m)
                        candles_3m = to_dict_candles(raw_3m)

                        momentum_signal = MicroMomentumDetector().detect(
                            candles_1m=candles_1m,
                            candles_3m=candles_3m,
                            candles_5m=candles_5m,
                            price=price,
                            support=support,
                            resistance=resistance,
                        )

                        if momentum_signal:
                            logger.info(
                                f"[Scalping:{self.user_id}] {symbol} MICRO MOMENTUM signal: "
                                f"{momentum_signal.direction} | {momentum_signal.reason}"
                            )
                            # Return as MicroScalpSignal
                            reasons = [
                                f"Sideways market: {sideways_result.reason}",
                                f"Micro momentum: {momentum_signal.reason}",
                            ]
                            if range_result:
                                reasons.insert(1, f"Range: {range_result.support:.4f} - {range_result.resistance:.4f}")

                            return MicroScalpSignal(
                                symbol=symbol,
                                side=momentum_signal.direction,
                                entry_price=momentum_signal.entry_price,
                                tp_price=momentum_signal.tp_price,
                                sl_price=momentum_signal.sl_price,
                                rr_ratio=momentum_signal.rr_ratio,
                                range_support=support or price * 0.995,
                                range_resistance=resistance or price * 1.005,
                                range_width_pct=range_result.range_width_pct if range_result else 0.5,
                                confidence=momentum_signal.confidence,
                                bounce_confirmed=False,
                                rsi_divergence_detected=False,
                                volume_ratio=1.0,
                                reasons=reasons,
                            )
                except Exception as e:
                    logger.warning(f"[Scalping:{self.user_id}] MicroMomentum error for {symbol}: {e}")

            if bounce_result is None:
                # Fallback: emit a conservative range-reversion candidate when
                # market is sideways and a valid range exists, even without a
                # clean wick bounce or micro-momentum trigger.
                if range_result is not None:
                    try:
                        closes = [float(c["close"]) for c in candles_5m[-20:]]
                        if len(closes) >= 15:
                            gains, losses = [], []
                            for i in range(1, len(closes)):
                                d = closes[i] - closes[i - 1]
                                gains.append(max(d, 0.0))
                                losses.append(max(-d, 0.0))
                            period = min(14, len(gains))
                            avg_gain = sum(gains[-period:]) / period if period else 0.0
                            avg_loss = sum(losses[-period:]) / period if period else 0.0
                            rsi_5m = 100.0 if avg_loss == 0 else (100 - (100 / (1 + (avg_gain / avg_loss))))
                        else:
                            rsi_5m = 50.0

                        support = range_result.support
                        resistance = range_result.resistance
                        width = max(1e-12, resistance - support)
                        pos_in_range = (price - support) / width  # 0=near support, 1=near resistance

                        direction = None
                        if pos_in_range <= 0.35 and rsi_5m <= 58:
                            direction = "LONG"
                        elif pos_in_range >= 0.65 and rsi_5m >= 42:
                            direction = "SHORT"

                        if direction is not None:
                            entry = price
                            tr_list_fb = []
                            for i in range(1, len(candles_5m)):
                                c = candles_5m[i]
                                p = candles_5m[i - 1]
                                tr_list_fb.append(max(c["high"] - c["low"], abs(c["high"] - p["close"]), abs(c["low"] - p["close"])))
                            atr_fb = (sum(tr_list_fb[-14:]) / 14) if len(tr_list_fb) >= 14 else 0.0
                            sl_buffer = (atr_fb * 0.6) if atr_fb > 0 else (entry * 0.0025)
                            if direction == "LONG":
                                tp = entry + 0.55 * (resistance - entry)
                                sl = support - sl_buffer
                                rr = (tp - entry) / (entry - sl) if (entry - sl) > 0 else 0
                            else:
                                tp = entry - 0.55 * (entry - support)
                                sl = resistance + sl_buffer
                                rr = (entry - tp) / (sl - entry) if (sl - entry) > 0 else 0

                            if rr >= getattr(self.config, "sideways_min_rr", 1.1):
                                reasons = [
                                    f"Sideways fallback: {sideways_result.reason}",
                                    f"Range reversion candidate ({pos_in_range*100:.0f}% in range, RSI={rsi_5m:.1f})",
                                    f"Range: {support:.4f} - {resistance:.4f} ({range_result.range_width_pct:.2f}%)",
                                ]
                                return MicroScalpSignal(
                                    symbol=symbol,
                                    side=direction,
                                    entry_price=entry,
                                    tp_price=round(tp, 6),
                                    sl_price=round(sl, 6),
                                    rr_ratio=round(rr, 2),
                                    range_support=support,
                                    range_resistance=resistance,
                                    range_width_pct=range_result.range_width_pct,
                                    confidence=72,
                                    bounce_confirmed=False,
                                    rsi_divergence_detected=False,
                                    volume_ratio=1.0,
                                    reasons=reasons,
                                )
                    except Exception as e:
                        logger.debug(f"[Scalping:{self.user_id}] {symbol} sideways fallback failed: {e}")

                logger.debug(f"[Scalping:{self.user_id}] {symbol} No bounce/momentum/fallback signal")
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

            # Calculate ATR (14 periods) to dynamically pad SL buffer
            atr = 0
            if len(candles_5m) > 14:
                tr_list = []
                for i in range(1, len(candles_5m)):
                    c = candles_5m[i]
                    p = candles_5m[i-1]
                    high = c['high']
                    low = c['low']
                    prev_close = p['close']
                    tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
                    tr_list.append(tr)
                atr = sum(tr_list[-14:]) / 14 if len(tr_list) >= 14 else 0

            # Step 6: Calculate TP/SL
            entry = price
            # Dynamic volatility buffer: 0.75x ATR. If ATR fails, fallback to 0.35%
            sl_buffer_price = (atr * 0.75) if atr > 0 else (entry * 0.0035)

            if direction == "LONG":
                tp = entry + 0.70 * (range_result.resistance - entry)
                sl = range_result.support - sl_buffer_price
            else:  # SHORT
                tp = entry - 0.70 * (entry - range_result.support)
                sl = range_result.resistance + sl_buffer_price

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

    def _passes_anti_flip_filters(self, signal) -> bool:
        """Require directional stability + block rapid opposite re-entry."""
        now = time.time()
        symbol = signal.symbol
        direction = signal.side  # LONG / SHORT

        # 1) Consecutive confirmation gate (stability filter)
        required = int(getattr(self.config, "signal_confirmations_required", 2))
        max_gap = int(getattr(self.config, "signal_confirmation_max_gap_seconds", 45))
        streak = self.signal_streaks.get(symbol)
        if not isinstance(streak, dict):
            streak = None
            self.signal_streaks[symbol] = None
        if not streak:
            self.signal_streaks[symbol] = {"direction": direction, "count": 1, "ts": now}
            if required > 1:
                logger.info(f"[Scalping:{self.user_id}] {symbol} anti-flip: first {direction} signal seen, waiting confirmation")
                return False
            streak = self.signal_streaks[symbol]

        last_dir = streak.get("direction")
        last_ts = float(streak.get("ts", 0))
        last_count = int(streak.get("count", 0))
        if direction == last_dir and now - last_ts <= max_gap:
            new_count = last_count + 1
            self.signal_streaks[symbol] = {"direction": direction, "count": new_count, "ts": now}
            if new_count < required:
                logger.info(f"[Scalping:{self.user_id}] {symbol} anti-flip: streak {new_count}/{required}, waiting")
                return False
        else:
            self.signal_streaks[symbol] = {"direction": direction, "count": 1, "ts": now}
            if required > 1:
                logger.info(f"[Scalping:{self.user_id}] {symbol} anti-flip: direction changed/reset to {direction}, waiting confirmation")
                return False

        # 2) Opposite-direction re-entry cooldown after close
        closed = self.last_closed_meta.get(symbol)
        if closed:
            closed_ts = float(closed.get("ts", 0))
            closed_side = closed.get("side")  # BUY / SELL
            closed_reason = str(closed.get("reason", ""))
            opposite_block = int(getattr(self.config, "anti_flip_opposite_seconds", 600))
            if "sideways" in closed_reason:
                opposite_block = max(opposite_block, int(getattr(self.config, "sideways_reentry_cooldown_seconds", 420)))

            is_opposite = (closed_side == "BUY" and direction == "SHORT") or (closed_side == "SELL" and direction == "LONG")
            if is_opposite and (now - closed_ts) < opposite_block:
                wait_left = int(opposite_block - (now - closed_ts))
                logger.info(
                    f"[Scalping:{self.user_id}] {symbol} anti-flip: blocked opposite re-entry "
                    f"{direction} for {wait_left}s after close_reason={closed_reason}"
                )
                return False

        # Streak consumed for this execution cycle
        self.signal_streaks.pop(symbol, None)
        return True

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
            # Auto Max-Safe leverage is passed in from caller
            # leverage = min(leverage, 10)  # Removed hardcoded cap
            
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
                f"Leverage={leverage}x (Auto Max-Safe), "
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
        
        # Check R:R (sideways uses a dedicated temporary floor)
        required_rr = self.config.sideways_min_rr if is_sideways else self.config.min_rr
        if signal.rr_ratio < required_rr:
            logger.debug(
                f"[Scalping:{self.user_id}] Signal rejected: "
                f"R:R {signal.rr_ratio} < {required_rr}"
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
            
            if not res or not isinstance(getattr(res, "data", None), list) or not res.data:
                return False
            
            total_pnl = 0.0
            for t in res.data:
                if not isinstance(t, dict):
                    continue
                try:
                    total_pnl += float(t.get("pnl_usdt", 0) or 0)
                except Exception:
                    continue
            
            # Get account balance
            session_res = s.table("autotrade_sessions").select("initial_deposit").eq(
                "telegram_id", self.user_id
            ).limit(1).execute()
            
            if not session_res or not isinstance(getattr(session_res, "data", None), list) or not session_res.data:
                return False

            first = session_res.data[0] if session_res.data else {}
            if not isinstance(first, dict):
                first = {}
            balance = float(first.get("initial_deposit", 100) or 100)
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
        pending_marked = False
        
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
                
                # ── Auto Max Pair Leverage Calculation ──
                from app.position_sizing import calculate_max_safe_leverage
                effective_leverage = calculate_max_safe_leverage(signal.entry_price, signal.sl_price, signal.symbol)
                
                logger.info(f"[Scalping:{self.user_id}] Auto Max Pair Leverage for {signal.symbol}: {effective_leverage}x (Baseline: {leverage}x)")
                
                # CRITICAL: Calculate position size based on risk (Phase 2)
                quantity, used_risk_sizing = self.calculate_position_size_pro(
                    entry_price=signal.entry_price,
                    sl_price=signal.sl_price,
                    capital=capital,
                    leverage=effective_leverage
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
                    "LINKUSDT": 0.1,  "UNIUSDT": 0.1,  "ATOMUSDT": 0.1,
                    "XAUUSDT": 0.01,  "CLUSDT": 0.01,  "QQQUSDT": 0.1
                }
                min_qty = MIN_QTY_MAP.get(signal.symbol, 0.001)
                
                # CRITICAL: Skip trade if qty too small - NEVER auto-raise leverage
                # Auto-raising leverage breaks risk management (user set leverage for specific risk %)
                if quantity_adjusted < min_qty:
                    logger.warning(
                        f"[Scalping:{self.user_id}] {signal.symbol} qty={quantity_adjusted:.6f} "
                        f"< min={min_qty}. Skipping - balance too small for this pair."
                    )
                    return False  # Silent skip, engine will try other pairs
                
                # ═══════════════════════════════════════════════════════════
                # Multi-user symbol coordination check
                # ═══════════════════════════════════════════════════════════
                can_enter, block_reason = await self.coordinator.can_enter(
                    user_id=self.user_id,
                    symbol=signal.symbol,
                    strategy=StrategyOwner.SCALP,
                    now_ts=time.time()
                )
                if not can_enter:
                    logger.warning(f"[Coordinator:{self.user_id}] Entry BLOCKED for {signal.symbol}: {block_reason}")
                    await self._notify_user(
                        f"⚠️ <b>Trade skipped on {signal.symbol}</b>\n\n"
                        f"<b>Reason:</b> {block_reason}\n\n"
                        f"Another strategy may own this symbol.\nBot will continue scanning."
                    )
                    return False

                # Mark pending
                await self.coordinator.set_pending(self.user_id, signal.symbol, StrategyOwner.SCALP)
                pending_marked = True

                # ═══════════════════════════════════════════════════════════
                # Unified entry path — see app/trade_execution.py
                # Atomic order with TP1 + SL on exchange + StackMentor register
                # ═══════════════════════════════════════════════════════════
                from app.trade_execution import open_managed_position
                from app.trading_mode import MicroScalpSignal as _MicroScalpSignalCheck
                _is_sideways_signal = isinstance(signal, _MicroScalpSignalCheck)

                exec_result = await open_managed_position(
                    client=self.client,
                    user_id=self.user_id,
                    symbol=signal.symbol,
                    side=signal.side,                # "LONG" / "SHORT"
                    entry_price=signal.entry_price,
                    sl_price=signal.sl_price,
                    quantity=quantity_adjusted,
                    leverage=effective_leverage,
                    # Sideways positions have very tight TP/SL — skip reconcile
                    # to avoid false emergency closes. Engine monitors via max_hold.
                    reconcile=not _is_sideways_signal,
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
                        open_order_id=exec_result.order_id or "",
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
                    trade_id = await self._save_position_to_db(position, signal, order_id=exec_result.order_id or "")
                    await self._notify_stackmentor_opened(
                        position,
                        signal,
                        levels,
                        order_id=exec_result.order_id or "-",
                        trade_id=trade_id,
                    )

                    # Confirm position with coordinator
                    position_side = PositionSide.LONG if signal.side == "LONG" else PositionSide.SHORT
                    await self.coordinator.confirm_open(
                        user_id=self.user_id,
                        symbol=signal.symbol,
                        strategy=StrategyOwner.SCALP,
                        side=position_side,
                        size=quantity_adjusted,
                        entry_price=signal.entry_price,
                        exchange_position_id=getattr(exec_result, 'position_id', None)
                    )
                    pending_marked = False

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

                    # Non-retryable conditions — clear pending before returning
                    if error_code == "insufficient_balance":
                        await self._notify_user("❌ Order failed: Insufficient balance")
                        await self.coordinator.clear_pending(self.user_id, signal.symbol)
                        pending_marked = False
                        return False
                    if error_code == "invalid_prices":
                        await self._notify_user(
                            f"⚠️ <b>Trade skipped: {signal.symbol}</b>\n\n"
                            f"Market moved before entry: {error_msg}"
                        )
                        await self.coordinator.clear_pending(self.user_id, signal.symbol)
                        pending_marked = False
                        return False
                    if error_code in ("auth", "ip_blocked"):
                        await self._notify_user(
                            f"⚠️ Exchange auth/IP error: {error_msg}\n"
                            f"Engine continues; check API key & proxy."
                        )
                        await self.coordinator.clear_pending(self.user_id, signal.symbol)
                        pending_marked = False
                        return False
                    if error_code == "reconcile_failed":
                        await self._notify_user(
                            f"🚨 <b>Position auto-closed: {signal.symbol}</b>\n\n"
                            f"Self-healing check found the live position did not match "
                            f"expected qty/TP/SL and could not be repaired. Position was "
                            f"closed to protect your capital.\n\n"
                            f"<code>{error_msg}</code>"
                        )
                        await self.coordinator.clear_pending(self.user_id, signal.symbol)
                        pending_marked = False
                        return False
                    if 'invalid symbol' in error_msg.lower():
                        await self._notify_user(f"❌ Order failed: Invalid symbol {signal.symbol}")
                        await self.coordinator.clear_pending(self.user_id, signal.symbol)
                        pending_marked = False
                        return False

                    # Retryable error — backoff
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
            
            except asyncio.TimeoutError:
                logger.warning(f"[Scalping:{self.user_id}] Order timeout (attempt {attempt+1})")
                if attempt == max_retries - 1 and pending_marked:
                    await self.coordinator.clear_pending(self.user_id, signal.symbol)
                    pending_marked = False
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
            
            except Exception as e:
                logger.error(f"[Scalping:{self.user_id}] Order exception (attempt {attempt+1}): {e}")
                if attempt == max_retries - 1 and pending_marked:
                    await self.coordinator.clear_pending(self.user_id, signal.symbol)
                    pending_marked = False
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
        
        # All retries failed — set cooldown to prevent spam
        if pending_marked:
            await self.coordinator.clear_pending(self.user_id, signal.symbol)
            pending_marked = False
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
                close_order_id = str(result.get("order_id") or "")
                fill_price, px_estimated = await self._resolve_exit_price(
                    position.symbol, position.entry_price, result
                )
                
                # Calculate PnL
                if position.side == "BUY":
                    pnl = (fill_price - position.entry_price) * position.quantity
                else:
                    pnl = (position.entry_price - fill_price) * position.quantity
                
                pnl_usdt = pnl
                pnl_net, open_fee, close_fee, used_exchange = await self._resolve_net_pnl(
                    symbol=position.symbol,
                    gross_pnl=pnl_usdt,
                    open_order_id=getattr(position, "open_order_id", "") or "",
                    close_order_id=close_order_id,
                )
                
                # Update database
                await self._update_position_closed(
                    position, fill_price, pnl_net, "max_hold_time_exceeded"
                )

                # Confirm position closed with coordinator
                await self.coordinator.confirm_closed(self.user_id, position.symbol, time.time())

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
                    f"Entry: {_fmt_price(position.entry_price)}\n"
                    f"Exit: {_fmt_price(fill_price)}{' (estimated)' if px_estimated else ''}\n"
                    f"Hold Time: 30 minutes\n"
                    f"PnL (net): <b>{self._fmt_pnl_usdt(pnl_net)} USDT</b>\n"
                    f"PnL (gross): <b>{self._fmt_pnl_usdt(pnl_usdt)} USDT</b>"
                    + (f"\nFees: {self._fmt_pnl_usdt(-(open_fee + close_fee))} USDT" if used_exchange else "")
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
        if position.symbol in self._closing_symbols:
            logger.info(f"[Scalping:{self.user_id}] Skip duplicate close attempt for {position.symbol}")
            return
        self._closing_symbols.add(position.symbol)
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
                close_order_id = str(result.get("order_id") or "")
                fill_price = float(result.get('fill_price', 0))
                # If exchange doesn't return fill_price, get current mark price
                if fill_price <= 0:
                    try:
                        ticker = await asyncio.to_thread(self.client.get_ticker, position.symbol)
                        if ticker.get('success'):
                            fill_price = float(ticker.get('mark_price', position.entry_price))
                        else:
                            fill_price = position.entry_price
                    except Exception:
                        fill_price = position.entry_price

                if position.side == "BUY":
                    pnl = (fill_price - position.entry_price) * position.quantity
                else:
                    pnl = (position.entry_price - fill_price) * position.quantity

                pnl_usdt = pnl
                pnl_net, open_fee, close_fee, used_exchange = await self._resolve_net_pnl(
                    symbol=position.symbol,
                    gross_pnl=pnl_usdt,
                    open_order_id=getattr(position, "open_order_id", "") or "",
                    close_order_id=close_order_id,
                )

                closed_now = await self._update_position_closed(
                    position, fill_price, pnl_net, "sideways_max_hold_exceeded"
                )
                if closed_now:
                    # Confirm position closed with coordinator
                    await self.coordinator.confirm_closed(self.user_id, position.symbol, time.time())

                    self.last_closed_meta[position.symbol] = {
                        "ts": time.time(),
                        "side": position.side,
                        "reason": "sideways_max_hold_exceeded",
                    }
                    await self._notify_user_once(
                        dedupe_key=f"sideways_2m:{position.symbol}:{position.entry_price:.4f}",
                        message=(
                            f"⏰ <b>SIDEWAYS Closed (2min)</b>\n\n"
                            f"Symbol: {position.symbol}\n"
                            f"Entry: {_fmt_price(position.entry_price)}\n"
                            f"Exit: {_fmt_price(fill_price)}\n"
                            f"Hold Time: {elapsed}s\n"
                            f"PnL (net): <b>{self._fmt_pnl_usdt(pnl_net)} USDT</b>\n"
                            f"PnL (gross): <b>{self._fmt_pnl_usdt(pnl_usdt)} USDT</b>"
                            + (f"\nFees: {self._fmt_pnl_usdt(-(open_fee + close_fee))} USDT" if used_exchange else "")
                        ),
                        ttl_sec=600,
                    )
                    # Prevent rapid churn on the same sideways pair.
                    sideways_cd = int(getattr(self.config, "sideways_reentry_cooldown_seconds", 420))
                    self.cooldown_tracker[position.symbol] = time.time() + max(self.config.cooldown_seconds, sideways_cd)
                    logger.info(
                        f"[Scalping:{self.user_id}] Applied sideways re-entry cooldown for "
                        f"{position.symbol}: {max(self.config.cooldown_seconds, sideways_cd)}s"
                    )
                self.positions.pop(position.symbol, None)
            else:
                logger.error(
                    f"[Scalping:{self.user_id}] Failed to close sideways position: {result.get('error')}"
                )
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error closing sideways max hold: {e}")
        finally:
            self._closing_symbols.discard(position.symbol)
    
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
                
                pnl_usdt = pnl
                
                closed_now = await self._update_position_closed(position, fill_price, pnl_usdt, "closed_tp")
                if closed_now:
                    # Confirm position closed with coordinator
                    await self.coordinator.confirm_closed(self.user_id, position.symbol, time.time())

                    self.last_closed_meta[position.symbol] = {
                        "ts": time.time(),
                        "side": position.side,
                        "reason": "closed_tp",
                    }
                    if position.is_sideways:
                        await self._notify_sideways_closed(position, fill_price, pnl_usdt, "closed_tp")
                    else:
                        await self._notify_user(
                            f"✅ <b>TP Hit!</b>\n\n"
                            f"Symbol: {position.symbol}\n"
                            f"Entry: {position.entry_price:.4f}\n"
                            f"Exit: {fill_price:.4f}\n"
                            f"PnL: <b>{pnl_usdt:+.2f} USDT</b> 🎉"
                        )

                # Social proof broadcast — kirim ke semua user jika profit >= 2 USDT
                if pnl_usdt >= 2.0:
                    try:
                        from app.social_proof import broadcast_profit
                        from app.supabase_repo import get_user_by_tid
                        user_data = get_user_by_tid(self.user_id)
                        fname = user_data.get("first_name", "User") if user_data else "User"
                        import asyncio as _asyncio
                        _asyncio.create_task(broadcast_profit(
                            bot=self.bot,
                            user_id=self.user_id,
                            first_name=fname,
                            symbol=position.symbol,
                            side=position.side,
                            pnl_usdt=pnl_usdt,
                            leverage=position.leverage,
                        ))
                    except Exception as _bp_err:
                        logger.warning(f"[Scalping:{self.user_id}] broadcast_profit failed: {_bp_err}")
                
                self.positions.pop(position.symbol, None)
        
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
                
                pnl_usdt = pnl
                
                closed_now = await self._update_position_closed(position, fill_price, pnl_usdt, "closed_sl")
                if closed_now:
                    # Confirm position closed with coordinator
                    await self.coordinator.confirm_closed(self.user_id, position.symbol, time.time())

                    self.last_closed_meta[position.symbol] = {
                        "ts": time.time(),
                        "side": position.side,
                        "reason": "closed_sl",
                    }
                    if position.is_sideways:
                        await self._notify_sideways_closed(position, fill_price, pnl_usdt, "closed_sl")
                    else:
                        await self._notify_user(
                            f"🛑 <b>SL Hit</b>\n\n"
                            f"Symbol: {position.symbol}\n"
                            f"Entry: {position.entry_price:.4f}\n"
                            f"Exit: {fill_price:.4f}\n"
                            f"PnL: <b>{pnl_usdt:+.2f} USDT</b>"
                        )

                self.positions.pop(position.symbol, None)
        
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
    
    async def _save_position_to_db(self, position: ScalpingPosition, signal, order_id: str = ""):
        """Save position to database, including sideways metadata if applicable."""
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
                "order_id": order_id or "",
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

            res = s.table("autotrade_trades").insert(row).execute()
            return res.data[0]["id"] if getattr(res, "data", None) else None
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error saving position to DB: {e}")
            return None
    
    async def _update_position_closed(self, position: ScalpingPosition, close_price: float,
                                     pnl: float, close_reason: str) -> bool:
        """Update position in database when closed.
        Returns True only when this call successfully closed an OPEN row.
        """
        try:
            s = _client()
            open_rows = s.table("autotrade_trades").select("id").eq(
                "telegram_id", self.user_id
            ).eq("symbol", position.symbol).eq("status", "open").order("opened_at", desc=True).limit(1).execute()
            if not open_rows.data:
                logger.info(f"[Scalping:{self.user_id}] No open DB row to close for {position.symbol} (already closed)")
                return False

            trade_id = open_rows.data[0]["id"]
            res = s.table("autotrade_trades").update({
                "close_price": close_price,
                "pnl_usdt": pnl,
                "close_reason": close_reason,
                "status": close_reason,
                "closed_at": datetime.utcnow().isoformat(),
            }).eq("id", trade_id).eq("status", "open").execute()
            if not getattr(res, "data", None):
                logger.info(f"[Scalping:{self.user_id}] DB close skipped for {position.symbol} (race already closed)")
                return False
            return True
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error updating position in DB: {e}")
            return False
    
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
            
            await self._notify_user_once(
                dedupe_key=f"{reason}:{position.symbol}:{position.entry_price:.4f}",
                message=(
                    f"{label}\n\n"
                    f"Symbol: {position.symbol}\n"
                    f"Entry: {position.entry_price:.4f}\n"
                    f"Exit: {fill_price:.4f}\n"
                    f"PnL: <b>{pnl:+.2f} USDT</b>"
                ),
                ttl_sec=600,
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
    
    async def _notify_stackmentor_opened(
        self,
        position: ScalpingPosition,
        signal,
        levels,
        order_id: str = "-",
        trade_id: Optional[int] = None,
    ):
        """Notify user when StackMentor position opened.

        `levels` is a `StackMentorLevels` dataclass from app.trade_execution.
        """
        try:
            risk_amount = abs(position.entry_price - levels.sl) * position.quantity
            acc_result = await asyncio.to_thread(self.client.get_account_info)
            current_equity = 0.0
            if acc_result.get("success"):
                available = float(acc_result.get("available", 0) or 0)
                frozen = float(acc_result.get("frozen", 0) or 0)
                unrealized = float(acc_result.get("total_unrealized_pnl", 0) or 0)
                current_equity = available + frozen + unrealized
            risk_pct_equity = (risk_amount / current_equity * 100) if current_equity > 0 else None
            direction = "Long" if position.side.upper() in ("BUY", "LONG") else "Short"
            opened_at = datetime.utcnow().strftime("%d %b %Y %H:%M:%S UTC")
            order_id_text = escape(str(order_id or "-"))

            await self.bot.send_message(
                chat_id=self.notify_chat_id,
                text=(
                    "🤖 <b>Cryptomentor AI Autotrade</b>\n\n"
                    f"<b>Direction:</b> {direction}\n"
                    f"<b>Trading Pair:</b> {position.symbol}\n"
                    f"<b>Entry:</b> {_fmt_price(position.entry_price)}\n"
                    f"<b>TP:</b> {_fmt_price(levels.tp1)}\n"
                    f"<b>SL:</b> {_fmt_price(levels.sl)}\n"
                    f"<b>Risk PNL:</b> ${risk_amount:.2f}\n"
                    + (
                        f"<b>Risk % on equity:</b> {risk_pct_equity:.2f}%\n"
                        if risk_pct_equity is not None else
                        "<b>Risk % on equity:</b> N/A\n"
                    )
                    + f"<b>Order ID:</b> <code>{order_id_text}</code>\n"
                    + f"<b>Date and time:</b> {opened_at}"
                ),
                parse_mode='HTML',
                reply_markup=_trade_detail_keyboard(trade_id=trade_id, order_id=order_id, symbol=position.symbol),
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

    async def _notify_user_once(self, dedupe_key: str, message: str, ttl_sec: int = 600):
        """Best-effort in-memory dedupe for repeated close notifications."""
        now = time.time()
        last_sent = self._recent_close_notifications.get(dedupe_key, 0)
        if now - last_sent < ttl_sec:
            logger.info(f"[Scalping:{self.user_id}] Suppressed duplicate notification: {dedupe_key}")
            return
        self._recent_close_notifications[dedupe_key] = now
        await self._notify_user(message)

    async def _load_existing_positions(self):
        """Load open positions from database on startup to resume monitoring"""
        try:
            from app.supabase_repo import _client as _sc
            from app.trading_mode import ScalpingPosition
            from datetime import datetime
            
            s = _sc()
            res = s.table("autotrade_trades").select("*").eq(
                "telegram_id", self.user_id
            ).eq("status", "open").execute()
            
            if res.data:
                logger.info(f"[Scalping:{self.user_id}] Found {len(res.data)} open trades in DB. Resuming tracking...")
                for row in res.data:
                    symbol = row.get("symbol")
                    if not symbol or symbol in self.positions:
                        continue
                    
                    # Convert ISO string to Unix timestamp
                    opened_at_str = row.get("opened_at")
                    try:
                        if opened_at_str:
                            # Handle different ISO formats (Z vs +00:00)
                            if opened_at_str.endswith('Z'):
                                opened_at_str = opened_at_str.replace('Z', '+00:00')
                            dt = datetime.fromisoformat(opened_at_str)
                            opened_at = dt.timestamp()
                        else:
                            opened_at = time.time()
                    except Exception as parse_err:
                        logger.warning(f"[Scalping:{self.user_id}] Could not parse timestamp {opened_at_str}: {parse_err}")
                        opened_at = time.time()
                    
                    pos = ScalpingPosition(
                        user_id=self.user_id,
                        symbol=symbol,
                        side=row.get("side", "BUY"),
                        entry_price=float(row.get("entry_price", 0)),
                        quantity=float(row.get("quantity", 0)),
                        leverage=int(row.get("leverage", 10)),
                        tp_price=float(row.get("tp_price", 0)),
                        sl_price=float(row.get("sl_price", 0)),
                        opened_at=opened_at
                    )
                    
                    # Check if it was a sideways trade
                    if row.get("trade_subtype") == "sideways_scalp":
                        pos.is_sideways = True
                    
                    self.positions[symbol] = pos
                    logger.info(f"[Scalping:{self.user_id}] Resumed tracking for {symbol} (opened {int(time.time() - opened_at)}s ago)")
            
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Failed to load existing positions: {e}")
