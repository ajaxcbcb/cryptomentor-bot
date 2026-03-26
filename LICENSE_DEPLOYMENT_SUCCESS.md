# ✅ License Deployment Success

## Deployment Summary

**Date:** 2026-03-26  
**VPS:** 147.93.156.165  
**Status:** ✅ SUCCESS

---

## License Info

```
WL_ID           : 64ff0e58-4fd7-4800-b79f-a38915df7480
SECRET_KEY      : 0cdfc39e-d17c-46c2-a143-27ec4258c5ff
DEPOSIT_ADDRESS : 0xff680baa2BaaD50f3756efF778eF673d0fd8cAF9
ADMIN_TELEGRAM_ID: 7675185179
```

**Status:** active  
**Balance:** $40 USD  
**Monthly Fee:** $10 USD  
**Expires:** 2026-04-25 (30 days)

---

## Bot Configuration

**Bot ID:** 8744237679  
**Service:** whitelabel-1.service  
**Location:** /root/cryptomentor-bot/whitelabel-1  
**Status:** ✅ Running

**License Check Result:**
```
[LicenseGuard] License valid — status: active
```

---

## Billing Flow

| Month | Action | Balance | Status | Expires |
|-------|--------|---------|--------|---------|
| 0 (Now) | Deposit $50 | $50 | - | - |
| 1 | First billing -$10 | $40 | active | +30 days |
| 2 | Auto-renew -$10 | $30 | active | +30 days |
| 3 | Auto-renew -$10 | $20 | active | +30 days |
| 4 | Auto-renew -$10 | $10 | active | +30 days |
| 5 | Auto-renew -$10 | $0 | active | +30 days |
| 6 | Billing failed | $0 | grace_period | +3 days |
| 6+3 days | Still no payment | $0 | suspended | - |

**Grace Period:** 3 days  
**Auto-suspend:** After 3 days in grace_period

---

## Credentials untuk Teman (UID: 7675185179)

Kasih credentials ini ke teman kamu untuk diisi di bot WL-nya:

```env
WL_ID=64ff0e58-4fd7-4800-b79f-a38915df7480
WL_SECRET_KEY=0cdfc39e-d17c-46c2-a143-27ec4258c5ff
LICENSE_API_URL=http://147.93.156.165:8080
```

**Deposit Address (untuk top-up):**
```
0xff680baa2BaaD50f3756efF778eF673d0fd8cAF9
```
Network: BSC (Binance Smart Chain)  
Token: USDT

---

## Services Running

### 1. License API
```bash
systemctl status license-api
```
- Port: 8080
- Status: ✅ Running
- Location: /root/cryptomentor-bot/license_server

### 2. Whitelabel Bot #1
```bash
systemctl status whitelabel-1
```
- Bot ID: 8744237679
- Status: ✅ Running
- License: ✅ Valid (active)
- Location: /root/cryptomentor-bot/whitelabel-1

---

## Testing

### Test License API
```bash
ssh root@147.93.156.165
python3 << 'EOF'
import requests
import json

url = 'http://localhost:8080/api/license/check'
data = {
    'wl_id': '64ff0e58-4fd7-4800-b79f-a38915df7480',
    'secret_key': '0cdfc39e-d17c-46c2-a143-27ec4258c5ff'
}

response = requests.post(url, json=data)
print('Status:', response.status_code)
print(json.dumps(response.json(), indent=2))
EOF
```

Expected output:
```json
{
  "valid": true,
  "expires_in_days": 29,
  "balance": 40.0,
  "warning": false,
  "status": "active"
}
```

### Test Bot in Telegram
1. Open Telegram
2. Search bot: `@[bot_username]` (Bot ID: 8744237679)
3. Send `/start`
4. Bot should respond immediately

---

## Monitoring Commands

### Check License Status
```bash
ssh root@147.93.156.165
cd /root/cryptomentor-bot/license_server
venv/bin/python3 << 'EOF'
import asyncio
from license_manager import LicenseManager

async def main():
    manager = LicenseManager()
    license_row = await manager.get_license('64ff0e58-4fd7-4800-b79f-a38915df7480')
    
    print('License Status:')
    print('  Status:', license_row['status'])
    print('  Balance:', license_row['balance_usdt'], 'USD')
    print('  Expires:', license_row['expires_at'])
    print('  Monthly Fee:', license_row['monthly_fee'], 'USD')

asyncio.run(main())
EOF
```

### Check Bot Logs
```bash
# Real-time logs
journalctl -u whitelabel-1 -f

# Last 50 lines
journalctl -u whitelabel-1 -n 50

# Filter license-related logs
journalctl -u whitelabel-1 -n 100 | grep License
```

### Check License API Logs
```bash
journalctl -u license-api -n 50
```

### Restart Services
```bash
# Restart bot
systemctl restart whitelabel-1

# Restart License API
systemctl restart license-api

# Check status
systemctl status whitelabel-1 license-api
```

---

## Manual Billing Test

Untuk test billing cycle sekarang (tanpa nunggu cron):

```bash
ssh root@147.93.156.165
cd /root/cryptomentor-bot/license_server
venv/bin/python3 << 'EOF'
import asyncio
from license_manager import LicenseManager

async def main():
    manager = LicenseManager()
    result = await manager.debit_billing('64ff0e58-4fd7-4800-b79f-a38915df7480')
    
    print('Billing Result:')
    print('  Success:', result['success'])
    print('  Balance Before:', result['balance_before'])
    print('  Balance After:', result['balance_after'])
    print('  New Status:', result['new_status'])
    print('  Expires At:', result['expires_at'])

asyncio.run(main())
EOF
```

---

## Troubleshooting

### Bot Not Starting
```bash
# Check logs
journalctl -u whitelabel-1 -n 100

# Check .env
cat /root/cryptomentor-bot/whitelabel-1/.env | grep -E '(WL_ID|LICENSE)'

# Restart
systemctl restart whitelabel-1
```

### License Check Failed
```bash
# Test License API
curl -X POST http://localhost:8080/api/license/check \
  -H "Content-Type: application/json" \
  -d '{"wl_id":"64ff0e58-4fd7-4800-b79f-a38915df7480","secret_key":"0cdfc39e-d17c-46c2-a143-27ec4258c5ff"}'

# Check License API status
systemctl status license-api

# Restart License API
systemctl restart license-api
```

### License Expired
```bash
# Add deposit
cd /root/cryptomentor-bot/license_server
venv/bin/python3 << 'EOF'
import asyncio
from license_manager import LicenseManager

async def main():
    manager = LicenseManager()
    success = await manager.credit_balance(
        wl_id='64ff0e58-4fd7-4800-b79f-a38915df7480',
        amount=20.0,
        tx_hash='0xTOP_UP_' + str(int(time.time())),
        block_number=99999999
    )
    print('Deposit success:', success)

asyncio.run(main())
EOF

# Run billing
cd /root/cryptomentor-bot/license_server
venv/bin/python3 -c "import asyncio; from license_manager import LicenseManager; asyncio.run(LicenseManager().debit_billing('64ff0e58-4fd7-4800-b79f-a38915df7480'))"
```

---

## Next Steps

1. ✅ License deployed and activated
2. ✅ Bot configured with new license
3. ✅ Bot running and license valid
4. 🔄 Test bot in Telegram
5. 🔄 Monitor logs for any issues
6. 🔄 Setup billing cron (optional, for auto-billing)
7. 🔄 Setup deposit monitor (optional, for auto-deposit detection)

---

## Important Notes

- License expires in 30 days (2026-04-25)
- Current balance: $40 (enough for 4 more months)
- Grace period: 3 days after balance runs out
- Auto-suspend: After 3 days in grace period
- Billing cron runs daily at 00:00 UTC

---

## Contact Info

**Admin Telegram ID:** 7675185179  
**VPS IP:** 147.93.156.165  
**License API:** http://147.93.156.165:8080

---

**Deployment completed successfully! 🎉**
