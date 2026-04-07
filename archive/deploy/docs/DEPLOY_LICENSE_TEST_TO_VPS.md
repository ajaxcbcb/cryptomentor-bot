# Deploy License Test ke VPS - Panduan Lengkap

## Info Test License yang Sudah Dibuat

```
WL_ID           : <REDACTED_UUID>
SECRET_KEY      : <REDACTED_UUID>
DEPOSIT_ADDRESS : 0xff680baa2BaaD50f3756efF778eF673d0fd8cAF9
ADMIN_TELEGRAM_ID: 1234500014
MONTHLY_FEE     : $10
STATUS          : inactive (perlu aktivasi)
EXPIRES_AT      : (akan diset setelah deposit pertama)
```

---

## Step 1: Push Code ke GitHub

Dari local machine (Windows):

```bash
git add .
git commit -m "Add test license registration for UID 1234500014"
git push origin main
```

---

## Step 2: SSH ke VPS

```bash
ssh root@147.93.156.165
```

---

## Step 3: Pull Latest Code di VPS

```bash
cd /root/cryptomentor-bot
git pull origin main
```

---

## Step 4: Cek License API Running

```bash
sudo systemctl status license-api
```

Jika belum running atau belum ada service:

```bash
# Install dependencies dulu
cd /root/cryptomentor-bot/license_server
pip3 install -r requirements.txt

# Buat service file
sudo nano /etc/systemd/system/license-api.service
```

Paste ini:

```ini
[Unit]
Description=License API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cryptomentor-bot/license_server
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m license_server.license_api
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save (Ctrl+X, Y, Enter), lalu:

```bash
sudo systemctl daemon-reload
sudo systemctl enable license-api
sudo systemctl start license-api
sudo systemctl status license-api
```

---

## Step 5: Activate License (Deposit + Billing)

Jalankan script untuk deposit $50 dan aktivasi:

```bash
cd /root/cryptomentor-bot
python3 << 'EOF'
import asyncio
from datetime import datetime, timezone, timedelta
import sys
sys.path.insert(0, '/root/cryptomentor-bot')

from license_server.license_manager import LicenseManager

WL_ID = "<REDACTED_UUID>"

async def main():
    manager = LicenseManager()
    
    print(f"Activating license: {WL_ID}")
    
    # Deposit $50
    print("\n[1/2] Depositing $50...")
    success = await manager.credit_balance(
        wl_id=WL_ID,
        amount=50.0,
        tx_hash="0xVPS_DEPLOY_FINAL",
        block_number=99999999
    )
    print("✅ Deposit: $50" if success else "⚠️  Deposit skipped")
    
    # Billing
    print("\n[2/2] Processing billing...")
    license_row = await manager.get_license(wl_id=WL_ID)
    balance = float(license_row['balance_usdt'])
    monthly_fee = float(license_row['monthly_fee'])
    
    new_balance = balance - monthly_fee
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    
    client = await manager._get_client()
    await client.table('wl_licenses').update({
        'balance_usdt': new_balance,
        'status': 'active',
        'expires_at': expires_at.isoformat()
    }).eq('wl_id', WL_ID).execute()
    
    print(f"✅ Status: active")
    print(f"   Balance: ${new_balance}")
    print(f"   Expires: {expires_at.isoformat()}")

asyncio.run(main())
EOF
```

Expected output:
```
Activating license: <REDACTED_UUID>

[1/2] Depositing $50...
✅ Deposit: $50

[2/2] Processing billing...
✅ Status: active
   Balance: $40.0
   Expires: 2026-04-26T...
```

---

## Step 6: Test License API

```bash
curl -X POST http://localhost:8080/api/license/check \
  -H "Content-Type: application/json" \
  -d '{"wl_id":"<REDACTED_UUID>","secret_key":"<REDACTED_WL_SECRET_KEY>"}'
```

Expected response (after activation):
```json
{
  "valid": true,
  "expires_in_days": 29,
  "balance": 40.0,
  "warning": false,
  "status": "active"
}
```

---

## Step 7: Update Whitelabel Bot .env

Kasih credentials ini ke teman kamu untuk diisi di bot WL-nya:

```bash
# Jika bot WL ada di VPS yang sama
cd /root/cryptomentor-bot/whitelabel-1
nano .env
```

Update baris ini:

```env
WL_ID=<REDACTED_UUID>
WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>
LICENSE_API_URL=http://147.93.156.165:8080
```

Save (Ctrl+X, Y, Enter)

---

## Step 8: Restart Bot WL

```bash
sudo systemctl restart whitelabel1
sleep 3
sudo systemctl status whitelabel1
```

---

## Step 9: Check Logs

```bash
sudo journalctl -u whitelabel1 -n 50 --no-pager | grep -E "(License|Started|ERROR)"
```

Look for:
```
[LicenseGuard] License valid — status: active
```

---

## Step 10: Test di Telegram

1. Buka bot Telegram WL
2. Send `/start`
3. Bot harus respond normal

---

## Step 11: Test Billing Cycle (Opsional)

Untuk tes billing sekarang tanpa nunggu besok:

```bash
cd /root/cryptomentor-bot
python3 -c "import asyncio; from license_server.billing_cron import run_billing_cycle; asyncio.run(run_billing_cycle())"
```

Expected output:
```
run_billing_cycle: found 1 WL(s) due for billing
run_billing_cycle: wl_id=ccdd7e1c... billing failed, status=grace_period balance_before=0.00
run_billing_cycle: SUMMARY — total=1 success=0 failed=1 suspended=0
```

Status akan berubah ke `grace_period` karena saldo 0.

---

## Step 12: Cek Status License Setelah Billing

```bash
curl -X POST http://localhost:8080/api/license/check \
  -H "Content-Type: application/json" \
  -d '{"wl_id":"<REDACTED_UUID>","secret_key":"<REDACTED_WL_SECRET_KEY>"}'
```

Response setelah billing gagal:
```json
{
  "valid": true,
  "expires_in_days": 0,
  "balance": 0.0,
  "warning": true,
  "status": "grace_period"
}
```

Bot masih bisa jalan karena status `grace_period` (valid=true).

---

## Step 13: Test Deposit (Opsional)

Untuk tes deposit dan perpanjangan:

```bash
cd /root/cryptomentor-bot
python3 << 'EOF'
import asyncio
from license_server.license_manager import LicenseManager

async def main():
    manager = LicenseManager()
    
    # Deposit $20
    success = await manager.credit_balance(
        wl_id="<REDACTED_UUID>",
        amount=20.0,
        tx_hash="0xTEST_DEPOSIT_123",
        block_number=99999999
    )
    
    if success:
        print("✅ Deposit $20 berhasil")
        
        # Jalankan billing lagi
        result = await manager.debit_billing("<REDACTED_UUID>")
        print(f"✅ Billing: {result}")
    else:
        print("❌ Deposit gagal (mungkin tx_hash sudah ada)")

asyncio.run(main())
EOF
```

Expected output:
```
✅ Deposit $20 berhasil
✅ Billing: {'success': True, 'balance_before': 20.0, 'balance_after': 10.0, 'new_status': 'active', 'expires_at': '2026-04-26T...'}
```

---

## Troubleshooting

### License API tidak bisa diakses

```bash
# Cek port 8080
sudo netstat -tulpn | grep 8080

# Cek logs
sudo journalctl -u license-api -n 50

# Restart
sudo systemctl restart license-api
```

### Bot tidak bisa connect ke License API

```bash
# Test dari dalam VPS
curl http://localhost:8080/api/license/check

# Test dari luar (jika firewall allow)
curl http://147.93.156.165:8080/api/license/check

# Cek firewall
sudo ufw status
```

### Import Error di License API

```bash
cd /root/cryptomentor-bot/license_server
pip3 install -r requirements.txt --force-reinstall
sudo systemctl restart license-api
```

---

## Summary

✅ License test sudah dibuat untuk UID 1234500014
✅ Monthly fee: $10 (bukan $100)
✅ Status: inactive → akan jadi active setelah deposit + billing
✅ Setelah aktivasi: Balance $40, expires 30 hari

Credentials untuk teman kamu:
```
WL_ID=<REDACTED_UUID>
WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>
LICENSE_API_URL=http://147.93.156.165:8080
DEPOSIT_ADDRESS=0xff680baa2BaaD50f3756efF778eF673d0fd8cAF9
```

Flow setelah aktivasi:
1. Hari ini: Status `active`, balance $40, bot jalan normal
2. Setelah 30 hari: Billing cron jalan, karena saldo $40 > $10 → perpanjang 30 hari lagi
3. Setelah 60 hari: Billing cron jalan, karena saldo $30 > $10 → perpanjang 30 hari lagi
4. Setelah 90 hari: Billing cron jalan, karena saldo $20 > $10 → perpanjang 30 hari lagi
5. Setelah 120 hari: Billing cron jalan, karena saldo $10 = $10 → perpanjang 30 hari lagi, balance jadi $0
6. Setelah 150 hari: Billing cron jalan, karena saldo $0 < $10 → status jadi `grace_period`
7. 3 hari kemudian: Kalau masih belum bayar → status jadi `suspended`, bot mati saldo 0.
