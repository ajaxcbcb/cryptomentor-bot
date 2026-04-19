from __future__ import annotations

from app.config import thresholds
from app.core.models import Candle, EntryZone, EntryZoneResult


def detect_order_block(candles: list[Candle], direction: str, config: object | None = None) -> EntryZone | None:
    if len(candles) < 3:
        return None
    ref = candles[-2]
    if direction == "LONG":
        low = min(ref.open, ref.close)
        high = max(ref.open, ref.close)
    else:
        low = min(ref.open, ref.close)
        high = max(ref.open, ref.close)
    return EntryZone(zone_type="OB", low=low, high=high)


def detect_fair_value_gap(candles: list[Candle], direction: str, config: object | None = None) -> EntryZone | None:
    if len(candles) < 3:
        return None
    c1, c2, c3 = candles[-3], candles[-2], candles[-1]
    if direction == "LONG" and c3.low > c1.high:
        return EntryZone(zone_type="FVG", low=c1.high, high=c3.low)
    if direction == "SHORT" and c3.high < c1.low:
        return EntryZone(zone_type="FVG", low=c3.high, high=c1.low)
    return None


def distance_to_zone(current_price: float, zone: EntryZone | None) -> float | None:
    if not zone or zone.low is None or zone.high is None:
        return None
    if zone.low <= current_price <= zone.high:
        return 0.0
    if current_price < zone.low:
        return (zone.low - current_price) / max(current_price, 1e-9)
    return (current_price - zone.high) / max(current_price, 1e-9)


def is_zone_tapped(current_price: float, zone: EntryZone | None) -> bool:
    d = distance_to_zone(current_price, zone)
    return d == 0.0


def detect_entry_zone(candles: list[Candle], direction: str, config: object | None = None) -> EntryZoneResult:
    if len(candles) < 3:
        return EntryZoneResult(exists=False, reasons=["insufficient_candles"])
    current = candles[-1].close

    fvg = detect_fair_value_gap(candles, direction, config)
    ob = detect_order_block(candles, direction, config)
    preferred = fvg or ob
    if not preferred:
        return EntryZoneResult(exists=False, reasons=["no_zone_detected"])

    dist = distance_to_zone(current, preferred)
    tapped = is_zone_tapped(current, preferred)
    near_tap = dist is not None and dist <= thresholds.ZONE_NEAR_PCT

    return EntryZoneResult(
        exists=True,
        preferred_zone=preferred,
        tapped=tapped,
        near_tap=near_tap,
        distance_pct=dist,
        reasons=[f"zone_detected_{preferred.zone_type.lower()}"]
    )
