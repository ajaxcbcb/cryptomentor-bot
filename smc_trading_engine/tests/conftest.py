from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.models import Candle


FIXTURES = Path(__file__).parent / "fixtures"


def load_candles(name: str) -> list[Candle]:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return [Candle(**row) for row in payload]


@pytest.fixture
def trending_candles() -> list[Candle]:
    return load_candles("candles_trending.json")


@pytest.fixture
def sideways_candles() -> list[Candle]:
    return load_candles("candles_sideways.json")


@pytest.fixture
def sweep_candles() -> list[Candle]:
    return load_candles("candles_sweep.json")


@pytest.fixture
def bos_candles() -> list[Candle]:
    return load_candles("candles_bos.json")


@pytest.fixture
def fvg_candles() -> list[Candle]:
    return load_candles("candles_fvg.json")


@pytest.fixture
def dead_trade_candles() -> list[Candle]:
    return load_candles("candles_dead_trade.json")
