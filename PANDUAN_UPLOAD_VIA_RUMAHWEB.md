# 📋 Panduan Upload File Verification via Rumah Web

## 🎯 File yang Perlu Diupload

File sudah saya buatkan di folder Anda:
- **Nama file**: `google25bce93832cdac80.html`
- **Lokasi**: `C:\V3-Final-Version\google25bce93832cdac80.html`

---

## 📝 Langkah-Langkah Upload

### Step 1: Login ke Panel Rumah Web

1. Buka browser
2. Kunjungi: **https://clientzone.rumahweb.com/** (atau URL panel Rumah Web Anda)
3. Login dengan akun Anda

---

### Step 2: Buka File Manager

Ada beberapa cara tergantung panel yang Anda gunakan:

#### Jika Pakai cPanel:
1. Cari menu **"File Manager"** atau **"Pengelola File"**
2. Klik untuk membuka

#### Jika Pakai Panel Lain:
1. Cari menu **"Files"**, **"File Manager"**, atau **"FTP"**
2. Klik untuk membuka

---

### Step 3: Navigate ke Folder Website

1. Di File Manager, cari folder website Anda
2. Kemungkinan lokasinya:
   - `/var/www/cryptomentor/` (paling mungkin)
   - `/public_html/`
   - `/home/cryptomentor/public_html/`
   - `/www/`

**Tips**: Cari folder yang berisi file website Anda (index.html, assets, dll)

---

### Step 4: Upload File

1. Klik tombol **"Upload"** atau **"Upload File"**
2. Pilih file: `google25bce93832cdac80.html` dari komputer Anda
3. Tunggu sampai upload selesai (file sangat kecil, hanya beberapa detik)
4. Klik **"Close"** atau **"Back to File Manager"**

---

### Step 5: Verify File Terupload

1. Refresh File Manager
2. Cari file `google25bce93832cdac80.html` di list
3. Pastikan file ada di folder yang sama dengan file website lainnya

---

### Step 6: Set Permissions (Optional tapi Recommended)

1. Klik kanan pada file `google25bce93832cdac80.html`
2. Pilih **"Permissions"** atau **"Change Permissions"**
3. Set ke: **644** (atau centang: Owner Read+Write, Group Read, World Read)
4. Klik **"Save"**

---

### Step 7: Test di Browser

1. Buka browser baru
2. Kunjungi: **https://cryptomentor.id/google25bce93832cdac80.html**
3. Anda harus melihat text: **google-site-verification: google25bce93832cdac80.html**

✅ Jika text muncul, file berhasil diupload!

---

### Step 8: Verify di Google Search Console

1. Kembali ke Google Search Console
2. Klik tombol **"VERIFIKASI"**
3. ✅ Selesai!

---

## 🔧 Troubleshooting

### File tidak muncul di browser (404 Error)

**Kemungkinan 1**: File di folder yang salah
- Pastikan file ada di folder root website (bukan di subfolder)
- Cek apakah ada file lain seperti `index.html` di folder yang sama

**Kemungkinan 2**: Permissions salah
- Set permissions ke 644
- Atau coba 755

**Kemungkinan 3**: Cache browser
- Tekan Ctrl+F5 untuk hard refresh
- Atau buka di incognito/private mode

---

## 📸 Screenshot Bantuan

Jika Anda kesulitan menemukan File Manager, screenshot panel Rumah Web Anda dan saya bisa bantu lebih spesifik.

---

## 🎯 Quick Checklist

- [ ] Login ke panel Rumah Web
- [ ] Buka File Manager
- [ ] Navigate ke folder website (`/var/www/cryptomentor/`)
- [ ] Upload file `google25bce93832cdac80.html`
- [ ] Set permissions ke 644
- [ ] Test URL di browser
- [ ] Verify di Google Search Console

---

## 💡 Tips

- File sangat kecil (hanya 1 line text), upload sangat cepat
- Jangan ubah nama file atau isinya
- Pastikan file di root folder website, bukan di subfolder
- Jangan hapus file setelah verification berhasil (Google akan re-check berkala)

---

Selamat mencoba! Jika ada kendala, screenshot dan tanyakan ke saya. 🚀
