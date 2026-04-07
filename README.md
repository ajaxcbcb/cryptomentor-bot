# CryptoMentor - Automated Trading Platform

**Version:** 2.0  
**Status:** ✅ Production  
**Last Updated:** April 7, 2026

---

## 🎯 Overview

CryptoMentor adalah platform trading automation yang komprehensif dengan fitur:

- 🤖 **AutoTrade System** - Automated copy trading dengan 2 mode (Scalping & Swing)
- 📊 **StackMentor** - 3-tier TP system untuk maximize profit
- 🔄 **Auto Mode Switching** - Otomatis switch mode berdasarkan market sentiment
- 🏦 **Multi-Exchange** - Support Bitunix, BingX, Binance, Bybit
- 🏷️ **Whitelabel System** - White-label solution untuk partners
- 🔐 **License Server** - Centralized license management

---

## 📁 Project Structure

```
.
├── Bismillah/              # Main bot (production)
│   ├── app/               # Core application modules
│   ├── db/                # Database migrations
│   └── bot.py             # Main entry point
│
├── Whitelabel #1/         # Whitelabel template
│   ├── app/               # Whitelabel modules
│   └── bot.py             # Whitelabel bot
│
├── license_server/        # License management
│   ├── license_api.py     # API server
│   ├── billing_cron.py    # Billing automation
│   └── deposit_monitor.py # Deposit tracking
│
├── docs/                  # Documentation
│   ├── 01_BISMILLAH_BOT_OVERVIEW.md
│   └── 02_AUTOTRADE_SYSTEM.md
│
└── db/                    # Shared database schemas
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL (Supabase)
- Telegram Bot Token
- Exchange API Keys

### Installation

```bash
# Clone repository
git clone <repository-url>
cd cryptomentor

# Install dependencies
pip install -r Bismillah/requirements.txt

# Configure environment
cp Bismillah/.env.example Bismillah/.env
# Edit .env with your credentials

# Run bot
cd Bismillah
python main.py
```

---

## 📚 Documentation

### Complete Documentation
- **[Complete System Documentation](COMPLETE_SYSTEM_DOCUMENTATION.md)** - Comprehensive system overview
- **[Documentation Index](README_DOCUMENTATION.md)** - All documentation files

### Key Features
- **[AutoTrade System](docs/02_AUTOTRADE_SYSTEM.md)** - Trading modes & strategies
- **[StackMentor Integration](SCALPING_STACKMENTOR_INTEGRATION.md)** - 3-tier TP system
- **[Quick Reference Guide](QUICK_REFERENCE_GUIDE.md)** - Quick lookup reference

### Deployment
- **[Deployment Guide](DEPLOY_SCALPING_STACKMENTOR.md)** - Step-by-step deployment
- **[Deployment Success](DEPLOYMENT_SUCCESS_STACKMENTOR.md)** - Latest deployment report
- **[Verification Checklist](VERIFICATION_CHECKLIST.md)** - QA checklist

---

## 🎯 Key Features

### 1. AutoTrade System

**Scalping Mode (5M)**
- StackMentor 3-tier TP (60%/30%/10%)
- Max hold time: 30 minutes
- Max risk: 5% per trade
- Auto-breakeven when TP1 hit

**Swing Mode (15M)**
- StackMentor 3-tier TP (60%/30%/10%)
- Multi-timeframe confluence
- BTC bias filter
- 13 trading pairs

### 2. Auto Mode Switching

- Runs every 15 minutes
- Analyzes BTC market sentiment
- Auto-switches between Scalping & Swing
- Confidence threshold: 50%

### 3. StackMentor System

- 3-tier TP for maximum profit
- TP1: 60% @ R:R 1:2
- TP2: 30% @ R:R 1:3
- TP3: 10% @ R:R 1:10
- Auto-breakeven protection

### 4. Multi-Exchange Support

- Bitunix
- BingX
- Binance
- Bybit

---

## 🏗️ Architecture

```
Users (Telegram)
       ↓
   Bot Layer
       ↓
┌──────┴──────┐
│             │
Bismillah   Whitelabel
   Bot         Bots
│             │
└──────┬──────┘
       ↓
License Server
       ↓
   Supabase DB
       ↓
Exchange APIs
```

---

## 🔧 Configuration

### Environment Variables

**Bismillah Bot** (`Bismillah/.env`):
```env
BOT_TOKEN=your_telegram_bot_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=<REDACTED_SUPABASE_KEY>
```

**Whitelabel** (`Whitelabel #1/.env`):
```env
BOT_TOKEN=your_bot_token
LICENSE_KEY=your_license_key
LICENSE_SERVER_URL=https://license-server.com
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=<REDACTED_SUPABASE_KEY>
```

**License Server** (`license_server/.env`):
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=<REDACTED_SUPABASE_KEY>
API_PORT=8000
```

---

## 📊 Database Schema

### Main Tables

- `users` - User registration & profile
- `autotrade_sessions` - AutoTrade sessions
- `autotrade_trades` - Trade history
- `tp_partial_tracking` - StackMentor TP tracking
- `user_api_keys` - Encrypted API keys
- `community_partners` - Community management

See: [Complete System Documentation](COMPLETE_SYSTEM_DOCUMENTATION.md#database-schema)

---

## 🚀 Deployment

### Production Deployment

```bash
# Deploy to VPS
scp -r Bismillah/ root@your-vps:/root/cryptomentor-bot/

# Install dependencies
ssh root@your-vps "cd /root/cryptomentor-bot && pip install -r requirements.txt"

# Setup systemd service
ssh root@your-vps "systemctl enable cryptomentor"
ssh root@your-vps "systemctl start cryptomentor"

# Check status
ssh root@your-vps "systemctl status cryptomentor"
```

See: [Deployment Guide](DEPLOY_SCALPING_STACKMENTOR.md)

---

## 📈 Monitoring

### Service Status
```bash
systemctl status cryptomentor
```

### Logs
```bash
journalctl -u cryptomentor -f
```

### Key Metrics
```sql
-- Active users
SELECT COUNT(*) FROM autotrade_sessions WHERE engine_active = true;

-- Trade performance
SELECT 
  COUNT(*) as total_trades,
  AVG(pnl_usdt) as avg_pnl
FROM autotrade_trades
WHERE closed_at > NOW() - INTERVAL '24 hours';
```

---

## 🔒 Security

### Best Practices

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Encrypt API keys** - Use AES-256-GCM encryption
3. **Use environment variables** - Never hardcode credentials
4. **Regular backups** - Backup database regularly
5. **Monitor logs** - Check for suspicious activity

### API Key Encryption

API keys are encrypted using AES-256-GCM before storage:
```python
from app.lib.crypto import encrypt, decrypt

encrypted = encrypt(api_secret)
decrypted = decrypt(encrypted)
```

---

## 🤝 Contributing

### Development Workflow

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Update documentation
5. Submit pull request

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Write tests

---

## 📞 Support

### Documentation
- [Complete System Documentation](COMPLETE_SYSTEM_DOCUMENTATION.md)
- [Quick Reference Guide](QUICK_REFERENCE_GUIDE.md)
- [Troubleshooting](COMPLETE_SYSTEM_DOCUMENTATION.md#troubleshooting)

### Issues
For bugs or feature requests, please create an issue on GitHub.

---

## 📝 Changelog

### Version 2.0 (April 7, 2026)

**Major Updates:**
- ✅ StackMentor integration for Scalping mode
- ✅ Auto mode switching based on market sentiment
- ✅ 3-tier TP system (60%/30%/10%)
- ✅ Auto-breakeven protection
- ✅ Emergency close if SL fails
- ✅ Comprehensive documentation

**Bug Fixes:**
- Fixed /autotrade command error
- Fixed indentation issues
- Improved error handling

See: [Deployment Success Report](DEPLOYMENT_SUCCESS_STACKMENTOR.md)

---

## 📄 License

Proprietary - All rights reserved

---

## 👥 Team

**Development Team**
- Lead Developer: [Your Name]
- Contributors: [Team Members]

---

## 🙏 Acknowledgments

- Telegram Bot API
- Supabase
- Exchange APIs (Bitunix, BingX, Binance, Bybit)

---

**Last Updated:** April 7, 2026  
**Version:** 2.0  
**Status:** ✅ Production Ready
