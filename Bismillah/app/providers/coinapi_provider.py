
# app/providers/coinapi_provider.py
"""
Compat layer: mempertahankan API 'CoinAPI' yang dipakai command/service,
namun implementasinya dialihkan ke Binance REST (Spot & Futures).
JANGAN ubah command atau DB.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.providers.binance_provider import (
    get_price as _bz_price,
    fetch_klines as _bz_klines,
    exchange_info as _bz_exchange_info,
    normalize_symbol as _bz_normalize,
)

# ---- Fungsi "CoinAPI" lama yang sekarang diarahkan ke Binance ----

def normalize_symbol(symbol: str) -> str:
    return _bz_normalize(symbol)

def get_price(symbol: str) -> float:
    """Harga spot (compat)."""
    return _bz_price(symbol, futures=False)

def get_price_spot(symbol: str) -> float:
    return _bz_price(symbol, futures=False)

def get_price_futures(symbol: str) -> float:
    return _bz_price(symbol, futures=True)

def get_ohlcv(symbol: str, interval: str, limit: int = 200) -> List[List[Any]]:
    """OHLCV spot."""
    return _bz_klines(symbol, interval=interval, limit=limit, futures=False)

def get_ohlcv_futures(symbol: str, interval: str, limit: int = 200) -> List[List[Any]]:
    """OHLCV futures (USDT-M)."""
    return _bz_klines(symbol, interval=interval, limit=limit, futures=True)

def fetch_klines(symbol: str, interval: str, limit: int = 200) -> List[List[Any]]:
    return _bz_klines(symbol, interval=interval, limit=limit, futures=False)

def fetch_klines_futures(symbol: str, interval: str, limit: int = 200) -> List[List[Any]]:
    return _bz_klines(symbol, interval=interval, limit=limit, futures=True)

def exchange_info(symbol: Optional[str] = None, futures: bool = False) -> Dict[str, Any]:
    return _bz_exchange_info(symbol, futures=futures)

def get_ohlcv_multi_timeframe(symbol: str, intervals: List[str], limit: int = 200, futures: bool = False) -> Dict[str, List[List[Any]]]:
    out: Dict[str, List[List[Any]]] = {}
    for itv in intervals:
        out[itv] = _bz_klines(symbol, interval=itv, limit=limit, futures=futures)
    return out

def get_latest_price(symbol: str) -> float:
    """Alias untuk get_price."""
    return get_price(symbol)

def get_ticker(symbol: str) -> Dict[str, Any]:
    """Return ticker data dengan price."""
    price = get_price(symbol)
    return {"price": price, "symbol": normalize_symbol(symbol)}
