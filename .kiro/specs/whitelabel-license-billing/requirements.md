# Requirements Document

## Introduction

Sistem billing otomatis untuk B2B whitelabel CryptoMentor AI. CryptoMentor (pusat) menjual lisensi ke Whitelabel Owner (WL Owner) yang menjalankan instance bot Telegram autotrade crypto mereka sendiri. Setiap WL instance memiliki database Supabase, bot token, dan API keys terpisah.

Sistem ini mencakup: HD Wallet untuk generate deposit address unik per WL, deteksi deposit USDT BEP-20 via BSCScan, manajemen lisensi di database pusat, auto-billing bulanan, license guard di sisi WL bot, dan License API REST endpoint.

## Glossary

- **Central_Server**: Server pusat CryptoMentor yang menjalankan License API, deposit monitor, dan billing engine
- **WL_Bot**: Instance bot Telegram milik WL Owner yang berjalan di server terpisah
- **WL_Owner**: Pelanggan B2B yang membeli lisensi untuk menjalankan WL_Bot
- **License_Manager**: Komponen di Central_Server yang mengelola data lisensi di Supabase pusat
- **HD_Wallet**: Hierarchical Deterministic Wallet berbasis BIP-44 untuk generate deposit address BSC
- **Deposit_Monitor**: Komponen di Central_Server yang memantau transaksi USDT BEP-20 masuk via BSCScan API
- **Billing_Engine**: Komponen cron job di Central_Server yang menjalankan pemotongan biaya bulanan
- **License_Guard**: Komponen di WL_Bot yang memvalidasi status lisensi ke License API
- **License_API**: REST API di Central_Server untuk validasi lisensi
- **USDT_BEP20**: Token USDT di jaringan BNB Smart Chain (BSC)
- **Master_Seed**: BIP-39 mnemonic phrase yang disimpan di Central_Server sebagai root HD Wallet
- **Deposit_Index**: Angka integer unik per WL yang digunakan sebagai derivation index BIP-44
- **Grace_Period**: Periode 3 hari setelah balance habis sebelum lisensi di-suspend
- **Secret_Key**: Token autentikasi unik per WL untuk mengakses License_API

---

## Requirements

### Requirement 1: HD Wallet — Generate Deposit Address per WL

**User Story:** As a CryptoMentor admin, I want each WL Owner to have a unique BSC deposit address derived from a single master seed, so that deposits can be tracked per WL without managing multiple private keys.

#### Acceptance Criteria

1. THE HD_Wallet SHALL derive BSC addresses menggunakan BIP-44 path `m/44'/60'/0'/0/{index}` dari Master_Seed
2. WHEN a new WL Owner is registered, THE License_Manager SHALL assign a unique Deposit_Index dan generate deposit address via HD_Wallet, lalu menyimpannya ke kolom `deposit_address` dan `deposit_index` di tabel `wl_licenses`
3. THE HD_Wallet SHALL memastikan setiap Deposit_Index hanya digunakan oleh satu WL Owner (unique constraint di database)
4. THE Master_Seed SHALL disimpan sebagai environment variable terenkripsi di Central_Server dan tidak pernah ditulis ke database atau log
5. WHERE Master_Seed diimport ke MetaMask, THE HD_Wallet SHALL menggunakan derivation path yang kompatibel dengan MetaMask default BIP-44 ETH path sehingga semua WL address dapat diakses dari satu wallet
6. IF Master_Seed tidak tersedia saat startup, THEN THE Central_Server SHALL menolak untuk start dan mencatat error ke log

### Requirement 2: Deposit Detection via BSCScan API

**User Story:** As a CryptoMentor admin, I want incoming USDT BEP-20 deposits to be detected automatically, so that WL Owner balance dapat di-credit tanpa proses manual.

#### Acceptance Criteria

1. WHEN Deposit_Monitor berjalan, THE Deposit_Monitor SHALL melakukan polling ke BSCScan API setiap 5 menit untuk setiap deposit address aktif di tabel `wl_licenses`
2. WHEN transaksi USDT BEP-20 masuk terdeteksi ke deposit address WL, THE Deposit_Monitor SHALL memverifikasi bahwa transaksi memiliki minimal 12 block confirmations sebelum memproses
3. WHEN transaksi terverifikasi, THE Deposit_Monitor SHALL menambahkan jumlah USDT ke kolom `balance_usdt` di tabel `wl_licenses` dan mencatat transaksi ke tabel `wl_deposits`
4. THE Deposit_Monitor SHALL memastikan setiap `tx_hash` hanya diproses satu kali (idempotent) dengan mengecek keberadaan `tx_hash` di tabel `wl_deposits` sebelum memproses
5. WHEN deposit berhasil dikreditkan, THE Deposit_Monitor SHALL mengirim notifikasi ke Telegram user ID milik WL_Owner via bot pusat dengan informasi jumlah deposit dan balance terbaru
6. IF BSCScan API mengembalikan error atau rate limit, THEN THE Deposit_Monitor SHALL melakukan retry dengan exponential backoff maksimal 3 kali sebelum mencatat error ke log dan melanjutkan ke address berikutnya

### Requirement 3: License Manager — Database Schema Pusat

**User Story:** As a CryptoMentor admin, I want all WL license data stored in a central Supabase database, so that billing, deposit, dan status lisensi dapat dikelola dari satu tempat.

#### Acceptance Criteria

1. THE License_Manager SHALL menyimpan data lisensi di tabel `wl_licenses` dengan kolom: `wl_id` (PK), `balance_usdt` (DECIMAL), `expires_at` (TIMESTAMPTZ), `status` (ENUM: active/grace_period/suspended/inactive), `monthly_fee` (DECIMAL, default 100), `deposit_address` (VARCHAR), `deposit_index` (INTEGER UNIQUE), `secret_key` (VARCHAR UNIQUE), `admin_telegram_id` (BIGINT), `created_at` (TIMESTAMPTZ)
2. THE License_Manager SHALL menyimpan riwayat deposit di tabel `wl_deposits` dengan kolom: `id` (PK), `wl_id` (FK), `tx_hash` (VARCHAR UNIQUE), `amount_usdt` (DECIMAL), `block_number` (BIGINT), `confirmed_at` (TIMESTAMPTZ), `created_at` (TIMESTAMPTZ)
3. THE License_Manager SHALL menyimpan riwayat billing di tabel `wl_billing_history` dengan kolom: `id` (PK), `wl_id` (FK), `amount_usdt` (DECIMAL), `billing_date` (DATE), `status` (ENUM: success/failed), `balance_before` (DECIMAL), `balance_after` (DECIMAL), `expires_at_before` (TIMESTAMPTZ), `expires_at_after` (TIMESTAMPTZ), `created_at` (TIMESTAMPTZ)
4. THE License_Manager SHALL menggunakan Row Level Security (RLS) di Supabase pusat sehingga hanya service role key yang dapat melakukan write ke ketiga tabel tersebut
5. WHEN a new WL Owner is onboarded, THE License_Manager SHALL generate `secret_key` berupa UUID v4 yang unik dan tidak dapat diprediksi

### Requirement 4: Auto-Billing Cron Job

**User Story:** As a CryptoMentor admin, I want monthly fees to be deducted automatically, so that lisensi WL Owner dikelola tanpa intervensi manual setiap bulan.

#### Acceptance Criteria

1. THE Billing_Engine SHALL berjalan sebagai cron job setiap hari pukul 00:00 UTC
2. WHEN Billing_Engine berjalan, THE Billing_Engine SHALL memproses semua WL dengan status `active` atau `grace_period` yang memiliki `expires_at` kurang dari atau sama dengan waktu saat ini (hari ini)
3. WHEN balance WL mencukupi (balance_usdt >= monthly_fee), THE Billing_Engine SHALL mengurangi `balance_usdt` sebesar `monthly_fee`, mengubah `expires_at` menjadi `expires_at + 30 hari`, mempertahankan status `active`, dan mencatat ke `wl_billing_history` dengan status `success`
4. WHEN balance WL tidak mencukupi (balance_usdt < monthly_fee), THE Billing_Engine SHALL mengubah status menjadi `grace_period`, mencatat ke `wl_billing_history` dengan status `failed`, dan mengirim pesan peringatan ke `admin_telegram_id` WL_Owner via bot pusat
5. WHILE status WL adalah `grace_period` dan sudah melewati 3 hari sejak pertama kali masuk grace_period, THE Billing_Engine SHALL mengubah status menjadi `suspended` dan mengirim notifikasi suspend ke `admin_telegram_id` WL_Owner
6. THE Billing_Engine SHALL memproses setiap WL dalam transaksi database atomik sehingga partial update tidak terjadi jika terdapat error di tengah proses
7. WHEN Billing_Engine selesai berjalan, THE Billing_Engine SHALL mencatat ringkasan eksekusi (jumlah WL diproses, sukses, gagal, suspended) ke log Central_Server

### Requirement 5: License Guard di WL Bot

**User Story:** As a WL Owner, I want my bot to automatically check its license status, so that bot berhenti beroperasi jika lisensi tidak valid dan saya mendapat notifikasi tepat waktu.

#### Acceptance Criteria

1. WHEN WL_Bot melakukan startup, THE License_Guard SHALL melakukan request ke License_API endpoint `POST /api/license/check` menggunakan `wl_id` dan `secret_key` yang dikonfigurasi di environment variable WL_Bot
2. WHEN License_Guard menerima respons `valid: true`, THE License_Guard SHALL mengizinkan WL_Bot untuk berjalan normal dan menjadwalkan check berikutnya setelah 24 jam
3. WHEN License_Guard menerima respons dengan `warning: true` dan `expires_in_days < 5`, THE License_Guard SHALL mengirim pesan peringatan ke admin WL_Bot via Telegram dan tetap mengizinkan bot berjalan
4. WHEN License_Guard menerima respons `valid: false` dengan status `suspended`, THE License_Guard SHALL mengirim pesan ke admin WL_Bot via Telegram bahwa bot di-suspend karena lisensi tidak aktif, lalu menghentikan proses WL_Bot
5. IF License_API tidak dapat dijangkau (network error atau timeout > 10 detik), THEN THE License_Guard SHALL menggunakan cached license status terakhir yang valid (maksimal 48 jam) dan mencatat warning ke log
6. IF cached license status sudah lebih dari 48 jam dan License_API masih tidak dapat dijangkau, THEN THE License_Guard SHALL menghentikan WL_Bot dan mengirim notifikasi ke admin WL_Bot
7. THE License_Guard SHALL menyimpan cached license status di file lokal yang persisten sehingga tetap tersedia setelah restart WL_Bot

### Requirement 6: License API — REST Endpoint

**User Story:** As a WL Bot operator, I want a secure API endpoint to check license validity, so that WL_Bot dapat memverifikasi status lisensinya secara programatik.

#### Acceptance Criteria

1. THE License_API SHALL menyediakan endpoint `POST /api/license/check` yang menerima JSON body `{"wl_id": string, "secret_key": string}`
2. WHEN request diterima dengan `wl_id` dan `secret_key` yang valid, THE License_API SHALL mengembalikan JSON response `{"valid": true, "expires_in_days": integer, "balance": float, "warning": boolean, "status": string}` dengan HTTP 200
3. WHEN request diterima dengan `secret_key` yang tidak cocok dengan `wl_id`, THE License_API SHALL mengembalikan HTTP 401 dengan body `{"error": "unauthorized"}`
4. WHEN request diterima dengan `wl_id` yang tidak ditemukan, THE License_API SHALL mengembalikan HTTP 404 dengan body `{"error": "not_found"}`
5. THE License_API SHALL mengisi field `warning: true` pada response jika `expires_in_days <= 5` atau `balance_usdt < monthly_fee`
6. THE License_API SHALL membatasi request rate maksimal 60 request per menit per `wl_id` untuk mencegah abuse
7. THE License_API SHALL mencatat setiap request ke log dengan timestamp, `wl_id`, dan response status (tanpa mencatat `secret_key`)
8. IF `secret_key` dalam request tidak sesuai format UUID v4, THEN THE License_API SHALL mengembalikan HTTP 400 dengan body `{"error": "invalid_request"}` tanpa melakukan query ke database

### Requirement 7: Keamanan dan Integritas Data

**User Story:** As a CryptoMentor admin, I want the billing system to be secure and data-consistent, so that tidak ada manipulasi balance atau akses tidak sah ke sistem lisensi.

#### Acceptance Criteria

1. THE Central_Server SHALL menyimpan Master_Seed hanya sebagai environment variable dan tidak pernah mengeksposnya melalui API, log, atau response apapun
2. THE License_API SHALL menggunakan HTTPS untuk semua komunikasi antara WL_Bot dan Central_Server
3. WHEN balance WL diupdate (deposit atau billing), THE License_Manager SHALL menggunakan database transaction untuk memastikan konsistensi antara `wl_licenses.balance_usdt` dan record di `wl_deposits` atau `wl_billing_history`
4. THE License_Manager SHALL memastikan `balance_usdt` tidak pernah bernilai negatif; IF operasi billing akan menghasilkan nilai negatif, THEN THE Billing_Engine SHALL mencatat status `failed` tanpa mengurangi balance
5. THE Central_Server SHALL merotasi log yang mengandung informasi sensitif dan menyimpan log maksimal 30 hari
