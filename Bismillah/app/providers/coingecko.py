
from app.providers.http import fetch_json

BASE = "https://api.coingecko.com/api/v3"

async def get_global():
    return await fetch_json(f"{BASE}/global", cache_key="cg:global", cache_ttl=60)
