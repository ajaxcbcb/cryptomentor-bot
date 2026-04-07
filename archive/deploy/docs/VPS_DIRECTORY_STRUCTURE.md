# VPS Directory Structure - CryptoMentor Bots

Dokumentasi lengkap struktur direktori di VPS Contabo untuk bot CryptoMentor dan Whitelabel.

## VPS Information

- **IP Address**: 147.93.156.165
- **User**: root
- **OS**: Linux (Ubuntu/Debian)
- **Base Directory**: /root/cryptomentor-bot

## Directory Structure

```
/root/cryptomentor-bot/
├── Bismillah/                          # Bot Pusat (CryptoMentor AI)
│   ├── .env                            # Environment variables (RAHASIA!)
│   ├── bot.py                          # Entry point bot pusat
│   ├── config.py                       # Configuration
│   ├── requirements.txt                # Python dependencies
│   ├── app/                            # Application modules
│   │   ├── handlers_autotrade.py       # Autotrade handlers
│   │   ├── handlers_basic.py           # Basic command handlers
│   │   ├── handlers_deepseek.py        # AI handlers
│   │   ├── handlers_free_signal.py     # Free signal handlers
│   │   ├── handlers_manual_signals.py  # Manual signal handlers
│   │   ├── handlers_skills.py          # Skills handlers
│   │   ├── autotrade_engine.py         # Autotrade engine
│   │   ├── bitunix_autotrade_client.py # Bitunix API client
│   │   ├── bitunix_ws_pnl.py          # Bitunix WebSocket PnL
│   │   ├── supabase_repo.py           # Supabase database
│   │   ├── users_repo.py              # User repository
│   │   ├── trade_history.py           # Trade history
│   │   ├── credits_guard.py           # Credits management
│   │   ├── rate_limiter.py            # Rate limiting
│   │   ├── safe_send.py               # Safe message sending
│   │   ├── scheduler.py               # Task scheduler
│   │   ├── lib/                       # Libraries
│   │   │   ├── auth.py
│   │   │   ├── crypto.py
│   │   │   └── guards.py
│   │   └── providers/                 # Data providers
│   │       ├── advanced_data_provider.py
│   │       ├── alternative_klines_provider.py
│   │       ├── binance_provider.py
│   │       ├── multi_source_provider.py
│   │       └── openai_direct.py
│   ├── data/                          # Runtime data
│   │   ├── autosignal_state.json
│   │   ├── chat_map.json
│   │   ├── dynamic_admins.json
│   │   └── users_local.json
│   └── db/                            # Database schemas
│       └── user_api_keys.sql
│
├── whitelabel-1/                      # Whitelabel Bot #1
│   ├── .env                           # Environment variables (RAHASIA!)
│   ├── bot.py                         # Entry point whitelabel bot
│   ├── config.py                      # Configuration
│   ├── requirements.txt               # Python dependencies
│   ├── app/                           # Application modules (sama seperti Bismillah)
│   │   ├── handlers_autotrade.py
│   │   ├── handlers_basic.py
│   │   ├── license_guard.py          # License validation
│   │   ├── autotrade_engine.py
│   │   ├── bitunix_autotrade_client.py
│   │   ├── supabase_repo.py
│   │   └── providers/
│   │       └── data_provider.py
│   ├── data/                          # Runtime data
│   │   └── license_cache.json        # License cache
│   └── db/                            # Database schemas
│       └── setup.sql
│
├── license_server/                    # License Server (untuk production)
│   ├── .env                           # Environment variables
│   ├── license_api.py                 # FastAPI license server
│   ├── license_manager.py             # License management logic
│   ├── billing_cron.py                # Billing automation
│   ├── deposit_monitor.py             # Deposit monitoring
│   ├── wallet_manager.py              # Wallet management
│   ├── register_wl.py                 # Register whitelabel script
│   ├── requirements.txt               # Python dependencies
│   └── db/
│       └── setup.sql                  # Database schema
│
└── db/                                # Shared database schemas
    ├── setup_supabase.sql
    ├── user_api_keys.sql
    ├── autotrade_trades.sql
    ├── user_skills.sql
    └── add_margin_mode.sql
```

## Systemd Services

### 1. Bot Pusat (CryptoMentor AI)
- **Service File**: `/etc/systemd/system/cryptomentor.service`
- **Working Directory**: `/root/cryptomentor-bot/Bismillah`
- **Command**: `python3 bot.py`
- **Status**: `sudo systemctl status cryptomentor`
- **Logs**: `sudo journalctl -u cryptomentor -f`

### 2. Whitelabel Bot #1
- **Service File**: `/etc/systemd/system/whitelabel1.service`
- **Working Directory**: `/root/cryptomentor-bot/whitelabel-1`
- **Command**: `/root/cryptomentor-bot/whitelabel-1/venv/bin/python bot.py`
- **Status**: `sudo systemctl status whitelabel1`
- **Logs**: `sudo journalctl -u whitelabel1 -f`

### 3. License Server (Optional - untuk production)
- **Service File**: `/etc/systemd/system/license-server.service`
- **Working Directory**: `/root/cryptomentor-bot/license_server`
- **Command**: `python3 license_api.py`
- **Port**: 8080
- **Status**: `sudo systemctl status license-server`

## Important Files & Locations

### Configuration Files (.env)

**Bot Pusat**: `/root/cryptomentor-bot/Bismillah/.env`
```env
BOT_TOKEN=<REDACTED_TELEGRAM_BOT_TOKEN>
ADMIN1=<REDACTED_ADMIN_ID>
SUPABASE_URL=https://jajtwunmngmturqwjpum.supabase.co
SUPABASE_ANON_KEY=<REDACTED_SUPABASE_KEY>
SUPABASE_SERVICE_KEY=<REDACTED_SUPABASE_KEY>
ENCRYPTION_KEY=<REDACTED_ENCRYPTION_KEY>
```

**Whitelabel Bot #1**: `/root/cryptomentor-bot/whitelabel-1/.env`
```env
BOT_TOKEN=<REDACTED_TELEGRAM_BOT_TOKEN>
ADMIN1=<REDACTED_ADMIN_ID>
SUPABASE_URL=https://jajtwunmngmturqwjpum.supabase.co
SUPABASE_ANON_KEY=<REDACTED_SUPABASE_KEY>
SUPABASE_SERVICE_KEY=<REDACTED_SUPABASE_KEY>
WL_ID=61796c-bd62-4ccc-5f45-a7731f7f6692
WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>
LICENSE_API_URL=http://147.93.156.165:8080
```

**License Server**: `/root/cryptomentor-bot/license_server/.env`
```env
SUPABASE_URL=https://jajtwunmngmturqwjpum.supabase.co
SUPABASE_SERVICE_KEY=<REDACTED_SUPABASE_KEY>
TRON_WALLET_ADDRESS=...
TRON_PRIVATE_KEY=...
```

### Virtual Environments

**Whitelabel Bot #1**: `/root/cryptomentor-bot/whitelabel-1/venv/`
- Python packages isolated untuk whitelabel bot
- Activate: `source /root/cryptomentor-bot/whitelabel-1/venv/bin/activate`

## Common Commands

### Service Management
```bash
# Start service
sudo systemctl start cryptomentor
sudo systemctl start whitelabel1

# Stop service
sudo systemctl stop cryptomentor
sudo systemctl stop whitelabel1

# Restart service
sudo systemctl restart cryptomentor
sudo systemctl restart whitelabel1

# Check status
sudo systemctl status cryptomentor
sudo systemctl status whitelabel1

# Enable auto-start on boot
sudo systemctl enable cryptomentor
sudo systemctl enable whitelabel1
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u cryptomentor -f
sudo journalctl -u whitelabel1 -f

# Last 50 lines
sudo journalctl -u cryptomentor -n 50
sudo journalctl -u whitelabel1 -n 50

# Logs from today
sudo journalctl -u cryptomentor --since today
sudo journalctl -u whitelabel1 --since today
```

### Git Operations
```bash
# Pull latest changes
cd /root/cryptomentor-bot/Bismillah
git pull origin main

cd /root/cryptomentor-bot/whitelabel-1
git pull origin main

# Check status
git status

# View changes
git diff
```

### Database Operations
```bash
# Connect to Supabase (via psql if needed)
# Or use Supabase dashboard: https://supabase.com/dashboard

# Backup database
# Use Supabase dashboard or pg_dump
```

## Bot Information

### Bot Pusat (CryptoMentor AI)
- **Bot ID**: 7144237679
- **Bot Username**: @CryptoMentorAI_bot (example)
- **Admin**: 1234500002
- **Database**: Supabase (jajtwunmngmturqwjpum)
- **Features**: Full features (signal generation + autotrade)

### Whitelabel Bot #1
- **Bot ID**: 8744237679
- **Bot Username**: @WhitelabelBot1 (example)
- **Admin**: 1234500002
- **Database**: Supabase (jajtwunmngmturqwjpum) - shared but isolated tables
- **Features**: Autotrade only (no signal generation)
- **License**: WL_ID: 61796c-bd62-4ccc-5f45-a7731f7f6692

## Backup & Recovery

### Important Files to Backup
1. `.env` files (semua bot)
2. `data/` directories (runtime data)
3. Database (Supabase - use dashboard backup)
4. Systemd service files

### Backup Command
```bash
# Backup all .env files
tar -czf env-backup-$(date +%Y%m%d).tar.gz \
  /root/cryptomentor-bot/Bismillah/.env \
  /root/cryptomentor-bot/whitelabel-1/.env \
  /root/cryptomentor-bot/license_server/.env

# Backup data directories
tar -czf data-backup-$(date +%Y%m%d).tar.gz \
  /root/cryptomentor-bot/Bismillah/data \
  /root/cryptomentor-bot/whitelabel-1/data
```

## Troubleshooting

### Bot Not Responding
```bash
# Check if service is running
sudo systemctl status whitelabel1

# Check logs for errors
sudo journalctl -u whitelabel1 -n 50

# Restart service
sudo systemctl restart whitelabel1
```

### Database Connection Error
```bash
# Verify Supabase credentials in .env
cat /root/cryptomentor-bot/whitelabel-1/.env | grep SUPABASE

# Test connection
cd /root/cryptomentor-bot/whitelabel-1
python3 -c "from app.supabase_repo import _client; print(_client())"
```

### License Check Failed
```bash
# Check license server status
sudo systemctl status license-server

# Check license API
curl http://localhost:8080/health

# View license cache
cat /root/cryptomentor-bot/whitelabel-1/data/license_cache.json
```

## Security Notes

⚠️ **PENTING - JANGAN SHARE**:
- Semua file `.env` berisi credentials rahasia
- Bot tokens
- Database credentials
- API keys
- Encryption keys
- Private keys (untuk wallet)

🔒 **Best Practices**:
- Backup `.env` files secara teratur
- Jangan commit `.env` ke git
- Gunakan strong passwords
- Enable firewall di VPS
- Regular security updates

## Monitoring

### Resource Usage
```bash
# CPU & Memory
top
htop

# Disk usage
df -h

# Process list
ps aux | grep python
```

### Network
```bash
# Check open ports
sudo netstat -tulpn

# Check connections
sudo ss -tulpn
```

---

**Last Updated**: 2026-03-26
**Maintained By**: CryptoMentor Team
**VPS**: Contabo - 147.93.156.165
