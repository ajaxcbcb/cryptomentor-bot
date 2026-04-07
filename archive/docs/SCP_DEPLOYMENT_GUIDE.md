# 📚 SCP Deployment Guide - Panduan Lengkap

## 🎯 Tentang SCP (Secure Copy Protocol)

SCP adalah protokol untuk transfer file secara aman antara komputer lokal dan remote server menggunakan SSH. Ini adalah cara paling reliable untuk push update ke VPS.

---

## 🔐 VPS Configuration

### Server Details:
```
Host:     147.93.156.165
User:     root
Port:     22
Path:     /root/cryptomentor-bot
Service:  cryptomentor.service
```

### Directory Structure:
```
/root/cryptomentor-bot/
├── Bismillah/
│   ├── app/
│   │   ├── demo_users.py
│   │   ├── handlers_community.py
│   │   ├── handlers_autotrade.py
│   │   └── ... (other app files)
│   ├── bot.py
│   └── ... (other Bismillah files)
├── license_server/
├── data/
└── ... (other project files)
```

---

## 🚀 Basic SCP Commands

### 1. Upload Single File
```bash
scp -P 22 <local_file> root@147.93.156.165:/root/cryptomentor-bot/<remote_path>
```

### 2. Upload Multiple Files
```bash
scp -P 22 file1.py file2.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
```

### 3. Upload Entire Directory
```bash
scp -P 22 -r <local_directory> root@147.93.156.165:/root/cryptomentor-bot/
```

### 4. Download File from VPS
```bash
scp -P 22 root@147.93.156.165:/root/cryptomentor-bot/<remote_file> <local_path>
```

---

## 📋 Standard Deployment Workflow

### Step 1: Upload Files
```bash
# Upload demo_users.py
scp -P 22 Bismillah/app/demo_users.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# Upload handlers_community.py
scp -P 22 Bismillah/app/handlers_community.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
```

### Step 2: Restart Service
```bash
ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor"
```

### Step 3: Check Status
```bash
ssh -p 22 root@147.93.156.165 "systemctl status cryptomentor --no-pager | head -20"
```

### Step 4: Monitor Logs
```bash
ssh -p 22 root@147.93.156.165 "journalctl -u cryptomentor -f"
```

---

## 🎨 Common Deployment Scenarios

### Scenario 1: Update Single Python File
```bash
# Upload file
scp -P 22 Bismillah/app/demo_users.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# Restart bot
ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor && systemctl status cryptomentor"
```

### Scenario 2: Update Multiple App Files
```bash
# Upload all files at once
scp -P 22 \
  Bismillah/app/demo_users.py \
  Bismillah/app/handlers_community.py \
  Bismillah/app/handlers_autotrade.py \
  root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# Restart
ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor"
```

### Scenario 3: Update Entire App Directory
```bash
# Upload entire app directory
scp -P 22 -r Bismillah/app root@147.93.156.165:/root/cryptomentor-bot/Bismillah/

# Restart
ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor"
```

### Scenario 4: Update with Backup
```bash
# Create backup first
ssh -p 22 root@147.93.156.165 "cd /root/cryptomentor-bot && mkdir -p backups/$(date +%Y%m%d_%H%M%S) && cp Bismillah/app/demo_users.py backups/$(date +%Y%m%d_%H%M%S)/"

# Upload new file
scp -P 22 Bismillah/app/demo_users.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# Restart
ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor"
```

---

## 🔧 Advanced SCP Options

### Preserve File Attributes
```bash
scp -P 22 -p file.py root@147.93.156.165:/root/cryptomentor-bot/
```

### Compress During Transfer (faster for large files)
```bash
scp -P 22 -C file.py root@147.93.156.165:/root/cryptomentor-bot/
```

### Verbose Output (for debugging)
```bash
scp -P 22 -v file.py root@147.93.156.165:/root/cryptomentor-bot/
```

### Limit Bandwidth (in Kbit/s)
```bash
scp -P 22 -l 1000 file.py root@147.93.156.165:/root/cryptomentor-bot/
```

---

## 🛠️ Service Management Commands

### Check Service Status
```bash
ssh -p 22 root@147.93.156.165 "systemctl status cryptomentor"
```

### Start Service
```bash
ssh -p 22 root@147.93.156.165 "systemctl start cryptomentor"
```

### Stop Service
```bash
ssh -p 22 root@147.93.156.165 "systemctl stop cryptomentor"
```

### Restart Service
```bash
ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor"
```

### View Logs (last 100 lines)
```bash
ssh -p 22 root@147.93.156.165 "journalctl -u cryptomentor -n 100"
```

### Follow Logs (real-time)
```bash
ssh -p 22 root@147.93.156.165 "journalctl -u cryptomentor -f"
```

### Check if Service is Running
```bash
ssh -p 22 root@147.93.156.165 "systemctl is-active cryptomentor"
```

---

## 📝 Quick Reference Commands

### Upload & Restart (One-liner)
```bash
scp -P 22 Bismillah/app/demo_users.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/ && ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor && systemctl status cryptomentor"
```

### Upload Multiple Files & Restart
```bash
scp -P 22 Bismillah/app/{demo_users.py,handlers_community.py} root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/ && ssh -p 22 root@147.93.156.165 "systemctl restart cryptomentor"
```

### Check VPS Directory Structure
```bash
ssh -p 22 root@147.93.156.165 "ls -la /root/cryptomentor-bot/Bismillah/app/"
```

### Check File Content on VPS
```bash
ssh -p 22 root@147.93.156.165 "cat /root/cryptomentor-bot/Bismillah/app/demo_users.py"
```

### Check Disk Space
```bash
ssh -p 22 root@147.93.156.165 "df -h"
```

### Check Memory Usage
```bash
ssh -p 22 root@147.93.156.165 "free -h"
```

---

## 🔍 Troubleshooting

### Problem: "Permission denied"
**Solution:**
```bash
# Check SSH key or use password authentication
ssh -p 22 root@147.93.156.165
```

### Problem: "No such file or directory"
**Solution:**
```bash
# Verify remote path exists
ssh -p 22 root@147.93.156.165 "ls -la /root/cryptomentor-bot/Bismillah/app/"

# Create directory if needed
ssh -p 22 root@147.93.156.165 "mkdir -p /root/cryptomentor-bot/Bismillah/app/"
```

### Problem: "Connection refused"
**Solution:**
```bash
# Check if SSH service is running
# Check firewall settings
# Verify IP address and port
```

### Problem: Bot doesn't restart
**Solution:**
```bash
# Check service status
ssh -p 22 root@147.93.156.165 "systemctl status cryptomentor"

# Check logs for errors
ssh -p 22 root@147.93.156.165 "journalctl -u cryptomentor -n 50"

# Try manual restart
ssh -p 22 root@147.93.156.165 "systemctl stop cryptomentor && sleep 2 && systemctl start cryptomentor"
```

### Problem: Python syntax error after upload
**Solution:**
```bash
# Test Python syntax on VPS
ssh -p 22 root@147.93.156.165 "cd /root/cryptomentor-bot && python3 -m py_compile Bismillah/app/demo_users.py"

# If error, rollback from backup
ssh -p 22 root@147.93.156.165 "cd /root/cryptomentor-bot && cp backups/BACKUP_DIR/demo_users.py Bismillah/app/"
```

---

## 🎯 Best Practices

### 1. Always Create Backup Before Update
```bash
ssh -p 22 root@147.93.156.165 "cd /root/cryptomentor-bot && mkdir -p backups/$(date +%Y%m%d_%H%M%S) && cp -r Bismillah/app backups/$(date +%Y%m%d_%H%M%S)/"
```

### 2. Test Locally First
```bash
# Test Python syntax locally
python3 -m py_compile Bismillah/app/demo_users.py

# Run local tests
python3 test_demo_users.py
```

### 3. Upload During Low Traffic
- Best time: Late night or early morning
- Avoid peak hours

### 4. Monitor Logs After Deployment
```bash
ssh -p 22 root@147.93.156.165 "journalctl -u cryptomentor -f"
```

### 5. Keep Deployment Documentation Updated
- Document every deployment
- Note any issues encountered
- Update this guide as needed

---

## 📊 Deployment Checklist

Before deployment:
- [ ] Test code locally
- [ ] Check Python syntax
- [ ] Review changes
- [ ] Create backup plan

During deployment:
- [ ] Create backup on VPS
- [ ] Upload files via SCP
- [ ] Verify files uploaded correctly
- [ ] Restart service

After deployment:
- [ ] Check service status
- [ ] Monitor logs for errors
- [ ] Test functionality
- [ ] Verify no regressions

---

## 🔙 Rollback Procedure

### Quick Rollback
```bash
# 1. SSH to VPS
ssh -p 22 root@147.93.156.165

# 2. List backups
cd /root/cryptomentor-bot/backups
ls -la

# 3. Restore from backup
cd /root/cryptomentor-bot
cp backups/BACKUP_DIR/demo_users.py Bismillah/app/
cp backups/BACKUP_DIR/handlers_community.py Bismillah/app/

# 4. Restart service
systemctl restart cryptomentor
systemctl status cryptomentor
```

---

## 📞 Emergency Contacts

If deployment fails:
1. Check logs: `journalctl -u cryptomentor -n 100`
2. Rollback to backup
3. Review error messages
4. Test locally before re-deploying

---

## 📝 Deployment Log Template

```
Date: YYYY-MM-DD HH:MM
Deployed by: [Your Name]
Files updated:
  - Bismillah/app/demo_users.py
  - Bismillah/app/handlers_community.py

Changes:
  - Added demo user 1234500004
  - Blocked Community Partners for demo users

Backup location: /root/cryptomentor-bot/backups/YYYYMMDD_HHMMSS

Status: ✅ Success / ❌ Failed
Notes: [Any additional notes]
```

---

**Last Updated**: 2026-03-31
**Version**: 1.0.0
**Maintained by**: CryptoMentor Team
