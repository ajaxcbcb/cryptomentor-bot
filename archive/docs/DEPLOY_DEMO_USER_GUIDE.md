# Deploy Demo User Update - Panduan Deployment

## 📋 Ringkasan Update

Update ini menambahkan user demo baru dan memblokir akses Community Partners untuk semua demo users.

### Perubahan:
1. ✅ Menambahkan Telegram UID `1234500004` (Bitunix UID: `933383167`) ke daftar demo users
2. ✅ Memblokir akses Community Partners untuk semua demo users
3. ✅ Demo users tetap bisa menggunakan autotrade dengan limit $50

### Files yang Diupdate:
- `Bismillah/app/demo_users.py` - Menambahkan user baru ke DEMO_USER_IDS
- `Bismillah/app/handlers_community.py` - Menambahkan check untuk block demo users

---

## 🚀 Cara Deploy ke VPS

### Opsi 1: Windows (Paling Mudah)

Double-click file:
```
deploy_demo_user_update.bat
```

### Opsi 2: PowerShell

```powershell
.\deploy_demo_user_update.ps1
```

### Opsi 3: Bash/Linux/Git Bash

```bash
chmod +x deploy_demo_user_update.sh
./deploy_demo_user_update.sh
```

---

## 📊 Apa yang Dilakukan Script?

1. **Backup** - Membuat backup file lama di VPS
2. **Upload** - Upload 2 file yang diupdate ke VPS
3. **Restart** - Restart bot service untuk apply perubahan
4. **Verify** - Check apakah bot berhasil restart

---

## ✅ Verifikasi Setelah Deploy

### 1. Check Bot Status
```bash
ssh -p 22 root@147.93.156.165
systemctl status cryptomentor-bot
```

### 2. Monitor Logs
```bash
ssh -p 22 root@147.93.156.165 'journalctl -u cryptomentor-bot -f'
```

### 3. Test dengan Demo User

Login sebagai user dengan Telegram ID `1234500004`, lalu:

1. Ketik `/autotrade`
2. Coba akses menu "Partners"
3. Harus muncul pesan error:
   ```
   ❌ Access Denied
   
   Community Partners feature is not available for demo accounts.
   
   Demo accounts are for testing purposes only and cannot access partner features.
   ```

---

## 🔙 Rollback (Jika Ada Masalah)

### 1. SSH ke VPS
```bash
ssh -p 22 root@147.93.156.165
```

### 2. Lihat Backup yang Tersedia
```bash
cd /root/CryptoMentor/backups
ls -la
```

### 3. Restore dari Backup
```bash
# Ganti BACKUP_DIR dengan nama folder backup yang sesuai
BACKUP_DIR="demo_user_update_20260331_120000"

cd /root/CryptoMentor
cp backups/$BACKUP_DIR/demo_users.py Bismillah/app/
cp backups/$BACKUP_DIR/handlers_community.py Bismillah/app/

# Restart bot
systemctl restart cryptomentor-bot
systemctl status cryptomentor-bot
```

---

## 🔍 Troubleshooting

### Bot Tidak Start Setelah Deploy

1. Check logs untuk error:
```bash
ssh -p 22 root@147.93.156.165 'journalctl -u cryptomentor-bot -n 100'
```

2. Check syntax error di Python:
```bash
ssh -p 22 root@147.93.156.165
cd /root/CryptoMentor
python3 -m py_compile Bismillah/app/demo_users.py
python3 -m py_compile Bismillah/app/handlers_community.py
```

3. Jika ada error, rollback ke backup

### SSH Connection Failed

1. Check koneksi internet
2. Verify VPS IP: `147.93.156.165`
3. Verify SSH port: `22`
4. Check SSH key atau password

### File Upload Failed

1. Check file path lokal
2. Verify VPS path: `/root/CryptoMentor`
3. Check disk space di VPS:
```bash
ssh -p 22 root@147.93.156.165 'df -h'
```

---

## 📝 Demo User Configuration

### Current Demo Users:
| Telegram UID | Bitunix UID | Status |
|--------------|-------------|--------|
| 1234500001 | - | Active |
| 1234500002 | - | Active |
| 1234500003 | - | Active |
| 1234500004 | 933383167 | **NEW** |

### Demo User Restrictions:
- ✅ Can use autotrade
- ✅ Bypass referral requirement
- ✅ Balance limit: $50 USD
- ❌ **CANNOT access Community Partners**
- ❌ Cannot register as community leader
- ❌ Cannot invite community members

---

## 🎯 Testing Checklist

Setelah deploy, test hal berikut:

- [ ] Bot berhasil restart tanpa error
- [ ] Demo user bisa login dan akses /autotrade
- [ ] Demo user bisa setup API key
- [ ] Demo user bisa start autotrade
- [ ] Demo user **TIDAK BISA** akses Community Partners
- [ ] Non-demo user masih bisa akses Community Partners normal
- [ ] Logs tidak ada error terkait demo_users atau handlers_community

---

## 📞 Support

Jika ada masalah saat deployment:
1. Check logs di VPS
2. Rollback ke backup jika perlu
3. Review error message
4. Test di local environment dulu

---

## 🔐 VPS Access Info

- **Host**: 147.93.156.165
- **User**: root
- **Port**: 22
- **Path**: /root/CryptoMentor
- **Service**: cryptomentor-bot

---

**Last Updated**: 2026-03-31
**Version**: 1.0.0
