
# app/providers/binance_client.py
from __future__ import annotations
from app.providers.binance_provider import get_price, fetch_klines, exchange_info, normalize_symbol
from app.providers.cmc_provider import get_global_stats  # re-export dari CMC
__all__ = ["get_price", "fetch_klines", "exchange_info", "normalize_symbol", "get_global_stats"]
