"""
RSIDivergenceDetector — detects bullish/bearish RSI divergence
over a 10-candle lookback window using Wilder's smoothing.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class DivergenceResult:
    detected: bool
    divergence_type: str  # "bullish", "bearish", or "none"
    confidence_bonus: int  # 10 if detected, 0 otherwise
    reason: str


class RSIDivergenceDetector:
    LOOKBACK = 10
    RSI_PERIOD = 14

    def _calculate_rsi_series(self, closes: List[float]) -> List[float]:
        """
        Calculate RSI values using Wilder's smoothing.

        Requires at least RSI_PERIOD + 1 closes.
        Returns a list of RSI values (one per close after the initial period).
        """
        period = self.RSI_PERIOD
        if len(closes) < period + 1:
            return []

        gains = []
        losses = []
        for i in range(1, period + 1):
            diff = closes[i] - closes[i - 1]
            gains.append(max(diff, 0.0))
            losses.append(max(-diff, 0.0))

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        rsi_values = []

        def _rsi(ag, al):
            if al == 0:
                return 100.0
            rs = ag / al
            return 100.0 - (100.0 / (1.0 + rs))

        rsi_values.append(_rsi(avg_gain, avg_loss))

        for i in range(period + 1, len(closes)):
            diff = closes[i] - closes[i - 1]
            gain = max(diff, 0.0)
            loss = max(-diff, 0.0)
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            rsi_values.append(_rsi(avg_gain, avg_loss))

        return rsi_values

    def detect(self, candles_5m: list, direction: str) -> DivergenceResult:
        """
        Detect RSI divergence over the last LOOKBACK candles.

        Args:
            candles_5m: list of candle dicts with at least 'close' key.
                        Requires minimum 24 candles (14 for RSI + 10 lookback).
            direction: "LONG" or "SHORT"

        Returns:
            DivergenceResult
        """
        min_candles = self.RSI_PERIOD + self.LOOKBACK
        if len(candles_5m) < min_candles:
            return DivergenceResult(
                detected=False,
                divergence_type="none",
                confidence_bonus=0,
                reason="Insufficient candles",
            )

        # We need RSI for candle[-11] and candle[-1].
        # To compute RSI at candle[-11] we need 14 candles before it.
        # Total closes needed: 14 (warmup) + 10 (lookback) + 1 (current) = 25
        # We use the last (RSI_PERIOD + LOOKBACK + 1) closes.
        needed = self.RSI_PERIOD + self.LOOKBACK + 1
        closes = [float(c["close"]) for c in candles_5m[-needed:]]

        rsi_series = self._calculate_rsi_series(closes)
        # rsi_series[0]  → RSI at closes[RSI_PERIOD]  (= candle at index RSI_PERIOD in our slice)
        # rsi_series[-1] → RSI of the last close
        # rsi_series[-11] → RSI 10 candles ago

        if len(rsi_series) < self.LOOKBACK + 1:
            return DivergenceResult(
                detected=False,
                divergence_type="none",
                confidence_bonus=0,
                reason="Insufficient RSI values computed",
            )

        rsi_now = rsi_series[-1]
        rsi_10_ago = rsi_series[-(self.LOOKBACK + 1)]

        price_now = closes[-1]
        price_10_ago = closes[-(self.LOOKBACK + 1)]

        # Bullish divergence: lower low in price, higher low in RSI
        if price_now < price_10_ago and rsi_now > rsi_10_ago:
            return DivergenceResult(
                detected=True,
                divergence_type="bullish",
                confidence_bonus=10,
                reason=(
                    f"Bullish divergence: price {price_10_ago:.4f}→{price_now:.4f} "
                    f"(lower low), RSI {rsi_10_ago:.2f}→{rsi_now:.2f} (higher low)"
                ),
            )

        # Bearish divergence: higher high in price, lower high in RSI
        if price_now > price_10_ago and rsi_now < rsi_10_ago:
            return DivergenceResult(
                detected=True,
                divergence_type="bearish",
                confidence_bonus=10,
                reason=(
                    f"Bearish divergence: price {price_10_ago:.4f}→{price_now:.4f} "
                    f"(higher high), RSI {rsi_10_ago:.2f}→{rsi_now:.2f} (lower high)"
                ),
            )

        return DivergenceResult(
            detected=False,
            divergence_type="none",
            confidence_bonus=0,
            reason=(
                f"No divergence: price {price_10_ago:.4f}→{price_now:.4f}, "
                f"RSI {rsi_10_ago:.2f}→{rsi_now:.2f}"
            ),
        )
