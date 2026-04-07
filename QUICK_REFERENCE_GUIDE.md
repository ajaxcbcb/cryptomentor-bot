# CryptoMentor AutoTrade - Quick Reference Guide

## 🎯 System Overview

Your CryptoMentor bot now has **intelligent auto-switching** between trading modes based on real-time market conditions.

---

## 🔄 How Auto Mode Switching Works

### Every 15 Minutes:
1. Bot analyzes BTC market sentiment
2. Detects if market is SIDEWAYS, TRENDING, or VOLATILE
3. Automatically switches all active users to optimal mode:
   - **SIDEWAYS** → SCALPING mode (5M timeframe, quick trades)
   - **TRENDING** → SWING mode (15M timeframe, trend following)
   - **VOLATILE** (50% area) → SCALPING mode (more opportunities)

### Market Indicators Used:
- **ADX** (trend strength)
- **Bollinger Band Width** (volatility)
- **ATR** (average true range)
- **Price Range Analysis** (support/resistance)

---

## 📊 Trading Modes Comparison

| Feature | SCALPING (5M) | SWING (15M) |
|---------|---------------|-------------|
| **Best For** | Sideways/ranging markets | Trending markets |
| **Timeframe** | 5 minutes | 15 minutes |
| **Max Hold** | 30 minutes | No limit |
| **TP Strategy** | Single TP (1.5R) | 3-tier TP (50%/40%/10%) |
| **Risk per Trade** | Max 5% | User setting |
| **Max Leverage** | 10x | User setting |
| **Trading Pairs** | 13 pairs | 13 pairs |
| **Scan Interval** | 15 seconds | 45 seconds |

---

## 🛡️ Safety Features

### Scalping Mode Protection:
1. ✅ Risk automatically capped at 5% maximum
2. ✅ Leverage automatically capped at 10x
3. ✅ Position size limited to 50% of balance
4. ✅ Emergency close if TP/SL setup fails
5. ✅ Fallback to ultra-safe 2% if calculation fails

### Swing Mode Protection:
1. ✅ BTC bias filter (skips altcoins if BTC very weak)
2. ✅ Multi-timeframe confluence required
3. ✅ StackMentor 3-tier TP with auto-breakeven
4. ✅ Daily loss limit circuit breaker (5%)
5. ✅ Professional risk management

---

## 📈 StackMentor 3-Tier TP System

**Available for ALL users (no minimum balance required)**

### How It Works:
1. **TP1 (50% position)** → R:R 1:2
   - When hit: SL auto-moves to breakeven (entry price)
   - Position becomes risk-free ✅

2. **TP2 (40% position)** → R:R 1:3
   - Captures extended move
   - SL already at breakeven

3. **TP3 (10% position)** → R:R 1:10
   - Captures moonshot moves
   - "Let winners run" strategy

### Benefits:
- ✅ Secure profits early (50% at TP1)
- ✅ Risk-free after TP1 (SL at breakeven)
- ✅ Capture big moves (TP3 at 10R)
- ✅ Professional money management

---

## 🎛️ User Dashboard

### What Users See:
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

### Dashboard Buttons:
- 📊 Status Portfolio
- 📈 Trade History
- 🛑 Stop AutoTrade / 🔄 Restart Engine
- 🧠 Bot Skills
- 👥 Community Partners (if verified)
- ⚙️ Settings
- 🔑 Change API Key

**Note:** "Trading Mode" button removed - mode is now automatic!

---

## 🔔 Notifications Users Receive

### 1. Mode Switch Notification
```
📊 Auto Mode Switch

Market Condition: SIDEWAYS (66%)
Mode: SWING → SCALPING

📋 Analysis:
ADX 18.5 < 25 (weak trend) | BB Width 0.025 (low volatility)

💡 Your engine will automatically use the optimal strategy.
⚙️ Disable auto-mode in /settings if you prefer manual control.
```

### 2. Trade Opened (Scalping)
```
⚡ SCALPING TRADE OPENED

Symbol: ETHUSDT
Side: LONG
Entry: 2,450.50
TP: 2,465.75 (1.5R)
SL: 2,440.25
Quantity: 0.05 ETH
Leverage: 10x
Risk: 5.0%

Confidence: 85%
Reasons:
✅ 1H uptrend + 15M EMA cross LONG
📊 Volume spike 1.8x
```

### 3. TP/SL Safety Alert
```
🚨 EMERGENCY CLOSE: ETHUSDT

Position opened but TP/SL setup FAILED!
Position closed immediately for safety.

TP Success: ❌
SL Success: ❌

Your capital is protected. ✅
```

### 4. Breakeven Protection
```
🔒 Breakeven Protection Activated

Symbol: ETHUSDT
Entry: 2,450.50
Old SL: 2,440.25
New SL: 2,450.50 (Breakeven)

Position is now risk-free! 🎉
```

---

## 🔧 Configuration Files

### Key Files:
- `Bismillah/app/autotrade_engine.py` - Swing mode engine
- `Bismillah/app/scalping_engine.py` - Scalping mode engine
- `Bismillah/app/market_sentiment_detector.py` - Market analysis
- `Bismillah/app/auto_mode_switcher.py` - Auto switching logic
- `Bismillah/app/handlers_autotrade.py` - Dashboard & UI
- `Bismillah/app/stackmentor.py` - 3-tier TP system
- `Bismillah/bot.py` - Bot initialization

### Database Tables:
- `autotrade_sessions` - User sessions & settings
- `autotrade_trades` - Trade history
- `user_api_keys` - Encrypted API keys
- `tp_partial_tracking` - StackMentor TP tracking

---

## 🚀 Deployment Commands

### Deploy to VPS:
```bash
# Copy files to VPS
scp Bismillah/app/scalping_engine.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/autotrade_engine.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/market_sentiment_detector.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/auto_mode_switcher.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/handlers_autotrade.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# Restart service
ssh root@147.93.156.165 "systemctl restart cryptomentor"

# Check status
ssh root@147.93.156.165 "systemctl status cryptomentor"
```

### Check Logs:
```bash
# View live logs
ssh root@147.93.156.165 "journalctl -u cryptomentor -f"

# View recent logs
ssh root@147.93.156.165 "journalctl -u cryptomentor -n 100"

# Check for errors
ssh root@147.93.156.165 "journalctl -u cryptomentor -p err -n 50"
```

---

## 📊 Monitoring

### What to Monitor:
1. **Auto Mode Switcher:** Check logs every 15 minutes for mode switches
2. **User Notifications:** Ensure users receive mode switch alerts
3. **Trade Execution:** Verify TP/SL are set correctly
4. **Risk Management:** Confirm scalping uses max 5% risk
5. **Market Sentiment:** Check if detection is accurate

### Key Log Messages:
```
[AutoModeSwitcher] Market: SIDEWAYS (66%) → Recommend: SCALPING
[AutoModeSwitcher] Switched 4/4 users to SCALPING mode
[Scalping:123456] Using RISK-BASED position sizing
[Scalping:123456] TP set @ 2465.75 ✅
[Scalping:123456] SL set @ 2440.25 ✅
```

---

## ⚠️ Troubleshooting

### Issue: Auto mode switcher not running
**Solution:**
```bash
# Check if bot is running
ssh root@147.93.156.165 "systemctl status cryptomentor"

# Check logs for switcher startup
ssh root@147.93.156.165 "journalctl -u cryptomentor | grep 'Auto Mode Switcher'"

# Should see: "✅ Auto Mode Switcher started (checks every 15 min)"
```

### Issue: Users not getting mode switch notifications
**Solution:**
1. Check if user has `auto_mode_enabled = true` in database
2. Check if engine is active (`engine_active = true`)
3. Verify bot has permission to send messages to user

### Issue: Scalping risk exceeds 5%
**Solution:**
- Check `calculate_position_size_pro()` function
- Verify risk cap is applied: `risk_pct = min(risk_pct, 5.0)`
- Check logs for "RISK-BASED sizing" messages

### Issue: TP/SL not being set
**Solution:**
- Check exchange API permissions (must have "Trade" permission)
- Verify emergency close system is working
- Check logs for "EMERGENCY CLOSE" messages

---

## 📝 User Settings

### Auto-Mode Setting:
Users can enable/disable auto-mode in `/settings`:
- **Enabled (default):** Bot auto-switches based on market
- **Disabled:** User manually selects mode (not recommended)

### Risk Settings:
- **Risk per Trade:** User can set 1-10% (scalping auto-caps at 5%)
- **Leverage:** User can set 1-125x (scalping auto-caps at 10x)
- **Margin Mode:** Cross or Isolated

---

## 🎯 Best Practices

### For Users:
1. ✅ Keep auto-mode enabled (optimal performance)
2. ✅ Start with conservative risk (2-3%)
3. ✅ Use recommended leverage (10-20x)
4. ✅ Monitor dashboard regularly
5. ✅ Don't disable TP/SL protection

### For Admins:
1. ✅ Monitor auto mode switcher logs
2. ✅ Check user feedback on mode switches
3. ✅ Verify market sentiment accuracy
4. ✅ Review trade performance by mode
5. ✅ Keep safety features enabled

---

## 📞 Support

### Common User Questions:

**Q: Why did my mode change automatically?**
A: The bot detected a market condition change and switched to the optimal mode for better performance.

**Q: Can I disable auto-mode?**
A: Yes, go to /settings and disable auto-mode. However, we recommend keeping it enabled for best results.

**Q: Why is my scalping risk capped at 5%?**
A: This is a safety feature to protect your capital. Scalping is high-frequency trading and requires conservative risk management.

**Q: What happens if TP/SL fails to set?**
A: The bot will immediately close the position to protect your capital. You'll receive a notification.

**Q: Can I use StackMentor with small balance?**
A: Yes! StackMentor is now available for all balance levels (no $60 minimum).

---

**Last Updated:** April 7, 2026
**System Version:** v2.0 (Auto Mode Switching)
**Status:** ✅ Fully Operational
