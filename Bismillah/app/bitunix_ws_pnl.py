"""
Bitunix WebSocket Live PnL Tracker
Subscribes to position updates via Bitunix private WebSocket,
then periodically pushes unrealized PnL updates to Telegram.
"""
import asyncio
import hashlib
import json
import logging
import time
import uuid
from typing import Dict, Optional, Callable

logger = logging.getLogger(__name__)

def _get_ws_url() -> str:
    """Build WS URL, always using wss:// scheme."""
    import os
    base = os.getenv('BITUNIX_WS_URL', '').rstrip('/')
    if not base:
        base = os.getenv('BITUNIX_BASE_URL', '').rstrip('/')
    if not base:
        return "wss://fapi.bitunix.com/private"
    # Force convert http(s) → ws(s), strip any trailing /private first
    base = base.replace('https://', 'wss://').replace('http://', 'ws://')
    base = base.rstrip('/')
    # Remove /private suffix if already present to avoid duplication
    if base.endswith('/private'):
        return base
    return f"{base}/private"

BITUNIX_WS_URL = _get_ws_url()

# user_id → WsPnlTracker instance
_trackers: Dict[int, "WsPnlTracker"] = {}


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _make_ws_sign(api_key: str, api_secret: str) -> tuple[str, str, str]:
    """Returns (nonce, timestamp, sign) for WS auth."""
    nonce = uuid.uuid4().hex
    timestamp = str(int(time.time() * 1000))
    digest = _sha256(nonce + timestamp + api_key)
    sign = _sha256(digest + api_secret)
    return nonce, timestamp, sign


class WsPnlTracker:
    """
    Connects to Bitunix private WebSocket, subscribes to position channel,
    and sends live PnL updates to Telegram every UPDATE_INTERVAL seconds.
    """
    UPDATE_INTERVAL = 5   # seconds between Telegram edits
    PING_INTERVAL   = 20  # seconds between WS pings
    RECONNECT_DELAY = 5

    def __init__(self, api_key: str, api_secret: str,
                 bot, chat_id: int, user_id: int):
        self.api_key    = api_key
        self.api_secret = api_secret
        self.bot        = bot
        self.chat_id    = chat_id
        self.user_id    = user_id

        self._task: Optional[asyncio.Task] = None
        self._positions: Dict[str, dict] = {}   # symbol → position data
        self._msg_id: Optional[int] = None      # Telegram message to edit
        self._running = False

    # ------------------------------------------------------------------ #

    def start(self):
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"[WsPnL:{self.user_id}] Tracker started")

    def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info(f"[WsPnL:{self.user_id}] Tracker stopped")

    # ------------------------------------------------------------------ #

    async def _run(self):
        while self._running:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.warning(f"[WsPnL:{self.user_id}] WS error: {e}, reconnecting in {self.RECONNECT_DELAY}s")
                await asyncio.sleep(self.RECONNECT_DELAY)

    async def _connect_and_listen(self):
        try:
            import websockets
        except ImportError:
            logger.error("[WsPnL] websockets package not installed. Run: pip install websockets")
            # Fallback to REST polling
            await self._rest_polling_fallback()
            return

        nonce, timestamp, sign = _make_ws_sign(self.api_key, self.api_secret)
        auth_msg = json.dumps({
            "op": "login",
            "args": [{
                "apiKey": self.api_key,
                "nonce": nonce,
                "timestamp": timestamp,
                "sign": sign,
            }]
        })
        sub_msg = json.dumps({
            "op": "subscribe",
            "args": ["position"]
        })

        ws_url = _get_ws_url()
        logger.info(f"[WsPnL:{self.user_id}] Connecting to {ws_url}")
        async with websockets.connect(ws_url, ping_interval=None) as ws:
            logger.info(f"[WsPnL:{self.user_id}] WS connected")
            await ws.send(auth_msg)

            # Wait for auth response
            auth_resp = await asyncio.wait_for(ws.recv(), timeout=10)
            logger.debug(f"[WsPnL:{self.user_id}] Auth: {auth_resp}")

            await ws.send(sub_msg)

            last_update = 0
            last_ping   = time.time()

            async for raw in ws:
                if not self._running:
                    break

                now = time.time()

                # Ping keepalive
                if now - last_ping > self.PING_INTERVAL:
                    await ws.send(json.dumps({"op": "ping"}))
                    last_ping = now

                try:
                    msg = json.loads(raw)
                except Exception:
                    continue

                # Handle position update
                if msg.get("topic") == "position" and msg.get("data"):
                    self._update_positions(msg["data"])

                # Push to Telegram every UPDATE_INTERVAL
                if now - last_update >= self.UPDATE_INTERVAL and self._positions:
                    await self._send_pnl_update()
                    last_update = now

    def _update_positions(self, data: list):
        """Parse position data from WS message."""
        for pos in data:
            symbol = pos.get("symbol", "")
            qty    = float(pos.get("qty", 0))
            if qty == 0:
                self._positions.pop(symbol, None)
                continue
            self._positions[symbol] = {
                "symbol":      symbol,
                "side":        pos.get("side", "").upper(),
                "qty":         qty,
                "entry_price": float(pos.get("openPrice", 0)),
                "mark_price":  float(pos.get("markPrice", 0)),
                "pnl":         float(pos.get("unrealizedPNL", 0)),
                "leverage":    pos.get("leverage", "?"),
            }

    async def _send_pnl_update(self):
        """Edit or send a Telegram message with live PnL."""
        if not self._positions:
            return

        total_pnl = sum(p["pnl"] for p in self._positions.values())
        pnl_emoji = "📈" if total_pnl >= 0 else "📉"
        lines = [f"{pnl_emoji} <b>Live PnL Update</b>  <i>{_ts()}</i>\n"]

        for p in self._positions.values():
            side_emoji = "🟢" if p["side"] == "BUY" else "🔴"
            pnl_sign   = "+" if p["pnl"] >= 0 else ""
            lines.append(
                f"{side_emoji} <b>{p['symbol']}</b> {p['side']} {p['leverage']}x\n"
                f"   Entry: <code>{p['entry_price']:.4f}</code> → Mark: <code>{p['mark_price']:.4f}</code>\n"
                f"   Unrealized PnL: <b>{pnl_sign}{p['pnl']:.4f} USDT</b>"
            )

        lines.append(f"\n💼 Total Unrealized: <b>{'+'if total_pnl>=0 else ''}{total_pnl:.4f} USDT</b>")
        text = "\n".join(lines)

        try:
            if self._msg_id:
                await self.bot.edit_message_text(
                    chat_id=self.chat_id,
                    message_id=self._msg_id,
                    text=text,
                    parse_mode='HTML'
                )
            else:
                msg = await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    parse_mode='HTML'
                )
                self._msg_id = msg.message_id
        except Exception as e:
            # Message not modified or deleted — reset msg_id
            if "message is not modified" not in str(e).lower():
                logger.debug(f"[WsPnL:{self.user_id}] Telegram edit error: {e}")
                self._msg_id = None

    async def _rest_polling_fallback(self):
        """Fallback: poll REST API every UPDATE_INTERVAL seconds."""
        logger.info(f"[WsPnL:{self.user_id}] Using REST polling fallback")
        from app.bitunix_autotrade_client import BitunixAutoTradeClient
        client = BitunixAutoTradeClient(api_key=self.api_key, api_secret=self.api_secret)

        while self._running:
            try:
                result = await asyncio.to_thread(client.get_positions)
                if result.get("success"):
                    self._positions = {}
                    for pos in result.get("positions", []):
                        self._positions[pos["symbol"]] = pos
                    if self._positions:
                        await self._send_pnl_update()
            except Exception as e:
                logger.debug(f"[WsPnL:{self.user_id}] REST poll error: {e}")
            await asyncio.sleep(self.UPDATE_INTERVAL)


def _ts() -> str:
    return time.strftime("%H:%M:%S")


# ------------------------------------------------------------------ #
#  Public API                                                          #
# ------------------------------------------------------------------ #

def start_pnl_tracker(user_id: int, api_key: str, api_secret: str,
                      bot, chat_id: int):
    """Start live PnL tracker for a user."""
    stop_pnl_tracker(user_id)
    tracker = WsPnlTracker(api_key, api_secret, bot, chat_id, user_id)
    tracker.start()
    _trackers[user_id] = tracker
    logger.info(f"[WsPnL] Tracker started for user {user_id}")


def stop_pnl_tracker(user_id: int):
    """Stop live PnL tracker for a user."""
    t = _trackers.pop(user_id, None)
    if t:
        t.stop()


def is_tracking(user_id: int) -> bool:
    t = _trackers.get(user_id)
    return t is not None and t._running
