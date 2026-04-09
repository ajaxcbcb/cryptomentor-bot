"""
MicroMomentumDetector — Sideways market scalping via 1M/3M momentum shift.

Strategy:
- Pakai 1M candles untuk detect EMA crossover (EMA5 vs EMA13)
- Konfirmasi dengan 3M candles: volume spike + candle direction
- Filter dengan 5M range: entry hanya jika ada ruang ke S/R berikutnya
- Target: 0.3-0.8% move dalam 5-15 menit
"""

import logging
from dataclasses import dataclass
from typing import Optional, List

logger = logging.getLogger(__name__)


@dataclass
class MomentumSignal:
    direction: str        # "LONG" or "SHORT"
    entry_price: float
    tp_price: float
    sl_price: float
    rr_ratio: float
    confidence: int       # 60-90
    reason: str


class MicroMomentumDetector:
    """
    Detects momentum shifts in sideways market using 1M/3M timeframes.
    
    Entry logic:
    1. EMA5 crosses EMA13 on 1M (fresh cross within last 2 candles)
    2. RSI 1M: 40-60 range (not overbought/oversold) with momentum direction
    3. 3M volume: current candle volume > 1.3x average (confirmation)
    4. 3M candle body direction matches signal
    5. 5M: price has room to move (not at S/R boundary)
    """

    EMA_FAST = 5
    EMA_SLOW = 13
    RSI_PERIOD = 9       # Shorter RSI for 1M
    MIN_VOLUME_RATIO = 1.3
    MIN_ROOM_PCT = 0.15  # Minimum 0.15% room to next S/R

    def detect(
        self,
        candles_1m: List[dict],
        candles_3m: List[dict],
        candles_5m: List[dict],
        price: float,
        support: Optional[float] = None,
        resistance: Optional[float] = None,
    ) -> Optional[MomentumSignal]:
        """
        Detect momentum shift signal.
        
        Args:
            candles_1m: 1-minute candles (min 20)
            candles_3m: 3-minute candles (min 10)
            candles_5m: 5-minute candles (min 20)
            price: current price
            support: optional support level from RangeAnalyzer
            resistance: optional resistance level from RangeAnalyzer
        
        Returns:
            MomentumSignal or None
        """
        if len(candles_1m) < 20 or len(candles_3m) < 10 or len(candles_5m) < 20:
            return None

        if price <= 0:
            return None

        # Step 1: EMA crossover on 1M
        ema_fast = self._ema([c['close'] for c in candles_1m], self.EMA_FAST)
        ema_slow = self._ema([c['close'] for c in candles_1m], self.EMA_SLOW)

        # Check previous candle EMAs for fresh cross
        ema_fast_prev = self._ema([c['close'] for c in candles_1m[:-1]], self.EMA_FAST)
        ema_slow_prev = self._ema([c['close'] for c in candles_1m[:-1]], self.EMA_SLOW)

        bullish_cross = ema_fast > ema_slow and ema_fast_prev <= ema_slow_prev
        bearish_cross = ema_fast < ema_slow and ema_fast_prev >= ema_slow_prev

        # Also accept: EMA already crossed within last 2 candles (momentum continuation)
        if not bullish_cross and not bearish_cross:
            ema_fast_2 = self._ema([c['close'] for c in candles_1m[:-2]], self.EMA_FAST)
            ema_slow_2 = self._ema([c['close'] for c in candles_1m[:-2]], self.EMA_SLOW)
            bullish_cross = ema_fast > ema_slow and ema_fast_2 <= ema_slow_2
            bearish_cross = ema_fast < ema_slow and ema_fast_2 >= ema_slow_2

        if not bullish_cross and not bearish_cross:
            return None

        direction = "LONG" if bullish_cross else "SHORT"

        # Step 2: RSI 1M filter — must be in momentum zone
        rsi = self._rsi([c['close'] for c in candles_1m], self.RSI_PERIOD)
        if direction == "LONG" and not (35 <= rsi <= 65):
            logger.debug(f"[MicroMomentum] LONG rejected: RSI {rsi:.1f} out of range")
            return None
        if direction == "SHORT" and not (35 <= rsi <= 65):
            logger.debug(f"[MicroMomentum] SHORT rejected: RSI {rsi:.1f} out of range")
            return None

        # RSI momentum bonus
        rsi_bonus = 0
        if direction == "LONG" and rsi > 50:
            rsi_bonus = 5
        elif direction == "SHORT" and rsi < 50:
            rsi_bonus = 5

        # Step 3: 3M volume confirmation
        volumes_3m = [c.get('volume', 0) for c in candles_3m[-11:-1]]
        avg_vol_3m = sum(volumes_3m) / len(volumes_3m) if volumes_3m else 0
        curr_vol_3m = candles_3m[-1].get('volume', 0)
        vol_ratio = curr_vol_3m / avg_vol_3m if avg_vol_3m > 0 else 0

        if vol_ratio < self.MIN_VOLUME_RATIO:
            logger.debug(f"[MicroMomentum] Rejected: 3M volume ratio {vol_ratio:.2f} < {self.MIN_VOLUME_RATIO}")
            return None

        vol_bonus = 5 if vol_ratio > 2.0 else 0

        # Step 4: 3M candle body direction matches signal
        last_3m = candles_3m[-1]
        body_bullish = last_3m['close'] > last_3m['open']
        body_bearish = last_3m['close'] < last_3m['open']

        if direction == "LONG" and not body_bullish:
            logger.debug(f"[MicroMomentum] LONG rejected: 3M candle bearish")
            return None
        if direction == "SHORT" and not body_bearish:
            logger.debug(f"[MicroMomentum] SHORT rejected: 3M candle bullish")
            return None

        # Step 5: Check room to move (if S/R available)
        room_bonus = 0
        if support and resistance:
            room_to_resistance = (resistance - price) / price * 100
            room_to_support = (price - support) / price * 100

            if direction == "LONG":
                if room_to_resistance < self.MIN_ROOM_PCT:
                    logger.debug(f"[MicroMomentum] LONG rejected: only {room_to_resistance:.3f}% room to resistance")
                    return None
                if room_to_resistance > 0.5:
                    room_bonus = 5
            else:
                if room_to_support < self.MIN_ROOM_PCT:
                    logger.debug(f"[MicroMomentum] SHORT rejected: only {room_to_support:.3f}% room to support")
                    return None
                if room_to_support > 0.5:
                    room_bonus = 5

        # Step 6: Calculate ATR from 5M for TP/SL
        atr_5m = self._atr([c for c in candles_5m[-15:]], price)
        if atr_5m <= 0:
            atr_5m = price * 0.002  # fallback 0.2%

        # TP/SL: tight for micro-scalp
        # SL = 0.8x ATR, TP = 1.5x SL (R:R 1:1.5 minimum)
        sl_dist = atr_5m * 0.8
        tp_dist = sl_dist * 1.8  # R:R 1:1.8

        if direction == "LONG":
            tp = price + tp_dist
            sl = price - sl_dist
            # Cap TP at resistance if available
            if resistance and tp > resistance * 0.998:
                tp = resistance * 0.995
                tp_dist = tp - price
        else:
            tp = price - tp_dist
            sl = price + sl_dist
            # Cap TP at support if available
            if support and tp < support * 1.002:
                tp = support * 1.005
                tp_dist = price - tp

        # Recalculate R:R
        rr = tp_dist / sl_dist if sl_dist > 0 else 0
        if rr < 1.2:
            logger.debug(f"[MicroMomentum] Rejected: R:R {rr:.2f} < 1.2")
            return None

        # Confidence score
        confidence = 62 + rsi_bonus + vol_bonus + room_bonus
        confidence = min(88, confidence)

        cross_type = "EMA5×EMA13 bullish cross" if direction == "LONG" else "EMA5×EMA13 bearish cross"
        reason = (
            f"1M {cross_type} | RSI={rsi:.0f} | "
            f"3M vol={vol_ratio:.1f}x avg | "
            f"ATR={atr_5m/price*100:.3f}% | R:R=1:{rr:.1f}"
        )

        logger.info(
            f"[MicroMomentum] {direction} signal: entry={price:.4f} "
            f"tp={tp:.4f} sl={sl:.4f} conf={confidence}% | {reason}"
        )

        return MomentumSignal(
            direction=direction,
            entry_price=price,
            tp_price=round(tp, 6),
            sl_price=round(sl, 6),
            rr_ratio=round(rr, 2),
            confidence=confidence,
            reason=reason,
        )

    # ── Helpers ──────────────────────────────────────────────────────

    def _ema(self, values: list, period: int) -> float:
        if len(values) < period:
            return values[-1] if values else 0.0
        k = 2 / (period + 1)
        ema = sum(values[:period]) / period
        for v in values[period:]:
            ema = v * k + ema * (1 - k)
        return ema

    def _rsi(self, closes: list, period: int) -> float:
        if len(closes) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _atr(self, candles: list, price: float) -> float:
        if len(candles) < 2:
            return price * 0.002
        trs = []
        for i in range(1, len(candles)):
            h = candles[i]['high']
            l = candles[i]['low']
            pc = candles[i - 1]['close']
            trs.append(max(h - l, abs(h - pc), abs(l - pc)))
        return sum(trs) / len(trs) if trs else price * 0.002
