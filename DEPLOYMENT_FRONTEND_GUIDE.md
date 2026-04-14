# 🚀 Frontend Deployment Guide - CryptoMentor

**Date**: April 10, 2026  
**Status**: Production Ready  
**Environment**: VPS (147.93.156.165)

---

## 📋 Quick Start

### Option 1: Python Script (Recommended - Windows/Mac/Linux)

```bash
# Install dependency
pip install paramiko

# Run deploy
python deploy_frontend.py
```

**What it does:**
✅ Builds frontend automatically  
✅ Deploys all dist/ files recursively  
✅ Reloads nginx automatically  
✅ Verifies deployment  

### Option 2: PowerShell Script (Windows Only)

```powershell
# Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run deploy
.\deploy_frontend.ps1

# Or with password
$env:VPS_PASSWORD = "rMM2m63P"
.\deploy_frontend.ps1
```

### Option 3: Manual SSH

```bash
# Build locally
cd website-frontend
npm run build
cd ..

# Deploy with SCP
scp -r website-frontend/dist/* root@147.93.156.165:/root/cryptomentor-bot/website-frontend/dist/

# Reload nginx
ssh root@147.93.156.165 "sudo systemctl reload nginx"
```

---

## 📁 Project Structure on VPS

```
/root/
├── cryptomentor-bot/
│   ├── website-frontend/
│   │   ├── dist/                          # Frontend static files
│   │   │   ├── index.html
│   │   │   ├── assets/
│   │   │   │   ├── index-DRDxfLDY.js
│   │   │   │   └── index-BL7XisQJ.css
│   │   │   └── [other assets]
│   │   └── [source code]
│   │
│   ├── website-backend/                   # FastAPI backend
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── nginx-api.conf
│   │   └── [other files]
│   │
│   └── Bismillah/                         # Main bot
```

---

## 🖇️ Nginx Configuration

**File**: `/etc/nginx/sites-available/www-cryptomentor.conf` (atau similar)

```nginx
server {
    server_name cryptomentor.id www.cryptomentor.id;

    # Frontend static files
    root /root/cryptomentor-bot/website-frontend/dist;
    index index.html;

    # Proxy /api/ ke FastAPI backend
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Cache control untuk index.html
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # Cache assets (long-term)
    location /assets/ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # SSL (Let's Encrypt)
    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/cryptomentor.id/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cryptomentor.id/privkey.pem;
}

# HTTP redirect
server {
    listen 80;
    server_name cryptomentor.id www.cryptomentor.id;
    return 301 https://$server_name$request_uri;
}
```

---

## 🔐 VPS Access Credentials

| Property | Value |
|----------|-------|
| Host | 147.93.156.165 |
| User | root |
| Port | 22 (SSH) |
| Password | rMM2m63P |

⚠️ **SECURITY NOTE**: Change password atau use SSH key!

---

## ✅ Deployment Checklist

- [ ] Build frontend locally (`npm run build`)
- [ ] Verify dist/ directory created
- [ ] Run deploy script
- [ ] Check console output for errors
- [ ] Verify nginx reload successful
- [ ] Test website URL: https://cryptomentor.id
- [ ] Check browser console for errors (F12)
- [ ] Verify API calls work: https://cryptomentor.id/api/health
- [ ] Clear browser cache if needed (Ctrl+Shift+Del)

---

## 🐛 Troubleshooting

### Build fails locally

```bash
# Clear node_modules and reinstall
rm -rf website-frontend/node_modules
cd website-frontend
npm install
npm run build
```

### SSH connection timeout

```bash
# Check VPS is reachable
ping 147.93.156.165

# Try manual SSH
ssh -v root@147.93.156.165

# Check firewall
sudo ufw status
```

### Nginx not reloading

```bash
# Check nginx syntax
sudo nginx -t

# Check nginx status
sudo systemctl status nginx

# Manual reload
sudo systemctl reload nginx

# Check error log
sudo tail -f /var/log/nginx/error.log
```

### Files not updating

1. **Clear browser cache**:
   - Ctrl+Shift+Del (Windows) or Cmd+Shift+Delete (Mac)
   - Or use DevTools (F12) → Performance → Disable cache
   - Or Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

2. **Check file permissions on VPS**:
   ```bash
   ls -la /root/cryptomentor-bot/website-frontend/dist/
   ```

3. **Verify ngix is serving right directory**:
   ```bash
   sudo nginx -T | grep root
   ```

---

## 📊 Deployment Script Details

### Python Script (`deploy_frontend.py`)

- ✅ Auto-builds frontend with `npm run build`
- ✅ Walks entire dist/ directory recursively
- ✅ Creates remote directories as needed
- ✅ Uploads all files (HTML, JS, CSS, assets)
- ✅ Auto-sets SSH key if exists (`~/.ssh/id_rsa`)
- ✅ Falls back to password auth
- ✅ Executes `sudo systemctl reload nginx`
- ✅ Verifies index.html exists on server

### PowerShell Script (`deploy_frontend.ps1`)

- ✅ Auto-builds with npm
- ✅ Uses Windows OpenSSH (Windows 10+)
- ✅ Recursive directory copy
- ✅ Nginx reload
- ✅ Color-coded output

### Bash Script (`deploy_frontend.sh`)

- ✅ Run on VPS after uploading
- ✅ Backs up existing dist/
- ✅ Uses `rsync` for smart copy
- ✅ Verifies deployment
- ✅ Nginx reload

---

## 🚀 CI/CD Integration

For automated deployment, you can:

1. **GitHub Actions**:
   ```yaml
   - name: Build
     run: npm run build
   
   - name: Deploy
     run: python deploy_frontend.py
     env:
       VPS_PASSWORD: ${{ secrets.VPS_PASSWORD }}
   ```

2. **Webhook Deploy**:
   ```bash
   # In webhook handler on VPS
   cd /root/cryptomentor-bot
   git pull origin main
   cd website-frontend
   npm install --production
   npm run build
   sudo systemctl reload nginx
   ```

---

## 📝 Deployment Log Example

```
✓ Build installed
✓ Build successful
📊 Siap deploy 42 files

🔐 Connecting...
✓ Connected to 147.93.156.165@root

📁 Deploy 42 files...
  ✓ index.html (3245 bytes)
  ✓ index-DRDxfLDY.js (125634 bytes)
  ✓ index-BL7XisQJ.css (45232 bytes)
  ✓ [33 more files]

🔄 Reloading nginx...
✓ Nginx reloaded!

✅ Verifying deployment...
✓ index.html found on server!

✓ Deploy berhasil!
  Frontend deployed ke: /root/cryptomentor-bot/website-frontend/dist
```

---

## ⏱️ Typical Deployment Time

| Step | Time |
|------|------|
| Build frontend | 2-5 seconds |
| Connect SSH | 1-2 seconds |
| Upload files | 3-10 seconds |
| Reload nginx | 1 second |
| Verify | 1 second |
| **Total** | **~10-20 seconds** |

---

## 📊 Project Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Frontend | React + Vite | 18.3.1 |
| Styling | TailwindCSS | 3.4.17 |
| Charts | Recharts | 3.8.1 |
| Build tool | Vite | 6.0.5 |
| Backend | FastAPI | Latest |
| Server | Nginx | 1.22+ |
| Python | Python | 3.9+ |

---

## 🔗 Useful Links

- **CryptoMentor Website**: https://cryptomentor.id
- **API Base URL**: https://cryptomentor.id/api
- **Admin Dashboard**: https://cryptomentor.id/dashboard
- **Leaderboard**: https://cryptomentor.id/leaderboard

---

## 📞 Support

For deployment issues:

1. Check console output for specific errors
2. Review troubleshooting section above
3. Check VPS logs: `sudo tail -f /var/log/nginx/error.log`
4. Verify VPS connectivity first
5. Contact DevOps team if needed

---

**Last Updated**: April 10, 2026  
**Maintained By**: Dev Team  
**Status**: ✅ Production Ready
