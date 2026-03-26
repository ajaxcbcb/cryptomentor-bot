# Deploy License System ke VPS - Quick Start

## 📋 Files yang Sudah Dibuat

1. **DEPLOY_LICENSE_TEST_TO_VPS.md** - Panduan lengkap step-by-step manual
2. **VPS_COMMANDS_TEST_LICENSE.txt** - Command siap copy-paste untuk VPS
3. **activate_test_license.py** - Script Python untuk aktivasi license
4. **deploy_test_license.sh** - Script bash otomatis (belum final)

## 🎯 License Test Info

```
WL_ID           : <REDACTED_UUID>
SECRET_KEY      : <REDACTED_UUID>
DEPOSIT_ADDRESS : 0xff680baa2BaaD50f3756efF778eF673d0fd8cAF9
ADMIN_TELEGRAM_ID: 1234500014
MONTHLY_FEE     : $10
```

## 🚀 Quick Deploy (Recommended)

### 1. Push Code ke GitHub

```bash
git add .
git commit -m "Add test license system for UID 1234500014"
git push origin main
```

### 2. SSH ke VPS

```bash
ssh root@147.93.156.165
```

### 3. Pull Latest Code

```bash
cd /root/cryptomentor-bot
git pull origin main
```

### 4. Activate License

Copy-paste command ini ke VPS (dari file `VPS_COMMANDS_TEST_LICENSE.txt`):

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
    
    # Deposit $50
    await manager.credit_balance(
        wl_id=WL_ID,
        amount=50.0,
        tx_hash="0xVPS_DEPLOY_FINAL",
        block_number=99999999
    )
    
    # Billing
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
    
    print(f"✅ Status: active, Balance: ${new_balance}, Expires: {expires_at.isoformat()}")

asyncio.run(main())
EOF
```

### 5. Test License API

```bash
curl -X POST http://localhost:8080/api/license/check \
  -H "Content-Type: application/json" \
  -d '{"wl_id":"<REDACTED_UUID>","secret_key":"<REDACTED_WL_SECRET_KEY>"}' | python3 -m json.tool
```

Expected:
```json
{
  "valid": true,
  "expires_in_days": 29,
  "balance": 40.0,
  "warning": false,
  "status": "active"
}
```

### 6. Kasih Credentials ke Teman

```
WL_ID=<REDACTED_UUID>
WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>
LICENSE_API_URL=http://147.93.156.165:8080
```

Teman kamu isi ke `.env` bot WL-nya, lalu restart bot.

## 📚 Dokumentasi Lengkap

- **DEPLOY_LICENSE_TEST_TO_VPS.md** - Panduan lengkap dengan troubleshooting
- **VPS_COMMANDS_TEST_LICENSE.txt** - Semua command siap pakai

## ✅ Checklist

- [ ] Push code ke GitHub
- [ ] SSH ke VPS
- [ ] Pull latest code
- [ ] Activate license (deposit + billing)
- [ ] Test License API
- [ ] Kasih credentials ke teman
- [ ] Teman update .env bot WL
- [ ] Teman restart bot
- [ ] Test /start di Telegram

## 🔄 Billing Flow

Dengan deposit $50 dan fee $10/bulan:

- Bulan 1-5: Auto-renew setiap bulan (balance: $40 → $30 → $20 → $10 → $0)
- Bulan 6: Balance $0, status → `grace_period` (bot masih jalan)
- Bulan 6 + 3 hari: Kalau belum top-up → status `suspended` (bot mati)

## 🆘 Troubleshooting

Lihat file **DEPLOY_LICENSE_TEST_TO_VPS.md** bagian Troubleshooting.

Quick checks:
```bash
# Check License API
sudo systemctl status license-api

# Check bot
sudo systemctl status whitelabel1

# View logs
sudo journalctl -u license-api -n 50
sudo journalctl -u whitelabel1 -n 50
```

## 📞 Support Commands

```bash
# Test billing manually
python3 -c "import asyncio; from license_server.billing_cron import run_billing_cycle; asyncio.run(run_billing_cycle())"

# Check license in DB
python3 << 'EOF'
import asyncio
from license_server.license_manager import LicenseManager

async def main():
    manager = LicenseManager()
    license_row = await manager.get_license("<REDACTED_UUID>")
    print(f"Status: {license_row['status']}")
    print(f"Balance: ${license_row['balance_usdt']}")
    print(f"Expires: {license_row['expires_at']}")

asyncio.run(main())
EOF
```

---

**VPS:** 147.93.156.165  
**User:** root  
**License API Port:** 8080
