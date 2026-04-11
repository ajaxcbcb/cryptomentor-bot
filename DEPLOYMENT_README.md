# 🚀 Deployment Scripts - Quick Reference

**Created**: April 10, 2026  
**Project**: CryptoMentor  
**VPS**: 147.93.156.165

---

## 📦 Available Scripts

| Script | Purpose | Platform | Features |
|--------|---------|----------|----------|
| `deploy_frontend.py` | Frontend only | Python (All OS) | Auto build, SSH/Password, Nginx reload |
| `deploy_frontend.ps1` | Frontend only | PowerShell (Windows) | Auto build, SCP, Color output |
| `deploy_frontend.sh` | Backend script | Bash (VPS) | Backup, Rsync, Nginx reload |
| `deploy_full_system.py` | Everything! | Python (All OS) | Frontend+Backend+Bot, selective deploy |

---

## 🚀 Quick Start

### Most Easy (Windows Users)
```powershell
# Run PowerShell script
.\deploy_frontend.ps1
```

### Most Powerful (All Platforms)
```bash
# Install library
pip install paramiko

# Run full system deploy
python deploy_full_system.py

# Or just frontend
python deploy_frontend.py
```

### Most Control (Manual SSH)
```bash
# Build
cd website-frontend && npm run build

# Upload
scp -r website-frontend/dist/* root@147.93.156.165:/root/cryptomentor-bot/website-frontend/dist/

# Reload
ssh root@147.93.156.165 "sudo systemctl reload nginx"
```

---

## 🎯 Deployment Options

### Option A: Frontend Only (Frontend Developers)
```bash
python deploy_frontend.py
```
- Builds frontend
- Uploads dist/ folder
- Reloads nginx
- Verifies deployment
- ⏱️ ~10-20 seconds

### Option B: Frontend + Backend (Full Stack)
```bash
python deploy_full_system.py
# Select option 2
```
- Same as Option A
- Plus uploads backend code
- Optionally restarts API service
- ⏱️ ~30-45 seconds

### Option C: Complete System (DevOps)
```bash
python deploy_full_system.py
# Select option 3
```
- Frontend + Backend + Bot code
- Selective deployment
- Multiple service management
- Full verification
- ⏱️ ~1-2 minutes

### Option D: Custom Selection
```bash
python deploy_full_system.py
# Select option 4
# Choose each component
```
- Deploy exactly what you need
- Perfect for partial updates

---

## 🔐 Credentials

**VPS Access:**
- Host: `147.93.156.165`
- User: `root`
- Password: `<REDACTED_VPS_PASSWORD>`

**Methods:**
1. **SSH Key** (Better) - Uses `~/.ssh/id_rsa` automatically
2. **Password** (Fallback) - Interactive prompt or `$env:VPS_PASSWORD`

⚠️ **Recommendation**: Set up SSH key for security!

---

## 🌳 Project Structure

```
c:\V3-Final-Version\
├── website-frontend/           # React/Vite frontend
│   ├── src/                    # Source code
│   ├── package.json
│   ├── dist/                   ← Deployed to VPS
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── website-backend/            # FastAPI backend
│   ├── main.py
│   ├── requirements.txt
│   ├── nginx-api.conf
│   └── nginx-www.conf
│
├── Bismillah/                  # Main Telegram bot
│   ├── bot.py
│   ├── main.py
│   └── requirements.txt
│
├── deploy_frontend.py          ← Frontend deploy (Python)
├── deploy_frontend.ps1         ← Frontend deploy (PowerShell)
├── deploy_frontend.sh          ← Backend deploy script (Bash)
├── deploy_full_system.py       ← Full system deploy (Python)
├── DEPLOYMENT_FRONTEND_GUIDE.md ← Complete guide
└── DEPLOYMENT_README.md        ← This file
```

---

## ✅ Deployment Checklist

Before deploying:
- [ ] Code committed to git
- [ ] All tests passing
- [ ] `npm run build` works locally
- [ ] No uncommitted changes
- [ ] VPS credentials ready

During deployment:
- [ ] Monitor speed (should be 10-30 seconds)
- [ ] Watch for errors in output

After deployment:
- [ ] Visit https://cryptomentor.id
- [ ] F12 → Console (no JS errors)
- [ ] Test /api endpoints
- [ ] Check mobile view
- [ ] Clear cache if needed (Ctrl+Shift+Del)

---

## 🐛 Common Issues

### 1. "Build failed"
```bash
cd website-frontend
npm install
npm run build
cd ..
```

### 2. "Connection timeout"
```bash
ping 147.93.156.165
ssh -v root@147.93.156.165
```

### 3. "Permission denied"
```bash
# On VPS:
sudo chown -R root:root /root/cryptomentor-bot
```

### 4. "Files not updating"
```bash
# Hard refresh in browser:
Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

# Or check cache:
https://cryptomentor.id/index.html
# Should have: Cache-Control: no-cache
```

### 5. "Nginx not reloading"
```bash
# Check syntax
sudo nginx -t

# Manual reload
sudo systemctl reload nginx

# View error log
sudo tail -f /var/log/nginx/error.log
```

---

## 📊 VPS Services

| Service | Port | Status | Restart |
|---------|------|--------|---------|
| Nginx | 80, 443 | `systemctl status nginx` | Auto-reload |
| FastAPI Backend | 8000 | `systemctl status cryptomentor-web` | `systemctl restart cryptomentor-web` |
| Telegram Bot | - | Manual manage | N/A |

---

## 🌐 URLs After Deploy

| URL | Purpose | Auth |
|-----|---------|------|
| https://cryptomentor.id | Frontend | Public |
| https://cryptomentor.id/api | Backend API | JWT Token |
| https://cryptomentor.id/dashboard | User Dashboard | Telegram Login |
| https://cryptomentor.id/leaderboard | Leaderboard | Public |

---

## 💾 Deployment Logs

Scripts save deployment logs to:
- `deployment_report_YYYYMMDD_HHMMSS.txt` (when using `deploy_full_system.py`)

Check this for verification and troubleshooting.

---

## 🔄 Automated Deployment

For CI/CD setup, modify GitHub Actions or similar:

```yaml
- name: Deploy Frontend
  env:
    VPS_PASSWORD: ${{ secrets.VPS_PASSWORD }}
  run: python deploy_frontend.py
```

---

## 👥 Team Workflow

**Frontend Dev** → Use `deploy_frontend.py` or `.ps1`  
**Backend Dev** → Use `deploy_full_system.py` (option 2)  
**DevOps** → Use `deploy_full_system.py` (option 3)  

---

## 📞 Support

For deployment issues:
1. Check this README
2. Review detailed guide: `DEPLOYMENT_FRONTEND_GUIDE.md`
3. Check VPS directly: `ssh root@147.93.156.165`
4. Contact DevOps team

---

**Last Updated**: April 10, 2026  
**Status**: ✅ Production Ready  
**Tested**: ✅ All scripts verified
