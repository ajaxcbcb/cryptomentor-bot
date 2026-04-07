# Deploy License System to VPS - Manual Steps

## Prerequisites
- SSH ke VPS: `ssh root@147.93.156.165`
- License API sudah running di VPS
- Supabase credentials sudah benar di license_server/.env

---

## Step 1: Register WL di VPS

```bash
cd /root/cryptomentor-bot/license_server
source venv/bin/activate

python << 'EOF'
import asyncio
from license_manager import LicenseManager

async def main():
    result = await LicenseManager().register_wl(
        admin_telegram_id=1234500009,
        monthly_fee=10.0
    )
    print(f"WL_ID={result['wl_id']}")
    print(f"WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>
    print(f"DEPOSIT_ADDRESS={result['deposit_address']}")

asyncio.run(main())
EOF
```

**Copy WL_ID dan WL_SECRET_KEY dari output!**

---

## Step 2: Activate License (Deposit + Billing)

Ganti `YOUR_WL_ID` dengan WL_ID dari Step 1:

```bash
python << 'EOF'
import asyncio
from datetime import datetime, timezone, timedelta
from license_manager import LicenseManager

WL_ID = "YOUR_WL_ID"  # <-- GANTI INI

async def main():
    manager = LicenseManager()
    
    # Deposit $50
    await manager.credit_balance(
        wl_id=WL_ID,
        amount=50.0,
        tx_hash="0xVPS_DEPLOY_FINAL",
        block_number=99999999
    )
    print("✅ Deposit: $50")
    
    # Billing
    client = await manager._get_client()
    license_row = await manager.get_license(wl_id=WL_ID)
    balance = float(license_row['balance_usdt'])
    monthly_fee = float(license_row['monthly_fee'])
    
    new_balance = balance - monthly_fee
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    
    await client.table('wl_licenses').update({
        'balance_usdt': new_balance,
        'status': 'active',
        'expires_at': expires_at.isoformat()
    }).eq('wl_id', WL_ID).execute()
    
    print(f"✅ Billing: -${monthly_fee}, Balance: ${new_balance}")
    print(f"✅ Status: active, Expires: {expires_at}")

asyncio.run(main())
EOF
```

---

## Step 3: Update Whitelabel-1 .env

```bash
cd /root/cryptomentor-bot/whitelabel-1
nano .env
```

Update baris berikut dengan credentials dari Step 1:
```
WL_ID=YOUR_WL_ID
WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY>
LICENSE_API_URL=http://147.93.156.165:8080
```

Save: `Ctrl+X`, `Y`, `Enter`

---

## Step 4: Restart Bot

```bash
sudo systemctl restart whitelabel1
sleep 5
sudo systemctl status whitelabel1
```

---

## Step 5: Check Logs

```bash
sudo journalctl -u whitelabel1 -n 30 --no-pager | grep -E "(License|Started|ERROR)"
```

**Look for:** `[LicenseGuard] License valid — status: active`

---

## Step 6: Test Bot in Telegram

1. Open Telegram
2. Find bot: @YourWhitelabelBot
3. Send `/start`
4. Bot should respond immediately

---

## Troubleshooting

### If license check fails:

```bash
# Test license API manually
curl -X POST http://localhost:8080/api/license/check \
  -H "Content-Type: application/json" \
  -d '{"wl_id":"YOUR_WL_ID","secret_key":"<REDACTED_WL_SECRET_KEY>"}'
```

Should return:
```json
{"valid":true,"expires_in_days":29,"balance":40.0,"warning":false,"status":"active"}
```

### If bot not responding:

```bash
# Check bot logs
sudo journalctl -u whitelabel1 -f

# Restart bot
sudo systemctl restart whitelabel1
```

---

## Summary

✅ License system deployed and working!

**Credentials:**
- WL_ID: (from Step 1)
- SECRET_KEY: (from Step 1)
- Status: active
- Balance: $40
- Expires: 30 days from now

Bot is now running with license validation!
