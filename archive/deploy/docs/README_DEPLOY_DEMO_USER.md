# 🚀 Deploy Demo User Update - Quick Start

## ⚡ Deploy Sekarang (Pilih Salah Satu)

### Windows
```
Double-click file: deploy_demo_user_update.bat
```

### PowerShell
```powershell
.\deploy_demo_user_update.ps1
```

### Bash/Git Bash/Linux
```bash
chmod +x deploy_demo_user_update.sh
./deploy_demo_user_update.sh
```

---

## 📋 Apa yang Diupdate?

✅ **Menambahkan user demo baru:**
- Telegram UID: `1234500004`
- Bitunix UID: `933383167`

✅ **Memblokir akses Community Partners untuk semua demo users**

Demo users tetap bisa:
- ✅ Menggunakan autotrade (limit $50)
- ✅ Setup API key
- ✅ Bypass referral requirement

Demo users TIDAK bisa:
- ❌ Akses Community Partners
- ❌ Daftar sebagai community leader
- ❌ Invite anggota komunitas

---

## 🔍 Verifikasi Setelah Deploy

### 1. Check bot status
```bash
ssh -p 22 root@147.93.156.165 "systemctl status cryptomentor-bot"
```

### 2. Monitor logs
```bash
ssh -p 22 root@147.93.156.165 "journalctl -u cryptomentor-bot -f"
```

### 3. Test dengan demo user
Login sebagai user `1234500004`, ketik `/autotrade`, coba akses "Partners" → harus muncul error "Access Denied"

---

## 🔙 Rollback (Jika Ada Masalah)

```bash
ssh -p 22 root@147.93.156.165
cd /root/CryptoMentor/backups
ls -la  # Cari folder backup terbaru
# Copy files dari backup
systemctl restart cryptomentor-bot
```

---

## 📞 Need Help?

- Check logs: `ssh -p 22 root@147.93.156.165 "journalctl -u cryptomentor-bot -n 100"`
- Check status: `ssh -p 22 root@147.93.156.165 "systemctl status cryptomentor-bot"`
- Rollback ke backup jika perlu

---

## 📁 Dokumentasi Lengkap

- `DEMO_USER_DEPLOYMENT_SUMMARY.md` - Summary lengkap
- `DEPLOY_DEMO_USER_GUIDE.md` - Panduan detail
- `DEPLOY_DEMO_USER_COMMANDS.txt` - Quick commands
- `DEMO_USER_UPDATE.md` - Technical details

---

**Status**: ✅ READY TO DEPLOY
