# 🚀 SCP Quick Reference Card

## 📋 VPS Info
```
Host: 147.93.156.165
User: root
Port: 22
Path: /root/cryptomentor-bot
Service: cryptomentor.service
```

---

## ⚡ Most Used Commands

### Upload Single File
```bash
scp -P 22 Bismillah/app/demo_users.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
```

### Upload Multiple Files
```bash
scp -P 22 Bismillah/app/{demo_users.py,handlers_community.py} root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
```

### Restart Bot
```bash
ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor"
```

### Check Status
```bash
ssh -p 22 root@147.93.156.165 "systemctl status cryptomentor"
```

### View Logs
```bash
ssh -p 22 root@147.93.156.165 "journalctl -u cryptomentor -f"
```

---

## 🎯 Complete Deployment (Copy-Paste)

### Standard Deployment
```bash
# Upload files
scp -P 22 Bismillah/app/demo_users.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp -P 22 Bismillah/app/handlers_community.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# Restart and check
ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor && sleep 3 && systemctl status cryptomentor --no-pager | head -20"
```

### One-Liner Deployment
```bash
scp -P 22 Bismillah/app/{demo_users.py,handlers_community.py} root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/ && ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor && systemctl status cryptomentor"
```

---

## 🔍 Verification Commands

### Check Files on VPS
```bash
ssh -p 22 root@147.93.156.165 "ls -la /root/cryptomentor-bot/Bismillah/app/ | grep -E 'demo_users|handlers_community'"
```

### View File Content
```bash
ssh -p 22 root@147.93.156.165 "cat /root/cryptomentor-bot/Bismillah/app/demo_users.py"
```

### Check Last 50 Log Lines
```bash
ssh -p 22 root@147.93.156.165 "journalctl -u cryptomentor -n 50"
```

---

## 🔙 Quick Rollback

```bash
# SSH to VPS
ssh -p 22 root@147.93.156.165

# List backups
cd /root/cryptomentor-bot/backups && ls -la

# Restore (replace BACKUP_DIR with actual folder name)
cd /root/cryptomentor-bot
cp backups/BACKUP_DIR/*.py Bismillah/app/

# Restart
systemctl restart cryptomentor
```

---

## 📊 Common File Paths

| Local Path | Remote Path |
|------------|-------------|
| `Bismillah/app/demo_users.py` | `/root/cryptomentor-bot/Bismillah/app/demo_users.py` |
| `Bismillah/app/handlers_community.py` | `/root/cryptomentor-bot/Bismillah/app/handlers_community.py` |
| `Bismillah/app/handlers_autotrade.py` | `/root/cryptomentor-bot/Bismillah/app/handlers_autotrade.py` |
| `Bismillah/bot.py` | `/root/cryptomentor-bot/Bismillah/bot.py` |
| `Bismillah/.env` | `/root/cryptomentor-bot/Bismillah/.env` |

---

## 🛠️ Service Commands

| Action | Command |
|--------|---------|
| Start | `ssh -p 22 root@147.93.156.165 "systemctl start cryptomentor"` |
| Stop | `ssh -p 22 root@147.93.156.165 "systemctl stop cryptomentor"` |
| Restart | `ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor"` |
| Status | `ssh -p 22 root@147.93.156.165 "systemctl status cryptomentor"` |
| Logs | `ssh -p 22 root@147.93.156.165 "journalctl -u cryptomentor -f"` |

---

## 💡 Pro Tips

1. **Use wildcards for multiple files:**
   ```bash
   scp -P 22 Bismillah/app/*.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
   ```

2. **Compress for faster transfer:**
   ```bash
   scp -P 22 -C large_file.py root@147.93.156.165:/root/cryptomentor-bot/
   ```

3. **Create backup before upload:**
   ```bash
   ssh -p 22 root@147.93.156.165 "cp /root/cryptomentor-bot/Bismillah/app/demo_users.py /root/cryptomentor-bot/backups/demo_users.py.$(date +%Y%m%d_%H%M%S)"
   ```

4. **Test syntax after upload:**
   ```bash
   ssh -p 22 root@147.93.156.165 "python3 -m py_compile /root/cryptomentor-bot/Bismillah/app/demo_users.py"
   ```

---

**Quick Access**: Save this file for instant reference during deployments!
