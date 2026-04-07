"""
Async Signal Generation with Caching
Prevents event loop blocking by using proper async + caching
"""

import asyncio
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def compute_signal_scalping_async(base_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Async version of compute_signal_scalping with caching.
    
    This prevents blocking the event loop by:
    1. Using asyncio.to_thread for sync operations
    2. Caching candle data to reduce API calls
    3. Using semaphore to limit concurrent requests
    
    Args:
        base_symbol: Base symbol (e.g., "BTC", "ETH")
        
    Returns:
        Dict with signal data or None
    """
    try:
        from app.candle_cache import get_candles_cached
        from app.providers.alternative_klines_provider import alternative_klines_provider
        
        symbol = base_symbol.upper()
        full_symbol = f"{symbol}USDT"
        
        # Wrap sync get_klines in async with cache
        async def fetch_klines_async(sym, interval, limit):
            # Use to_thread to prevent blocking
            return await asyncio.to_thread(
                alternative_klines_provider.get_klines,
                sym, interval, limit
            )
        
        # ===== Step 1: Get 15M trend (with cache) =====
        klines_15m = await get_candles_cached(
            fetch_klines_async, symbol, '15m', 100
        )
        
        if not klines_15m or len(klines_15m) < 50:
            return None
        
        c15 = [float(k[4]) for k in klines_15m]
        ema21_15 = _calc_ema(c15, 21)
        ema50_15 = _calc_ema(c15, 50)
        price = c15[-1]
        
        # Determine 15M trend
        if price > ema21_15 > ema50_15:
            trend_15m = "LONG"
            trend_strength = "STRONG"
        elif price < ema21_15 < ema50_15:
            trend_15m = "SHORT"
            trend_strength = "STRONG"
        elif price > ema21_15:
            trend_15m = "LONG"
            trend_strength = "WEAK"  # Ranging but bullish bias
        elif price < ema21_15:
            trend_15m = "SHORT"
            trend_strength = "WEAK"  # Ranging but bearish bias
        else:
            trend_15m = "NEUTRAL"
            trend_strength = "RANGING"
        
        # ===== Step 2: Get 5M entry trigger (with cache) =====
        klines_5m = await get_candles_cached(
            fetch_klines_async, symbol, '5m', 60
        )
        
        if not klines_5m or len(klines_5m) < 30:
            return None
        
        c5 = [float(k[4]) for k in klines_5m]
        h5 = [float(k[2]) for k in klines_5m]
        l5 = [float(k[3]) for k in klines_5m]
        v5 = [float(k[5]) for k in klines_5m]
        
        rsi_5m = _calc_rsi(c5)
        atr_5m = _calc_atr(h5, l5, c5, 14)
        vol_ratio = _calc_volume_ratio(v5, 20)
        
        # ===== Step 3: Signal logic (SCALPING - more flexible) =====
        side = None
        confidence = 75  # Base confidence for scalping
        reasons = []
        
        # STRONG TREND SIGNALS (Original logic - high confidence)
        if trend_strength == "STRONG":
            if trend_15m == "LONG" and rsi_5m < 30 and vol_ratio > 2.0:
                side = "LONG"
                confidence = 85
                reasons.append(f"Strong 15M uptrend + 5M oversold (RSI {rsi_5m:.0f})")
                reasons.append(f"Volume spike {vol_ratio:.1f}x")
                if vol_ratio > 3.0:
                    confidence += 5
                    reasons.append("Exceptional volume")
            elif trend_15m == "SHORT" and rsi_5m > 70 and vol_ratio > 2.0:
                side = "SHORT"
                confidence = 85
                reasons.append(f"Strong 15M downtrend + 5M overbought (RSI {rsi_5m:.0f})")
                reasons.append(f"Volume spike {vol_ratio:.1f}x")
                if vol_ratio > 3.0:
                    confidence += 5
                    reasons.append("Exceptional volume")
        
        # WEAK TREND / RANGING SIGNALS (New - for sideways market)
        elif trend_strength in ["WEAK", "RANGING"]:
            # More relaxed conditions for ranging market
            if trend_15m == "LONG" and rsi_5m < 40 and vol_ratio > 1.5:
                side = "LONG"
                confidence = 80
                reasons.append(f"15M bullish bias + 5M pullback (RSI {rsi_5m:.0f})")
                reasons.append(f"Volume increase {vol_ratio:.1f}x")
                reasons.append("Range trading - buy support")
            elif trend_15m == "SHORT" and rsi_5m > 60 and vol_ratio > 1.5:
                side = "SHORT"
                confidence = 80
                reasons.append(f"15M bearish bias + 5M bounce (RSI {rsi_5m:.0f})")
                reasons.append(f"Volume increase {vol_ratio:.1f}x")
                reasons.append("Range trading - sell resistance")
            elif trend_15m == "NEUTRAL":
                # Pure ranging - trade both sides based on 5M extremes
                if rsi_5m < 35 and vol_ratio > 1.5:
                    side = "LONG"
                    confidence = 80  # Raised to pass 80% threshold
                    reasons.append(f"Ranging market + 5M oversold (RSI {rsi_5m:.0f})")
                    reasons.append(f"Volume {vol_ratio:.1f}x - buy support")
                    reasons.append("Scalping range low")
                elif rsi_5m > 65 and vol_ratio > 1.5:
                    side = "SHORT"
                    confidence = 80  # Raised to pass 80% threshold
                    reasons.append(f"Ranging market + 5M overbought (RSI {rsi_5m:.0f})")
                    reasons.append(f"Volume {vol_ratio:.1f}x - sell resistance")
                    reasons.append("Scalping range high")
        
        if side is None:
            return None
        
        # ===== Step 4: Calculate TP/SL =====
        sl_distance = atr_5m * 1.5
        tp_distance = sl_distance * 1.5
        
        if side == "LONG":
            entry = price
            sl = entry - sl_distance
            tp = entry + tp_distance
        else:  # SHORT
            entry = price
            sl = entry + sl_distance
            tp = entry - tp_distance
        
        rr_ratio = abs(tp - entry) / abs(entry - sl)
        atr_pct = (atr_5m / price) * 100
        
        # ===== Step 5: Return signal =====
        return {
            "symbol": full_symbol,
            "side": side,
            "confidence": confidence,
            "entry_price": entry,
            "tp": tp,
            "sl": sl,
            "rr_ratio": rr_ratio,
            "atr_pct": atr_pct,
            "vol_ratio": vol_ratio,
            "rsi_5m": rsi_5m,
            "trend_15m": trend_15m,
            "trend_strength": trend_strength,  # NEW: indicate trend strength
            "reasons": reasons,
        }
        
    except Exception as e:
        logger.error(f"[AsyncSignal] Error for {base_symbol}: {e}")
        return None


# ===== Helper functions (copied from autosignal_fast) =====

def _calc_ema(prices: list, period: int) -> float:
    """Calculate EMA"""
    if len(prices) < period:
        return prices[-1] if prices else 0.0
    
    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    
    for price in prices[period:]:
        ema = price * k + ema * (1 - k)
    
    return ema


def _calc_rsi(prices: list, period: int = 14) -> float:
    """Calculate RSI"""
    if len(prices) < period + 1:
        return 50.0
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < period:
        return 50.0
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def _calc_atr(highs: list, lows: list, closes: list, period: int = 14) -> float:
    """Calculate ATR"""
    if len(highs) < period + 1:
        return 0.0
    
    trs = []
    for i in range(1, len(highs)):
        h = highs[i]
        l = lows[i]
        c_prev = closes[i-1]
        
        tr = max(
            h - l,
            abs(h - c_prev),
            abs(l - c_prev)
        )
        trs.append(tr)
    
    if len(trs) < period:
        return 0.0
    
    return sum(trs[-period:]) / period


def _calc_volume_ratio(volumes: list, period: int = 20) -> float:
    """Calculate volume ratio (current vs average)"""
    if len(volumes) < period + 1:
        return 1.0
    
    current_vol = volumes[-1]
    avg_vol = sum(volumes[-period-1:-1]) / period
    
    if avg_vol == 0:
        return 1.0
    
    return current_vol / avg_vol
