
import time
import asyncio
import httpx

class HTTPCache:
    def __init__(self, ttl=30): 
        self.ttl, self._d = ttl, {}
    
    def get(self, k): 
        v = self._d.get(k)
        if not v: 
            return None
        exp, data = v
        if time.time() > exp: 
            self._d.pop(k, None)
            return None
        return data
    
    def set(self, k, data, ttl=None): 
        self._d[k] = (time.time() + (ttl or self.ttl), data)

_cache = HTTPCache()

async def fetch_json(url, method="GET", headers=None, params=None, timeout=12, cache_key=None, cache_ttl=None):
    if cache_key:
        c = _cache.get(cache_key)
        if c is not None: 
            return c
    
    for i in range(1, 4):
        try:
            async with httpx.AsyncClient(timeout=timeout) as cli:
                r = await cli.request(method, url, headers=headers, params=params)
                if r.status_code in (429, 502, 503): 
                    await asyncio.sleep(0.6 * i)
                    continue
                r.raise_for_status()
                data = r.json()
                if cache_key: 
                    _cache.set(cache_key, data, cache_ttl)
                return data
        except Exception:
            if i == 3: 
                raise
            await asyncio.sleep(0.5 * i)
