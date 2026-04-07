# License Middleware Implementation

## Overview

Implemented runtime license checking middleware that blocks all user access when the admin's license is suspended.

## Problem Solved

Previously, the bot only checked license at startup. If the license was suspended while the bot was running, users could still interact with the bot until it was restarted.

## Solution

Added a middleware layer that checks license status before processing any user update.

## Implementation Details

### 1. New Method in LicenseGuard (`license_guard.py`)

```python
async def check_license_valid(self) -> bool:
    """
    Check apakah license valid saat ini (untuk middleware).
    Returns True jika valid, False jika suspended/invalid.
    Tidak mengirim notifikasi (sudah dikirim di startup_check).
    """
```

This method:
- Checks license via API with cache fallback
- Returns boolean (True = valid, False = suspended)
- Does NOT send notifications (to avoid spam)
- Uses same cache logic as startup_check

### 2. License Middleware (`license_middleware.py`)

New middleware class that:
- Runs BEFORE all other handlers (group=-1)
- Checks license every 60 seconds (cached to reduce API calls)
- Blocks all user requests when license is suspended
- Allows admin access even when suspended (for troubleshooting)
- Sends user-friendly message to blocked users

### 3. Bot Integration (`bot.py`)

```python
from app.license_middleware import LicenseMiddleware
license_middleware = LicenseMiddleware(license_guard)
app.add_handler(license_middleware, group=-1)
```

Middleware is registered with `group=-1` to ensure it runs before all other handlers.

## Behavior

### When License is ACTIVE:
- ✅ All users can use the bot normally
- ✅ All commands work
- ✅ No blocking or restrictions

### When License is SUSPENDED:
- ❌ Regular users are BLOCKED
- ✅ Admins can still access (for troubleshooting)
- 📩 Users see: "🚫 Bot Temporarily Unavailable"
- 🔔 Admin receives notification (once) with deposit instructions

## Performance Optimization

- License check is cached for 60 seconds
- Reduces API calls from potentially hundreds per minute to 1 per minute
- Cache is shared across all user requests
- No performance impact on user experience

## Testing

Run the test script to verify implementation:

```bash
python test_license_middleware.py
```

This will:
1. Check current license status
2. Verify cache functionality
3. Test rapid checks (cache performance)
4. Show middleware behavior summary

## Admin Access

Admins (defined in `ADMIN_IDS` config) can always access the bot, even when suspended. This allows:
- Checking bot status
- Troubleshooting issues
- Verifying deposit/payment
- Restarting services if needed

## User Experience

When a user tries to use a suspended bot:

**For /start or any command:**
```
🚫 Bot Temporarily Unavailable

This bot is currently suspended due to license payment.

Please contact the bot administrator for more information.
```

**For callback buttons:**
```
⚠️ Bot suspended — contact admin
```

## Files Modified

1. `Whitelabel #1/app/license_guard.py` - Added `check_license_valid()` method
2. `Whitelabel #1/bot.py` - Registered middleware
3. `Whitelabel #1/app/license_middleware.py` - New middleware implementation

## Deployment

To deploy to VPS:

```bash
# SSH to VPS
ssh root@147.93.156.165

# Navigate to project
cd /root/CryptoMentor-Telegram-Bot

# Pull latest changes
git pull origin main

# Restart whitelabel bot
systemctl restart whitelabel-1

# Check status
systemctl status whitelabel-1

# View logs
journalctl -u whitelabel-1 -f
```

## Verification

After deployment, verify the middleware is working:

1. Check bot logs for middleware registration:
   ```
   License middleware registered — will block users if license suspended
   ```

2. Test with suspended license:
   - Set balance to $0 in database
   - Try to use bot as regular user → should be blocked
   - Try to use bot as admin → should work

3. Test with active license:
   - Restore balance
   - Try to use bot as regular user → should work

## Edge Cases Handled

1. **API Down**: Falls back to cache (48-hour grace period)
2. **Cache Expired + API Down**: Blocks users (safe default)
3. **Rapid Requests**: Uses 60-second cache to prevent API spam
4. **Admin Access**: Always allowed, even when suspended
5. **Channel Posts**: Skipped (no user to block)
6. **Development Mode**: Middleware disabled if LICENSE_API_URL not set

## Security

- Users cannot bypass the middleware
- Middleware runs at group=-1 (highest priority)
- All handlers are blocked when license invalid
- Admin access preserved for emergency troubleshooting

## Future Improvements

Potential enhancements:
1. Add grace period notification (e.g., "Bot will be suspended in 24 hours")
2. Show remaining balance to admin in bot status
3. Add webhook for instant license status updates (instead of polling)
4. Implement rate limiting per user to prevent abuse

## Summary

✅ Users are now completely blocked when admin hasn't paid
✅ Middleware checks license before every user request
✅ Performance optimized with 60-second cache
✅ Admin access preserved for troubleshooting
✅ User-friendly error messages
✅ No spam notifications
✅ Automatic reactivation when license restored
