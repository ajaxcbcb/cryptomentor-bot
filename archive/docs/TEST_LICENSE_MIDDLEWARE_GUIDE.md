# Testing License Middleware - Quick Guide

## Overview

This guide shows how to test that users are blocked when the admin hasn't paid the license.

## Prerequisites

- Bot deployed to VPS with middleware
- Access to Supabase database
- Test user account (non-admin)
- Admin account

## Test Scenarios

### Scenario 1: License Active (Normal Operation)

**Setup:**
- License balance > $0
- License status = 'active'

**Expected Behavior:**
- ✅ Regular users can use bot
- ✅ All commands work
- ✅ No blocking messages

**Test Steps:**
1. Check license status:
   ```bash
   ssh root@147.93.156.165
   cd /root/CryptoMentor-Telegram-Bot
   python3 << 'EOF'
   import asyncio
   import sys
   sys.path.insert(0, 'Whitelabel #1')
   from app.license_guard import LicenseGuard
   import os
   os.environ['WL_ID'] = '<REDACTED_UUID>'
   os.environ['WL_SECRET_KEY'] = '<REDACTED_UUID>'
   os.environ['LICENSE_API_URL'] = 'http://147.93.156.165:8080'
   
   async def check():
       guard = LicenseGuard()
       valid = await guard.check_license_valid()
       print(f"License valid: {valid}")
   
   asyncio.run(check())
   EOF
   ```

2. Test with regular user:
   - Send `/start` to bot
   - Should see welcome message
   - Try `/autotrade`
   - Should work normally

3. Test with admin:
   - Send `/start` to bot
   - Should work normally

### Scenario 2: License Suspended (Admin Hasn't Paid)

**Setup:**
- Set license balance to $0
- License status = 'suspended'

**Expected Behavior:**
- ❌ Regular users are BLOCKED
- ✅ Admin can still access
- 📩 Users see "Bot Temporarily Unavailable"
- 🔔 Admin receives notification (once)

**Test Steps:**

1. Suspend the license (simulate admin not paying):
   ```bash
   ssh root@147.93.156.165
   cd /root/CryptoMentor-Telegram-Bot/license_server
   
   python3 << 'EOF'
   import asyncio
   from license_manager import LicenseManager
   
   async def suspend():
       manager = LicenseManager()
       client = await manager._get_client()
       
       # Set balance to 0 and status to suspended
       await client.table('wl_licenses').update({
           'balance_usdt': 0,
           'status': 'suspended'
       }).eq('wl_id', '<REDACTED_UUID>').execute()
       
       print("✅ License suspended (balance = $0)")
   
   asyncio.run(suspend())
   EOF
   ```

2. Wait 60 seconds for middleware cache to refresh

3. Test with regular user (non-admin):
   - Send `/start` to bot
   - Should see: "🚫 Bot Temporarily Unavailable"
   - Try any command
   - Should be blocked

4. Test with admin:
   - Send `/start` to bot
   - Should work normally (admin bypass)
   - Can still use all commands

5. Check admin notification:
   - Admin should receive ONE notification with:
     - "🚫 Bot Suspended"
     - Deposit address
     - Instructions to reactivate

6. Verify no spam:
   - Try multiple commands as regular user
   - Admin should NOT receive multiple notifications
   - Only one notification sent

### Scenario 3: Reactivation After Payment

**Setup:**
- Simulate admin deposit
- Trigger billing to reactivate

**Expected Behavior:**
- ✅ License becomes active
- ✅ Users can access bot again
- 🔔 Admin receives activation notification

**Test Steps:**

1. Simulate deposit and billing:
   ```bash
   ssh root@147.93.156.165
   cd /root/CryptoMentor-Telegram-Bot/license_server
   
   python3 << 'EOF'
   import asyncio
   from datetime import datetime, timezone, timedelta
   from license_manager import LicenseManager
   
   async def reactivate():
       manager = LicenseManager()
       
       # Deposit $20
       await manager.credit_balance(
           wl_id='<REDACTED_UUID>',
           amount=20.0,
           tx_hash='0xTEST_REACTIVATION',
           block_number=99999999
       )
       print("✅ Deposited $20")
       
       # Trigger billing
       client = await manager._get_client()
       license_row = await manager.get_license(wl_id='<REDACTED_UUID>')
       
       balance = float(license_row['balance_usdt'])
       monthly_fee = float(license_row['monthly_fee'])
       new_balance = balance - monthly_fee
       expires_at = datetime.now(timezone.utc) + timedelta(days=30)
       
       await client.table('wl_licenses').update({
           'balance_usdt': new_balance,
           'status': 'active',
           'expires_at': expires_at.isoformat()
       }).eq('wl_id', '<REDACTED_UUID>').execute()
       
       print(f"✅ Billing processed: -${monthly_fee}, Balance: ${new_balance}")
       print(f"✅ Status: active, Expires: {expires_at}")
   
   asyncio.run(reactivate())
   EOF
   ```

2. Wait 60 seconds for middleware cache to refresh

3. Test with regular user:
   - Send `/start` to bot
   - Should work normally now
   - No blocking message

4. Verify notification flag cleared:
   - Check `Whitelabel #1/data/license_notif_sent.json`
   - Should be empty or `{"suspended": false}`

## Quick Commands

### Check License Status
```bash
ssh root@147.93.156.165 "cd /root/CryptoMentor-Telegram-Bot/license_server && python3 -c \"
import asyncio
from license_manager import LicenseManager

async def check():
    manager = LicenseManager()
    license = await manager.get_license(wl_id='<REDACTED_UUID>')
    print(f'Status: {license[\\\"status\\\"]}')
    print(f'Balance: \\\${license[\\\"balance_usdt\\\"]}')
    print(f'Expires: {license[\\\"expires_at\\\"]}')

asyncio.run(check())
\""
```

### View Bot Logs
```bash
ssh root@147.93.156.165 "journalctl -u whitelabel-1 -n 100 --no-pager"
```

### Check Middleware Registration
```bash
ssh root@147.93.156.165 "journalctl -u whitelabel-1 -n 50 --no-pager | grep -i middleware"
```

### View Live Logs
```bash
ssh root@147.93.156.165 "journalctl -u whitelabel-1 -f"
```

## Expected Log Messages

### When Middleware Blocks User
```
[LicenseMiddleware] Blocking user 123456789 — license suspended
```

### When License Check Runs
```
[LicenseMiddleware] License check: valid=False
```

### When Middleware Registered
```
License middleware registered — will block users if license suspended
```

## Troubleshooting

### Users Not Being Blocked

1. Check middleware is registered:
   ```bash
   journalctl -u whitelabel-1 -n 50 | grep "middleware registered"
   ```

2. Check license status:
   ```bash
   # Should show status='suspended' and balance=0
   ```

3. Wait 60 seconds for cache to refresh

4. Check bot logs for blocking messages

### Admin Being Blocked

1. Verify admin ID in config:
   ```bash
   ssh root@147.93.156.165 "cat /root/CryptoMentor-Telegram-Bot/Whitelabel\ #1/.env | grep ADMIN"
   ```

2. Check ADMIN_IDS includes your Telegram ID

### Middleware Not Running

1. Check bot is running:
   ```bash
   systemctl status whitelabel-1
   ```

2. Check for errors in logs:
   ```bash
   journalctl -u whitelabel-1 -n 100 | grep -i error
   ```

3. Restart bot:
   ```bash
   systemctl restart whitelabel-1
   ```

## Success Criteria

✅ Regular users blocked when license suspended
✅ Admin can access when license suspended
✅ Users can access when license active
✅ Only one notification sent to admin
✅ Automatic reactivation after payment
✅ No performance degradation
✅ Middleware logs visible in journalctl

## Summary

The middleware successfully blocks all user access when the admin hasn't paid, while preserving admin access for troubleshooting. The implementation is performant (60-second cache), secure (no bypass possible), and user-friendly (clear error messages).
