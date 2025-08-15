
import os
import re
from app.providers.http import fetch_json

KEY = os.getenv("COINAPI_API_KEY")
BASE = "https://rest.coinapi.io/v1"

def _hdr():
    if not KEY:
        raise RuntimeError("COINAPI_API_KEY empty")
    return {"X-CoinAPI-Key": KEY}

_CACHE = {}

async def resolve_symbol_id(coin: str, kind: str) -> str | None:
    # kind: "spot"|"perp"
    k = (coin.upper(), kind)
    if k in _CACHE:
        return _CACHE[k]
    
    data = await fetch_json(f"{BASE}/symbols", headers=_hdr(),
                            params={"filter_asset_id": coin.upper()},
                            cache_key=f"ca:symbols:{coin}", cache_ttl=600)
    
    # pilih USDT + SPOT/PERP, prioritaskan BINANCE, lalu BYBIT/OKX
    prio = ["BINANCE", "BYBIT", "OKX"]
    
    def ok(s):
        sid = s.get("symbol_id", "")
        aq = s.get("asset_id_quote", "")
        if kind == "perp":
            return "PERP" in sid and ("USDT" in sid or "USDT" == aq)
        return "SPOT" in sid and ("USDT" in sid or "USDT" == aq)
    
    cand = [s for s in data if ok(s)]
    cand.sort(key=lambda s: next((i for i, e in enumerate(prio) if s.get("symbol_id", "").startswith(e)), 99))
    sid = cand[0]["symbol_id"] if cand else None
    _CACHE[k] = sid
    return sid

async def ohlcv(coin: str, period="5MIN", limit=300, kind="spot"):
    try:
        sid = await resolve_symbol_id(coin, kind)
        if sid:
            data = await fetch_json(f"{BASE}/ohlcv/{sid}/history", headers=_hdr(),
                                    params={"period_id": period, "limit": limit},
                                    cache_key=f"ca:ohlcv:{sid}:{period}:{limit}", cache_ttl=20)
            rows = [{"time": d["time_period_end"], "open": float(d["price_open"]),
                     "high": float(d["price_high"]), "low": float(d["price_low"]),
                     "close": float(d["price_close"]), "volume": float(d.get("volume_traded", 0.0))} for d in data]
            if rows:
                return rows
    except Exception:
        pass
    
    # fallback Binance
    from app.providers.binance import klines
    return await klines(f"{coin.upper()}USDT", "5m", limit)

async def spot_rate(coin: str):
    d = await fetch_json(f"{BASE}/exchangerate/{coin.upper()}/USDT", headers=_hdr(),
                         cache_key=f"ca:rate:{coin}", cache_ttl=10)
    return float(d["rate"])
