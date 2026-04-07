"""
AutoTrade Engine — Professional Grade Trading Loop
Strategy: Multi-timeframe confluence + SMC + Risk Management
- Min R:R 1:2, dynamic SL via ATR
- Drawdown circuit breaker (stop if -5% daily)
- Volatility filter (no trade in low-volatility ranging market)
- Confidence threshold >= 68 (only high-quality setups)
- Max 1 position per symbol, max 3 concurrent positions
- StackMentor: 3-tier TP strategy (50%/40%/10% at R:R 1:2/1:3/1:10)
"""
import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, date

logger = logging.getLogger(__name__)

# Import StackMentor system
from app.stackmentor import (
    STACKMENTOR_CONFIG,
    calculate_stackmentor_levels,
    calculate_qty_splits,
    register_stackmentor_position,
    monitor_stackmentor_positions,
)

_running_tasks: Dict[int, asyncio.Task] = {}

# Track posisi yang sudah hit TP1 (breakeven mode): user_id → set of symbols
_tp1_hit_positions: Dict[int, set] = {}

# ─────────────────────────────────────────────
#  Engine config (professional defaults)
# ─────────────────────────────────────────────
ENGINE_CONFIG = {
    "symbols":            ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "DOT", "MATIC", "LINK", "UNI", "ATOM"],  # 13 pairs sama seperti scalping
    "scan_interval":      45,       # detik antar scan
    "min_confidence":     68,       # hanya sinyal berkualitas tinggi
    "max_trades_per_day": 999,       # unlimited — push trading volume
    "max_concurrent":     4,        # max 4 posisi bersamaan (tetap 4 untuk risk management)
    "min_rr_ratio":       2.0,      # minimum Risk:Reward 1:2 (untuk validasi entry)
    "daily_loss_limit":   0.05,     # circuit breaker: stop jika -5% dari modal
    "atr_sl_multiplier":  2.0,      # SL = 2.0x ATR (lebih lebar, tahan manipulasi candle)
    "use_stackmentor":    True,     # Enable StackMentor 3-tier TP for ALL users
    "atr_tp1_multiplier": 4.0,      # TP1 = 4.0x ATR → R:R 1:2 (ambil 75% posisi) [LEGACY]
    "atr_tp2_multiplier": 6.0,      # TP2 = 6.0x ATR → R:R 1:3 (sisa 25% posisi) [LEGACY]
    "tp1_close_pct":      0.75,     # tutup 75% posisi di TP1 [LEGACY]
    "min_atr_pct":        0.4,      # filter: skip jika ATR < 0.4% (market flat)
    "max_atr_pct":        8.0,      # filter: skip jika ATR > 8% (terlalu volatile)
    "rsi_long_max":       65,       # jangan LONG jika RSI > 65 (overbought)
    "rsi_short_min":      35,       # jangan SHORT jika RSI < 35 (oversold)
    "volume_spike_min":   1.1,      # volume harus > 1.1x rata-rata
    "wick_rejection_max": 0.60,     # skip entry jika wick > 60% dari candle range (manipulasi)
}

QTY_PRECISION = {
    "BTCUSDT": 3, "ETHUSDT": 2, "SOLUSDT": 1, "BNBUSDT": 2,
    "XRPUSDT": 0, "ADAUSDT": 0, "DOGEUSDT": 0, "AVAXUSDT": 2,
    "DOTUSDT": 1, "MATICUSDT": 0,
}

# Cooldown tracker: symbol → timestamp terakhir flip
_flip_cooldown: Dict[str, float] = {}
FLIP_COOLDOWN_SECONDS        = 1800  # 30 menit antar flip per simbol (trending market)
FLIP_COOLDOWN_SIDEWAYS_SECS  = 900   # 15 menit saat BTC sideways (lebih responsif)
FLIP_MIN_CONFIDENCE          = 75    # flip hanya jika sinyal baru sangat kuat
FLIP_MIN_CONFIDENCE_SIDEWAYS = 70    # threshold lebih rendah saat sideways (range trading)


def _is_reversal(open_side: str, new_signal: Dict, btc_is_sideways: bool = False) -> bool:
    """
    Cek apakah sinyal baru adalah reversal dari posisi aktif.

    Mode TRENDING (default):
    - Confidence >= 75%, 1H trend flip, CHoCH market structure

    Mode SIDEWAYS (BTC ranging):
    - Confidence >= 70%, EMA cross cukup (tidak perlu full CHoCH)
    - Cocok untuk range trading: flip di support/resistance
    """
    import time
    symbol   = new_signal.get("symbol", "?")
    new_side = new_signal.get("side")

    if not new_side:
        return False

    # Arah harus berlawanan
    if open_side == "BUY" and new_side != "SHORT":
        logger.debug(f"[Reversal:{symbol}] No flip — signal same direction ({new_side})")
        return False
    if open_side == "SELL" and new_side != "LONG":
        logger.debug(f"[Reversal:{symbol}] No flip — signal same direction ({new_side})")
        return False

    conf = new_signal.get("confidence", 0)
    min_conf = FLIP_MIN_CONFIDENCE_SIDEWAYS if btc_is_sideways else FLIP_MIN_CONFIDENCE

    if conf < min_conf:
        logger.info(f"[Reversal:{symbol}] No flip — confidence {conf}% < {min_conf}%")
        return False

    trend_1h = new_signal.get("trend_1h", "NEUTRAL")
    struct   = new_signal.get("market_structure", "ranging")

    if btc_is_sideways:
        # Mode sideways: cukup EMA cross + RSI extreme (tidak perlu full CHoCH)
        # Ini untuk range trading — flip di area support/resistance
        rsi_15 = new_signal.get("rsi_15", 50)
        smc_ok = struct in ("uptrend", "downtrend", "ranging")  # accept semua struktur

        if open_side == "BUY":
            # Flip ke SHORT: butuh RSI overbought atau trend sudah SHORT
            rsi_extreme = rsi_15 > 60
            trend_ok    = trend_1h in ("SHORT", "NEUTRAL")
            if not (rsi_extreme or trend_ok):
                logger.info(f"[Reversal:{symbol}] Sideways no flip SHORT — RSI={rsi_15:.0f} trend={trend_1h}")
                return False
        else:
            # Flip ke LONG: butuh RSI oversold atau trend sudah LONG
            rsi_extreme = rsi_15 < 40
            trend_ok    = trend_1h in ("LONG", "NEUTRAL")
            if not (rsi_extreme or trend_ok):
                logger.info(f"[Reversal:{symbol}] Sideways no flip LONG — RSI={rsi_15:.0f} trend={trend_1h}")
                return False

        cooldown_secs = FLIP_COOLDOWN_SIDEWAYS_SECS
        logger.info(f"[Reversal:{symbol}] Sideways mode — relaxed flip check passed")
    else:
        # Mode trending: syarat ketat (CHoCH)
        if open_side == "BUY" and trend_1h != "SHORT":
            logger.info(f"[Reversal:{symbol}] No flip — 1H trend not SHORT yet ({trend_1h})")
            return False
        if open_side == "SELL" and trend_1h != "LONG":
            logger.info(f"[Reversal:{symbol}] No flip — 1H trend not LONG yet ({trend_1h})")
            return False

        if open_side == "BUY" and struct != "downtrend":
            logger.info(f"[Reversal:{symbol}] No flip — structure not downtrend ({struct})")
            return False
        if open_side == "SELL" and struct != "uptrend":
            logger.info(f"[Reversal:{symbol}] No flip — structure not uptrend ({struct})")
            return False

        cooldown_secs = FLIP_COOLDOWN_SECONDS

    # Cooldown check
    last_flip = _flip_cooldown.get(symbol, 0)
    elapsed   = time.time() - last_flip
    if elapsed < cooldown_secs:
        logger.info(f"[Reversal:{symbol}] No flip — cooldown {int(cooldown_secs - elapsed)}s remaining")
        return False

    mode_label = "SIDEWAYS" if btc_is_sideways else "TRENDING"
    logger.warning(
        f"[Reversal:{symbol}] ✅ FLIP APPROVED [{mode_label}] — "
        f"{open_side} → {new_side} | conf={conf}% | 1H={trend_1h} | struct={struct}"
    )
    return True


# ─────────────────────────────────────────────
#  BTC Bias Filter — Market Leader Analysis
# ─────────────────────────────────────────────
def _get_btc_bias() -> Dict:
    """
    Analisis BTC sebagai market leader untuk filter altcoin signals.
    Return: {"bias": "BULLISH"/"BEARISH"/"NEUTRAL", "strength": 0-100, "reasons": [...]}
    
    Professional logic:
    - BTC harus punya directional bias yang jelas sebelum trade altcoin
    - Kalau BTC ranging/indecisive → skip semua altcoin (avoid whipsaw)
    - Altcoin signal harus align dengan BTC bias
    """
    try:
        from app.providers.alternative_klines_provider import alternative_klines_provider
        
        # Fetch BTC multi-timeframe data
        klines_4h  = alternative_klines_provider.get_klines("BTC", interval='4h',  limit=50)
        klines_1h  = alternative_klines_provider.get_klines("BTC", interval='1h',  limit=100)
        klines_15m = alternative_klines_provider.get_klines("BTC", interval='15m', limit=60)
        
        if not klines_4h or not klines_1h or not klines_15m:
            logger.warning("[BTCBias] Insufficient data")
            return {"bias": "NEUTRAL", "strength": 0, "reasons": ["Insufficient BTC data"]}
        
        # ── 4H: Higher timeframe trend (most important) ────────────────
        c4h = [float(k[4]) for k in klines_4h]
        h4h = [float(k[2]) for k in klines_4h]
        l4h = [float(k[3]) for k in klines_4h]
        v4h = [float(k[5]) for k in klines_4h]
        
        ema21_4h = _calc_ema(c4h, 21)
        ema50_4h = _calc_ema(c4h, 50)
        price_4h = c4h[-1]
        
        # 4H trend direction
        if price_4h > ema21_4h > ema50_4h:
            trend_4h = "BULLISH"
        elif price_4h < ema21_4h < ema50_4h:
            trend_4h = "BEARISH"
        else:
            trend_4h = "NEUTRAL"
        
        # ── 1H: Intermediate trend confirmation ────────────────────────
        c1h = [float(k[4]) for k in klines_1h]
        h1h = [float(k[2]) for k in klines_1h]
        l1h = [float(k[3]) for k in klines_1h]
        v1h = [float(k[5]) for k in klines_1h]
        
        ema21_1h = _calc_ema(c1h, 21)
        ema50_1h = _calc_ema(c1h, 50)
        price_1h = c1h[-1]
        rsi_1h   = _calc_rsi(c1h)
        
        if price_1h > ema21_1h > ema50_1h:
            trend_1h = "BULLISH"
        elif price_1h < ema21_1h < ema50_1h:
            trend_1h = "BEARISH"
        else:
            trend_1h = "NEUTRAL"
        
        # ── 15M: Short-term momentum ───────────────────────────────────
        c15 = [float(k[4]) for k in klines_15m]
        h15 = [float(k[2]) for k in klines_15m]
        l15 = [float(k[3]) for k in klines_15m]
        v15 = [float(k[5]) for k in klines_15m]
        
        ema9_15  = _calc_ema(c15, 9)
        ema21_15 = _calc_ema(c15, 21)
        rsi_15   = _calc_rsi(c15)
        
        if ema9_15 > ema21_15:
            trend_15m = "BULLISH"
        elif ema9_15 < ema21_15:
            trend_15m = "BEARISH"
        else:
            trend_15m = "NEUTRAL"
        
        # ── Volume confirmation ────────────────────────────────────────
        vol_ratio_1h = _calc_volume_ratio(v1h, 20)
        has_volume   = vol_ratio_1h >= 1.2  # Volume harus > 1.2x average
        
        # ── Market structure (swing highs/lows) ────────────────────────
        swing_highs, swing_lows = [], []
        w = 3
        for i in range(w, len(c1h) - w):
            if h1h[i] == max(h1h[i - w:i + w + 1]):
                swing_highs.append(h1h[i])
            if l1h[i] == min(l1h[i - w:i + w + 1]):
                swing_lows.append(l1h[i])
        
        structure = "ranging"
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            if swing_highs[-1] > swing_highs[-2] and swing_lows[-1] > swing_lows[-2]:
                structure = "uptrend"  # HH + HL
            elif swing_highs[-1] < swing_highs[-2] and swing_lows[-1] < swing_lows[-2]:
                structure = "downtrend"  # LH + LL
        
        # ── Decision logic: require multi-timeframe alignment ──────────
        reasons = []
        strength = 50  # base strength
        
        # BULLISH bias requirements
        if trend_4h == "BULLISH" and trend_1h == "BULLISH":
            bias = "BULLISH"
            strength += 20
            reasons.append(f"4H+1H bullish alignment")
            
            if trend_15m == "BULLISH":
                strength += 10
                reasons.append(f"15M momentum bullish")
            
            if structure == "uptrend":
                strength += 10
                reasons.append(f"BOS: HH+HL (uptrend)")
            
            if has_volume:
                strength += 10
                reasons.append(f"Volume confirmation {vol_ratio_1h:.1f}x")
            
            if rsi_1h < 70:  # Not overbought
                strength += 5
            else:
                strength -= 10
                reasons.append(f"⚠️ RSI overbought {rsi_1h:.0f}")
        
        # BEARISH bias requirements
        elif trend_4h == "BEARISH" and trend_1h == "BEARISH":
            bias = "BEARISH"
            strength += 20
            reasons.append(f"4H+1H bearish alignment")
            
            if trend_15m == "BEARISH":
                strength += 10
                reasons.append(f"15M momentum bearish")
            
            if structure == "downtrend":
                strength += 10
                reasons.append(f"BOS: LH+LL (downtrend)")
            
            if has_volume:
                strength += 10
                reasons.append(f"Volume confirmation {vol_ratio_1h:.1f}x")
            
            if rsi_1h > 30:  # Not oversold
                strength += 5
            else:
                strength -= 10
                reasons.append(f"⚠️ RSI oversold {rsi_1h:.0f}")
        
        # NEUTRAL — conflicting signals or ranging
        else:
            bias = "NEUTRAL"
            strength = 30  # Low strength
            reasons.append(f"Conflicting timeframes: 4H={trend_4h} 1H={trend_1h} 15M={trend_15m}")
            if structure == "ranging":
                reasons.append(f"Market structure: ranging (no clear HH/HL or LH/LL)")
        
        # Cap strength
        strength = int(min(max(strength, 0), 100))
        
        logger.info(
            f"[BTCBias] {bias} strength={strength}% | "
            f"4H={trend_4h} 1H={trend_1h} 15M={trend_15m} | "
            f"struct={structure} vol={vol_ratio_1h:.1f}x RSI={rsi_1h:.0f}"
        )
        
        return {
            "bias": bias,
            "strength": strength,
            "reasons": reasons,
            "trend_4h": trend_4h,
            "trend_1h": trend_1h,
            "structure": structure,
            "rsi_1h": round(rsi_1h, 1),
        }
    
    except Exception as e:
        logger.warning(f"_get_btc_bias error: {e}", exc_info=True)
        return {"bias": "NEUTRAL", "strength": 0, "reasons": [f"Error: {e}"]}
def _calc_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    trs = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    return sum(trs[-period:]) / period if len(trs) >= period else sum(trs) / len(trs) if trs else 0.0


def _calc_ema(data: List[float], period: int) -> float:
    if len(data) < period:
        return sum(data) / len(data)
    k = 2 / (period + 1)
    e = sum(data[:period]) / period
    for v in data[period:]:
        e = v * k + e * (1 - k)
    return e


def _calc_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0:
        return 100.0
    return 100 - (100 / (1 + ag / al))


def _calc_volume_ratio(volumes: List[float], period: int = 20) -> float:
    if len(volumes) < period + 1:
        return 1.0
    avg = sum(volumes[-period - 1:-1]) / period
    return volumes[-1] / avg if avg > 0 else 1.0


# ─────────────────────────────────────────────
#  Professional Signal Engine
# ─────────────────────────────────────────────
def _compute_signal_pro(base_symbol: str, btc_bias: Optional[Dict] = None) -> Optional[Dict]:
    """
    Multi-timeframe confluence signal:
    1H trend filter + 15M entry trigger + SMC confluence + BTC bias filter
    Requires: min R:R 2:1, ATR-based SL/TP, volume confirmation, BTC alignment
    """
    symbol = base_symbol.upper() + "USDT"
    cfg = ENGINE_CONFIG
    
    # ── BTC Bias Filter (relaxed for swing trade) ──────────────
    btc_is_sideways = False
    if btc_bias:
        btc_bias_dir = btc_bias.get("bias", "NEUTRAL")
        btc_strength = btc_bias.get("strength", 0)
        btc_is_sideways = (btc_bias_dir == "NEUTRAL" or btc_strength < 50)  # Lowered from 60 to 50

    # Only skip altcoins if BTC is VERY weak (strength < 40)
    if base_symbol.upper() != "BTC" and btc_bias and btc_bias.get("strength", 100) < 40:
        logger.info(
            f"[Signal] {symbol} SKIPPED — BTC very weak "
            f"(bias={btc_bias.get('bias','?')} strength={btc_bias.get('strength',0)}%)"
        )
        return None

    try:
        from app.providers.alternative_klines_provider import alternative_klines_provider

        # ── Data fetch: 1H (trend) + 15M (entry) ──────────────────────
        klines_1h  = alternative_klines_provider.get_klines(base_symbol.upper(), interval='1h',  limit=100)
        klines_15m = alternative_klines_provider.get_klines(base_symbol.upper(), interval='15m', limit=60)

        if not klines_1h or len(klines_1h) < 50:
            logger.warning(f"[Signal] {symbol} insufficient 1H data")
            return None
        if not klines_15m or len(klines_15m) < 30:
            logger.warning(f"[Signal] {symbol} insufficient 15M data")
            return None

        # ── 1H: Trend direction ────────────────────────────────────────
        c1h = [float(k[4]) for k in klines_1h]
        h1h = [float(k[2]) for k in klines_1h]
        l1h = [float(k[3]) for k in klines_1h]
        v1h = [float(k[5]) for k in klines_1h]

        ema21_1h  = _calc_ema(c1h, 21)
        ema50_1h  = _calc_ema(c1h, 50)
        rsi_1h    = _calc_rsi(c1h)
        atr_1h    = _calc_atr(h1h, l1h, c1h, 14)
        price     = c1h[-1]
        atr_pct   = (atr_1h / price) * 100

        # Volatility filter
        if atr_pct < cfg["min_atr_pct"]:
            logger.info(f"[Signal] {symbol} ATR too low ({atr_pct:.2f}%) — market flat, skip")
            return None
        if atr_pct > cfg["max_atr_pct"]:
            logger.info(f"[Signal] {symbol} ATR too high ({atr_pct:.2f}%) — too volatile, skip")
            return None

        # 1H trend bias
        if price > ema21_1h > ema50_1h:
            trend_1h = "LONG"
        elif price < ema21_1h < ema50_1h:
            trend_1h = "SHORT"
        else:
            trend_1h = "NEUTRAL"
        
        # ── BTC Alignment Check (altcoin must follow BTC) ──────────────
        if base_symbol.upper() != "BTC" and btc_bias:
            btc_bias_dir = btc_bias.get("bias", "NEUTRAL")
            
            # Altcoin trend must align with BTC bias
            if btc_bias_dir == "BULLISH" and trend_1h == "SHORT":
                logger.info(
                    f"[Signal] {symbol} SKIPPED — BTC bullish but {symbol} bearish "
                    f"(counter-trend not allowed)"
                )
                return None
            elif btc_bias_dir == "BEARISH" and trend_1h == "LONG":
                logger.info(
                    f"[Signal] {symbol} SKIPPED — BTC bearish but {symbol} bullish "
                    f"(counter-trend not allowed)"
                )
                return None

        # ── 15M: Entry trigger ─────────────────────────────────────────
        c15 = [float(k[4]) for k in klines_15m]
        h15 = [float(k[2]) for k in klines_15m]
        l15 = [float(k[3]) for k in klines_15m]
        v15 = [float(k[5]) for k in klines_15m]

        ema9_15   = _calc_ema(c15, 9)
        ema21_15  = _calc_ema(c15, 21)
        ema9_prev = _calc_ema(c15[:-1], 9)
        ema21_prev= _calc_ema(c15[:-1], 21)
        rsi_15    = _calc_rsi(c15)
        atr_15    = _calc_atr(h15, l15, c15, 14)
        vol_ratio = _calc_volume_ratio(v15)

        # ── SMC: Market structure (swing highs/lows) ───────────────────
        swing_highs, swing_lows = [], []
        w = 3
        for i in range(w, len(c15) - w):
            if h15[i] == max(h15[i - w:i + w + 1]):
                swing_highs.append(h15[i])
            if l15[i] == min(l15[i - w:i + w + 1]):
                swing_lows.append(l15[i])

        market_structure = "ranging"
        smc_bonus = 0
        smc_reasons = []

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            if swing_highs[-1] > swing_highs[-2] and swing_lows[-1] > swing_lows[-2]:
                market_structure = "uptrend"
                smc_reasons.append("📈 BOS: HH+HL (Uptrend)")
                smc_bonus += 10
            elif swing_highs[-1] < swing_highs[-2] and swing_lows[-1] < swing_lows[-2]:
                market_structure = "downtrend"
                smc_reasons.append("📉 BOS: LH+LL (Downtrend)")
                smc_bonus += 10

        # Order Block detection
        for i in range(max(0, len(c15) - 15), len(c15) - 2):
            body_pct = abs(c15[i] - float(klines_15m[i][1])) / float(klines_15m[i][1]) * 100
            if body_pct > 0.8:
                if c15[i] > float(klines_15m[i][1]) and l15[i] <= price <= h15[i] * 1.003:
                    smc_reasons.append(f"🟩 Bullish OB: {l15[i]:.4f}–{h15[i]:.4f}")
                    smc_bonus += 8
                elif c15[i] < float(klines_15m[i][1]) and l15[i] * 0.997 <= price <= h15[i]:
                    smc_reasons.append(f"🟥 Bearish OB: {l15[i]:.4f}–{h15[i]:.4f}")
                    smc_bonus += 8

        # FVG detection
        for i in range(1, min(8, len(c15) - 1)):
            idx = len(c15) - 1 - i
            if idx < 2:
                break
            if l15[idx + 1] > h15[idx - 1] and h15[idx - 1] <= price <= l15[idx + 1]:
                smc_reasons.append(f"⬆️ Bullish FVG: {h15[idx-1]:.4f}–{l15[idx+1]:.4f}")
                smc_bonus += 6
                break
            elif h15[idx + 1] < l15[idx - 1] and h15[idx + 1] <= price <= l15[idx - 1]:
                smc_reasons.append(f"⬇️ Bearish FVG: {h15[idx+1]:.4f}–{l15[idx-1]:.4f}")
                smc_bonus += 6
                break

        # ── Signal decision: require 1H + 15M alignment ───────────────
        side = None
        confidence = 50
        reasons = []

        # EMA crossover on 15M
        ema_cross_long  = ema9_15 > ema21_15 and ema9_prev <= ema21_prev
        ema_cross_short = ema9_15 < ema21_15 and ema9_prev >= ema21_prev
        ema_trend_long  = ema9_15 > ema21_15
        ema_trend_short = ema9_15 < ema21_15

        if trend_1h == "LONG":
            if ema_cross_long:
                side = "LONG"; confidence = 75
                reasons.append(f"✅ 1H uptrend + 15M EMA cross LONG (RSI {rsi_15:.0f})")
            elif ema_trend_long and rsi_15 < 55:
                side = "LONG"; confidence = 68
                reasons.append(f"✅ 1H uptrend + 15M EMA aligned + RSI {rsi_15:.0f}")
        elif trend_1h == "SHORT":
            if ema_cross_short:
                side = "SHORT"; confidence = 75
                reasons.append(f"✅ 1H downtrend + 15M EMA cross SHORT (RSI {rsi_15:.0f})")
            elif ema_trend_short and rsi_15 > 45:
                side = "SHORT"; confidence = 68
                reasons.append(f"✅ 1H downtrend + 15M EMA aligned + RSI {rsi_15:.0f}")

        # Neutral 1H: only take if strong SMC confluence
        if side is None and smc_bonus >= 18:
            if ema_trend_long and market_structure == "uptrend":
                side = "LONG"; confidence = 65
                reasons.append(f"SMC confluence LONG (1H neutral)")
            elif ema_trend_short and market_structure == "downtrend":
                side = "SHORT"; confidence = 65
                reasons.append(f"SMC confluence SHORT (1H neutral)")

        if side is None:
            logger.info(f"[Signal] {symbol} no confluence — 1H={trend_1h}, struct={market_structure}")
            return None
        
        # ── BTC Bias Bonus (altcoin gets confidence boost if aligned) ──
        if base_symbol.upper() != "BTC" and btc_bias:
            btc_bias_dir = btc_bias.get("bias", "NEUTRAL")
            btc_strength = btc_bias.get("strength", 0)
            
            if (btc_bias_dir == "BULLISH" and side == "LONG") or \
               (btc_bias_dir == "BEARISH" and side == "SHORT"):
                bonus = int(btc_strength * 0.15)  # Up to +15% confidence
                confidence += bonus
                reasons.append(f"🔥 BTC {btc_bias_dir} bias aligned (+{bonus}%)")

        # ── RSI filter: avoid overbought/oversold entries ──────────────
        if side == "LONG"  and rsi_15 > cfg["rsi_long_max"]:
            logger.info(f"[Signal] {symbol} LONG blocked — RSI {rsi_15:.0f} overbought")
            return None
        if side == "SHORT" and rsi_15 < cfg["rsi_short_min"]:
            logger.info(f"[Signal] {symbol} SHORT blocked — RSI {rsi_15:.0f} oversold")
            return None

        # ── Volume confirmation ────────────────────────────────────────
        if vol_ratio >= cfg["volume_spike_min"]:
            confidence += 5
            reasons.append(f"📊 Volume spike {vol_ratio:.1f}x")
        else:
            confidence -= 3  # penalize low volume

        # ── SMC bonus ─────────────────────────────────────────────────
        if market_structure == ("uptrend" if side == "LONG" else "downtrend"):
            confidence += smc_bonus
        elif market_structure == ("downtrend" if side == "LONG" else "uptrend"):
            confidence -= 8  # counter-trend penalty

        # ── ATR-based SL/TP (professional sizing) ─────────────────────
        # Use 1H ATR for SL/TP to avoid noise from 15M
        sl_dist  = atr_1h * cfg["atr_sl_multiplier"]
        tp1_dist = atr_1h * cfg["atr_tp1_multiplier"]   # R:R 1:2 — ambil 75%
        tp2_dist = atr_1h * cfg["atr_tp2_multiplier"]   # R:R 1:3 — sisa 25%

        if side == "LONG":
            sl  = price - sl_dist
            tp1 = price + tp1_dist
            tp2 = price + tp2_dist
        else:
            sl  = price + sl_dist
            tp1 = price - tp1_dist
            tp2 = price - tp2_dist

        # ── R:R validation (pakai TP1 sebagai basis minimum) ──────────
        rr = tp1_dist / sl_dist
        if rr < cfg["min_rr_ratio"]:
            logger.info(f"[Signal] {symbol} R:R {rr:.2f} < {cfg['min_rr_ratio']} — skip")
            return None

        # ── Candle manipulation filter (wick rejection) ───────────────
        # Skip entry jika candle terakhir punya wick dominan ke arah entry
        # Ini tanda manipulasi / stop hunt sebelum reversal
        last_open  = float(klines_15m[-1][1])
        last_close = c15[-1]
        last_high  = h15[-1]
        last_low   = l15[-1]
        candle_range = last_high - last_low
        if candle_range > 0:
            if side == "LONG":
                # Wick bawah besar = stop hunt ke bawah, tapi close di atas = OK
                # Wick atas besar = rejection dari atas = BAHAYA untuk LONG
                upper_wick = last_high - max(last_open, last_close)
                wick_ratio = upper_wick / candle_range
                if wick_ratio > cfg["wick_rejection_max"]:
                    logger.info(
                        f"[Signal] {symbol} LONG blocked — upper wick {wick_ratio:.0%} "
                        f"(manipulation candle, wait for clean close)"
                    )
                    return None
            else:  # SHORT
                # Wick bawah besar = rejection dari bawah = BAHAYA untuk SHORT
                lower_wick = min(last_open, last_close) - last_low
                wick_ratio = lower_wick / candle_range
                if wick_ratio > cfg["wick_rejection_max"]:
                    logger.info(
                        f"[Signal] {symbol} SHORT blocked — lower wick {wick_ratio:.0%} "
                        f"(manipulation candle, wait for clean close)"
                    )
                    return None

        confidence = int(min(max(confidence, 50), 95))

        logger.info(
            f"[Signal] {symbol} {side} conf={confidence}% "
            f"entry={price:.4f} sl={sl:.4f} tp={tp1:.4f} "
            f"RR={rr:.1f} ATR={atr_pct:.2f}% vol={vol_ratio:.1f}x"
        )

        return {
            "symbol":           symbol,
            "side":             side,
            "confidence":       confidence,
            "entry_price":      price,
            "tp1":              round(tp1, 6),
            "tp2":              round(tp2, 6),
            "sl":               round(sl, 6),
            "rr_ratio":         round(rr, 2),
            "atr_pct":          round(atr_pct, 2),
            "vol_ratio":        round(vol_ratio, 2),
            "reasons":          reasons + smc_reasons,
            "market_structure": market_structure,
            "trend_1h":         trend_1h,
            "rsi_15":           round(rsi_15, 1),
            "rsi_1h":           round(rsi_1h, 1),
            "btc_is_sideways":  btc_is_sideways,
        }

    except Exception as e:
        logger.warning(f"_compute_signal_pro error {base_symbol}: {e}", exc_info=True)
        return None


# ─────────────────────────────────────────────
#  Engine lifecycle
# ─────────────────────────────────────────────
def is_running(user_id: int) -> bool:
    t = _running_tasks.get(user_id)
    return t is not None and not t.done()


def stop_engine(user_id: int):
    t = _running_tasks.get(user_id)
    if t and not t.done():
        t.cancel()
        logger.info(f"AutoTrade stopped for user {user_id}")
    
    # Update engine_active flag in database
    try:
        from app.supabase_repo import _client
        s = _client()
        s.table("autotrade_sessions").upsert({
            "telegram_id": int(user_id),
            "engine_active": False
        }, on_conflict="telegram_id").execute()
    except Exception as e:
        logger.warning(f"[Engine:{user_id}] Failed to update engine_active flag: {e}")


def start_engine(bot, user_id: int, api_key: str, api_secret: str,
                 amount: float, leverage: int, notify_chat_id: int,
                 is_premium: bool = False, silent: bool = False, exchange_id: str = "bitunix"):
    stop_engine(user_id)
    
    # Load trading mode
    from app.trading_mode_manager import TradingModeManager, TradingMode
    trading_mode = TradingModeManager.get_mode(user_id)
    
    # Get exchange client
    from app.exchange_registry import get_client
    client = get_client(exchange_id, api_key, api_secret)

    def _done_cb(task: asyncio.Task):
        # Update engine_active flag when engine stops
        try:
            from app.supabase_repo import _client
            s = _client()
            s.table("autotrade_sessions").upsert({
                "telegram_id": int(user_id),
                "engine_active": False
            }, on_conflict="telegram_id").execute()
        except Exception as e:
            logger.warning(f"[Engine:{user_id}] Failed to update engine_active flag: {e}")
        
        if task.cancelled():
            logger.info(f"AutoTrade cancelled for user {user_id}")
        elif task.exception():
            logger.error(f"AutoTrade CRASHED for user {user_id}: {task.exception()}", exc_info=task.exception())

    # Start appropriate engine based on mode
    if trading_mode == TradingMode.SCALPING:
        from app.scalping_engine import ScalpingEngine
        engine = ScalpingEngine(
            user_id=user_id,
            client=client,
            bot=bot,
            notify_chat_id=notify_chat_id
        )
        task = asyncio.create_task(engine.run())
        logger.info(f"[AutoTrade:{user_id}] Started SCALPING engine (exchange={exchange_id})")
    else:
        # Existing swing trading logic
        task = asyncio.create_task(
            _trade_loop(bot, user_id, api_key, api_secret, amount, leverage, notify_chat_id, is_premium, silent, exchange_id)
        )
        logger.info(f"[AutoTrade:{user_id}] Started SWING engine (exchange={exchange_id}, amount={amount}, leverage={leverage}x, premium={is_premium})")
    
    task.add_done_callback(_done_cb)
    _running_tasks[user_id] = task
    
    # Update engine_active flag in database
    try:
        from app.supabase_repo import _client
        s = _client()
        s.table("autotrade_sessions").upsert({
            "telegram_id": int(user_id),
            "engine_active": True
        }, on_conflict="telegram_id").execute()
    except Exception as e:
        logger.warning(f"[Engine:{user_id}] Failed to update engine_active flag: {e}")


# ─────────────────────────────────────────────
#  Main trading loop
# ─────────────────────────────────────────────
async def _trade_loop(bot, user_id: int, api_key: str, api_secret: str,
                      amount: float, leverage: int, notify_chat_id: int,
                      is_premium: bool = False, silent: bool = False, exchange_id: str = "bitunix"):
    import sys, os
    bismillah_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if bismillah_root not in sys.path:
        sys.path.insert(0, bismillah_root)

    from app.exchange_registry import get_client, get_exchange
    from app.supabase_repo import _client
    from app.bitunix_ws_pnl import start_pnl_tracker, stop_pnl_tracker, is_tracking

    # Get exchange-specific client
    ex_cfg = get_exchange(exchange_id)
    client = get_client(exchange_id, api_key, api_secret)
    cfg    = ENGINE_CONFIG

    logger.info(f"[Engine:{user_id}] Using exchange: {ex_cfg['name']} ({exchange_id})")

    # Premium user: RR 1:3 dengan dual TP (75%/25%) + breakeven SL
    # Free user: RR 1:2 single TP (behaviour lama)
    if is_premium:
        cfg = dict(ENGINE_CONFIG)  # copy agar tidak mutate global
        # Dual TP sudah di ENGINE_CONFIG, tidak perlu override
        # Flag untuk aktifkan dual TP logic
    _dual_tp_enabled = is_premium

    trades_today      = 0
    last_trade_date   = date.today()
    had_open_position = False
    daily_pnl_usdt    = 0.0   # track realized PnL for circuit breaker
    daily_loss_limit  = amount * cfg["daily_loss_limit"]

    # Init TP1 tracker untuk user ini
    if user_id not in _tp1_hit_positions:
        _tp1_hit_positions[user_id] = set()

    def calc_qty(symbol: str, notional: float, price: float) -> float:
        """Legacy position sizing (fixed margin) - kept for backward compatibility"""
        precision = QTY_PRECISION.get(symbol, 3)
        qty = round(notional / price, precision)
        min_qty = 10 ** (-precision) if precision > 0 else 1
        return qty if qty >= min_qty else 0.0
    
    def calc_qty_with_risk(symbol: str, entry: float, sl: float, leverage: int) -> tuple:
        """
        Calculate position size using risk-based sizing that respects user's max loss per trade.
        
        CRITICAL: This function ensures that if SL hits, user loses EXACTLY risk_percentage of balance.
        Leverage is used to calculate margin required, NOT to amplify position size beyond risk limit.
        
        Formula:
        1. Risk Amount = Balance * Risk%
        2. SL Distance = |Entry - SL|
        3. Position Size (in base currency) = Risk Amount / SL Distance
        4. Margin Required = (Position Size * Entry Price) / Leverage
        
        Returns:
            (qty, used_risk_sizing): tuple of (quantity, whether risk sizing was used)
        """
        try:
            # Get risk percentage from database
            from app.supabase_repo import get_risk_per_trade
            risk_pct = get_risk_per_trade(user_id)
            
            # Get current balance from exchange
            bal_result = client.get_balance()
            if not bal_result.get('success'):
                raise Exception(f"Balance fetch failed: {bal_result.get('error')}")
            
            balance = bal_result.get('balance', 0)
            if balance <= 0:
                raise Exception(f"Invalid balance: {balance}")
            
            # Calculate position size using risk calculator
            from app.risk_calculator import calculate_position_size as calc_risk
            
            calc = calc_risk(
                last_balance=balance,
                risk_percentage=risk_pct,
                entry_price=entry,
                stop_loss_price=sl
            )
            
            if calc['status'] != 'success':
                raise Exception(f"Risk calculation failed: {calc['error_message']}")
            
            # Get position size in base currency (e.g., BTC amount)
            position_size = calc['position_size']
            
            # Round to exchange precision
            precision = QTY_PRECISION.get(symbol, 3)
            qty = round(position_size, precision)
            
            # Validate minimum quantity
            min_qty = 10 ** (-precision) if precision > 0 else 1
            if qty < min_qty:
                raise Exception(f"Quantity {qty} below minimum {min_qty}")
            
            # Calculate margin required (for logging only - exchange handles this)
            position_value = qty * entry
            margin_required = position_value / leverage
            
            # Validate margin available
            if margin_required > balance:
                raise Exception(
                    f"Insufficient margin: need ${margin_required:.2f}, have ${balance:.2f}. "
                    f"Reduce risk % or increase balance."
                )
            
            logger.info(
                f"[RiskCalc:{user_id}] {symbol} - "
                f"Balance=${balance:.2f}, Risk={risk_pct}%, "
                f"Entry=${entry:.2f}, SL=${sl:.2f}, "
                f"Risk_Amt=${calc['risk_amount']:.2f}, "
                f"Position_Size={position_size:.8f}, "
                f"Qty={qty}, "
                f"Position_Value=${position_value:.2f}, "
                f"Margin_Required=${margin_required:.2f} (Leverage={leverage}x), "
                f"Max_Loss_If_SL=${calc['risk_amount']:.2f}"
            )
            
            return qty, True  # Success - used risk-based sizing
            
        except Exception as e:
            logger.warning(
                f"[RiskSizing:{user_id}] FAILED: {e} - Falling back to fixed margin system"
            )
            
            # FALLBACK: Use old fixed margin system for backward compatibility
            qty_fallback = calc_qty(symbol, amount * leverage, entry)
            
            logger.info(
                f"[RiskSizing:{user_id}] FALLBACK - Using fixed margin: "
                f"amount=${amount}, leverage={leverage}x, qty={qty_fallback}"
            )
            
            return qty_fallback, False  # Fallback used

    logger.info(f"[Engine:{user_id}] PRO ENGINE STARTED — symbols={cfg['symbols']}, "
                f"min_conf={cfg['min_confidence']}, min_rr={cfg['min_rr_ratio']}, "
                f"daily_loss_limit={daily_loss_limit:.2f} USDT")

    try:
        if not silent:
            await asyncio.sleep(1)
            await bot.send_message(
                chat_id=notify_chat_id,
                text=(
                    "🤖 <b>AutoTrade PRO Engine Active!</b>\n\n"
                    f"📊 Strategy: Multi-timeframe (1H trend + 15M entry)\n"
                    f"🎯 Min Confidence: {cfg['min_confidence']}%\n"
                    + (
                        f"⚖️ R:R: 1:2 (TP1, 75%) → 1:3 (TP2, 25%)\n"
                        f"🔒 Breakeven: SL geser ke entry setelah TP1 hit\n"
                        f"👑 Mode: <b>PREMIUM</b>\n"
                        if is_premium else
                        f"⚖️ Min R:R Ratio: 1:{cfg['min_rr_ratio']}\n"
                    )
                    + f"🛡 Daily Loss Limit: {daily_loss_limit:.2f} USDT ({cfg['daily_loss_limit']*100:.0f}%)\n"
                    f"📈 Mode: <b>Unlimited trades/day</b>\n\n"
                    "Bot only executes high-quality setups. Patience = profit."
                ),
                parse_mode='HTML'
            )
    except Exception as _startup_err:
        logger.warning(f"[Engine:{user_id}] Startup notification failed (non-fatal): {_startup_err}")

    while True:
        try:
            # ── Check if engine stop requested ────────────────────────
            try:
                if asyncio.current_task().cancelled():
                    logger.info(f"[Engine:{user_id}] Task cancelled, exiting loop")
                    break
            except Exception:
                pass  # Ignore check errors
            
            # ── Reset harian ──────────────────────────────────────────
            today = date.today()
            if today != last_trade_date:
                trades_today    = 0
                daily_pnl_usdt  = 0.0
                last_trade_date = today
                logger.info(f"[Engine:{user_id}] New day — counters reset")

            # ── Circuit breaker: daily loss limit ─────────────────────
            if daily_pnl_usdt <= -daily_loss_limit:
                logger.warning(f"[Engine:{user_id}] Daily loss limit hit ({daily_pnl_usdt:.2f} USDT), pausing until tomorrow")
                await bot.send_message(
                    chat_id=notify_chat_id,
                    text=(
                        f"🛑 <b>Circuit Breaker Triggered</b>\n\n"
                        f"Today's loss: <b>{daily_pnl_usdt:.2f} USDT</b>\n"
                        f"Limit: {daily_loss_limit:.2f} USDT ({cfg['daily_loss_limit']*100:.0f}% of capital)\n\n"
                        "Bot has stopped trading today to protect your capital.\n"
                        "Will resume tomorrow. 🔄"
                    ),
                    parse_mode='HTML'
                )
                # Tunggu sampai hari berikutnya
                while date.today() == today:
                    await asyncio.sleep(300)
                continue

            # ── Demo user: balance cap $50 ────────────────────────────
            from app.demo_users import is_demo_user, DEMO_BALANCE_LIMIT
            if is_demo_user(user_id):
                try:
                    acc_info = await asyncio.wait_for(
                        asyncio.to_thread(client.get_account_info),
                        timeout=8.0
                    )
                    if acc_info.get('success'):
                        total_balance = acc_info.get('available', 0) + acc_info.get('total_unrealized_pnl', 0)
                        # Only stop if balance significantly exceeds limit (10% buffer)
                        if total_balance > (DEMO_BALANCE_LIMIT * 1.1):
                            await bot.send_message(
                                chat_id=notify_chat_id,
                                text=(
                                    "⚠️ <b>Demo Limit Reached</b>\n\n"
                                    f"Your balance has exceeded the <b>${DEMO_BALANCE_LIMIT:.0f} demo limit</b>.\n\n"
                                    "This is a <b>special demo account</b> — the bot has been stopped automatically.\n\n"
                                    "To increase your balance limit, contact @yongdnf3 🙂"
                                ),
                                parse_mode='HTML'
                            )
                            stop_engine(user_id)
                            logger.info(f"[Engine:{user_id}] Demo user stopped: balance ${total_balance:.2f} > ${DEMO_BALANCE_LIMIT:.0f}")
                            return
                except Exception as e:
                    logger.warning(f"[Engine:{user_id}] Failed to check demo balance: {e}")

            # ── Cek posisi terbuka ────────────────────────────────────
            pos_result     = await asyncio.to_thread(client.get_positions)
            open_positions = pos_result.get('positions', []) if pos_result.get('success') else []
            occupied_syms  = {p['symbol'] for p in open_positions}

            # Deteksi posisi baru tutup (TP/SL hit) — estimasi PnL
            if had_open_position and not open_positions:
                had_open_position = False
                # Bersihkan TP1 tracker karena semua posisi sudah tutup
                _tp1_hit_positions[user_id] = set()
                if is_tracking(user_id):
                    stop_pnl_tracker(user_id)

                # ── Update trade history: posisi ditutup ──────────────
                try:
                    from app.trade_history import get_open_trades, save_trade_close, build_loss_reasoning
                    from app.providers.alternative_klines_provider import alternative_klines_provider
                    open_db_trades = get_open_trades(user_id)
                    for db_trade in open_db_trades:
                        sym_base = db_trade["symbol"].replace("USDT", "")
                        # Ambil harga terakhir untuk estimasi exit
                        # FIXED: Gunakan mark price dari exchange, bukan klines
                        try:
                            # Try to get current mark price from exchange
                            ticker_result = await asyncio.to_thread(client.get_ticker, db_trade["symbol"])
                            if ticker_result.get('success') and ticker_result.get('mark_price'):
                                exit_px = float(ticker_result['mark_price'])
                            else:
                                # Fallback to klines
                                klines = alternative_klines_provider.get_klines(sym_base, interval='1m', limit=2)
                                exit_px = float(klines[-1][4]) if klines else float(db_trade.get("entry_price", 0))
                        except Exception as e:
                            logger.warning(f"[Engine:{user_id}] Failed to get exit price for {sym_base}: {e}")
                            # Last resort: use entry price (will result in 0 PnL)
                            exit_px = float(db_trade.get("entry_price", 0))

                        entry_px = float(db_trade.get("entry_price", 0))
                        db_side  = db_trade.get("side", "LONG")
                        raw_pnl  = (exit_px - entry_px) if db_side == "LONG" else (entry_px - exit_px)
                        pnl_usdt = raw_pnl * float(db_trade.get("qty", 0))

                        if pnl_usdt < 0:
                            # Loss — generate reasoning
                            try:
                                curr_sig = await asyncio.to_thread(
                                    _compute_signal_pro, sym_base
                                )
                            except Exception:
                                curr_sig = None
                            loss_reason = build_loss_reasoning(db_trade, curr_sig)
                            close_status = "closed_sl"
                        else:
                            loss_reason  = ""
                            close_status = "closed_tp"

                        save_trade_close(
                            trade_id=db_trade["id"],
                            exit_price=exit_px,
                            pnl_usdt=pnl_usdt,
                            close_reason=close_status,
                            loss_reasoning=loss_reason,
                        )
                        daily_pnl_usdt += pnl_usdt

                        # Broadcast profit besar ke semua user (social proof)
                        if pnl_usdt >= 5.0 and close_status == "closed_tp":
                            try:
                                from app.social_proof import broadcast_profit
                                from app.supabase_repo import get_user_by_tid
                                user_data = get_user_by_tid(user_id)
                                fname = user_data.get("first_name", "User") if user_data else "User"
                                asyncio.create_task(broadcast_profit(
                                    bot=bot,
                                    user_id=user_id,
                                    first_name=fname,
                                    symbol=db_trade.get("symbol", ""),
                                    side=db_trade.get("side", "LONG"),
                                    pnl_usdt=pnl_usdt,
                                    leverage=db_trade.get("leverage", leverage),
                                ))
                            except Exception as _bp_err:
                                logger.warning(f"[Engine:{user_id}] broadcast_profit failed: {_bp_err}")

                except Exception as _he:
                    logger.warning(f"[Engine:{user_id}] trade_history close failed: {_he}")
                await bot.send_message(
                    chat_id=notify_chat_id,
                    text=(
                        f"🔔 <b>Position Closed</b> (TP/SL hit)\n\n"
                        f"📊 Trades today: <b>{trades_today}</b>\n"
                        f"🔄 Looking for next setup..."
                    ),
                    parse_mode='HTML'
                )

            if open_positions:
                had_open_position = True

            # ── StackMentor Monitor: Check TP2/TP3 hits ──────────────
            if cfg.get("use_stackmentor", True):
                try:
                    await monitor_stackmentor_positions(
                        bot=bot,
                        user_id=user_id,
                        client=client,
                        notify_chat_id=notify_chat_id
                    )
                except Exception as _sm_err:
                    logger.warning(f"[StackMentor:{user_id}] Monitor error: {_sm_err}")

            # ── TP1 Monitor: cek apakah harga sudah melewati TP1 ─────
            # Hanya untuk premium user (dual TP mode) [LEGACY - will be replaced by StackMentor]
            if _dual_tp_enabled and open_positions and user_id in _tp1_hit_positions:
                for pos in open_positions:
                    pos_symbol = pos.get("symbol", "")
                    if pos_symbol in _tp1_hit_positions.get(user_id, set()):
                        continue  # sudah di breakeven mode, skip

                    # Cari data trade yang sesuai untuk tahu TP1 dan entry
                    try:
                        from app.trade_history import get_open_trades
                        db_trades = get_open_trades(user_id)
                        for db_t in db_trades:
                            if db_t["symbol"] != pos_symbol:
                                continue
                            db_entry  = float(db_t.get("entry_price", 0))
                            db_tp1    = float(db_t.get("tp_price", 0))
                            db_side   = db_t.get("side", "LONG")
                            db_qty    = float(db_t.get("qty", 0))
                            mark_px   = float(pos.get("mark_price", 0)) or db_entry

                            tp1_hit = (db_side == "LONG"  and mark_px >= db_tp1 and db_tp1 > 0) or \
                                      (db_side == "SHORT" and mark_px <= db_tp1 and db_tp1 > 0)

                            if not tp1_hit:
                                continue

                            logger.info(f"[Engine:{user_id}] TP1 HIT {pos_symbol} @ {mark_px:.4f} — closing 75%, moving SL to breakeven")

                            # Close 75% posisi
                            close_side_tp1 = "SELL" if db_side == "LONG" else "BUY"
                            prec_tp1       = QTY_PRECISION.get(pos_symbol, 3)
                            qty_to_close   = round(db_qty * cfg["tp1_close_pct"], prec_tp1)

                            if qty_to_close > 0:
                                partial_result = await asyncio.to_thread(
                                    client.close_partial, pos_symbol, close_side_tp1, qty_to_close
                                )
                                if not partial_result.get("success"):
                                    logger.warning(f"[Engine:{user_id}] Partial close failed: {partial_result.get('error')}")
                                    continue

                            await asyncio.sleep(1)

                            # Geser SL ke entry (breakeven)
                            be_result = await asyncio.to_thread(
                                client.set_position_sl, pos_symbol, db_entry
                            )

                            # Tandai sudah breakeven
                            _tp1_hit_positions[user_id].add(pos_symbol)

                            tp1_profit_pct = abs(mark_px - db_entry) / db_entry * 100
                            await bot.send_message(
                                chat_id=notify_chat_id,
                                text=(
                                    f"🎯 <b>TP1 HIT — {pos_symbol}</b>\n\n"
                                    f"✅ Closed 75% position @ <code>{mark_px:.4f}</code>\n"
                                    f"💰 Profit locked: +{tp1_profit_pct:.2f}%\n\n"
                                    f"🔒 <b>SL moved to entry (breakeven)</b>\n"
                                    f"📍 Breakeven: <code>{db_entry:.4f}</code>\n\n"
                                    f"⏳ Remaining 25% running to TP2...\n"
                                    f"{'✅ SL updated' if be_result.get('success') else '⚠️ SL update failed — check manually'}"
                                ),
                                parse_mode='HTML'
                            )
                            break
                    except Exception as _tp1e:
                        logger.warning(f"[Engine:{user_id}] TP1 monitor error: {_tp1e}")

            # ── Reversal check: apakah struktur pasar flip? ───────────
            if open_positions:
                for pos in open_positions:
                    pos_symbol  = pos.get("symbol", "")
                    pos_side    = pos.get("side", "").upper()   # BUY / SELL
                    pos_qty     = float(pos.get("qty", 0))
                    base_symbol = pos_symbol.replace("USDT", "")

                    if not pos_qty or base_symbol not in cfg["symbols"]:
                        continue

                    # Scan sinyal baru untuk simbol ini
                    try:
                        rev_sig = await asyncio.to_thread(_compute_signal_pro, base_symbol, btc_bias)
                    except Exception:
                        continue

                    if not rev_sig or not _is_reversal(pos_side, rev_sig, rev_sig.get("btc_is_sideways", False)):
                        continue

                    import time
                    # ── CHoCH terdeteksi — eksekusi flip ─────────────
                    new_side    = rev_sig["side"]
                    new_entry   = rev_sig["entry_price"]
                    new_tp      = rev_sig["tp1"]
                    new_sl      = rev_sig["sl"]
                    new_conf    = rev_sig["confidence"]
                    new_struct  = rev_sig["market_structure"]
                    new_trend   = rev_sig["trend_1h"]

                    logger.warning(
                        f"[Engine:{user_id}] CHoCH DETECTED {pos_symbol}: "
                        f"{pos_side} → {new_side} | conf={new_conf}% | "
                        f"struct={new_struct} | 1H={new_trend}"
                    )

                    await bot.send_message(
                        chat_id=notify_chat_id,
                        text=(
                            f"🔄 <b>CHoCH Detected — Reversal {pos_symbol}</b>\n\n"
                            f"Active position: <b>{'LONG' if pos_side=='BUY' else 'SHORT'}</b>\n"
                            f"New signal: <b>{new_side}</b>\n\n"
                            f"📊 1H Trend: <b>{new_trend}</b>\n"
                            f"🏗 Structure: <b>{new_struct}</b> (CHoCH)\n"
                            f"🧠 Confidence: <b>{new_conf}%</b>\n"
                            f"{'🔀 Mode: <b>SIDEWAYS FLIP</b> (range trading)' if rev_sig.get('btc_is_sideways') else '📈 Mode: <b>TREND FLIP</b> (CHoCH confirmed)'}\n\n"
                            f"⚡ Closing position and flipping to {new_side}..."
                        ),
                        parse_mode='HTML'
                    )

                    # Step 1: Close posisi aktif
                    close_side  = "SELL" if pos_side == "BUY" else "BUY"
                    close_result = await asyncio.to_thread(
                        client.place_order, pos_symbol, close_side, pos_qty,
                        order_type='market', reduce_only=True
                    )

                    if not close_result.get("success"):
                        close_err = close_result.get("error", "Unknown")
                        logger.error(f"[Engine:{user_id}] Flip close FAILED: {close_err}")
                        await bot.send_message(
                            chat_id=notify_chat_id,
                            text=f"⚠️ <b>Failed to close position for flip:</b> {close_err}\nReversal cancelled.",
                            parse_mode='HTML'
                        )
                        continue

                    await asyncio.sleep(1)  # beri waktu exchange proses close

                    # Step 2: Open posisi baru arah berlawanan
                    flip_qty = calc_qty(pos_symbol, amount * leverage, new_entry)
                    if flip_qty <= 0:
                        logger.warning(f"[Engine:{user_id}] Flip qty=0 for {pos_symbol}, skip open")
                        continue

                    await asyncio.to_thread(client.set_leverage, pos_symbol, leverage)
                    open_result = await asyncio.to_thread(
                        client.place_order_with_tpsl, pos_symbol,
                        "BUY" if new_side == "LONG" else "SELL",
                        flip_qty, new_tp, new_sl
                    )

                    if open_result.get("success"):
                        _flip_cooldown[pos_symbol] = time.time()
                        trades_today += 1
                        sl_pct = abs(new_entry - new_sl) / new_entry * 100
                        tp_pct = abs(new_tp - new_entry) / new_entry * 100

                        # ── Update history: close trade lama, buka trade baru ──
                        try:
                            from app.trade_history import (
                                close_open_trades_by_symbol, save_trade_open, build_loss_reasoning,
                                get_open_trades
                            )
                            # Estimasi PnL trade lama
                            old_trades = get_open_trades(user_id)
                            for ot in old_trades:
                                if ot["symbol"] == pos_symbol:
                                    old_entry = float(ot.get("entry_price", new_entry))
                                    old_side  = ot.get("side", "LONG")
                                    raw_pnl   = (new_entry - old_entry) if old_side == "LONG" else (old_entry - new_entry)
                                    pnl_est   = raw_pnl * float(ot.get("qty", 0))
                                    loss_r    = build_loss_reasoning(ot, rev_sig) if pnl_est < 0 else ""
                                    from app.trade_history import save_trade_close
                                    save_trade_close(
                                        trade_id=ot["id"],
                                        exit_price=new_entry,
                                        pnl_usdt=pnl_est,
                                        close_reason="closed_flip",
                                        loss_reasoning=loss_r,
                                    )
                            # Simpan trade baru hasil flip
                            save_trade_open(
                                telegram_id=user_id,
                                symbol=pos_symbol,
                                side=new_side,
                                entry_price=new_entry,
                                qty=flip_qty,
                                leverage=leverage,
                                tp_price=new_tp,
                                sl_price=new_sl,
                                signal=rev_sig,
                                order_id=open_result.get("order_id", ""),
                                is_flip=True,
                            )
                        except Exception as _he:
                            logger.warning(f"[Engine:{user_id}] flip trade_history failed: {_he}")
                        await bot.send_message(
                            chat_id=notify_chat_id,
                            text=(
                                f"✅ <b>FLIP SUCCESSFUL — {pos_symbol}</b>\n\n"
                                f"{'LONG' if pos_side=='BUY' else 'SHORT'} → <b>{new_side}</b>\n"
                                f"💵 Entry: <code>{new_entry:.4f}</code>\n"
                                f"🎯 TP: <code>{new_tp:.4f}</code> (+{tp_pct:.1f}%)\n"
                                f"🛑 SL: <code>{new_sl:.4f}</code> (-{sl_pct:.1f}%)\n"
                                f"📦 Qty: {flip_qty} | {leverage}x\n"
                                f"🧠 Confidence: {new_conf}%\n"
                                f"⚖️ R:R: 1:{rev_sig['rr_ratio']:.1f}"
                            ),
                            parse_mode='HTML'
                        )
                        logger.info(f"[Engine:{user_id}] Flip SUCCESS {pos_symbol} → {new_side}")
                    else:
                        flip_err = open_result.get("error", "Unknown")
                        logger.error(f"[Engine:{user_id}] Flip open FAILED: {flip_err}")
                        await bot.send_message(
                            chat_id=notify_chat_id,
                            text=(
                                f"⚠️ <b>Old position closed but failed to open {new_side}:</b>\n"
                                f"{flip_err}\n\nBot is still running, looking for next setup."
                            ),
                            parse_mode='HTML'
                        )

            # ── Concurrent positions limit ─────────────────────────────
            if len(open_positions) >= cfg["max_concurrent"]:
                logger.info(f"[Engine:{user_id}] Max concurrent positions ({cfg['max_concurrent']}) reached")
                await asyncio.sleep(cfg["scan_interval"])
                continue

            # ── Scan symbols ──────────────────────────────────────────
            available = [s for s in cfg["symbols"] if (s + "USDT") not in occupied_syms]
            if not available:
                await asyncio.sleep(cfg["scan_interval"])
                continue
            
            # ── Get BTC bias first (market leader analysis) ───────────
            btc_bias = await asyncio.to_thread(_get_btc_bias)
            btc_bias_dir = btc_bias.get("bias", "NEUTRAL")
            btc_strength = btc_bias.get("strength", 0)
            
            logger.info(
                f"[Engine:{user_id}] BTC Bias: {btc_bias_dir} ({btc_strength}%) — "
                f"{', '.join(btc_bias.get('reasons', [])[:2])}"
            )

            # Saat BTC sideways: hanya scan BTC sendiri (altcoin diblokir di _compute_signal_pro)
            # BTC bisa range trade dengan confidence lebih tinggi
            btc_sideways_mode = (btc_bias_dir == "NEUTRAL" or btc_strength < 60)
            min_conf_scan = cfg["min_confidence"] + 5 if btc_sideways_mode else cfg["min_confidence"]

            candidates: List[Dict] = []
            for sym in available:
                try:
                    sig = await asyncio.to_thread(_compute_signal_pro, sym, btc_bias)
                    if sig and sig.get('confidence', 0) >= min_conf_scan:
                        candidates.append(sig)
                        logger.info(f"[Engine:{user_id}] Candidate: {sym} {sig['side']} "
                                    f"conf={sig['confidence']}% RR={sig['rr_ratio']}"
                                    f"{' [SIDEWAYS]' if sig.get('btc_is_sideways') else ''}")
                except Exception as e:
                    logger.warning(f"[Engine:{user_id}] Scan error {sym}: {e}")

            if not candidates:
                logger.info(f"[Engine:{user_id}] No quality setups found, waiting...")
                await asyncio.sleep(cfg["scan_interval"])
                continue

            # Pilih sinyal terbaik: prioritas confidence, lalu R:R
            best = max(candidates, key=lambda s: (s['confidence'], s['rr_ratio']))

            sig        = best
            symbol     = sig['symbol']
            side       = sig['side']
            entry      = sig['entry_price']
            tp1        = sig['tp1']
            tp2        = sig['tp2']
            sl         = sig['sl']
            confidence = sig['confidence']
            rr_ratio   = sig['rr_ratio']

            # ── Hitung qty dengan risk-based sizing (Phase 2) ─────────────
            # Try risk-based position sizing first, fallback to fixed margin if fails
            qty, used_risk_sizing = calc_qty_with_risk(symbol, entry, sl, leverage)
            
            if qty <= 0:
                logger.warning(f"[Engine:{user_id}] qty=0 for {symbol}, skip")
                await asyncio.sleep(cfg["scan_interval"])
                continue
            
            # Log which method was used
            if used_risk_sizing:
                logger.info(f"[Engine:{user_id}] Using RISK-BASED position sizing for {symbol}")
            else:
                logger.info(f"[Engine:{user_id}] Using FIXED MARGIN position sizing for {symbol} (fallback)")

            # ── StackMentor: Calculate 3-tier TP levels ───────────────
            # All users are eligible for StackMentor (no minimum balance)
            from app.supabase_repo import is_stackmentor_eligible_by_balance
            
            stackmentor_enabled = False
            try:
                # Get user's current balance from exchange
                bal_result = await asyncio.to_thread(client.get_balance)
                user_balance = bal_result.get('balance', 0) if bal_result.get('success') else 0
                
                # All users are eligible for StackMentor
                stackmentor_enabled = cfg.get("use_stackmentor", True) and is_stackmentor_eligible_by_balance(user_balance)
                
                if stackmentor_enabled:
                    logger.info(f"[StackMentor:{user_id}] Enabled for balance ${user_balance:.2f} ✅")
                else:
                    logger.info(f"[StackMentor:{user_id}] Disabled in config (balance: ${user_balance:.2f})")
            except Exception as _sm_check_err:
                logger.warning(f"[StackMentor:{user_id}] Balance check failed: {_sm_check_err}")
                stackmentor_enabled = False
            
            precision  = QTY_PRECISION.get(symbol, 3)
            if stackmentor_enabled:
                # StackMentor: 3-tier TP strategy (50%/40%/10%)
                tp1_sm, tp2_sm, tp3_sm = calculate_stackmentor_levels(
                    entry_price=entry,
                    sl_price=sl,
                    side=side
                )
                qty_tp1, qty_tp2, qty_tp3 = calculate_qty_splits(qty, precision)
                
                # Override signal TP with StackMentor levels
                tp1 = tp1_sm
                tp2 = tp2_sm
                tp3 = tp3_sm
                
                logger.info(
                    f"[StackMentor:{user_id}] {symbol} {side} — "
                    f"TP1={tp1:.4f}(50%) TP2={tp2:.4f}(40%) TP3={tp3:.4f}(10%)"
                )
            elif _dual_tp_enabled:
                # Legacy premium: 75%/25% split
                qty_tp1 = round(qty * cfg["tp1_close_pct"], precision)
                qty_tp2 = round(qty - qty_tp1, precision)
                qty_tp3 = 0
                tp3 = tp2
                if qty_tp1 <= 0 or qty_tp2 <= 0:
                    qty_tp1 = qty
                    qty_tp2 = 0
                    qty_tp3 = 0
            else:
                # Legacy free: single TP
                qty_tp1 = qty
                qty_tp2 = 0
                qty_tp3 = 0
                tp3 = tp1

            # ── Set leverage ──────────────────────────────────────────
            await asyncio.to_thread(client.set_leverage, symbol, leverage)

            # ── Validate SL price before placing order ────────────────
            # Get current mark price to ensure SL is valid
            try:
                ticker_result = await asyncio.to_thread(client.get_ticker, symbol)
                if ticker_result.get('success'):
                    current_mark_price = float(ticker_result.get('mark_price', entry))
                    
                    # Validate SL based on side
                    if side == "LONG":
                        # For LONG: SL must be BELOW mark price
                        if sl >= current_mark_price:
                            logger.warning(f"[Engine:{user_id}] Invalid SL for LONG: {sl:.4f} >= {current_mark_price:.4f}, adjusting...")
                            sl = current_mark_price * 0.98  # Set SL 2% below current price
                    else:  # SHORT
                        # For SHORT: SL must be ABOVE mark price
                        if sl <= current_mark_price:
                            logger.warning(f"[Engine:{user_id}] Invalid SL for SHORT: {sl:.4f} <= {current_mark_price:.4f}, adjusting...")
                            sl = current_mark_price * 1.02  # Set SL 2% above current price
                    
                    # Also validate TP
                    if side == "LONG":
                        if tp1 <= current_mark_price:
                            logger.warning(f"[Engine:{user_id}] Invalid TP for LONG: {tp1:.4f} <= {current_mark_price:.4f}, skipping trade")
                            await asyncio.sleep(cfg["scan_interval"])
                            continue
                    else:  # SHORT
                        if tp1 >= current_mark_price:
                            logger.warning(f"[Engine:{user_id}] Invalid TP for SHORT: {tp1:.4f} >= {current_mark_price:.4f}, skipping trade")
                            await asyncio.sleep(cfg["scan_interval"])
                            continue
            except Exception as _val_err:
                logger.warning(f"[Engine:{user_id}] SL validation failed: {_val_err}, proceeding with original SL")

            # ── Place order dengan TP1 sebagai TP utama ───────────────
            # Premium: TP2 dimonitor manual oleh engine (setelah TP1 hit, SL geser ke entry)
            # Free: single TP di RR 1:2
            _tp_for_order = tp1 if _dual_tp_enabled else tp1
            order_result = await asyncio.to_thread(
                client.place_order_with_tpsl, symbol,
                "BUY" if side == "LONG" else "SELL",
                qty, _tp_for_order, sl
            )

            if not order_result.get('success'):
                err = order_result.get('error', 'Unknown')
                logger.error(f"[Engine:{user_id}] Order FAILED: {err}")

                # Handle SL price validation error (30029)
                if '30029' in str(err) or 'SL price must be' in str(err):
                    logger.warning(f"[Engine:{user_id}] SL price validation error, skipping this trade")
                    await bot.send_message(
                        chat_id=notify_chat_id,
                        text=(
                            f"⚠️ <b>Trade skipped</b>\n\n"
                            f"Market moved too fast - SL price became invalid.\n"
                            f"Bot will look for next setup.\n\n"
                            f"This is normal in volatile markets."
                        ),
                        parse_mode='HTML'
                    )
                    await asyncio.sleep(cfg["scan_interval"])
                    continue

                # Cek apakah ini benar-benar API key invalid (bukan transient error)
                is_auth_error = 'TOKEN_INVALID' in str(err) or 'SIGNATURE_ERROR' in str(err)
                is_ip_blocked = 'HTTP 403' in str(err) or 'IP_BLOCKED' in str(err) or ('403' in str(err) and 'IP' in str(err))

                if is_auth_error or is_ip_blocked:
                    # Retry sekali dulu sebelum menyerah — bisa jadi timestamp drift atau proxy glitch
                    logger.warning(f"[Engine:{user_id}] Auth/IP error, retrying once in 15s: {err}")
                    await asyncio.sleep(15)
                    retry_result = await asyncio.to_thread(
                        client.place_order_with_tpsl, symbol,
                        "BUY" if side == "LONG" else "SELL",
                        qty, tp1, sl
                    )
                    if retry_result.get('success'):
                        order_result = retry_result
                        # Lanjut ke bawah dengan order sukses
                    else:
                        retry_err = retry_result.get('error', '')
                        # Hanya stop jika TOKEN_INVALID — IP_BLOCKED jangan stop, bisa recover
                        if 'TOKEN_INVALID' in str(retry_err):
                            await bot.send_message(
                                chat_id=notify_chat_id,
                                text=(
                                    "❌ <b>AutoTrade Dihentikan - API Key Salah</b>\n\n"
                                    "⚠️ <b>Masalah:</b> API Key atau Secret Key yang Anda masukkan salah atau tidak valid.\n\n"
                                    "🔧 <b>Penyebab Umum:</b>\n"
                                    "• API Key/Secret Key salah saat input\n"
                                    "• API Key memiliki IP restriction (harus tanpa IP)\n"
                                    "• API Key sudah expired atau dihapus\n"
                                    "• Permissions tidak lengkap (harus ada Futures Trading)\n\n"
                                    "✅ <b>Cara Memperbaiki:</b>\n"
                                    "1. Buka Bitunix → API Management\n"
                                    "2. Hapus API Key lama\n"
                                    "3. Buat API Key baru:\n"
                                    "   • <b>TANPA IP Restriction</b>\n"
                                    "   • Enable <b>Futures Trading</b>\n"
                                    "   • Copy API Key & Secret Key dengan benar\n"
                                    "4. Ketik /autotrade → Change API Key\n"
                                    "5. Paste API Key & Secret Key yang baru\n\n"
                                    "❓ <b>Butuh Bantuan?</b>\n"
                                    "Hubungi Admin: @BillFarr\n"
                                    "Admin akan membantu Anda setup API Key dengan benar."
                                ),
                                parse_mode='HTML'
                            )
                            return
                        elif 'IP_BLOCKED' in str(retry_err):
                            # IP still blocked — wait longer, don't stop engine
                            await bot.send_message(
                                chat_id=notify_chat_id,
                                text=(
                                    "⚠️ <b>Server IP blocked by Bitunix</b>\n\n"
                                    "Bot will retry in 5 minutes.\n"
                                    "Make sure <b>PROXY_URL</b> is set in Railway Variables."
                                ),
                                parse_mode='HTML'
                            )
                            await asyncio.sleep(300)
                            continue
                        else:
                            await bot.send_message(
                                chat_id=notify_chat_id,
                                text=f"⚠️ <b>Order failed (2x):</b> {retry_err}\n\nBot is still running.",
                                parse_mode='HTML'
                            )
                            await asyncio.sleep(cfg["scan_interval"])
                            continue
                else:
                    # Pesan error spesifik berdasarkan kode
                    if '20003' in str(err) or 'Insufficient balance' in str(err):
                        bal_result = await asyncio.to_thread(client.get_balance)
                        bal_usdt = bal_result.get('balance', 0) if bal_result.get('success') else 0
                        margin_needed = round(amount, 2)
                        await bot.send_message(
                            chat_id=notify_chat_id,
                            text=(
                                f"⚠️ <b>Order failed: Insufficient balance</b>\n\n"
                                f"💰 Your futures balance: <b>{bal_usdt:.2f} USDT</b>\n"
                                f"📦 Required margin: <b>~{margin_needed:.2f} USDT</b>\n\n"
                                f"Solutions:\n"
                                f"• Transfer USDT from <b>Spot → Futures</b> on Bitunix\n"
                                f"• Or reduce your autotrade capital\n\n"
                                f"Bot is still running and will retry."
                            ),
                            parse_mode='HTML'
                        )
                    else:
                        await bot.send_message(
                            chat_id=notify_chat_id,
                            text=f"⚠️ <b>Order failed:</b> {err}\n\nBot is still running.",
                            parse_mode='HTML'
                        )
                    await asyncio.sleep(cfg["scan_interval"])
                    continue

                # Jika retry sukses, pastikan order_result sudah diupdate di atas
                if not order_result.get('success'):
                    await asyncio.sleep(cfg["scan_interval"])
                    continue

            order_id = order_result.get('order_id', '-')
            trades_today += 1
            had_open_position = True

            # Tandai posisi ini belum hit TP1
            if user_id not in _tp1_hit_positions:
                _tp1_hit_positions[user_id] = set()
            _tp1_hit_positions[user_id].discard(symbol)

            # ── Register with StackMentor for monitoring ──────────────
            if stackmentor_enabled:
                register_stackmentor_position(
                    user_id=user_id,
                    symbol=symbol,
                    entry_price=entry,
                    sl_price=sl,
                    tp1=tp1,
                    tp2=tp2,
                    tp3=tp3,
                    total_qty=qty,
                    qty_tp1=qty_tp1,
                    qty_tp2=qty_tp2,
                    qty_tp3=qty_tp3,
                    side=side,
                    leverage=leverage
                )

            # ── Simpan ke trade history ───────────────────────────────
            try:
                from app.trade_history import save_trade_open
                save_trade_open(
                    telegram_id=user_id,
                    symbol=symbol,
                    side=side,
                    entry_price=entry,
                    qty=qty,
                    leverage=leverage,
                    tp_price=tp1,
                    sl_price=sl,
                    signal=sig,
                    order_id=order_id,
                    is_flip=False,
                    # StackMentor fields
                    tp1_price=tp1,
                    tp2_price=tp2,
                    tp3_price=tp3,
                    qty_tp1=qty_tp1,
                    qty_tp2=qty_tp2,
                    qty_tp3=qty_tp3,
                    strategy="stackmentor" if stackmentor_enabled else "legacy",
                )
            except Exception as _he:
                logger.warning(f"[Engine:{user_id}] trade_history save failed: {_he}")

            # ── Kalkulasi risk/reward untuk notifikasi ─────────────────
            sl_pct      = abs(entry - sl)  / entry * 100
            tp1_pct     = abs(tp1 - entry) / entry * 100
            tp2_pct     = abs(tp2 - entry) / entry * 100
            
            # Get actual balance and risk info for notification
            from app.supabase_repo import get_risk_per_trade
            risk_pct = get_risk_per_trade(user_id)
            bal_result = await asyncio.to_thread(client.get_balance)
            current_balance = bal_result.get('balance', 0) if bal_result.get('success') else 0
            risk_amount = current_balance * (risk_pct / 100) if current_balance > 0 else (amount * (sl_pct / 100) * leverage)
            
            # Calculate potential profit based on actual position size
            reward_tp1  = qty * abs(tp1 - entry)
            reward_tp2  = qty * abs(tp2 - entry)

            trend_1h   = sig.get('trend_1h', '-')
            struct      = sig.get('market_structure', 'ranging')
            rsi_15      = sig.get('rsi_15', 0)
            atr_pct     = sig.get('atr_pct', 0)
            vol_ratio   = sig.get('vol_ratio', 1)
            all_reasons = sig.get('reasons', [])

            struct_emoji = {"uptrend": "📈", "downtrend": "📉", "ranging": "↔️"}.get(struct, "↔️")
            trend_emoji  = {"LONG": "🟢", "SHORT": "🔴", "NEUTRAL": "⚪"}.get(trend_1h, "⚪")

            reasons_text = "\n".join(f"  • {r}" for r in all_reasons[:5])

            await bot.send_message(
                chat_id=notify_chat_id,
                text=(
                    f"✅ <b>ORDER EXECUTED</b>  [#{trades_today} today]\n\n"
                    f"📊 {symbol} | {side}\n"
                    f"💵 Entry: <code>{entry:.4f}</code>\n"
                    + (
                        f"🎯 TP1: <code>{tp1:.4f}</code> (+{tp1_pct:.1f}%) — 50% posisi\n"
                        f"🎯 TP2: <code>{tp2:.4f}</code> (+{tp2_pct:.1f}%) — 40% posisi\n"
                        f"🎯 TP3: <code>{tp3:.4f}</code> (+{abs(tp3 - entry) / entry * 100:.1f}%) — 10% posisi\n"
                        f"🛑 SL: <code>{sl:.4f}</code> (-{sl_pct:.1f}%)\n"
                        f"📦 Qty: {qty}\n\n"
                        f"⚖️ R:R: <b>1:2 → 1:3 → 1:10</b> (StackMentor 🎯)\n"
                        f"🤖 <i>Partial close otomatis saat harga hit TP</i>\n"
                        f"🔒 Setelah TP1 hit → SL geser ke entry (breakeven)\n"
                        if stackmentor_enabled else
                        (
                            f"🎯 TP1: <code>{tp1:.4f}</code> (+{tp1_pct:.1f}%) — 75% posisi\n"
                            f"🎯 TP2: <code>{tp2:.4f}</code> (+{tp2_pct:.1f}%) — 25% posisi\n"
                            f"🛑 SL: <code>{sl:.4f}</code> (-{sl_pct:.1f}%)\n"
                            f"📦 Qty: {qty}\n\n"
                            f"⚖️ R:R: <b>1:2 → 1:3</b> (dual TP)\n"
                            f"🤖 <i>Partial close otomatis saat harga hit TP</i>\n"
                            f"🔒 Setelah TP1 hit → SL geser ke entry (breakeven)\n"
                            if _dual_tp_enabled else
                            f"🎯 TP: <code>{tp1:.4f}</code> (+{tp1_pct:.1f}%)\n"
                            f"🛑 SL: <code>{sl:.4f}</code> (-{sl_pct:.1f}%)\n"
                            f"📦 Qty: {qty}\n\n"
                            f"⚖️ R:R Ratio: <b>1:{rr_ratio:.1f}</b>\n"
                        )
                    )
                    + f"{trend_emoji} 1H Trend: <b>{trend_1h}</b>\n"
                    f"{struct_emoji} Structure: <b>{struct}</b>\n"
                    f"📊 RSI 15M: {rsi_15} | ATR: {atr_pct:.2f}% | Vol: {vol_ratio:.1f}x\n\n"
                    f"🧠 Reasons:\n{reasons_text}\n\n"
                    + (
                        f"💰 Potential profit: +{reward_tp2:.2f} USDT (full TP)\n"
                        if _dual_tp_enabled or stackmentor_enabled else
                        f"💰 Potential profit: +{reward_tp1:.2f} USDT\n"
                    )
                    + f"⚠️ Max loss: -{risk_amount:.2f} USDT\n"
                    + (f"💼 Balance: ${current_balance:.2f} | Risk: {risk_pct}%\n" if current_balance > 0 else "")
                    + f"🧠 Confidence: {confidence}%\n"
                    + (
                        f"🎯 <b>StackMentor Active</b> (3-tier TP)\n"
                        if stackmentor_enabled else
                        f"💡 StackMentor disabled in config\n"
                        if not _dual_tp_enabled else
                        ""
                    )
                    + f"🔖 Order ID: <code>{order_id}</code>"
                ),
                parse_mode='HTML'
            )

            # ── Start PnL tracker ─────────────────────────────────────
            start_pnl_tracker(user_id=user_id, api_key=api_key, api_secret=api_secret,
                               bot=bot, chat_id=notify_chat_id)

            # ── Update session ────────────────────────────────────────
            try:
                _client().table("autotrade_sessions").update({
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("telegram_id", user_id).execute()
            except Exception:
                pass

            await asyncio.sleep(cfg["scan_interval"])

        except asyncio.CancelledError:
            stop_pnl_tracker(user_id)
            try:
                await bot.send_message(chat_id=notify_chat_id,
                                       text="🛑 <b>AutoTrade stopped.</b>", parse_mode='HTML')
            except Exception:
                pass
            return

        except Exception as e:
            err_str = str(e)
            logger.error(f"[Engine:{user_id}] Loop error: {e}", exc_info=True)
            # Jangan stop engine karena network/timeout error — hanya retry
            if any(x in err_str for x in ['TOKEN_INVALID', 'SIGNATURE_ERROR']):
                # Auth error di luar order placement — kemungkinan transient, retry 3x
                logger.warning(f"[Engine:{user_id}] Auth error in loop, will retry: {err_str}")
                await asyncio.sleep(60)  # tunggu lebih lama sebelum retry
            else:
                await asyncio.sleep(30)
