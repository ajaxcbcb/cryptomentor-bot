"""
RangeAnalyzer: Identifies valid Support and Resistance levels from swing highs/lows.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RangeResult:
    support: float
    resistance: float
    range_width_pct: float
    support_touches: int
    resistance_touches: int


class RangeAnalyzer:
    TOLERANCE_PCT = 0.0015  # 0.15% clustering tolerance
    MIN_TOUCHES = 2
    MIN_RANGE_PCT = 0.005   # 0.5%
    MAX_RANGE_PCT = 0.040   # 4.0% (expanded from 3.0% for more opportunities)

    def analyze(self, candles_5m: list, price: float) -> Optional[RangeResult]:
        """
        Identify valid Support and Resistance levels from the last 30 candles.

        Algorithm:
        a. Collect swing highs: candle[i].high > candle[i-1].high AND candle[i].high > candle[i+1].high
        b. Collect swing lows: candle[i].low < candle[i-1].low AND candle[i].low < candle[i+1].low
        c. Cluster levels within TOLERANCE_PCT into one level (use average price in cluster)
        d. Count touches per cluster: a candle "touches" a level if its high or low is within TOLERANCE_PCT
        e. Keep only clusters with touches >= MIN_TOUCHES
        f. Resistance = highest valid cluster ABOVE current price
        g. Support = lowest valid cluster BELOW current price
        h. If no valid support OR no valid resistance: return None
        i. Calculate range_width_pct = (resistance - support) / price * 100
        j. If range_width_pct < 0.5% OR > 4.0%: return None
        k. Return RangeResult
        """
        candles = candles_5m[-30:] if len(candles_5m) >= 30 else candles_5m
        if len(candles) < 3:
            return None

        # Step a & b: Collect swing highs and swing lows (skip first and last candle)
        raw_levels = []
        for i in range(1, len(candles) - 1):
            c_prev = candles[i - 1]
            c_curr = candles[i]
            c_next = candles[i + 1]

            # Swing high
            if c_curr['high'] > c_prev['high'] and c_curr['high'] > c_next['high']:
                raw_levels.append(c_curr['high'])

            # Swing low
            if c_curr['low'] < c_prev['low'] and c_curr['low'] < c_next['low']:
                raw_levels.append(c_curr['low'])

        if not raw_levels:
            return None

        # Step c: Cluster levels within TOLERANCE_PCT
        raw_levels.sort()
        clusters = self._cluster_levels(raw_levels)

        # Step d & e: Count touches per cluster, keep only clusters with >= MIN_TOUCHES
        valid_clusters = []
        for cluster_price in clusters:
            touches = self._count_touches(candles, cluster_price)
            if touches >= self.MIN_TOUCHES:
                valid_clusters.append((cluster_price, touches))

        if not valid_clusters:
            return None

        # Step f: Resistance = highest valid cluster ABOVE current price
        resistance_candidates = [(p, t) for p, t in valid_clusters if p > price]
        # Step g: Support = lowest valid cluster BELOW current price
        support_candidates = [(p, t) for p, t in valid_clusters if p < price]

        # Step h: If no valid support OR no valid resistance: return None
        if not resistance_candidates or not support_candidates:
            return None

        resistance, resistance_touches = min(resistance_candidates, key=lambda x: x[0])
        support, support_touches = max(support_candidates, key=lambda x: x[0])

        # Step i: Calculate range_width_pct
        range_width_pct = (resistance - support) / price * 100

        # Step j: Validate range width
        if range_width_pct < self.MIN_RANGE_PCT * 100 or range_width_pct > self.MAX_RANGE_PCT * 100:
            return None

        # Step k: Return RangeResult
        return RangeResult(
            support=support,
            resistance=resistance,
            range_width_pct=range_width_pct,
            support_touches=support_touches,
            resistance_touches=resistance_touches,
        )

    def _cluster_levels(self, sorted_levels: list) -> list:
        """
        Cluster price levels that are within TOLERANCE_PCT of each other.
        Returns a list of cluster average prices.
        """
        if not sorted_levels:
            return []

        clusters = []
        current_cluster = [sorted_levels[0]]

        for level in sorted_levels[1:]:
            # Check if this level is within TOLERANCE_PCT of the cluster average
            cluster_avg = sum(current_cluster) / len(current_cluster)
            if abs(level - cluster_avg) / cluster_avg <= self.TOLERANCE_PCT:
                current_cluster.append(level)
            else:
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [level]

        # Don't forget the last cluster
        clusters.append(sum(current_cluster) / len(current_cluster))
        return clusters

    def _count_touches(self, candles: list, level: float) -> int:
        """
        Count how many candles touch a level (high or low within TOLERANCE_PCT).
        """
        count = 0
        for candle in candles:
            high_touch = abs(candle['high'] - level) / level <= self.TOLERANCE_PCT
            low_touch = abs(candle['low'] - level) / level <= self.TOLERANCE_PCT
            if high_touch or low_touch:
                count += 1
        return count
