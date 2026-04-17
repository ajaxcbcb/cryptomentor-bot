"""
Bitunix service for the website backend.

Reuses the same BitunixAutoTradeClient and AES-GCM crypto module that the
Telegram bot uses, so every live value on the website matches what the bot
shows (balance, positions, PnL, trade history, leverage, margin mode, ...).

User API keys are stored in Supabase `user_api_keys` table (api_secret
encrypted with the shared ENCRYPTION_KEY env var).
"""

import os
import sys
import asyncio
import logging
import copy
import time
from threading import Lock
from datetime import datetime
from typing import Dict, Any, Optional

from app.db.supabase import _client
logger = logging.getLogger(__name__)

# Lightweight in-memory cache to dampen repeated high-frequency polling bursts
# from the web dashboard (positions/account endpoints).
_LIVE_CACHE: dict[tuple[str, int], tuple[float, Dict[str, Any]]] = {}
_LIVE_CACHE_LOCK = Lock()
_ACCOUNT_CACHE_TTL = float(os.getenv("BITUNIX_ACCOUNT_CACHE_TTL_SECONDS", "2.5"))
_POSITIONS_CACHE_TTL = float(os.getenv("BITUNIX_POSITIONS_CACHE_TTL_SECONDS", "2.0"))


def _cache_get(kind: str, telegram_id: int, ttl: float) -> Optional[Dict[str, Any]]:
    now = time.time()
    key = (kind, int(telegram_id))
    with _LIVE_CACHE_LOCK:
        hit = _LIVE_CACHE.get(key)
        if not hit:
            return None
        ts, payload = hit
        if now - ts > ttl:
            _LIVE_CACHE.pop(key, None)
            return None
        return copy.deepcopy(payload)


def _cache_set(kind: str, telegram_id: int, payload: Dict[str, Any]) -> None:
    key = (kind, int(telegram_id))
    with _LIVE_CACHE_LOCK:
        _LIVE_CACHE[key] = (time.time(), copy.deepcopy(payload))


def _cache_invalidate_user(telegram_id: int) -> None:
    uid = int(telegram_id)
    with _LIVE_CACHE_LOCK:
        for key in list(_LIVE_CACHE.keys()):
            if key[1] == uid:
                _LIVE_CACHE.pop(key, None)

# Make the bot package importable so we can reuse the existing client + crypto
# (single source of truth — mirrors handlers_autotrade.py behaviour).
_BISMILLAH_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "Bismillah")
)
if _BISMILLAH_PATH not in sys.path:
    sys.path.insert(0, _BISMILLAH_PATH)

# Also add Bismillah/app to path for direct imports
_BISMILLAH_APP_PATH = os.path.join(_BISMILLAH_PATH, "app")
if _BISMILLAH_APP_PATH not in sys.path:
    sys.path.insert(0, _BISMILLAH_APP_PATH)

try:
    from bitunix_autotrade_client import BitunixAutoTradeClient  # type: ignore
    from lib.crypto import decrypt, encrypt  # type: ignore
    _BITUNIX_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] Bitunix client not available: {e}")
    BitunixAutoTradeClient = None
    decrypt = None
    encrypt = None
    _BITUNIX_AVAILABLE = False


# ---------------------------------------------------------------- keys ---- #

def get_user_api_keys(telegram_id: int) -> Optional[Dict[str, str]]:
    """Fetch + decrypt the user's stored exchange API keys (bitunix only for now)."""
    s = _client()
    res = (
        s.table("user_api_keys")
        .select("*")
        .eq("telegram_id", int(telegram_id))
        .eq("exchange", "bitunix")
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    row = res.data[0]
    if not _BITUNIX_AVAILABLE or decrypt is None:
        return None
    try:
        secret = decrypt(row["api_secret_enc"])
    except Exception:
        return None
    return {
        "api_key": row["api_key"],
        "api_secret": secret,
        "exchange": row.get("exchange", "bitunix"),
        "key_hint": row.get("key_hint") or row["api_key"][-4:],
    }


def save_user_api_keys(telegram_id: int, api_key: str, api_secret: str, exchange: str = "bitunix"):
    """Encrypt and upsert API keys into Supabase."""
    if not _BITUNIX_AVAILABLE or encrypt is None:
        raise PermissionError("Bitunix crypto module not available on this server")
    s = _client()
    row = {
        "telegram_id": int(telegram_id),
        "exchange": exchange,
        "api_key": api_key,
        "api_secret_enc": encrypt(api_secret),
        "key_hint": api_key[-4:],
        "updated_at": datetime.utcnow().isoformat(),
    }
    s.table("user_api_keys").upsert(row, on_conflict="telegram_id,exchange").execute()


def delete_user_api_keys(telegram_id: int, exchange: str = "bitunix"):
    """Remove stored API keys for a user."""
    s = _client()
    s.table("user_api_keys").delete().eq("telegram_id", int(telegram_id)).eq("exchange", exchange).execute()


def _client_for(telegram_id: int) -> "BitunixAutoTradeClient":
    if not _BITUNIX_AVAILABLE or BitunixAutoTradeClient is None:
        raise PermissionError("Bitunix client not available on this server")
    keys = get_user_api_keys(telegram_id)
    if not keys:
        raise PermissionError("Bitunix API keys not configured for this user")
    return BitunixAutoTradeClient(
        api_key=keys["api_key"], api_secret=keys["api_secret"]
    )


# -------------------------------------------------------- read helpers ---- #
# All Bitunix SDK calls are sync (requests/curl_cffi) — wrap in to_thread so
# they don't block the FastAPI event loop.

async def fetch_account(telegram_id: int) -> Dict[str, Any]:
    cached = _cache_get("account", telegram_id, _ACCOUNT_CACHE_TTL)
    if cached is not None:
        return cached
    client = _client_for(telegram_id)
    res = await asyncio.to_thread(client.get_account_info)
    _cache_set("account", telegram_id, res)
    return res


async def fetch_positions(telegram_id: int) -> Dict[str, Any]:
    cached = _cache_get("positions", telegram_id, _POSITIONS_CACHE_TTL)
    if cached is not None:
        return cached
    client = _client_for(telegram_id)
    res = await asyncio.to_thread(client.get_positions)
    _cache_set("positions", telegram_id, res)
    return res


async def fetch_trade_history(telegram_id: int, symbol: str = None) -> Dict[str, Any]:
    client = _client_for(telegram_id)
    if symbol:
        return await asyncio.to_thread(client.get_trade_history, symbol)
    return await asyncio.to_thread(client.get_trade_history)


async def fetch_connection(telegram_id: int) -> Dict[str, Any]:
    client = _client_for(telegram_id)
    return await asyncio.to_thread(client.check_connection)


async def fetch_connection_with_keys(api_key: str, api_secret: str) -> Dict[str, Any]:
    """Test Bitunix connectivity using raw credentials without saving them."""
    if not _BITUNIX_AVAILABLE or BitunixAutoTradeClient is None:
        raise PermissionError("Bitunix client not available on this server")
    client = BitunixAutoTradeClient(api_key=api_key, api_secret=api_secret)
    return await asyncio.to_thread(client.check_connection)


async def set_position_tpsl(telegram_id: int, symbol: str, tp_price: float, sl_price: float) -> Dict[str, Any]:
    client = _client_for(telegram_id)
    res = await asyncio.to_thread(client.set_position_tpsl, symbol, tp_price, sl_price)
    _cache_invalidate_user(telegram_id)
    return res


async def set_position_sl(telegram_id: int, symbol: str, sl_price: float) -> Dict[str, Any]:
    client = _client_for(telegram_id)
    res = await asyncio.to_thread(client.set_position_sl, symbol, sl_price)
    _cache_invalidate_user(telegram_id)
    return res


async def place_market_with_tpsl(
    telegram_id: int,
    symbol: str,
    side: str,
    qty: float,
    tp_price: float,
    sl_price: float,
    leverage: int = 10,
) -> Dict[str, Any]:
    """Open a market position with TP/SL attached. side is BUY/SELL."""
    client = _client_for(telegram_id)
    # Best-effort leverage sync (mirrors the bot's behaviour); ignore failures.
    try:
        await asyncio.to_thread(client.set_leverage, symbol, int(leverage), "cross")
    except Exception:
        pass
    res = await asyncio.to_thread(
        client.place_order_with_tpsl, symbol, side, qty, tp_price, sl_price
    )
    _cache_invalidate_user(telegram_id)
    return res


async def close_market_position(
    telegram_id: int,
    symbol: str,
    close_side: str,
    qty: float,
    position_side: str | None = None,
) -> Dict[str, Any]:
    """
    Close position via reduce-only market order.
    close_side: SELL to close LONG, BUY to close SHORT.
    """
    client = _client_for(telegram_id)
    res = await asyncio.to_thread(
        client.close_partial, symbol, close_side, qty, position_side
    )
    _cache_invalidate_user(telegram_id)
    return res
