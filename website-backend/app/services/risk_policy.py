from __future__ import annotations

from dataclasses import dataclass
from typing import Any


AUTO_RISK_MIN_PCT = 0.25
AUTO_RISK_MAX_PCT = 10.0
ONE_CLICK_RISK_MIN_PCT = 0.25
ONE_CLICK_RISK_MAX_PCT = 10.0
HIGH_RISK_WARN_PCT = 5.0
LOW_EQUITY_THRESHOLD_USD = 30.0
LOW_EQUITY_MIN_RISK_PCT = 3.0


@dataclass(frozen=True)
class RiskBand:
    key: str
    label: str
    min_inclusive: float
    max_exclusive: float | None


RISK_BANDS = (
    RiskBand("conservative", "Conservative", 0.0, 2.0),
    RiskBand("moderate", "Moderate", 2.0, 5.0),
    RiskBand("high", "High Risk", 5.0, 10.0),
    RiskBand("extreme", "Max Risk", 10.0, None),
)


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def auto_risk_min_by_equity(equity: Any = None) -> float:
    eq = _to_float(equity, 0.0)
    if eq > 0 and eq < LOW_EQUITY_THRESHOLD_USD:
        return max(AUTO_RISK_MIN_PCT, LOW_EQUITY_MIN_RISK_PCT)
    return AUTO_RISK_MIN_PCT


def clamp_auto_risk(value: Any, default: float = 3.0, equity: Any = None) -> float:
    risk = _to_float(value, default)
    min_risk = auto_risk_min_by_equity(equity)
    return max(min_risk, min(AUTO_RISK_MAX_PCT, risk))


def clamp_one_click_risk(value: Any, default: float = 1.0) -> float:
    risk = _to_float(value, default)
    return max(ONE_CLICK_RISK_MIN_PCT, min(ONE_CLICK_RISK_MAX_PCT, risk))


def is_high_risk(risk_pct: float) -> bool:
    return float(risk_pct) > HIGH_RISK_WARN_PCT


def risk_band(risk_pct: float, all_in: bool = False) -> RiskBand:
    if all_in or float(risk_pct) >= ONE_CLICK_RISK_MAX_PCT:
        return RISK_BANDS[-1]
    v = float(risk_pct)
    for band in RISK_BANDS[:-1]:
        if v >= band.min_inclusive and (band.max_exclusive is None or v < band.max_exclusive):
            return band
    return RISK_BANDS[0]
