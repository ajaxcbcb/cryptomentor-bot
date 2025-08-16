
# app/autosignal.py
import os, json, time, requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from telegram.helpers import escape_markdown

from app.chat_store import get_private_chat_id
from app.safe_send import safe_dm

# === Konfigurasi inti ===
MIN_INTERVAL_SEC = 1800                 # clamp min 30 menit
DEFAULT_INTERVAL_SEC = 1800             # default 30 menit
TOP_N = 25                              # CMC top 25
MIN_CONFIDENCE = 75                     # threshold kirim
TIMEFRAME = os.getenv("FUTURES_TF", "15m")
QUOTE = os.getenv("FUTURES_QUOTE", "USDT").upper()
COOLDOWN_MIN = int(os.getenv("AUTOSIGNAL_COOLDOWN_MIN", "60"))

CMC_API_KEY = (os.getenv("CMC_API_KEY") or "").strip()
CMC_BASE = "https://pro-api.coinmarketcap.com/v1"

DATA_DIR = os.getenv("DATA_DIR", "data")
STATE_PATH = os.path.join(DATA_DIR, "autosignal_state.json")

def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _now():
    return datetime.now(timezone.utc)

def _get_scan_interval() -> int:
    raw = os.getenv("AUTOSIGNAL_INTERVAL_SEC", str(DEFAULT_INTERVAL_SEC))
    try: v = int(raw)
    except: v = DEFAULT_INTERVAL_SEC
    return max(v, MIN_INTERVAL_SEC)
SCAN_INTERVAL_SEC = _get_scan_interval()

# === State (anti-spam) ===
def _load_state() -> Dict[str, Any]:
    _ensure_dir()
    if not os.path.exists(STATE_PATH):
        return {"last_sent": {}, "enabled": True}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_sent": {}, "enabled": True}

def _save_state(d: Dict[str, Any]):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, STATE_PATH)

def autosignal_enabled() -> bool:
    return bool(_load_state().get("enabled", True))

def set_autosignal_enabled(flag: bool):
    s = _load_state()
    s["enabled"] = bool(flag)
    _save_state(s)

def _cd_key(symbol: str, side: str) -> str:
    return f"{symbol}:{side}"

def _can_send(state: Dict[str, Any], symbol: str, side: str) -> bool:
    k = _cd_key(symbol, side)
    ts = state.get("last_sent", {}).get(k)
    if not ts: return True
    ago = _now() - datetime.fromisoformat(ts)
    return ago >= timedelta(minutes=COOLDOWN_MIN)

def _mark_sent(state: Dict[str, Any], symbol: str, side: str):
    state.setdefault("last_sent", {})
    state["last_sent"][_cd_key(symbol, side)] = _now().isoformat()

# === CMC Top 25 ===
def cmc_top_symbols(limit: int = TOP_N) -> List[str]:
    if not CMC_API_KEY:
        raise RuntimeError("CMC_API_KEY belum diset")
    url = f"{CMC_BASE}/cryptocurrency/listings/latest"
    params = {"start": 1, "limit": max(1, limit), "convert": "USD", "sort": "market_cap", "sort_dir": "desc"}
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY, "Accept": "application/json"}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json().get("data", [])
    return [it["symbol"].upper() for it in data if "symbol" in it]

# === Audience (Supabase lifetime + admin + consent) ===
def list_recipients() -> List[int]:
    from app.supabase_conn import sb_list_users
    admins = set()
    for k in ("ADMIN_USER_ID", "ADMIN2_USER_ID"):
        val = os.getenv(k)
        if val and val.isdigit():
            admins.add(int(val))
    
    # Also check ADMIN1, ADMIN2 format
    for i in range(1, 10):
        val = os.getenv(f"ADMIN{i}")
        if val and val.isdigit():
            admins.add(int(val))
    
    # lifetime dari Supabase
    rows = sb_list_users({
        "is_premium": "eq.true",
        "banned": "eq.false",
        "premium_until": "is.null",
        "select": "telegram_id"
    })
    tids = set(admins)
    for r in rows:
        tid = r.get("telegram_id")
        if tid and get_private_chat_id(int(tid)):
            tids.add(int(tid))
    
    # admin juga butuh consent supaya tidak 403
    for a in list(admins):
        if get_private_chat_id(a) is None:
            tids.discard(a)
    return sorted(tids)

# === Formatter (selaraskan gaya /futures_signals) ===
def _md2(s) -> str:
    return escape_markdown(str(s), version=2)

def format_signal_text(sig: dict) -> str:
    pair = sig.get("symbol", "?")
    side = sig.get("side", "?")
    conf = sig.get("confidence", 0)
    price = sig.get("price")
    tf = sig.get("timeframe", TIMEFRAME)
    reasons = sig.get("reasons", [])
    entry = sig.get("entry_price")
    tp1 = sig.get("tp1")
    tp2 = sig.get("tp2") 
    sl = sig.get("sl")
    
    price_line = f"\nPrice: *{_md2(price)}*" if price is not None else ""
    reason_line = f"\nReason: {_md2(', '.join(reasons)[:300])}" if reasons else ""
    
    trading_levels = ""
    if entry and tp1 and tp2 and sl:
        trading_levels = f"\nEntry: *{_md2(entry)}*\nTP1: *{_md2(tp1)}*\nTP2: *{_md2(tp2)}*\nSL: *{_md2(sl)}*"
    
    return (
        f"🚨 *AUTO FUTURES SIGNAL*\n"
        f"Pair: *{_md2(pair)}*\n"
        f"TF: *{_md2(tf)}*\n"
        f"Side: *{_md2(side)}*\n"
        f"Confidence: *{_md2(conf)}%*"
        f"{price_line}{trading_levels}{reason_line}"
    )

# === INTI: salin logika dari /futures_signals (tanpa engine terpisah) ===
def compute_signal_for_symbol(base_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Clone exact logic from /futures_signals handler
    """
    try:
        # Import AI assistant to use same logic
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from ai_assistant import AIAssistant
        from crypto_api import CryptoAPI
        
        ai = AIAssistant()
        crypto_api = CryptoAPI()
        
        symbol = base_symbol.upper()
        
        # >>> PASTE_FROM_FUTURES_SIGNALS_START
        # Use exact same logic as /futures_signals command
        
        # Get price data with CoinMarketCap integration
        price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
        if 'error' in price_data or not price_data.get('price'):
            return None
            
        current_price = price_data.get('price', 0)
        if current_price <= 0:
            return None
            
        # Get futures data from Binance
        futures_data = crypto_api.get_futures_data(symbol)
        
        # Multi-timeframe analysis like in /futures_signals
        ohlcv_1h = ai.get_coinapi_ohlcv_data(symbol, '1HRS', 100)
        ohlcv_4h = ai.get_coinapi_ohlcv_data(symbol, '4HRS', 100)
        
        primary_indicators = {}
        higher_tf_indicators = {}
        
        if ohlcv_1h.get('success'):
            primary_indicators = ai.calculate_technical_indicators(ohlcv_1h['data'])
        
        if ohlcv_4h.get('success'):
            higher_tf_indicators = ai.calculate_technical_indicators(ohlcv_4h['data'])
            
        if 'error' in primary_indicators:
            return None
            
        # Generate enhanced trading signal (same as /futures_signals)
        signal_data = ai._generate_enhanced_trading_signal(
            primary_indicators, higher_tf_indicators, futures_data, current_price, {}
        )
        
        if signal_data['direction'] == 'NEUTRAL':
            return None
            
        # Calculate trading levels (same as /futures_signals)
        trading_levels = ai._calculate_advanced_trading_levels(
            current_price, signal_data, primary_indicators, {}
        )
        
        # Determine confidence using same logic
        confidence = signal_data.get('confidence', 0)
        
        # Generate reasons using same logic as AI assistant
        reasons = []
        if signal_data.get('strategy'):
            reasons.append(signal_data['strategy'])
        if signal_data.get('momentum_score', 0) > 0.6:
            reasons.append("Strong momentum")
        if signal_data.get('trend_alignment'):
            reasons.append("Trend alignment")
            
        # Get price change for additional context
        change_24h = price_data.get('change_24h', 0)
        if abs(change_24h) > 5:
            reasons.append(f"24h: {change_24h:+.1f}%")
        
        side = signal_data['direction']
        price = current_price
        
        # >>> PASTE_FROM_FUTURES_SIGNALS_END
        
        if side is None or side == 'NEUTRAL':
            return None
            
        return {
            "symbol": f"{symbol}USDT",
            "timeframe": TIMEFRAME,
            "price": price,
            "side": side,
            "confidence": int(confidence),
            "reasons": reasons,
            "entry_price": trading_levels.get('entry'),
            "tp1": trading_levels.get('tp1'),
            "tp2": trading_levels.get('tp2'), 
            "sl": trading_levels.get('stop_loss')
        }
        
    except Exception as e:
        print(f"Error computing signal for {base_symbol}: {e}")
        return None

# === Broadcast ===
async def _broadcast(bot, sig: Dict[str, Any]) -> int:
    receivers = list_recipients()
    if not receivers:
        return 0
    text = format_signal_text(sig)
    sent = 0
    for uid in receivers:
        if get_private_chat_id(uid) is None:
            continue
        try:
            await safe_dm(bot, uid, text)
            sent += 1
            await asyncio.sleep(0.2)  # Rate limiting
        except Exception as e:
            print(f"Failed to send to {uid}: {e}")
            continue
    return sent

# === Satu siklus scan ===
async def run_scan_once(bot) -> Dict[str, Any]:
    if not autosignal_enabled():
        return {"ok": True, "sent": 0, "notes": "disabled"}
    try:
        bases = cmc_top_symbols(TOP_N)
    except Exception as e:
        return {"ok": False, "sent": 0, "error": f"CMC error: {e}"}

    state = _load_state()
    total_sent = 0
    notes = []

    for b in bases:
        try:
            sig = compute_signal_for_symbol(b)
        except Exception as e:
            notes.append(f"{b}{QUOTE}: compute_err:{e}")
            continue

        if not sig:
            continue
        if int(sig.get("confidence", 0)) < MIN_CONFIDENCE:
            continue

        sym = sig.get("symbol", f"{b}{QUOTE}")
        side = sig.get("side", "")
        if not _can_send(state, sym, side):
            continue

        try:
            count = await _broadcast(bot, sig)
            if count > 0:
                _mark_sent(state, sym, side)
                _save_state(state)
                total_sent += count
                print(f"[AutoSignal] Sent {sym} {side} to {count} users")
        except Exception as e:
            notes.append(f"{sym}: send_err:{e}")

    return {"ok": True, "sent": total_sent, "notes": ", ".join(notes)}

# === Scheduler ===
def start_background_scheduler(application):
    jq = getattr(application, "job_queue", None)
    if jq is None:
        print("[AutoSignal] No job_queue")
        return

    async def _tick(ctx):
        try:
            import asyncio
            result = await run_scan_once(ctx.application.bot)
            if result.get("sent", 0) > 0:
                print(f"[AutoSignal] Scan result: {result}")
        except Exception as e:
            print(f"[AutoSignal] tick err: {e}")

    # dedup
    for j in jq.jobs():
        if j.name == "autosignal":
            j.schedule_removal()

    jq.run_repeating(_tick, interval=SCAN_INTERVAL_SEC, first=10, name="autosignal")
    print(f"[AutoSignal] ✅ started (interval={SCAN_INTERVAL_SEC}s ≈ {SCAN_INTERVAL_SEC//60}m, top={TOP_N}, minConf={MIN_CONFIDENCE}%, tf={TIMEFRAME}, quote={QUOTE})")
"""
Sumber kebenaran status Auto Signals di runtime.
Dipakai oleh panel /admin untuk menampilkan ON/OFF.
"""

import os
from threading import Event

# default ON jika env AUTO_SIGNALS_DEFAULT=1, selain itu OFF
_default_on = os.getenv("AUTO_SIGNALS_DEFAULT", "1") == "1"
_state = Event()
if _default_on:
    _state.set()
else:
    _state.clear()

def is_auto_signal_running() -> bool:
    """Kembalikan True jika Auto Signals sedang aktif."""
    return _state.is_set()

def start_auto_signals() -> None:
    """Nyalakan Auto Signals (hanya flag status; worker dijalankan di tempat lain)."""
    _state.set()

def stop_auto_signals() -> None:
    """Matikan Auto Signals (flag status)."""
    _state.clear()

def set_auto_signal_running(flag: bool) -> None:
    """Set Auto Signals status dengan flag boolean."""
    _state.set() if flag else _state.clear()
