
import time
import asyncio
import httpx

class HTTPCache:
    def __init__(self, ttl=15):
        self.ttl = ttl
        self._data = {}  # key: (expire_ts, payload)

    def get(self, key):
        now = time.time()
        item = self._data.get(key)
        if not item: return None
        exp, payload = item
        if now > exp:
            self._data.pop(key, None)
            return None
        return payload

    def set(self, key, payload):
        self._data[key] = (time.time() + self.ttl, payload)

cache = HTTPCache()

async def fetch_json(url, headers=None, params=None, timeout=12, cache_key=None, cache_ttl=None):
    if cache_key:
        item = cache.get(cache_key)
        if item is not None:
            return item
    for attempt in range(1, 4):  # 3x retry backoff
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.get(url, headers=headers, params=params)
                if r.status_code == 429:
                    await asyncio.sleep(0.8 * attempt)
                    continue
                r.raise_for_status()
                data = r.json()
                if cache_key and cache_ttl:
                    HTTPCache(cache_ttl)._data = cache._data  # reuse dict
                    HTTPCache(cache_ttl).set(cache_key, data)
                    cache.set(cache_key, data)
                return data
        except Exception:
            if attempt == 3:
                raise
            await asyncio.sleep(0.5 * attempt)
