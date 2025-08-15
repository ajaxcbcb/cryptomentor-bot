
import os
from app.providers.http import fetch_json

CMC_KEY = os.getenv("CMC_API_KEY")
BASE = "https://pro-api.coinmarketcap.com/v1"

def _hdr():
    if not CMC_KEY: 
        raise RuntimeError("CMC_API_KEY empty")
    return {"X-CMC_PRO_API_KEY": CMC_KEY}

async def get_global_metrics():
    return await fetch_json(f"{BASE}/global-metrics/quotes/latest",
                            headers=_hdr(), cache_key="cmc:global", cache_ttl=60)

async def get_quotes(symbols):
    sym = ",".join(symbols)
    return await fetch_json(f"{BASE}/cryptocurrency/quotes/latest",
                            headers=_hdr(), params={"symbol": sym},
                            cache_key=f"cmc:quotes:{sym}", cache_ttl=60)
