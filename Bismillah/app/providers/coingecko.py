from typing import Dict, Any, List
from app.providers.http import fetch_json

BASE = "https://api.coingecko.com/api/v3"

async def get_global():
    return await fetch_json(f"{BASE}/global", cache_key="cg:global", cache_ttl=60)

async def get_simple_prices(ids):
    return await fetch_json(f"{BASE}/simple/price",
        params={"ids": ",".join(ids), "vs_currencies": "usd", "include_24hr_change": "true"},
        cache_key=f"cg:prices:{','.join(ids)}", cache_ttl=60)