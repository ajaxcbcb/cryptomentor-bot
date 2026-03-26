# Deployment Guide - Push ke VPS Contabo

Panduan lengkap untuk deploy bot ke VPS Contabo dari local machine.

## Metode 1: Automatic Deployment (Recommended)

### Prerequisites
- Git repository sudah di-push ke GitHub/GitLab
- SSH access ke VPS Contabo
- VPS sudah clone repository

### Step 1: Commit & Push Changes

```bash
# Di local machine (Windows)
git add .
git commit -m "Update whitelabel bot with full autotrade"
git push origin main
```

### Step 2: Deploy ke VPS

```bash
# Jalankan deployment script
bash deploy_to_vps.sh 147.93.156.165 root
```

Script ini akan:
1. ✅ Push changes ke git
2. ✅ SSH ke VPS
3. ✅ Pull latest changes
4. ✅ Install dependencies
5. ✅ Restart semua services (cryptomentor, whitelabel1, license-server)
6. ✅ Show status

## Metode 2: Manual Deployment

### Step 1: Push ke Git

```bash
git add .
git commit -m "Your commit message"
git push origin main
```

### Step 2: SSH ke VPS

```bash
ssh root@147.93.156.165
```

### Step 3: Pull Changes

```bash
cd /root/cryptomentor-bot
git pull origin main
```

### Step 4: Install Dependencies

```bash
# Whitelabel #1
cd "Whitelabel #1"
pip3 install -r requirements.txt

# Bismillah (main bot)
cd ../Bismillah
pip3 install -r requirements.txt

# License server
cd ../license_server
pip3 install -r requirements.txt
```

### Step 5: Setup Whitelabel Service (First Time Only)

```bash
cd /root/cryptomentor-bot
bash setup_whitelabel_vps.sh
```

### Step 6: Restart Services

```bash
# Restart main bot
sudo systemctl restart cryptomentor

# Restart whitelabel bot
sudo systemctl restart whitelabel1

# Restart license server
sudo systemctl restart license-server

# Check status
sudo systemctl status cryptomentor whitelabel1 license-server
```

## Metode 3: Using SCP (Direct File Transfer)

Jika git tidak tersedia atau ada masalah:

```bash
# Copy entire Whitelabel #1 folder
scp -r "Whitelabel #1" root@147.93.156.165:/root/cryptomentor-bot/

# Copy specific files
scp "Whitelabel #1/bot.py" root@147.93.156.165:"/root/cryptomentor-bot/Whitelabel #1/"
scp "Whitelabel #1/app/handlers_basic.py" root@147.93.156.165:"/root/cryptomentor-bot/Whitelabel #1/app/"
```

## First Time Setup di VPS

Jika ini pertama kali setup whitelabel di VPS:

### 1. Clone Repository (if not exists)

```bash
cd /root
git clone https://github.com/yourusername/cryptomentor-bot.git
cd cryptomentor-bot
```

### 2. Configure Environment

```bash
cd "Whitelabel #1"
cp .env.example .env
nano .env
```

Set these values:
```env
BOT_TOKEN=8744237679:AAGltv_2UtgjuFZx2UGK43_6WeMqjGRHpR4
ADMIN1=801937545
SUPABASE_URL=https://jajtwunmngmturqwjpum.supabase.co
SUPABASE_ANON_KEY=your_key
SUPABASE_SERVICE_KEY=your_key
WL_ID=39b6bd7f-51b8-444c-9342-850e5b96f0e6
WL_SECRET_KEY=e783747d-29aa-4af5-b667-04552f8822ee
LICENSE_API_URL=http://147.93.156.165:8080
ENCRYPTION_KEY=your_encryption_key
```

### 3. Run Setup Script

```bash
cd /root/cryptomentor-bot
bash setup_whitelabel_vps.sh
```

### 4. Verify Installation

```bash
# Check if service is running
sudo systemctl status whitelabel1

# View logs
sudo journalctl -u whitelabel1 -f

# Test bot
# Send /start to bot di Telegram
```

## Troubleshooting

### Bot tidak start

```bash
# Check logs
sudo journalctl -u whitelabel1 -n 50

# Check if port is in use
sudo netstat -tulpn | grep python

# Restart service
sudo systemctl restart whitelabel1
```

### License check failed

```bash
# Check if license server is running
sudo systemctl status license-server

# Check license server logs
sudo journalctl -u license-server -n 50

# Test license API
curl http://147.93.156.165:8080/health
```

### Database connection error

```bash
# Verify Supabase credentials in .env
nano "/root/cryptomentor-bot/Whitelabel #1/.env"

# Test connection
cd "/root/cryptomentor-bot/Whitelabel #1"
python3 -c "from app.supabase_repo import _client; print(_client())"
```

### Git conflicts

```bash
cd /root/cryptomentor-bot
git stash
git pull origin main
git stash pop
```

## Monitoring

### View Logs

```bash
# Real-time logs
sudo journalctl -u whitelabel1 -f

# Last 100 lines
sudo journalctl -u whitelabel1 -n 100

# Logs from today
sudo journalctl -u whitelabel1 --since today
```

### Check Status

```bash
# All services
sudo systemctl status cryptomentor whitelabel1 license-server

# Just whitelabel
sudo systemctl status whitelabel1
```

### Resource Usage

```bash
# CPU & Memory
top -p $(pgrep -f "whitelabel.*bot.py")

# Disk usage
df -h
```

## Quick Commands Reference

```bash
# Deploy from local
bash deploy_to_vps.sh

# Setup on VPS (first time)
bash setup_whitelabel_vps.sh

# Restart bot
sudo systemctl restart whitelabel1

# View logs
sudo journalctl -u whitelabel1 -f

# Check status
sudo systemctl status whitelabel1

# Stop bot
sudo systemctl stop whitelabel1

# Start bot
sudo systemctl start whitelabel1

# Edit config
nano "/root/cryptomentor-bot/Whitelabel #1/.env"
```

## Notes

- VPS IP: `147.93.156.165`
- VPS User: `root`
- Bot Path: `/root/cryptomentor-bot/Whitelabel #1`
- Service Name: `whitelabel1`
- Bot ID: `8744237679`

## Support

Jika ada masalah, cek:
1. Logs: `sudo journalctl -u whitelabel1 -n 50`
2. Service status: `sudo systemctl status whitelabel1`
3. License server: `sudo systemctl status license-server`
4. Network: `ping 147.93.156.165`
