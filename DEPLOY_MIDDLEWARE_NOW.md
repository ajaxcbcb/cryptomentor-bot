# Deploy License Middleware - Quick Start

## What This Does

Blocks all user access to the bot when the admin hasn't paid the license fee.

## Quick Deploy (3 Steps)

### Step 1: Run Deployment Script

```bash
bash deploy_license_middleware.sh
```

This will:
- Commit changes to GitHub
- SSH to VPS and pull changes
- Restart the bot
- Show status

### Step 2: Verify Deployment

Check that middleware is registered:

```bash
ssh root@147.93.156.165 "journalctl -u whitelabel-1 -n 50 | grep middleware"
```

Expected output:
```
License middleware registered — will block users if license suspended
```

### Step 3: Test It Works

**Test with active license (current state):**
1. Send `/start` to bot as regular user
2. Should work normally ✅

**Test with suspended license:**
1. Suspend license (set balance to $0):
   ```bash
   ssh root@147.93.156.165 << 'EOF'
   cd /root/CryptoMentor-Telegram-Bot/license_server
   python3 -c "
   import asyncio
   from license_manager import LicenseManager
   
   async def suspend():
       manager = LicenseManager()
       client = await manager._get_client()
       await client.table('wl_licenses').update({
           'balance_usdt': 0,
           'status': 'suspended'
       }).eq('wl_id', '<REDACTED_UUID>').execute()
       print('✅ License suspended')
   
   asyncio.run(suspend())
   "
   EOF
   ```

2. Wait 60 seconds for cache to refresh

3. Send `/start` to bot as regular user
4. Should see: "🚫 Bot Temporarily Unavailable" ✅

4. Send `/start` as admin
5. Should work normally ✅

**Restore license:**
```bash
ssh root@147.93.156.165 << 'EOF'
cd /root/CryptoMentor-Telegram-Bot/license_server
python3 -c "
import asyncio
from datetime import datetime, timezone, timedelta
from license_manager import LicenseManager

async def restore():
    manager = LicenseManager()
    client = await manager._get_client()
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    await client.table('wl_licenses').update({
        'balance_usdt': 10.0,
        'status': 'active',
        'expires_at': expires_at.isoformat()
    }).eq('wl_id', '<REDACTED_UUID>').execute()
    print('✅ License restored')

asyncio.run(restore())
"
EOF
```

## What Happens Now

### When License is Active:
- ✅ Users can use bot normally
- ✅ All commands work
- ✅ No blocking

### When License is Suspended:
- ❌ Users are blocked
- ✅ Admin can still access
- 📩 Users see "Bot Temporarily Unavailable"
- 🔔 Admin gets notification with deposit address

### When Admin Pays:
- ✅ Bot automatically reactivates
- ✅ Users can access again
- 🔔 Admin gets activation notification

## Monitoring

View live logs:
```bash
ssh root@147.93.156.165 "journalctl -u whitelabel-1 -f"
```

Check license status:
```bash
ssh root@147.93.156.165 "cd /root/CryptoMentor-Telegram-Bot/license_server && python3 -c \"
import asyncio
from license_manager import LicenseManager

async def check():
    manager = LicenseManager()
    license = await manager.get_license(wl_id='<REDACTED_UUID>')
    print(f'Status: {license[\\\"status\\\"]}')
    print(f'Balance: \\\${license[\\\"balance_usdt\\\"]}')

asyncio.run(check())
\""
```

## Troubleshooting

### Users Not Being Blocked

1. Check middleware is registered:
   ```bash
   ssh root@147.93.156.165 "journalctl -u whitelabel-1 -n 50 | grep middleware"
   ```

2. Wait 60 seconds for cache to refresh

3. Check license status is actually 'suspended'

### Bot Not Starting

1. Check logs for errors:
   ```bash
   ssh root@147.93.156.165 "journalctl -u whitelabel-1 -n 100"
   ```

2. Restart bot:
   ```bash
   ssh root@147.93.156.165 "systemctl restart whitelabel-1"
   ```

## Documentation

- **Technical Details**: `LICENSE_MIDDLEWARE_IMPLEMENTATION.md`
- **Testing Guide**: `TEST_LICENSE_MIDDLEWARE_GUIDE.md`
- **Summary**: `LICENSE_MIDDLEWARE_SUMMARY.md`

## Support

If you encounter issues:
1. Check the logs: `journalctl -u whitelabel-1 -n 100`
2. Verify license status in database
3. Restart the bot: `systemctl restart whitelabel-1`
4. Check middleware is registered in logs

## Success!

Once deployed, your whitelabel bot will:
- ✅ Block users when you haven't paid
- ✅ Allow admin access for troubleshooting
- ✅ Automatically reactivate when you pay
- ✅ Send clear notifications
- ✅ Perform efficiently with caching

The license system is now fully enforced at runtime!
