# Scalping Mode - Quick Start Guide

## 🎯 What is Scalping Mode?

Scalping Mode adalah fitur trading high-frequency yang menggunakan timeframe 5 menit untuk menangkap pergerakan harga cepat dengan target profit 1.5R dan maksimal holding time 30 menit.

### Perbedaan Scalping vs Swing Mode

| Feature | Scalping Mode (5M) | Swing Mode (15M) |
|---------|-------------------|------------------|
| **Timeframe** | 5 minutes | 15 minutes |
| **Scan Interval** | 15 seconds | 45 seconds |
| **Trades/Day** | 10-20 trades | 2-3 trades |
| **Profit Target** | Single TP at 1.5R | 3-tier TP (StackMentor) |
| **Max Hold Time** | 30 minutes | No limit |
| **Trading Pairs** | BTC, ETH | BTC, ETH, SOL, BNB |
| **Min Confidence** | 80% | 68% |
| **Strategy** | Quick in-out | Trend following |

## 🚀 How to Enable Scalping Mode

### Step 1: Open AutoTrade Dashboard
```
/autotrade
```

### Step 2: Click Trading Mode Button
Klik tombol **"⚙️ Trading Mode"** di dashboard

### Step 3: Select Scalping Mode
Klik **"⚡ Scalping Mode (5M)"**

### Step 4: Confirm
Bot akan restart engine dan mulai scanning dengan parameter scalping

## 📊 Scalping Mode Features

### 1. Fast Signal Generation
- Scan setiap 15 detik
- Analisis 15M trend + 5M entry trigger
- RSI extreme detection (>70 or <30)
- Volume spike detection (>2x average)

### 2. Single Take Profit
- TP di 1.5R (Risk:Reward 1:1.5)
- Close 100% position saat TP hit
- No partial closes (berbeda dengan StackMentor)

### 3. Max Hold Time Protection
- Posisi otomatis close setelah 30 menit
- Mencegah holding terlalu lama
- Maximize trading opportunities

### 4. Cooldown System
- 5 menit cooldown per symbol
- Mencegah overtrading
- Reduce fee accumulation

### 5. High Confidence Filter
- Minimum 80% confidence
- Volume spike required (>2x)
- 15M trend validation mandatory

## 📈 Trading Strategy

### Entry Criteria
1. **15M Trend Analysis**
   - Uptrend: Price > EMA21 > EMA50 → LONG only
   - Downtrend: Price < EMA21 < EMA50 → SHORT only
   - Neutral: No trade

2. **5M Entry Trigger**
   - LONG: RSI < 30 (oversold) + Volume > 2x
   - SHORT: RSI > 70 (overbought) + Volume > 2x

3. **Confidence Calculation**
   - Base: 80%
   - Volume > 3x: +5%
   - Order Block/FVG: +5%
   - Max: 95%

### Exit Strategy
1. **Take Profit (TP)**
   - TP = Entry + (1.5 × SL distance)
   - Close 100% position

2. **Stop Loss (SL)**
   - SL = Entry ± (1.5 × ATR 5M)
   - No breakeven move

3. **Max Hold Time**
   - Force close after 30 minutes
   - Close at market price

## ⚠️ Risk Management

### Circuit Breaker
- Daily loss limit: 5% of capital
- Applies to both scalping + swing trades
- Auto-stop when limit reached

### Position Limits
- Max 4 concurrent positions
- Shared between scalping and swing
- No duplicate positions on same symbol

### Cooldown
- 5 minutes between signals on same pair
- Prevents overtrading
- Reduces fee impact

## 💰 Expected Performance

### Volume Impact
- **Current (Swing):** 2-3 trades/day
- **With Scalping:** 10-20 trades/day
- **Volume Increase:** +50-80%

### Win Rate Target
- **Target:** 60%+ win rate
- **Average R:R:** 1.5
- **Profit Factor:** >1.5

### Fee Consideration
- More trades = more fees
- Typical fee: 0.02-0.05% per trade
- 20 trades/day = 0.4-1% daily fees
- Ensure profit > fees

## 📱 Notifications

### Position Opened
```
⚡ SCALP Trade Opened

Symbol: BTCUSDT
Side: LONG
Entry: 67000.00
TP: 68500.00 (1.5R)
SL: 66000.00
Confidence: 85%
Max Hold: 30 minutes

Reasons:
• 15M uptrend + 5M oversold
• Volume spike 2.5x
```

### Position Closed (TP)
```
✅ TP Hit!

Symbol: BTCUSDT
Entry: 67000.00
Exit: 68500.00
PnL: +150.00 USDT 🎉
```

### Position Closed (Max Hold)
```
⏰ Position Closed (Max Hold Time)

Symbol: BTCUSDT
Entry: 67000.00
Exit: 67800.00
Hold Time: 30 minutes
PnL: +80.00 USDT
```

## 🔧 Troubleshooting

### No Signals Generated
**Possible Reasons:**
- Market too flat (ATR < 0.3%)
- Market too volatile (ATR > 10%)
- No clear 15M trend
- RSI not extreme enough
- Volume too low (<2x)
- Cooldown active

**Solution:** Wait for better market conditions

### Frequent Max Hold Closes
**Possible Reasons:**
- Market ranging (no clear direction)
- TP too far (1.5R might not hit in 30 min)

**Solution:** This is normal in ranging markets

### High Fee Impact
**Possible Reasons:**
- Too many trades
- Small profit per trade

**Solution:** 
- Monitor daily PnL
- Ensure profit > fees
- Consider switching to Swing Mode if fees too high

## 📊 Performance Monitoring

### Check Trading Stats
```
/autotrade → Trade History
```

Filter by:
- Trade Type: Scalping
- Timeframe: 5m

### Key Metrics to Track
- Win Rate (target: >60%)
- Average R:R (should be ~1.5)
- Average Hold Time (should be <30 min)
- Daily PnL (should be positive after fees)
- Max Hold Time violations (should be low)

## 🔄 Switching Back to Swing Mode

### Step 1: Open Trading Mode Menu
```
/autotrade → ⚙️ Trading Mode
```

### Step 2: Select Swing Mode
Klik **"📊 Swing Mode (15M)"**

### Step 3: Confirm
Bot akan restart dengan parameter swing

## 💡 Tips for Success

### 1. Start Small
- Test dengan capital kecil dulu
- Monitor performance 1-2 minggu
- Scale up jika profitable

### 2. Monitor Fees
- Track daily fee accumulation
- Ensure profit > fees
- Consider fee rebates from exchange

### 3. Market Conditions
- Scalping works best in trending markets
- Avoid during major news events
- Best during high liquidity hours

### 4. Risk Management
- Never risk more than 1-2% per trade
- Use proper position sizing
- Respect circuit breaker

### 5. Patience
- Not every scan will generate signal
- Quality > quantity
- Wait for high-confidence setups

## 📞 Support

### Get Help
- Check logs: `/autotrade → Status`
- Report issues to admin
- Join community for tips

### Feedback
- Share your experience
- Suggest improvements
- Help improve the system

---

## 🎯 Quick Commands

| Command | Description |
|---------|-------------|
| `/autotrade` | Open dashboard |
| Click "⚙️ Trading Mode" | Open mode selector |
| Click "⚡ Scalping Mode" | Enable scalping |
| Click "📊 Swing Mode" | Enable swing |
| Click "📈 Trade History" | View trades |
| Click "📊 Status Portfolio" | Check balance |

---

**Happy Scalping! ⚡💰**

*Remember: Scalping requires active monitoring and discipline. Always trade responsibly.*
