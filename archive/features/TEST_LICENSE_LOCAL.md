# Test License System Locally

Panduan untuk test license system di lokal sebelum deploy ke production.

## Prerequisites

1. Python 3.10+ sudah terinstall
2. Dependencies sudah terinstall:
   ```bash
   cd license_server
   pip install -r requirements.txt
   ```

## Step 1: Jalankan License API

Buka terminal pertama dan jalankan:

```bash
cd license_server
python license_api.py
```

Output yang diharapkan:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

## Step 2: Test License API

Buka terminal kedua dan jalankan test script:

```bash
python test_license_local.py
```

Output yang diharapkan:
```
Testing license check for WL_ID: 61796c-bd62-4ccc-5f45-a7731f7f6692
URL: http://localhost:8080/api/license/check
Payload: {'wl_id': '61796c-bd62-4ccc-5f45-a7731f7f6692', 'secret_key': '<REDACTED_WL_SECRET_KEY>'}

Status Code: 200
Response: {'valid': True/False, 'expires_in_days': X, 'balance': Y, 'warning': True/False, 'status': 'active/inactive/grace_period'}

✅ License check berhasil!
```

## Step 3: Test Whitelabel Bot dengan License Check

Setelah license API berjalan, test whitelabel bot:

```bash
cd "Whitelabel #1"
python bot.py
```

Bot akan:
1. Check license via http://localhost:8080
2. Jika valid: bot akan start dan merespon command
3. Jika invalid: bot akan kirim notifikasi ke admin dan halt

## Troubleshooting

### Error: ModuleNotFoundError

Pastikan dependencies sudah terinstall:
```bash
cd license_server
pip install -r requirements.txt
```

### Error: Connection refused

Pastikan license_api.py sudah berjalan di terminal pertama.

### Error: License check failed

Cek apakah WL_ID dan WL_SECRET_KEY di `Whitelabel #1/.env` sudah benar:
```
WL_ID=61796c-bd62-4ccc-5f45-a7731f7f6692
WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>
LICENSE_API_URL=http://localhost:8080
```

## Status License di Database

Untuk cek status license di Supabase:

1. Buka Supabase dashboard: https://xrbqnocovfymdikngaza.supabase.co
2. Masuk ke Table Editor → wl_licenses
3. Cari row dengan wl_id = `61796c-bd62-4ccc-5f45-a7731f7f6692`
4. Cek kolom:
   - `status`: harus 'active' agar valid
   - `balance_usdt`: saldo USDT
   - `expires_at`: tanggal expired
   - `monthly_fee`: biaya bulanan

## Test Payment Flow (Admin2)

Admin2 (user_id: 1234500009) bisa test payment flow:

1. Start bot: `/start`
2. Klik "Start Auto Trading"
3. Bot akan minta API key Bitunix
4. Setelah setup, bot akan mulai autotrade

Untuk test license payment:
1. Admin2 bisa lihat deposit address di database
2. Kirim USDT BEP-20 ke deposit address
3. Deposit monitor akan detect dan credit balance
4. Billing cron akan auto-debit setiap hari

## Next Steps

Setelah test lokal berhasil:
1. Deploy license API ke VPS (port 8080)
2. Update `LICENSE_API_URL` di whitelabel bot ke `http://147.93.156.165:8080`
3. Restart whitelabel bot di VPS
4. Setup systemd service untuk license_api, billing_cron, deposit_monitor
