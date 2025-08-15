
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.env import COINAPI_API_KEY
from app.providers.http import fetch_json

BASE = "https://rest.coinapi.io/v1"

def _headers():
    if not COINAPI_API_KEY:
        raise RuntimeError("COINAPI_API_KEY belum di-set")
    return {"X-CoinAPI-Key": COINAPI_API_KEY}

def _symbol(coin: str, quote="USDT"):
    s = coin.upper()
    if s.endswith(quote):  # jika sudah format pair
        return s
    return f"{s}{quote}"

async def get_price_spot(coin: str) -> float:
    # Gunakan /exchangerate/{asset_id_base}/{asset_id_quote}
    url = f"{BASE}/exchangerate/{coin.upper()}/USDT"
    data = await fetch_json(url, headers=_headers(), cache_key=f"caprice:{coin}", cache_ttl=10)
    return float(data["rate"])

async def get_ohlcv(coin: str, period="5MIN", limit=200) -> List[Dict]:
    # /ohlcv/{symbol}/history?period_id=5MIN&limit=200
    symbol = f"{coin.upper()}/USDT"
    url = f"{BASE}/ohlcv/{symbol}/history"
    params = {"period_id": period, "limit": limit}
    data = await fetch_json(url, headers=_headers(), params=params, cache_key=f"caohlcv:{coin}:{period}", cache_ttl=20)
    # Normalisasi keys -> open, high, low, close, volume, time
    rows = []
    for d in data:
        rows.append({
            "time": d.get("time_period_end"),
            "open": float(d["price_open"]),
            "high": float(d["price_high"]),
            "low": float(d["price_low"]),
            "close": float(d["price_close"]),
            "volume": float(d.get("volume_traded", 0.0)),
        })
    return rows
