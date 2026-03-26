# Implementation Plan: Whitelabel License Billing

## Overview

Implementasi sistem billing otomatis B2B untuk CryptoMentor Whitelabel menggunakan Python. Central_Server terdiri dari 5 komponen utama: HD Wallet Manager, License Manager, Deposit Monitor, Billing Engine, dan License API. WL_Bot mendapat satu komponen tambahan: License Guard.

## Tasks

- [x] 1. Setup project structure dan database schema
  - Buat direktori `license_server/` di root workspace dengan subdirektori `db/` dan `tests/`
  - Buat `license_server/requirements.txt` dengan semua dependencies: `bip_utils`, `eth_account`, `fastapi`, `uvicorn`, `slowapi`, `apscheduler`, `httpx`, `supabase`, `python-dotenv`, `hypothesis`, `pytest`, `pytest-asyncio`
  - Buat `license_server/.env.example` dengan semua environment variable yang dibutuhkan Central_Server
  - Buat `license_server/db/setup.sql` dengan DDL lengkap: enum types, tabel `wl_licenses`, `wl_deposits`, `wl_billing_history`, indexes, RLS policies, dan Supabase RPC `process_billing`
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 7.1_

- [x] 2. Implementasi HD Wallet Manager
  - [x] 2.1 Buat `license_server/wallet_manager.py` dengan class `HDWalletManager`
    - Implementasi `__init__` yang menerima mnemonic string dan raise `RuntimeError` jika kosong, raise `ValueError` jika mnemonic invalid
    - Implementasi `derive_address(index: int) -> str` menggunakan BIP-44 path `m/44'/60'/0'/0/{index}` via `bip_utils`, return checksummed address via `eth_account`
    - Implementasi `get_next_index(used_indices: list[int]) -> int` yang return min unused index >= 0
    - _Requirements: 1.1, 1.4, 1.5, 1.6_

  - [ ]* 2.2 Tulis property test untuk HD Wallet Manager
    - **Property 1: HD Wallet Derivation Determinism** — derive address dua kali dari mnemonic dan index yang sama harus menghasilkan address identik
    - **Validates: Requirements 1.1**
    - **Property 2: Deposit Index Uniqueness** — sequence registrasi tidak boleh menghasilkan deposit_index atau deposit_address yang sama
    - **Validates: Requirements 1.2, 1.3**
    - Tambahkan unit test: verifikasi path `m/44'/60'/0'/0/0` kompatibel MetaMask, startup error jika MASTER_SEED_MNEMONIC kosong

- [x] 3. Implementasi License Manager
  - [x] 3.1 Buat `license_server/license_manager.py` dengan class `LicenseManager`
    - Implementasi `register_wl(admin_telegram_id, monthly_fee)` yang generate `secret_key` UUID v4, assign `deposit_index` via `HDWalletManager.get_next_index`, derive `deposit_address`, INSERT ke `wl_licenses`
    - Implementasi `get_license(wl_id)` yang SELECT dari `wl_licenses`
    - Implementasi `credit_balance(wl_id, amount, tx_hash, block_number)` yang atomic INSERT `wl_deposits` + UPDATE `wl_licenses.balance_usdt`, return `False` jika `tx_hash` sudah ada (idempotent)
    - Implementasi `debit_billing(wl_id)` yang call Supabase RPC `process_billing`
    - _Requirements: 1.2, 1.3, 2.3, 2.4, 3.1, 3.2, 3.3, 3.5, 7.3, 7.4_

  - [ ]* 3.2 Tulis property test untuk License Manager
    - **Property 3: Secret Key Format** — setiap `secret_key` yang di-generate harus match regex UUID v4
    - **Validates: Requirements 3.5**
    - Tambahkan unit test: CRUD operations, RLS enforcement, `credit_balance` idempotency dengan tx_hash duplikat

- [x] 4. Implementasi Deposit Monitor
  - [x] 4.1 Buat `license_server/deposit_monitor.py` dengan class `DepositMonitor`
    - Implementasi `run()` sebagai asyncio main loop yang poll semua active deposit addresses setiap 300 detik
    - Implementasi `poll_address(wl_id, address)` yang GET BSCScan `tokentx` endpoint, filter USDT contract `0x55d398326f99059fF775485246999027B3197955`, check `MIN_CONFIRMATIONS = 12`
    - Implementasi `process_tx(wl_id, tx)` yang call `license_manager.credit_balance()` dan kirim notifikasi Telegram ke WL Owner via bot pusat jika sukses
    - Implementasi exponential backoff `[1s, 2s, 4s]` max 3 retries untuk BSCScan API error/rate limit
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 4.2 Tulis property test untuk Deposit Monitor
    - **Property 4: Deposit Confirmation Threshold** — transaksi dengan < 12 confirmations tidak boleh di-credit; >= 12 confirmations harus eligible
    - **Validates: Requirements 2.2**
    - **Property 5: Deposit Credit Round-Trip** — balance setelah credit harus = balance_before + amount, dan record `wl_deposits` harus ada dengan tx_hash dan amount yang benar
    - **Validates: Requirements 2.3**
    - **Property 6: Deposit Idempotency** — memproses tx_hash yang sama dua kali tidak boleh mengubah balance atau insert duplicate row
    - **Validates: Requirements 2.4**
    - Tambahkan unit test: retry logic BSCScan 429, notifikasi Telegram failure tidak abort proses, skip tx dengan amount 0

- [ ] 5. Checkpoint — Pastikan semua tests pass
  - Pastikan semua tests pass, tanyakan ke user jika ada pertanyaan.

- [x] 6. Implementasi Billing Engine
  - [x] 6.1 Buat `license_server/billing_cron.py` dengan `AsyncIOScheduler` dan fungsi `run_billing_cycle()`
    - Setup `CronTrigger(hour=0, minute=0, timezone='UTC')` via APScheduler
    - Implementasi `run_billing_cycle()` yang query semua WL dengan `status IN ('active', 'grace_period')` dan `expires_at <= NOW()`
    - Untuk setiap WL: call `license_manager.debit_billing(wl_id)`, kirim warning Telegram ke `admin_telegram_id` jika status menjadi `grace_period`
    - Implementasi grace period suspension: jika WL sudah `grace_period` > 3 hari (cek dari `wl_billing_history` entry pertama dengan status `failed`), UPDATE status ke `suspended` dan kirim notifikasi
    - Log ringkasan eksekusi: total WL diproses, sukses, gagal, suspended
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [ ]* 6.2 Tulis property test untuk Billing Engine
    - **Property 7: Billing Success Outcome** — jika `balance >= monthly_fee` dan `expires_at <= NOW()`, setelah billing: balance berkurang tepat `monthly_fee`, `expires_at` bertambah 30 hari, status tetap `active`, history record `success` ter-insert
    - **Validates: Requirements 4.3**
    - **Property 8: Billing Failure Outcome** — jika `balance < monthly_fee` dan `expires_at <= NOW()`, setelah billing: balance tidak berubah, status menjadi `grace_period`, history record `failed` ter-insert
    - **Validates: Requirements 4.4**
    - **Property 9: Grace Period to Suspended Transition** — WL dengan `grace_period` dan entry billing_history pertama > 3 hari lalu harus di-transition ke `suspended`
    - **Validates: Requirements 4.5**
    - **Property 18: Balance Non-Negative Invariant** — `balance_usdt` tidak pernah negatif setelah sequence billing operations apapun
    - **Validates: Requirements 7.4**
    - Tambahkan unit test: Supabase RPC failure untuk satu WL tidak abort cycle, log summary format

- [x] 7. Implementasi License API
  - [x] 7.1 Buat `license_server/license_api.py` dengan FastAPI app
    - Setup FastAPI app dengan `slowapi` rate limiter: 60 req/menit per `wl_id`
    - Implementasi `POST /api/license/check` yang menerima `{"wl_id": str, "secret_key": str}`
    - Validasi awal: regex UUID v4 untuk `secret_key` sebelum query DB; return HTTP 400 `{"error": "invalid_request"}` jika invalid
    - Query `wl_licenses` via `LicenseManager.get_license()`; return HTTP 404 jika tidak ditemukan, HTTP 401 jika `secret_key` tidak cocok
    - Hitung `expires_in_days`, set `warning: true` jika `expires_in_days <= 5` ATAU `balance_usdt < monthly_fee`
    - Return HTTP 200 dengan `{"valid", "expires_in_days", "balance", "warning", "status"}`
    - Log setiap request: timestamp, `wl_id`, response status (TANPA `secret_key`)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 7.2_

  - [ ]* 7.2 Tulis property test untuk License API
    - **Property 13: API Valid Credentials Response Shape** — request dengan `wl_id` dan `secret_key` valid harus return HTTP 200 dengan semua required fields
    - **Validates: Requirements 6.2**
    - **Property 14: API Unauthorized Response** — `wl_id` valid + `secret_key` tidak cocok harus return HTTP 401 `{"error": "unauthorized"}`
    - **Validates: Requirements 6.3**
    - **Property 15: API Not Found Response** — `wl_id` tidak ada harus return HTTP 404 `{"error": "not_found"}`
    - **Validates: Requirements 6.4**
    - **Property 16: Warning Field Logic** — `warning: true` jika `expires_in_days <= 5` OR `balance < monthly_fee`; `warning: false` jika keduanya false
    - **Validates: Requirements 6.5**
    - **Property 17: Invalid Secret Key Format Returns 400** — `secret_key` bukan UUID v4 harus return HTTP 400 tanpa DB query
    - **Validates: Requirements 6.8**
    - Tambahkan unit test: rate limit 429 response, log tidak mengandung `secret_key`, Supabase connection failure return 503

- [ ] 8. Checkpoint — Pastikan semua tests pass
  - Pastikan semua tests pass, tanyakan ke user jika ada pertanyaan.

- [x] 9. Implementasi License Guard di WL Bot
  - [x] 9.1 Buat `Whitelabel #1/app/license_guard.py` dengan class `LicenseGuard`
    - Implementasi `startup_check() -> bool` yang call `_call_api()`, simpan response ke cache via `_save_cache()`, return `True` jika `valid: true`, return `False` dan kirim notifikasi Telegram jika `valid: false` dan `status: suspended`
    - Implementasi `periodic_check_loop()` sebagai asyncio loop yang check setiap 86400 detik (24 jam)
    - Implementasi `_call_api() -> dict | None` dengan timeout 10 detik via `httpx`; return `None` jika network error atau timeout
    - Implementasi `_load_cache() -> dict | None` yang baca `data/license_cache.json`; return `None` jika file tidak ada atau corrupt
    - Implementasi `_save_cache(response: dict)` yang tulis response + `cached_at` timestamp ke `data/license_cache.json`
    - Fallback logic: jika API tidak bisa dijangkau, gunakan cache jika `cached_at` < 48 jam; jika cache > 48 jam dan API masih down, halt bot dan kirim notifikasi
    - Kirim warning Telegram ke admin jika `warning: true` dan `expires_in_days < 5`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ]* 9.2 Tulis property test untuk License Guard
    - **Property 10: License Guard Allow on Valid Response** — response dengan `valid: true` harus membuat `startup_check()` return `True`
    - **Validates: Requirements 5.2**
    - **Property 11: License Guard Deny on Suspended Response** — response dengan `valid: false` dan `status: suspended` harus membuat `startup_check()` return `False`
    - **Validates: Requirements 5.4**
    - **Property 12: Cache Persistence Round-Trip** — response yang di-save ke cache file harus bisa di-load kembali dengan `cached_at` timestamp yang valid
    - **Validates: Requirements 5.7**
    - Tambahkan unit test: cache stale boundary tepat 48 jam, cache file corrupt/missing, API 5xx treated as network error

- [x] 10. Wiring dan integrasi
  - [x] 10.1 Integrasikan `LicenseGuard` ke startup WL Bot
    - Import dan inisialisasi `LicenseGuard` di `Whitelabel #1/bot.py`
    - Panggil `await license_guard.startup_check()` sebelum bot mulai polling; halt jika return `False`
    - Schedule `license_guard.periodic_check_loop()` sebagai asyncio task
    - _Requirements: 5.1, 5.2_

  - [x] 10.2 Pastikan semua komponen Central_Server dapat dijalankan sebagai standalone process
    - Tambahkan `if __name__ == "__main__"` entry point di `deposit_monitor.py` dan `billing_cron.py`
    - Pastikan `license_api.py` dapat dijalankan via `uvicorn license_server.license_api:app --port 8080`
    - Verifikasi semua env vars di-load via `python-dotenv` dengan error yang jelas jika ada yang missing
    - _Requirements: 1.6, 7.1_

- [ ] 11. Final checkpoint — Pastikan semua tests pass
  - Jalankan seluruh test suite di `license_server/tests/`, pastikan semua pass. Tanyakan ke user jika ada pertanyaan.

## Notes

- Tasks bertanda `*` bersifat opsional dan dapat di-skip untuk MVP yang lebih cepat
- Setiap task mereferensikan requirements spesifik untuk traceability
- Property tests menggunakan `hypothesis` dengan minimum 100 examples per property (`@settings(max_examples=100)`)
- Setiap property test harus diberi komentar: `# Feature: whitelabel-license-billing, Property N: <nama>`
- `MASTER_SEED_MNEMONIC` tidak boleh pernah muncul di log, response API, atau database
- Semua operasi write ke Supabase menggunakan service role key
