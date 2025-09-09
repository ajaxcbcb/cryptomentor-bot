
# app/providers/cmc_provider.py
from __future__ import annotations
import os, httpx
from typing import Any, Dict

CMC_API_KEY = (
    os.getenv("CMC_PRO_API_KEY")
    or os.getenv("COINMARKETCAP_API_KEY")
    or os.getenv("CMC_API_KEY")
)
CMC_BASE_URL = os.getenv("CMC_BASE_URL", "https://pro-api.coinmarketcap.com")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "15"))

class _HTTP:
    def __init__(self):
        self.client = httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True)
    def get(self, path: str, params: Dict[str, Any] | None = None):
        headers = {"Accept": "application/json"}
        if CMC_API_KEY:
            headers["X-CMC_PRO_API_KEY"] = CMC_API_KEY
        r = self.client.get(CMC_BASE_URL + path, params=params, headers=headers)
        r.raise_for_status()
        return r

_http = _HTTP()

def get_global_stats() -> Dict[str, Any]:
    r = _http.get("/v1/global-metrics/quotes/latest")
    data = r.json().get("data", {})
    usd = (data.get("quote") or {}).get("USD", {})
    return {
        "last_updated": data.get("last_updated"),
        "btc_dominance": data.get("btc_dominance"),
        "eth_dominance": data.get("eth_dominance"),
        "total_market_cap_usd": usd.get("total_market_cap"),
        "total_volume_24h_usd": usd.get("total_volume_24h"),
        "defi_market_cap_usd": usd.get("defi_market_cap"),
        "stablecoin_market_cap_usd": usd.get("stablecoin_market_cap"),
    }
