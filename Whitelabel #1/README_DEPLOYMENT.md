# Whitelabel #1 Bot - Deployment Guide

## Bot Info
- **Bot ID**: 8744237679
- **Bot Name**: CryptoMentor AI (Whitelabel #1)
- **Admin**: 1234500002
- **Focus**: Automated Trading Only (No Signal Generation)

## Features

✅ **Automated Trading**
- Bitunix futures trading with AI signals
- Real-time PnL tracking via WebSocket
- Risk management (SL/TP)
- 24/7 automated execution

✅ **User Management**
- Welcome credits for new users
- Supabase database integration
- User registration & tracking

✅ **License System**
- License-based billing via central server
- DEV MODE for local testing (no license required)
- Cache fallback for API downtime

## Quick Start

### Local Testing (DEV MODE)
```bash
cd "Whitelabel #1"
python bot.py
```

Bot will run in DEV MODE (no license check) if `LICENSE_API_URL` is empty in `.env`.

### Production Deployment

#### 1. Configure Environment
```bash
cp .env.example .env
nano .env
```

Required settings:
```env
# Telegram
BOT_TOKEN=<REDACTED_TELEGRAM_BOT_TOKEN>
ADMIN1=<REDACTED_ADMIN_ID>

# Supabase (separate instance for WL#1)
SUPABASE_URL=https://jajtwunmngmturqwjpum.supabase.co
SUPABASE_ANON_KEY=<REDACTED_SUPABASE_KEY>
SUPABASE_SERVICE_KEY=<REDACTED_SUPABASE_KEY>

# License Server (for production)
WL_ID=<REDACTED_UUID>
WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>
LICENSE_API_URL=http://147.93.156.165:8080

# Bot Settings
WELCOME_CREDITS=100
BOT_NAME=CryptoMentor AI
BOT_TAGLINE=Your AI Crypto Trading Assistant

# Encryption (for API keys)
ENCRYPTION_KEY=<REDACTED_ENCRYPTION_KEY>
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Setup Database
Run SQL setup in your Supabase instance:
```bash
cat db/setup.sql
```

#### 4. Run Bot

**Option A: Direct Run**
```bash
python bot.py
```

**Option B: With systemd (Recommended for VPS)**
```bash
# Copy service file
sudo cp ../whitelabel1.service /etc/systemd/system/

# Edit WorkingDirectory path if needed
sudo nano /etc/systemd/system/whitelabel1.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable whitelabel1
sudo systemctl start whitelabel1

# Check status
sudo systemctl status whitelabel1

# View logs
sudo journalctl -u whitelabel1 -f
```

## Available Commands

### User Commands
- `/start` - Start bot & setup autotrade
- `/autotrade` - AutoTrade dashboard
- `/help` - Show help message
- `/status` - Check bot status

### Admin Commands
(Admin only - configured via ADMIN1 in .env)
- Access admin panel via bot

## Bot Flow

### New User Flow
1. User sends `/start`
2. Bot registers user in Supabase
3. User receives welcome credits
4. Bot shows autotrade intro with buttons:
   - "🤖 Start Auto Trading" → Setup flow
   - "❓ Help" → Help message

### Returning User Flow
1. User sends `/start`
2. Bot checks if API keys exist
3. If yes → Show autotrade dashboard
4. If no → Show setup intro

### Autotrade Setup Flow
1. User clicks "Start Auto Trading"
2. Bot guides through:
   - Bitunix registration (with referral)
   - API key creation
   - Capital & leverage setup
3. Bot starts automated trading

## Architecture

```
Whitelabel #1/
├── bot.py                      # Entry point
├── config.py                   # Configuration loader
├── app/
│   ├── handlers_basic.py       # /start, /help handlers
│   ├── handlers_autotrade.py   # Autotrade setup & dashboard
│   ├── autotrade_engine.py     # Trading logic
│   ├── bitunix_autotrade_client.py  # Bitunix API client
│   ├── bitunix_ws_pnl.py       # WebSocket PnL tracking
│   ├── license_guard.py        # License validation
│   ├── supabase_repo.py        # Database operations
│   ├── users_repo.py           # User management
│   ├── trade_history.py        # Trade tracking
│   └── providers/
│       └── data_provider.py    # Isolated API keys
└── data/
    └── license_cache.json      # License cache (auto-generated)
```

## License System

### Production Mode
Bot checks license status:
- **On startup**: Must pass license check to start
- **Every 24 hours**: Periodic validation
- **Cache fallback**: Uses cache if API unreachable (max 48h)

### DEV MODE
Set `LICENSE_API_URL=` (empty) in .env to skip license checks for local testing.

## Differences from Main Bot

| Feature | Main Bot (Bismillah) | Whitelabel #1 |
|---------|---------------------|---------------|
| Signal Generation | ✅ Yes | ❌ No |
| AI Analysis | ✅ Yes | ❌ No |
| Manual Signals | ✅ Yes | ❌ No |
| AutoTrade | ✅ Yes | ✅ Yes |
| License System | ❌ No | ✅ Yes |
| Database | Shared | Isolated |
| API Rate Limits | Shared | Isolated |

## Troubleshooting

### Bot won't start
1. Check if LICENSE_API_URL is reachable
2. For testing, set `LICENSE_API_URL=` (empty) to run in DEV MODE
3. Check logs: `sudo journalctl -u whitelabel1 -n 50`

### License check failed
1. Verify `WL_ID` and `WL_SECRET_KEY` are correct
2. Check if license server is running at `LICENSE_API_URL`
3. Ensure license has sufficient balance

### Bot not responding to commands
1. Check if bot is running: `systemctl status whitelabel1`
2. Verify BOT_TOKEN is correct
3. Check Telegram API connectivity

### Database errors
1. Verify Supabase credentials in .env
2. Check if database tables exist (run setup.sql)
3. Ensure ENCRYPTION_KEY is set for API key storage

## Running Both Bots on Same VPS

Yes, you can run both CryptoMentor (main) and Whitelabel #1 on the same VPS:

### Resource Requirements
- **RAM**: 2GB minimum (1GB per bot)
- **CPU**: 2 cores
- **Storage**: 10GB
- **Network**: Stable for WebSocket connections

### Isolation
Both bots are fully isolated:
- ✅ Different bot tokens
- ✅ Separate Supabase instances
- ✅ Isolated API rate limits
- ✅ Independent processes

### Running Both
```bash
# Main bot
sudo systemctl start cryptomentor

# Whitelabel #1
sudo systemctl start whitelabel1

# Check both
sudo systemctl status cryptomentor whitelabel1
```

## Support

For issues or questions, contact the main CryptoMentor admin.

## License

This is a whitelabel instance of CryptoMentor AI. License managed by central license server.

