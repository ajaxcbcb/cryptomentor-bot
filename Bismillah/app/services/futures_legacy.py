
from typing import List, Dict, Any
from app.utils.async_tools import gather_safe
from app.services.analysis import analyze_coin_futures

DEFAULT_COINS = ["BTC", "ETH", "BNB", "SOL", "XRP"]

async def futures_signals_legacy(coins: List[str] | None) -> List[Dict[str, Any]]:
    """
    Versi lama:
    - Tidak scan Top 30 otomatis.
    - Tidak ada filter confidence.
    - Jika argumen kosong, gunakan DEFAULT_COINS.
    - Kembalikan list dict apa adanya & biarkan formatter lama yang render.
    """
    coins_up = [c.upper() for c in (coins or DEFAULT_COINS)]
    tasks = [analyze_coin_futures(c) for c in coins_up]
    results = await gather_safe(tasks)

    out: List[Dict[str, Any]] = []
    for c, r in zip(coins_up, results):
        if isinstance(r, Exception):
            out.append({"coin": c, "error": str(r)})
        else:
            # Hapus field "confidence"/"ok" jika versi lama tidak memakainya
            r.pop("confidence", None)
            r.pop("ok", None)
            out.append(r)
    return out
