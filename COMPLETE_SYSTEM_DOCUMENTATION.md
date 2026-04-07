# CryptoMentor Complete System Documentation

**Date:** April 7, 2026  
**Version:** 2.0 (Auto Mode Switching + StackMentor Integration)  
**Status:** ✅ PRODUCTION

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Bismillah Bot (Main)](#bismillah-bot)
4. [Whitelabel System](#whitelabel-system)
5. [License Server](#license-server)
6. [AutoTrade System](#autotrade-system)
7. [Database Schema](#database-schema)
8. [Deployment](#deployment)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 System Overview

CryptoMentor adalah platform trading automation yang terdiri dari 3 komponen utama:

### 1. **Bismillah Bot** (Main Product)
- Telegram bot untuk crypto trading signals & automation
- AutoTrade engine dengan 2 mode (Scalping & Swing)
- StackMentor 3-tier TP system
- Auto mode switching berdasarkan market sentiment
- Multi-exchange support (Bitunix, BingX, Binance, Bybit)

### 2. **Whitelabel System**
- White-label solution untuk partners
- License-based billing system
- Isolated database per whitelabel
- Custom branding support

### 3. **License Server**
- Centralized license management
- Billing & deposit monitoring
- API for license validation
- Automated billing cron jobs

---


## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USERS (Telegram)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐         ┌──────────────┐
│ Bismillah Bot │         │ Whitelabel   │
│   (Main)      │         │   Bots       │
└───────┬───────┘         └──────┬───────┘
        │                        │
        │                        │
        ├────────────────────────┤
        │                        │
        ▼                        ▼
┌────────────────────────────────────┐
│      License Server (API)          │
│  - License validation              │
│  - Billing management              │
│  - Deposit monitoring              │
└────────────────┬───────────────────┘
                 │
                 ▼
┌────────────────────────────────────┐
│         Supabase Database          │
│  - User data                       │
│  - Trading sessions                │
│  - Trade history                   │
│  - StackMentor tracking            │
└────────────────────────────────────┘
```

### Component Interaction

```
User → Telegram → Bot → Exchange API → Market
                   ↓
              Supabase DB
                   ↓
           Background Tasks:
           - Auto Mode Switcher (15 min)
           - Engine Restore (on restart)
           - Maintenance Notifier (daily)
           - StackMentor Monitor (continuous)
```

---

## 📦 Bismillah Bot (Main Product)

### Core Features

1. **Free Signals**
   - Manual signal generation
   - AI-powered analysis
   - Support/resistance detection
   - Risk management suggestions

2. **Premium Signals**
   - Higher frequency
   - Advanced analysis
   - Priority support

3. **AutoTrade**
   - 2 modes: Scalping & Swing
   - Auto mode switching
   - StackMentor 3-tier TP
   - Multi-exchange support

4. **Skills & Education**
   - Trading tutorials
   - Risk management guides
   - Market analysis lessons

5. **Community Features**
   - Community partners
   - Referral system
   - Social proof

### Key Files

**Entry Point:**
- `bot.py` - Main bot class
- `main.py` - Application launcher

**AutoTrade:**
- `app/autotrade_engine.py` - Swing mode
- `app/scalping_engine.py` - Scalping mode (NEW: StackMentor)
- `app/stackmentor.py` - 3-tier TP system
- `app/auto_mode_switcher.py` - Auto switching
- `app/market_sentiment_detector.py` - Market analysis

**Handlers:**
- `app/handlers_autotrade.py` - AutoTrade commands
- `app/handlers_manual_signals.py` - Manual signals
- `app/handlers_free_signal.py` - Free signals
- `app/handlers_skills.py` - Education
- `app/handlers_community.py` - Community

**Exchange Clients:**
- `app/bitunix_autotrade_client.py`
- `app/bingx_autotrade_client.py`
- `app/binance_autotrade_client.py`
- `app/bybit_autotrade_client.py`

**Database:**
- `app/supabase_repo.py` - Supabase operations
- `database.py` - SQLite (legacy)

---


## 🏷️ Whitelabel System

### Overview

Whitelabel system memungkinkan partners untuk:
- Deploy bot dengan branding sendiri
- Isolated database per whitelabel
- License-based billing
- Custom configuration

### Directory Structure

```
Whitelabel #1/
├── bot.py                    # Whitelabel bot instance
├── config.py                 # Custom configuration
├── .env                      # Environment variables
│
├── app/
│   ├── license_middleware.py  # License validation
│   ├── license_guard.py       # License enforcement
│   ├── handlers_basic.py      # Basic commands
│   ├── handlers_admin.py      # Admin commands
│   └── providers/
│       └── data_provider.py   # Data provider
│
└── db/
    └── setup.sql              # Database schema
```

### Key Features

1. **License Validation**
   - Validates license on startup
   - Checks license status before commands
   - Auto-disable if license expired

2. **Isolated Database**
   - Separate Supabase project per whitelabel
   - No data sharing between whitelabels

3. **Custom Branding**
   - Custom bot name
   - Custom welcome message
   - Custom commands

### Configuration

**File:** `Whitelabel #1/.env`

```env
# Bot Configuration
BOT_TOKEN=your_bot_token
BOT_NAME=YourBotName

# License Server
LICENSE_SERVER_URL=https://license-server.com
LICENSE_KEY=your_license_key

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=<REDACTED_SUPABASE_KEY>
```

---

## 🔐 License Server

### Overview

Centralized license management system untuk:
- License validation
- Billing management
- Deposit monitoring
- Usage tracking

### Directory Structure

```
license_server/
├── license_api.py           # FastAPI server
├── license_manager.py       # License operations
├── billing_cron.py          # Billing automation
├── deposit_monitor.py       # Deposit tracking
├── register_wl.py           # Register whitelabel
├── register_test_wl.py      # Test registration
├── test_connections.py      # Connection tests
├── .env                     # Configuration
│
└── db/
    └── setup.sql            # Database schema
```

### API Endpoints

**Base URL:** `https://license-server.com`

1. **Validate License**
   ```
   POST /api/validate
   Body: { "license_key": "xxx" }
   Response: { "valid": true, "expires_at": "2026-12-31" }
   ```

2. **Check Status**
   ```
   GET /api/status/{license_key}
   Response: { "status": "active", "balance": 100.00 }
   ```

3. **Update Usage**
   ```
   POST /api/usage
   Body: { "license_key": "xxx", "usage": 10 }
   ```

### Billing System

**File:** `license_server/billing_cron.py`

**How It Works:**
1. Runs daily (cron job)
2. Checks all active licenses
3. Deducts daily fee from balance
4. Suspends license if balance < 0
5. Sends notification to owner

**Daily Fee:** $1.00 per day (configurable)

### Deposit Monitoring

**File:** `license_server/deposit_monitor.py`

**How It Works:**
1. Monitors deposit wallet
2. Detects incoming deposits
3. Credits license balance
4. Sends confirmation notification

---


## 💾 Database Schema

### Supabase Tables

#### 1. `users`
User registration and profile
```sql
- telegram_id (PK)
- username
- first_name
- last_name
- language
- credits
- is_premium
- referral_code
- created_at
```

#### 2. `autotrade_sessions`
AutoTrade user sessions
```sql
- telegram_id (PK)
- initial_deposit
- current_balance
- total_profit
- status (active/inactive)
- leverage
- margin_mode
- risk_mode
- risk_per_trade
- auto_mode_enabled
- engine_active
- trading_mode (scalping/swing)
- started_at
- updated_at
```

#### 3. `autotrade_trades`
Trade history
```sql
- id (PK)
- telegram_id
- symbol
- side (BUY/SELL)
- entry_price
- exit_price
- quantity
- leverage
- pnl_usdt
- status (open/closed_tp/closed_sl)
- opened_at
- closed_at
```

#### 4. `tp_partial_tracking`
StackMentor 3-tier TP tracking
```sql
- id (PK)
- telegram_id
- symbol
- side
- entry_price
- quantity
- leverage
- tp1_price, tp1_qty, tp1_hit
- tp2_price, tp2_qty, tp2_hit
- tp3_price, tp3_qty, tp3_hit
- sl_price
- sl_moved_to_breakeven
- status
- created_at
- updated_at
```

#### 5. `user_api_keys`
Encrypted API keys
```sql
- telegram_id (PK)
- exchange
- api_key
- api_secret_enc (encrypted)
- key_hint
- created_at
- updated_at
```

#### 6. `community_partners`
Community partner management
```sql
- id (PK)
- community_code
- community_name
- owner_telegram_id
- bitunix_referral_code
- bitunix_referral_url
- status (active/inactive)
- created_at
```

#### 7. `user_skills`
User education progress
```sql
- telegram_id (PK)
- skill_id
- completed
- score
- completed_at
```

---

## 🚀 Deployment

### VPS Setup

**Server:** root@147.93.156.165  
**Path:** `/root/cryptomentor-bot/`  
**Service:** `cryptomentor.service`

### Deployment Commands

```bash
# 1. Deploy files
scp -r Bismillah/ root@147.93.156.165:/root/cryptomentor-bot/

# 2. Install dependencies
ssh root@147.93.156.165 "cd /root/cryptomentor-bot && pip install -r requirements.txt"

# 3. Restart service
ssh root@147.93.156.165 "systemctl restart cryptomentor"

# 4. Check status
ssh root@147.93.156.165 "systemctl status cryptomentor"

# 5. Monitor logs
ssh root@147.93.156.165 "journalctl -u cryptomentor -f"
```

### Service Configuration

**File:** `/etc/systemd/system/cryptomentor.service`

```ini
[Unit]
Description=CryptoMentor Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cryptomentor-bot
ExecStart=/root/cryptomentor-bot/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---


## 📊 Monitoring

### Key Metrics

1. **Service Health**
   ```bash
   systemctl status cryptomentor
   ```

2. **Active Users**
   ```sql
   SELECT COUNT(*) FROM autotrade_sessions WHERE engine_active = true;
   ```

3. **Trade Performance**
   ```sql
   SELECT 
     COUNT(*) as total_trades,
     SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) as winning_trades,
     AVG(pnl_usdt) as avg_pnl
   FROM autotrade_trades
   WHERE closed_at > NOW() - INTERVAL '24 hours';
   ```

4. **StackMentor Performance**
   ```sql
   SELECT 
     COUNT(*) as total_positions,
     SUM(CASE WHEN tp1_hit THEN 1 ELSE 0 END) as tp1_hits,
     SUM(CASE WHEN tp2_hit THEN 1 ELSE 0 END) as tp2_hits,
     SUM(CASE WHEN tp3_hit THEN 1 ELSE 0 END) as tp3_hits
   FROM tp_partial_tracking
   WHERE created_at > NOW() - INTERVAL '24 hours';
   ```

### Log Monitoring

**Important Log Patterns:**

1. **Auto Mode Switching**
   ```bash
   journalctl -u cryptomentor | grep "AutoModeSwitcher"
   ```

2. **StackMentor Positions**
   ```bash
   journalctl -u cryptomentor | grep "StackMentor position opened"
   ```

3. **Errors**
   ```bash
   journalctl -u cryptomentor -p err -n 50
   ```

4. **Trade Execution**
   ```bash
   journalctl -u cryptomentor | grep "Order placed"
   ```

### Alerts

**Set up alerts for:**
- Service down
- High error rate
- Low trade success rate
- StackMentor failures
- License expiration

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Bot Not Responding
**Symptoms:** Bot doesn't respond to commands

**Solutions:**
```bash
# Check service status
systemctl status cryptomentor

# Restart service
systemctl restart cryptomentor

# Check logs
journalctl -u cryptomentor -n 100
```

#### 2. AutoTrade Not Starting
**Symptoms:** Engine shows "inactive" after start

**Solutions:**
- Check API keys are valid
- Verify exchange connection
- Check balance is sufficient
- Review error logs

#### 3. StackMentor Not Working
**Symptoms:** Positions don't have 3-tier TP

**Solutions:**
- Verify StackMentor module is loaded
- Check database table exists
- Review StackMentor logs
- Verify exchange supports TP orders

#### 4. Auto Mode Switcher Not Running
**Symptoms:** Mode doesn't switch automatically

**Solutions:**
```bash
# Check if switcher is running
journalctl -u cryptomentor | grep "Auto Mode Switcher started"

# Check recent switches
journalctl -u cryptomentor | grep "AutoModeSwitcher" | tail -20

# Verify users have auto_mode_enabled
SELECT telegram_id, auto_mode_enabled FROM autotrade_sessions;
```

#### 5. License Validation Failed
**Symptoms:** Whitelabel bot shows license error

**Solutions:**
- Check license server is running
- Verify license key is correct
- Check license balance
- Review license expiration date

---

## 📚 Additional Documentation

### Detailed Guides

1. **AutoTrade System**
   - See: `docs/02_AUTOTRADE_SYSTEM.md`
   - Covers: Trading modes, StackMentor, Auto switching

2. **StackMentor Integration**
   - See: `SCALPING_STACKMENTOR_INTEGRATION.md`
   - Covers: Implementation details, benefits, testing

3. **Deployment Guide**
   - See: `DEPLOY_SCALPING_STACKMENTOR.md`
   - Covers: Deployment steps, verification, rollback

4. **Verification Checklist**
   - See: `VERIFICATION_CHECKLIST.md`
   - Covers: Code verification, testing, monitoring

---

## 🎯 Quick Reference

### Important Commands

```bash
# Deploy
scp file.py root@147.93.156.165:/root/cryptomentor-bot/path/

# Restart
ssh root@147.93.156.165 "systemctl restart cryptomentor"

# Logs
ssh root@147.93.156.165 "journalctl -u cryptomentor -f"

# Status
ssh root@147.93.156.165 "systemctl status cryptomentor"
```

### Important Files

- **Main Bot:** `Bismillah/bot.py`
- **AutoTrade:** `Bismillah/app/autotrade_engine.py`
- **Scalping:** `Bismillah/app/scalping_engine.py`
- **StackMentor:** `Bismillah/app/stackmentor.py`
- **Auto Switcher:** `Bismillah/app/auto_mode_switcher.py`

### Important URLs

- **VPS:** root@147.93.156.165
- **Supabase:** https://xrbqnocovfymdikngaza.supabase.co
- **License Server:** (configure in .env)

---

**Last Updated:** April 7, 2026  
**Version:** 2.0  
**Status:** ✅ Production Ready
