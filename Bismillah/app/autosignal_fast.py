# app/autosignal_fast.py
"""
Fast Auto Signal - WITHOUT AI Reasoning
Uses simple technical indicators for speed
"""
import os, json, time, requests, asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from telegram.helpers import escape_markdown

from app.chat_store import get_private_chat_id
from app.safe_send import safe_dm

# === Config ===
MIN_INTERVAL_SEC = 1800
DEFAULT_INTERVAL_SEC = 1800
TOP_N = 25
MIN_CONFIDENCE = 75
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

# === State ===
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

# === Recipients ===
def list_recipients() -> List[int]:
    from app.supabase_conn import sb_list_users
    admins = set()
    for k in ("ADMIN_USER_ID", "ADMIN2_USER_ID"):
        val = os.getenv(k)
        if val and val.isdigit():
            admins.add(int(val))
    
    for i in range(1, 10):
        val = os.getenv(f"ADMIN{i}")
        if val and val.isdigit():
            admins.add(int(val))
    
    # Lifetime users
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
    
    for a in list(admins):
        if get_private_chat_id(a) is None:
            tids.discard(a)
    return sorted(tids)

# === Formatter ===
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
    smc_data = sig.get("smc_data", {})
    
    price_line = f"\nPrice: *{_md2(price)}*" if price is not None else ""
    reason_line = f"\nReason: {_md2(', '.join(reasons)[:300])}" if reasons else ""
    
    trading_levels = ""
    if entry and tp1 and tp2 and sl:
        trading_levels = f"\n\n📊 *Trading Levels:*\nEntry: *{_md2(entry)}*\nTP1: *{_md2(tp1)}*\nTP2: *{_md2(tp2)}*\nSL: *{_md2(sl)}*"
    
    # SMC info
    smc_info = ""
    if smc_data:
        structure = smc_data.get('structure', 'unknown')
        ob_count = smc_data.get('order_blocks', 0)
        fvg_count = smc_data.get('fvgs', 0)
        ema_21 = smc_data.get('ema_21', 0)
        
        smc_parts = []
        if structure != 'unknown':
            smc_parts.append(f"Structure: {structure}")
        if ob_count > 0:
            smc_parts.append(f"OB: {ob_count}")
        if fvg_count > 0:
            smc_parts.append(f"FVG: {fvg_count}")
        if ema_21 > 0:
            smc_parts.append(f"EMA21: {ema_21:.2f}")
        
        if smc_parts:
            smc_info = f"\n\n🧠 *SMC:* {_md2(', '.join(smc_parts))}"
    
    return (
        f"🚨 *AUTO FUTURES SIGNAL*\n"
        f"Pair: *{_md2(pair)}*\n"
        f"TF: *{_md2(tf)}*\n"
        f"Side: *{_md2(side)}*\n"
        f"Confidence: *{_md2(conf)}%*"
        f"{price_line}{trading_levels}{reason_line}{smc_info}"
    )

# === FAST Signal Generation with SMC ===
def compute_signal_fast(base_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fast signal generation using SMC + SnD zones
    Includes: Order Blocks, FVG, Market Structure, Week High/Low, EMA 21
    """
    try:
        from snd_zone_detector import detect_snd_zones
        from crypto_api import CryptoAPI
        from smc_analyzer import smc_analyzer
        
        crypto_api = CryptoAPI()
        symbol = base_symbol.upper()
        full_symbol = f"{symbol}USDT"
        
        # Get price (fast)
        price_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
        if 'error' in price_data or not price_data.get('price'):
            return None
            
        current_price = price_data.get('price', 0)
        if current_price <= 0:
            return None
        
        change_24h = price_data.get('change_24h', 0)
        volume_24h = price_data.get('volume_24h', 0)
        
        # Get SMC analysis
        smc_result = smc_analyzer.analyze(full_symbol, TIMEFRAME, limit=200)
        if 'error' in smc_result:
            print(f"SMC analysis failed for {full_symbol}: {smc_result.get('error')}")
            smc_result = {}
        
        # Get SnD zones (fast - no AI)
        snd_result = detect_snd_zones(full_symbol, TIMEFRAME, limit=50)
        if 'error' in snd_result:
            snd_result = {}
        
        demand_zones = snd_result.get('demand_zones', [])
        supply_zones = snd_result.get('supply_zones', [])
        
        # SMC data
        order_blocks = smc_result.get('order_blocks', [])
        fvgs = smc_result.get('fvgs', [])
        structure = smc_result.get('structure', {})
        week_high = smc_result.get('week_high', 0)
        week_low = smc_result.get('week_low', 0)
        ema_21 = smc_result.get('ema_21', 0)
        
        # Signal logic with SMC
        reasons = []
        side = None
        confidence = 50
        
        # 1. Check Order Blocks (SMC)
        bullish_ob = [ob for ob in order_blocks if ob.type == 'bullish']
        bearish_ob = [ob for ob in order_blocks if ob.type == 'bearish']
        
        if bullish_ob:
            nearest_ob = min(bullish_ob, key=lambda ob: abs(current_price - ob.low))
            if abs(current_price - nearest_ob.low) / current_price < 0.015:  # Within 1.5%
                side = "LONG"
                confidence = min(90, 70 + nearest_ob.strength / 5)
                reasons.append(f"Bullish OB (strength: {nearest_ob.strength:.0f})")
        
        if bearish_ob and side is None:
            nearest_ob = min(bearish_ob, key=lambda ob: abs(current_price - ob.high))
            if abs(current_price - nearest_ob.high) / current_price < 0.015:  # Within 1.5%
                side = "SHORT"
                confidence = min(90, 70 + nearest_ob.strength / 5)
                reasons.append(f"Bearish OB (strength: {nearest_ob.strength:.0f})")
        
        # 2. Check FVG (Fair Value Gap)
        if fvgs and side is None:
            bullish_fvg = [fvg for fvg in fvgs if fvg.type == 'bullish']
            bearish_fvg = [fvg for fvg in fvgs if fvg.type == 'bearish']
            
            if bullish_fvg:
                nearest_fvg = bullish_fvg[0]
                if current_price >= nearest_fvg.bottom and current_price <= nearest_fvg.top:
                    side = "LONG"
                    confidence = 80
                    reasons.append("Inside bullish FVG")
            
            if bearish_fvg and side is None:
                nearest_fvg = bearish_fvg[0]
                if current_price >= nearest_fvg.bottom and current_price <= nearest_fvg.top:
                    side = "SHORT"
                    confidence = 80
                    reasons.append("Inside bearish FVG")
        
        # 3. Check Market Structure
        if structure and side is None:
            trend = structure.get('trend', 'ranging')
            if trend == 'uptrend' and change_24h > 2:
                side = "LONG"
                confidence = 75
                reasons.append("Uptrend structure + momentum")
            elif trend == 'downtrend' and change_24h < -2:
                side = "SHORT"
                confidence = 75
                reasons.append("Downtrend structure + momentum")
        
        # 4. Check SnD zones (fallback)
        if demand_zones and side is None:
            nearest_demand = min(demand_zones, key=lambda z: abs(current_price - z.midpoint))
            distance_pct = abs(current_price - nearest_demand.midpoint) / current_price * 100
            
            if distance_pct < 2:  # Within 2% of demand
                side = "LONG"
                confidence = min(85, 70 + nearest_demand.strength / 5)
                reasons.append(f"Near demand zone")
        
        if supply_zones and side is None:
            nearest_supply = min(supply_zones, key=lambda z: abs(current_price - z.midpoint))
            distance_pct = abs(current_price - nearest_supply.midpoint) / current_price * 100
            
            if distance_pct < 2:  # Within 2% of supply
                side = "SHORT"
                confidence = min(85, 70 + nearest_supply.strength / 5)
                reasons.append(f"Near supply zone")
        
        # 5. EMA 21 confirmation
        if ema_21 > 0 and side:
            if side == "LONG" and current_price > ema_21:
                confidence += 5
                reasons.append(f"Above EMA21")
            elif side == "SHORT" and current_price < ema_21:
                confidence += 5
                reasons.append(f"Below EMA21")
        
        # 6. Week High/Low context
        if week_high > 0 and week_low > 0:
            if side == "LONG" and current_price < week_low * 1.02:
                confidence += 5
                reasons.append("Near week low")
            elif side == "SHORT" and current_price > week_high * 0.98:
                confidence += 5
                reasons.append("Near week high")
        
        # 7. Strong momentum signals (fallback)
        if side is None:
            if change_24h > 5 and volume_24h > 1000000:
                side = "LONG"
                confidence = 75
                reasons.append(f"Strong momentum: {change_24h:+.1f}%")
            elif change_24h < -5 and volume_24h > 1000000:
                side = "SHORT"
                confidence = 75
                reasons.append(f"Strong reversal: {change_24h:.1f}%")
        
        if side is None or confidence < MIN_CONFIDENCE:
            return None
        
        # Calculate trading levels using SMC
        if side == "LONG":
            entry = current_price
            # Use Order Block or FVG for better TP/SL
            if bullish_ob:
                nearest_ob = min(bullish_ob, key=lambda ob: abs(current_price - ob.low))
                sl = nearest_ob.low * 0.995  # Just below OB
                tp1 = current_price * 1.025  # 2.5% profit
                tp2 = current_price * 1.05   # 5% profit
            else:
                tp1 = current_price * 1.02  # 2% profit
                tp2 = current_price * 1.04  # 4% profit
                sl = current_price * 0.98   # 2% stop loss
        else:  # SHORT
            entry = current_price
            # Use Order Block or FVG for better TP/SL
            if bearish_ob:
                nearest_ob = min(bearish_ob, key=lambda ob: abs(current_price - ob.high))
                sl = nearest_ob.high * 1.005  # Just above OB
                tp1 = current_price * 0.975  # 2.5% profit
                tp2 = current_price * 0.95   # 5% profit
            else:
                tp1 = current_price * 0.98  # 2% profit
                tp2 = current_price * 0.96  # 4% profit
                sl = current_price * 1.02   # 2% stop loss
        
        return {
            "symbol": full_symbol,
            "timeframe": TIMEFRAME,
            "price": current_price,
            "side": side,
            "confidence": int(confidence),
            "reasons": reasons,
            "entry_price": entry,
            "tp1": tp1,
            "tp2": tp2,
            "sl": sl,
            "smc_data": {
                "order_blocks": len(order_blocks),
                "fvgs": len(fvgs),
                "structure": structure.get('trend', 'ranging') if structure else 'unknown',
                "ema_21": ema_21,
                "week_high": week_high,
                "week_low": week_low
            }
        }
        
    except Exception as e:
        print(f"Error computing fast signal for {base_symbol}: {e}")
        import traceback
        traceback.print_exc()
        return None

# === Broadcast ===
async def _broadcast(bot, sig: Dict[str, Any]) -> int:
    receivers = list_recipients()
    if not receivers:
        return 0
    text = format_signal_text(sig)
    sent = 0
    
    # Track signal to database for AI iteration
    signal_id = None
    try:
        from app.signal_tracker_integration import track_signal_given
        # Track signal for first user (representative)
        if receivers:
            signal_id = track_signal_given(
                user_id=receivers[0],  # Use first user as representative
                symbol=sig.get("symbol", ""),
                timeframe=sig.get("timeframe", TIMEFRAME),
                entry_price=sig.get("entry_price", 0),
                tp1=sig.get("tp1", 0),
                tp2=sig.get("tp2", 0),
                sl=sig.get("sl", 0),
                signal_type=sig.get("side", "LONG")
            )
            print(f"[AutoSignal] Tracked signal: {signal_id}")
    except Exception as e:
        print(f"[AutoSignal] Failed to track signal: {e}")
    
    for uid in receivers:
        if get_private_chat_id(uid) is None:
            continue
        try:
            await safe_dm(bot, uid, text)
            sent += 1
            await asyncio.sleep(0.2)
        except Exception as e:
            print(f"Failed to send to {uid}: {e}")
            continue
    return sent

# === Scan ===
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
            # Use FAST signal generation (no AI)
            sig = compute_signal_fast(b)
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
            result = await run_scan_once(ctx.application.bot)
            if result.get("sent", 0) > 0:
                print(f"[AutoSignal] Scan result: {result}")
        except Exception as e:
            print(f"[AutoSignal] tick err: {e}")

    # Remove old jobs
    for j in jq.jobs():
        if j.name == "autosignal_fast":
            j.schedule_removal()

    jq.run_repeating(_tick, interval=SCAN_INTERVAL_SEC, first=10, name="autosignal_fast")
    print(f"[AutoSignal FAST] ✅ started (interval={SCAN_INTERVAL_SEC}s ≈ {SCAN_INTERVAL_SEC//60}m, top={TOP_N}, minConf={MIN_CONFIDENCE}%, tf={TIMEFRAME})")
    print(f"[AutoSignal FAST] 🧠 Using SMC Analysis (Order Blocks, FVG, Market Structure, EMA21)")
