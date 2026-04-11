# 📋 Panduan Upload File Verification via PuTTY

## Langkah 1: Buka PuTTY

1. Buka aplikasi PuTTY
2. Masukkan:
   - Host Name: **147.93.156.165**
   - Port: **22**
   - Connection type: **SSH**
3. Klik **"Open"**
4. Login dengan username: **root** (dan password Anda)

---

## Langkah 2: Copy Command Ini

Setelah login ke VPS, copy paste command ini (SEMUA sekaligus):

```bash
echo "google-site-verification: google25bce93832cdac80.html" > /var/www/cryptomentor/google25bce93832cdac80.html && chmod 644 /var/www/cryptomentor/google25bce93832cdac80.html && chown www-data:www-data /var/www/cryptomentor/google25bce93832cdac80.html && echo "✅ File created!" && cat /var/www/cryptomentor/google25bce93832cdac80.html && curl -s https://cryptomentor.id/google25bce93832cdac80.html
```

---

## Langkah 3: Verify Output

Anda harus melihat output seperti ini:

```
✅ File created!
google-site-verification: google25bce93832cdac80.html
google-site-verification: google25bce93832cdac80.html
```

Jika muncul 2x text "google-site-verification", berarti berhasil!

---

## Langkah 4: Test di Browser

Buka browser dan kunjungi:
```
https://cryptomentor.id/google25bce93832cdac80.html
```

Harus muncul text: **google-site-verification: google25bce93832cdac80.html**

---

## Langkah 5: Verify di Google Search Console

1. Kembali ke Google Search Console
2. Klik tombol **"VERIFIKASI"**
3. ✅ Selesai!

---

## 🔧 Troubleshooting

### Jika command gagal:

**Error: Permission denied**
```bash
# Pastikan Anda login sebagai root
sudo su
```

**Error: Directory not found**
```bash
# Cek apakah directory ada
ls -la /var/www/cryptomentor/
```

**Error: File tidak bisa diakses via browser**
```bash
# Cek nginx config
nginx -t
systemctl status nginx
```

---

## 📝 Alternative: Step by Step Commands

Jika command panjang tidak work, jalankan satu per satu:

```bash
# 1. Create file
echo "google-site-verification: google25bce93832cdac80.html" > /var/www/cryptomentor/google25bce93832cdac80.html

# 2. Set permission
chmod 644 /var/www/cryptomentor/google25bce93832cdac80.html

# 3. Set owner
chown www-data:www-data /var/www/cryptomentor/google25bce93832cdac80.html

# 4. Verify
cat /var/www/cryptomentor/google25bce93832cdac80.html

# 5. Test URL
curl https://cryptomentor.id/google25bce93832cdac80.html
```

---

## ✅ Success Indicators

- ✅ File created without errors
- ✅ `cat` command shows correct content
- ✅ `curl` command returns the verification text
- ✅ Browser shows the verification text
- ✅ Google Search Console verification succeeds

---

Selamat mencoba! 🚀
