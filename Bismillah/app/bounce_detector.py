"""
BounceDetector — confirms price is bouncing from a S/R level
based on wick analysis of the last candle.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BounceResult:
    direction: str    # "LONG" or "SHORT"
    level: float      # S/R level that was bounced from
    wick_ratio: float # wick_length / body_length
    reason: str       # description for signal reasons


class BounceDetector:
    PROXIMITY_PCT = 0.004  # 0.4% proximity threshold (relaxed from 0.2% for tight sideways market)

    def detect(
        self,
        last_candle: dict,
        support: float,
        resistance: float,
        price: float,
    ) -> Optional[BounceResult]:
        """
        Detect a bounce from support (LONG) or resistance (SHORT).

        Args:
            last_candle: dict with keys 'open', 'high', 'low', 'close'
            support: support level
            resistance: resistance level
            price: current price

        Returns:
            BounceResult if bounce confirmed, None otherwise
        """
        open_ = float(last_candle["open"])
        high = float(last_candle["high"])
        low = float(last_candle["low"])
        close = float(last_candle["close"])

        body = abs(close - open_)
        upper_wick = high - max(open_, close)
        lower_wick = min(open_, close) - low

        # Doji — no meaningful bounce signal
        if body == 0:
            return None

        # Bounce LONG from support
        near_support = abs(price - support) / support < self.PROXIMITY_PCT
        if near_support and lower_wick > body:
            wick_ratio = lower_wick / body
            return BounceResult(
                direction="LONG",
                level=support,
                wick_ratio=round(wick_ratio, 4),
                reason=f"Bounce LONG from support {support:.4f} | lower_wick/body={wick_ratio:.2f}",
            )

        # Bounce SHORT from resistance
        near_resistance = abs(price - resistance) / resistance < self.PROXIMITY_PCT
        if near_resistance and upper_wick > body:
            wick_ratio = upper_wick / body
            return BounceResult(
                direction="SHORT",
                level=resistance,
                wick_ratio=round(wick_ratio, 4),
                reason=f"Bounce SHORT from resistance {resistance:.4f} | upper_wick/body={wick_ratio:.2f}",
            )

        return None
