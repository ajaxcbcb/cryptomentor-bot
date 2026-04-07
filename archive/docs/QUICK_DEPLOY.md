# Quick Deploy Guide - Whitelabel #1 ke VPS

## ✅ Step 1: Code sudah di-push ke GitHub

Code sudah berhasil di-push ke: `https://github.com/cryptomentor139-cell/cryptomentor-bot.git`

## 📋 Step 2: Deploy ke VPS Contabo

### Opsi A: Automatic Deployment (Recommended)

Dari local machine (Windows), jalankan:

```bash
bash deploy_to_vps.sh 147.93.156.165 root
```

Script ini akan otomatis:
1. SSH ke VPS
2. Pull latest code dari GitHub
3. Install dependencies
4. Restart semua services

### Opsi B: Manual Deployment

#### 1. SSH ke VPS

```bash
ssh root@147.93.156.165
```

#### 2. Pull Latest Code

```bash
cd /root/cryptomentor-bot
git pull github main
```

#### 3. Setup Whitelabel Bot (First Time Only)

```bash
bash setup_whitelabel_vps.sh
```

Script ini akan:
- Install dependencies
- Create systemd service
- Setup data directory
- Start bot

#### 4. Configure Environment

```bash
nano "/root/cryptomentor-bot/Whitelabel #1/.env"
```

Pastikan setting ini benar:
```env
# Telegram
BOT_TOKEN=<REDACTED_TELEGRAM_BOT_TOKEN>
ADMIN1=<REDACTED_ADMIN_ID>

# Supabase
SUPABASE_URL=https://jajtwunmngmturqwjpum.supabase.co
SUPABASE_ANON_KEY=<REDACTED_SUPABASE_KEY>
SUPABASE_SERVICE_KEY=<REDACTED_SUPABASE_KEY>

# License Server (PRODUCTION)
WL_ID=<REDACTED_UUID>
WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>
LICENSE_API_URL=http://147.93.156.165:8080

# Encryption
ENCRYPTION_KEY=<REDACTED_ENCRYPTION_KEY>
```

#### 5. Start Bot

```bash
sudo systemctl start whitelabel1
```

#### 6. Check Status

```bash
# Check if running
sudo systemctl status whitelabel1

# View logs
sudo journalctl -u whitelabel1 -f
```

## 🔍 Verification

### 1. Check Service Status

```bash
sudo systemctl status whitelabel1
```

Should show: `Active: active (running)`

### 2. Check Logs

```bash
sudo journalctl -u whitelabel1 -n 50
```

Look for:
- `LICENSE_API_URL not set — running in DEV MODE` (if testing)
- `Whitelabel #1 bot starting...`
- `Application started`

### 3. Test Bot

Send `/start` to bot di Telegram (@WL#1)

Bot should respond with welcome message and autotrade setup buttons.

## 🚨 Troubleshooting

### Bot tidak start

```bash
# Check logs
sudo journalctl -u whitelabel1 -n 100

# Common issues:
# 1. License server not reachable
#    → Set LICENSE_API_URL= (empty) for DEV MODE
# 2. Missing dependencies
#    → cd "Whitelabel #1" && pip3 install -r requirements.txt
# 3. Database connection error
#    → Check SUPABASE_URL and keys in .env
```

### License check failed

```bash
# Check license server
sudo systemctl status license-server

# Test license API
curl http://147.93.156.165:8080/health

# If license server down, use DEV MODE:
nano "/root/cryptomentor-bot/Whitelabel #1/.env"
# Set: LICENSE_API_URL=
```

### Bot responds but autotrade doesn't work

```bash
# Check if Supabase tables exist
# Run setup.sql in Supabase dashboard

# Check encryption key
# Make sure ENCRYPTION_KEY is set in .env
```

## 📊 Monitoring

### Real-time Logs

```bash
sudo journalctl -u whitelabel1 -f
```

### Check All Services

```bash
sudo systemctl status cryptomentor whitelabel1 license-server
```

### Resource Usage

```bash
# CPU & Memory
htop

# Disk space
df -h
```

## 🔄 Update Bot (Future Updates)

### Method 1: Automatic

From local machine:
```bash
bash deploy_to_vps.sh
```

### Method 2: Manual

On VPS:
```bash
cd /root/cryptomentor-bot
git pull github main
sudo systemctl restart whitelabel1
```

## 📝 Important Files

- **Bot Code**: `/root/cryptomentor-bot/Whitelabel #1/`
- **Config**: `/root/cryptomentor-bot/Whitelabel #1/.env`
- **Service**: `/etc/systemd/system/whitelabel1.service`
- **Logs**: `journalctl -u whitelabel1`

## 🎯 Next Steps

1. ✅ Deploy bot ke VPS
2. ✅ Test `/start` command
3. ✅ Setup autotrade dengan test account
4. ✅ Monitor logs untuk errors
5. ✅ Configure license server (production)

## 💡 Tips

- Use DEV MODE (empty LICENSE_API_URL) for testing
- Monitor logs regularly: `journalctl -u whitelabel1 -f`
- Keep .env file secure (contains API keys)
- Backup database regularly
- Test with small capital first

## 📞 Support

Jika ada masalah:
1. Check logs: `sudo journalctl -u whitelabel1 -n 100`
2. Check service: `sudo systemctl status whitelabel1`
3. Check license server: `sudo systemctl status license-server`
4. Test bot: Send `/start` di Telegram

---

**VPS Info:**
- IP: 147.93.156.165
- User: root
- Bot Path: /root/cryptomentor-bot/Whitelabel #1
- Service: whitelabel1
- Bot ID: 8744237679
