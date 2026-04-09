"""
SidewaysDetector — menentukan apakah kondisi market saat ini sideways atau trending.

Tiga metrik dengan voting (minimal 2 dari 3 harus terpenuhi untuk SIDEWAYS):
  - atr_relative_pct < 0.3  → vote sideways
  - ema_spread_pct   < 0.2  → vote sideways
  - range_width_pct  < 1.5  → vote sideways
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

MIN_CANDLES_5M  = 20
MIN_CANDLES_15M = 50
ATR_PERIOD      = 14


@dataclass
class SidewaysResult:
    is_sideways: bool
    atr_relative_pct: float   # ATR / price * 100
    ema_spread_pct: float     # |EMA21 - EMA50| / price * 100
    range_width_pct: float    # (max_high - min_low) dari 20 candle 5M / price * 100
    reason: str               # Alasan klasifikasi untuk logging


class SidewaysDetector:
    """Mendeteksi kondisi market sideways berdasarkan ATR, EMA spread, dan range width."""

    # Threshold klasifikasi
    ATR_THRESHOLD        = 0.3   # %
    EMA_SPREAD_THRESHOLD = 0.2   # %
    RANGE_WIDTH_THRESHOLD = 1.5  # %

    def detect(
        self,
        candles_5m: list,
        candles_15m: list,
        price: float,
    ) -> SidewaysResult:
        """
        Tentukan apakah market sedang sideways atau trending.

        Args:
            candles_5m:  List candle 5M (minimal 20). Setiap candle adalah dict
                         dengan key: 'open', 'high', 'low', 'close', 'volume'.
            candles_15m: List candle 15M (minimal 50).
            price:       Harga saat ini (digunakan sebagai denominator persentase).

        Returns:
            SidewaysResult dengan is_sideways=True jika salah satu kondisi terpenuhi.
        """
        # Validasi minimum candle
        if len(candles_5m) < MIN_CANDLES_5M:
            reason = f"Insufficient 5M candles: {len(candles_5m)} < {MIN_CANDLES_5M}"
            logger.warning(f"[SidewaysDetector] {reason}")
            return SidewaysResult(
                is_sideways=False,
                atr_relative_pct=0.0,
                ema_spread_pct=0.0,
                range_width_pct=0.0,
                reason=reason,
            )

        if len(candles_15m) < MIN_CANDLES_15M:
            reason = f"Insufficient 15M candles: {len(candles_15m)} < {MIN_CANDLES_15M}"
            logger.warning(f"[SidewaysDetector] {reason}")
            return SidewaysResult(
                is_sideways=False,
                atr_relative_pct=0.0,
                ema_spread_pct=0.0,
                range_width_pct=0.0,
                reason=reason,
            )

        atr_relative_pct = self._calc_atr_relative_pct(candles_5m, price)
        ema_spread_pct   = self._calc_ema_spread_pct(candles_15m, price)
        range_width_pct  = self._calc_range_width_pct(candles_5m[-20:], price)

        sideways_votes = []
        if atr_relative_pct < self.ATR_THRESHOLD:
            sideways_votes.append(f"ATR_relative={atr_relative_pct:.4f}% < {self.ATR_THRESHOLD}%")
        if ema_spread_pct < self.EMA_SPREAD_THRESHOLD:
            sideways_votes.append(f"EMA_spread={ema_spread_pct:.4f}% < {self.EMA_SPREAD_THRESHOLD}%")
        if range_width_pct < self.RANGE_WIDTH_THRESHOLD:
            sideways_votes.append(f"Range_width={range_width_pct:.4f}% < {self.RANGE_WIDTH_THRESHOLD}%")

        # Butuh minimal 2 dari 3 kondisi untuk dianggap SIDEWAYS
        is_sideways = len(sideways_votes) >= 2
        sideways_reasons = sideways_votes

        if is_sideways:
            reason = "SIDEWAYS: " + "; ".join(sideways_reasons)
        else:
            reason = (
                f"TRENDING: ATR={atr_relative_pct:.4f}% EMA_spread={ema_spread_pct:.4f}% "
                f"Range={range_width_pct:.4f}%"
            )

        logger.info(
            f"[SidewaysDetector] {reason} | "
            f"atr={atr_relative_pct:.4f}% ema_spread={ema_spread_pct:.4f}% "
            f"range={range_width_pct:.4f}%"
        )

        return SidewaysResult(
            is_sideways=is_sideways,
            atr_relative_pct=atr_relative_pct,
            ema_spread_pct=ema_spread_pct,
            range_width_pct=range_width_pct,
            reason=reason,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _calc_atr_relative_pct(self, candles: list, price: float) -> float:
        """Hitung 14-period ATR dari candles lalu bagi dengan price * 100."""
        if len(candles) < ATR_PERIOD + 1:
            # Tidak cukup candle untuk ATR penuh; gunakan semua yang ada
            period = len(candles) - 1
        else:
            period = ATR_PERIOD

        true_ranges = []
        for i in range(1, period + 1):
            idx = len(candles) - period - 1 + i  # ambil period candle terakhir
            c = candles[idx]
            prev_close = candles[idx - 1]['close']
            high = c['high']
            low  = c['low']
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low  - prev_close),
            )
            true_ranges.append(tr)

        if not true_ranges or price == 0:
            return 0.0

        atr = sum(true_ranges) / len(true_ranges)
        return (atr / price) * 100

    def _calc_ema(self, values: list, period: int) -> float:
        """Hitung EMA dari list nilai menggunakan formula standar."""
        if not values:
            return 0.0
        k = 2 / (period + 1)
        ema = values[0]
        for v in values[1:]:
            ema = v * k + ema * (1 - k)
        return ema

    def _calc_ema_spread_pct(self, candles: list, price: float) -> float:
        """Hitung |EMA21 - EMA50| dari candles 15M lalu bagi dengan price * 100."""
        closes = [c['close'] for c in candles]
        ema21 = self._calc_ema(closes, 21)
        ema50 = self._calc_ema(closes, 50)
        if price == 0:
            return 0.0
        return (abs(ema21 - ema50) / price) * 100

    def _calc_range_width_pct(self, candles: list, price: float) -> float:
        """Hitung (max_high - min_low) dari candles lalu bagi dengan price * 100."""
        if not candles or price == 0:
            return 0.0
        max_high = max(c['high'] for c in candles)
        min_low  = min(c['low']  for c in candles)
        return ((max_high - min_low) / price) * 100
