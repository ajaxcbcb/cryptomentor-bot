# CryptoMentor AutoTrade System - Current Status

**Date:** April 7, 2026
**Status:** ✅ ALL SYSTEMS OPERATIONAL

---

## 🎯 Completed Features

### 1. ✅ Swing Trade Engine Fix (13 Pairs)
- **Status:** Deployed to VPS
- **Changes:**
  - Increased trading pairs from 10 to 13 (added LINK, UNI, ATOM)
  - Relaxed BTC Bias Filter from 60% to 40% threshold
  - Only skips altcoins if BTC strength < 40% (very weak)
- **File:** `Bismillah/app/autotrade_engine.py`
- **Result:** Swing engines now get more trading opportunities

### 2. ✅ StackMentor 3-Tier TP System
- **Status:** Active for ALL users
- **Features:**
  - TP1: 50% position at R:R 1:2
  - TP2: 40% position at R:R 1:3
  - TP3: 10% position at R:R 1:10
  - Auto-move SL to breakeven when TP1 hit
- **Changes:** Removed $60 minimum balance requirement
- **Files:** 
  - `Bismillah/app/stackmentor.py`
  - `Bismillah/app/supabase_repo.py`
  - `Bismillah/app/autotrade_engine.py`

### 3. ✅ Auto Mode Switcher (Market Sentiment Detection)
- **Status:** Running as background task
- **Features:**
  - Detects market condition every 15 minutes
  - Auto-switches between SCALPING (sideways) and SWING (trending)
  - Uses ADX, Bollinger Bands, ATR, and range analysis
  - Confidence threshold: 50% (aggressive switching)
  - VOLATILE markets (50% area) default to SCALPING
- **Files:**
  - `Bismillah/app/market_sentiment_detector.py`
  - `Bismillah/app/auto_mode_switcher.py`
  - `Bismillah/bot.py` (initialized on startup)
  - `db/add_auto_mode_switcher.sql`

### 4. ✅ Market Sentiment Display on Dashboard
- **Status:** Active on all dashboards
- **Features:**
  - Shows condition (SIDEWAYS/TRENDING/VOLATILE)
  - Shows confidence percentage
  - Shows optimal trading mode
  - Removed manual "Trading Mode" button (now automatic)
- **File:** `Bismillah/app/handlers_autotrade.py`
- **Applied to:** Both `cmd_autotrade` and `callback_dashboard` functions

### 5. ✅ Scalping Engine Risk Management (CRITICAL FIX)
- **Status:** Deployed to VPS
- **Critical Safety Features:**
  - **Risk capped at 5% maximum** for scalping mode
  - **Leverage capped at 10x** for safety
  - **Position size safety check:** Max 50% of balance per trade
  - **Fallback safety:** Ultra-safe 2% risk if calculation fails
  - **Emergency TP/SL protection:** Position closed immediately if TP or SL fails to set
  - **User notifications:** Alerts sent for all safety events
- **File:** `Bismillah/app/scalping_engine.py`
- **Result:** Users protected from large losses due to improper risk management

---

## 📊 System Architecture

### Trading Modes
1. **SCALPING (5M)** - For sideways/ranging markets
   - 5-minute timeframe
   - Single TP at 1.5R
   - 30-minute max hold time
   - Maximum 5% risk per trade
   - Maximum 10x leverage

2. **SWING (15M)** - For trending markets
   - 15-minute timeframe
   - 3-tier TP system (StackMentor)
   - Multi-timeframe confluence
   - Professional risk management

### Auto Mode Switching Logic
```
Market Condition Detection (every 15 minutes):
├─ ADX < 25 → SIDEWAYS (confidence boost)
├─ ADX > 40 → TRENDING (confidence boost)
├─ BB Width < 0.03 → SIDEWAYS
├─ BB Width > 0.08 → TRENDING
├─ ATR < 0.8% → SIDEWAYS
├─ ATR > 2.0% → TRENDING
└─ Range-bound check → SIDEWAYS

If confidence >= 50%:
├─ SIDEWAYS → Switch to SCALPING mode
├─ TRENDING → Switch to SWING mode
└─ VOLATILE (50% area) → Default to SCALPING
```

### Risk Management Hierarchy
```
Scalping Mode:
1. User's risk % setting
2. Cap at 5% maximum (safety)
3. Leverage cap at 10x (safety)
4. Position size cap at 50% of balance
5. Fallback to 2% risk if calculation fails
6. Emergency close if TP/SL setup fails

Swing Mode:
1. User's risk % setting
2. Professional position sizing
3. StackMentor 3-tier TP system
4. BTC bias filter (40% threshold)
5. Multi-timeframe confluence
```

---

## 🔧 Configuration

### Engine Config (Swing Mode)
- **Pairs:** 13 (BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, DOT, MATIC, LINK, UNI, ATOM)
- **Scan Interval:** 45 seconds
- **Min Confidence:** 68%
- **Max Concurrent:** 4 positions
- **Min R:R:** 2.0
- **Daily Loss Limit:** 5%
- **BTC Bias Threshold:** 40% (relaxed from 60%)

### Scalping Config
- **Pairs:** 13 (same as swing)
- **Scan Interval:** 15 seconds
- **Min Confidence:** 80%
- **Max Concurrent:** 3 positions
- **Min R:R:** 1.5
- **Max Risk:** 5% per trade
- **Max Leverage:** 10x
- **Max Hold Time:** 30 minutes

### Auto Mode Switcher Config
- **Check Interval:** 15 minutes
- **Min Confidence:** 50%
- **Symbol:** BTC (market leader)

---

## 🚀 Deployment Status

### VPS Deployment
- **Server:** root@147.93.156.165
- **Path:** /root/cryptomentor-bot/
- **Service:** cryptomentor
- **Status:** ✅ Running

### Last Deployment
- **Date:** Recent (from context transfer)
- **Files Deployed:**
  - `Bismillah/app/scalping_engine.py` (critical risk management fix)
  - `Bismillah/app/autotrade_engine.py` (13 pairs + BTC bias relaxed)
  - `Bismillah/app/market_sentiment_detector.py`
  - `Bismillah/app/auto_mode_switcher.py`
  - `Bismillah/app/handlers_autotrade.py` (dashboard with sentiment)
- **Service:** Restarted successfully

---

## 📈 User Experience

### Dashboard Display
```
🤖 Auto Trade Dashboard

✅ Status: ACTIVE
⚡ Mode: SCALPING (5M) (Auto)

📊 Market Sentiment
🟡 SIDEWAYS (66%)
💡 Optimal: SCALPING

💵 Trading Capital: $100.00
💳 Balance: $105.50 USDT
📈 Profit: +5.50 USDT

⚙️ Leverage: 10x | Margin: Cross ♾️
🔑 API Key: ...abc123
🏦 Exchange: 🔷 Bitunix
⚙️ 🟢 Engine running
```

### Auto Mode Switch Notification
```
📊 Auto Mode Switch

Market Condition: SIDEWAYS (66%)
Mode: SWING → SCALPING

📋 Analysis:
ADX 18.5 < 25 (weak trend) | BB Width 0.025 (low volatility) | ATR 0.65% (low volatility) | Price range-bound

💡 Your engine will automatically use the optimal strategy for current market conditions.

⚙️ Disable auto-mode in /settings if you prefer manual control.
```

---

## ✅ Verification Checklist

- [x] Swing engine has 13 pairs (same as scalping)
- [x] BTC bias filter relaxed to 40% threshold
- [x] StackMentor available for all balance levels
- [x] Auto mode switcher running as background task
- [x] Market sentiment displayed on dashboard
- [x] Manual "Trading Mode" button removed
- [x] Scalping risk capped at 5% maximum
- [x] Scalping leverage capped at 10x
- [x] Emergency TP/SL protection active
- [x] All changes deployed to VPS
- [x] Service restarted successfully

---

## 🎯 Key Achievements

1. **More Trading Opportunities:** Swing engines now trade 13 pairs with relaxed BTC filter
2. **Automatic Optimization:** System auto-switches between scalping and swing based on market
3. **User Safety:** Scalping mode has multiple safety layers to prevent large losses
4. **Better UX:** Dashboard shows market sentiment and optimal mode
5. **Universal Access:** StackMentor 3-tier TP available for all users

---

## 📝 Notes

- All engines (24 total) are updated with the same logic
- Auto mode switcher checks every 15 minutes
- VOLATILE markets (50% confidence area) default to SCALPING for more opportunities
- Users can disable auto-mode in settings if they prefer manual control
- Emergency close system protects users if TP/SL setup fails

---

**System Status:** ✅ FULLY OPERATIONAL
**Last Updated:** April 7, 2026
**Next Review:** Monitor user feedback and trading performance
