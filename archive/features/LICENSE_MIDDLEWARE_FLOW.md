# License Middleware Flow Diagram

## Overview

This document shows how the license middleware blocks users when the admin hasn't paid.

## Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER SENDS MESSAGE                       │
│                      (e.g., /start, /autotrade)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT RECEIVES UPDATE                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LICENSE MIDDLEWARE (Group -1)                  │
│                    Runs BEFORE all handlers                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Is User Admin? │
                    └────────┬───────┘
                             │
                ┌────────────┴────────────┐
                │                         │
               YES                       NO
                │                         │
                ▼                         ▼
    ┌───────────────────┐    ┌──────────────────────┐
    │  ALLOW (Skip      │    │  Check License Cache │
    │  License Check)   │    │  (Updated every 60s) │
    └─────────┬─────────┘    └──────────┬───────────┘
              │                          │
              │              ┌───────────┴───────────┐
              │              │                       │
              │         License Valid          License Suspended
              │              │                       │
              │              ▼                       ▼
              │    ┌──────────────────┐   ┌──────────────────────┐
              │    │  ALLOW REQUEST   │   │   BLOCK REQUEST      │
              │    │  Continue to     │   │   Send Error Message │
              │    │  Handlers        │   │   Return None        │
              │    └────────┬─────────┘   └──────────────────────┘
              │             │
              └─────────────┴─────────────┐
                                          │
                                          ▼
                            ┌──────────────────────────┐
                            │   COMMAND HANDLERS       │
                            │   (cmd_start,            │
                            │    cmd_autotrade, etc)   │
                            └──────────┬───────────────┘
                                       │
                                       ▼
                            ┌──────────────────────────┐
                            │   RESPONSE TO USER       │
                            └──────────────────────────┘
```

## License Check Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    LICENSE MIDDLEWARE TRIGGERED                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────────┐
                    │  Check Cache Age   │
                    │  (Last check < 60s?)│
                    └────────┬───────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
              YES                        NO
                │                         │
                ▼                         ▼
    ┌───────────────────┐    ┌──────────────────────┐
    │  Use Cached       │    │  Call License API    │
    │  Result           │    │  check_license_valid()│
    └─────────┬─────────┘    └──────────┬───────────┘
              │                          │
              │              ┌───────────┴───────────┐
              │              │                       │
              │         API Success            API Failed
              │              │                       │
              │              ▼                       ▼
              │    ┌──────────────────┐   ┌──────────────────────┐
              │    │  Update Cache    │   │  Use Cache Fallback  │
              │    │  Return Result   │   │  (48h grace period)  │
              │    └────────┬─────────┘   └──────────┬───────────┘
              │             │                         │
              └─────────────┴─────────────────────────┘
                                          │
                                          ▼
                            ┌──────────────────────────┐
                            │   Return Valid/Invalid   │
                            └──────────────────────────┘
```

## User Experience Flow

### Scenario 1: License Active

```
User → /start
  ↓
Middleware: Check license (cached: valid ✅)
  ↓
Allow request
  ↓
cmd_start handler
  ↓
User sees: "👋 Welcome! ..."
```

### Scenario 2: License Suspended (Regular User)

```
User → /start
  ↓
Middleware: Check license (cached: suspended ❌)
  ↓
Block request
  ↓
Send error message
  ↓
User sees: "🚫 Bot Temporarily Unavailable..."
  ↓
Request stopped (handlers not called)
```

### Scenario 3: License Suspended (Admin)

```
Admin → /start
  ↓
Middleware: Is admin? YES ✅
  ↓
Skip license check
  ↓
Allow request
  ↓
cmd_start handler
  ↓
Admin sees: "👋 Welcome! ..." (works normally)
```

## Cache Update Flow

```
Time: 00:00 → User request → Check license → Cache updated → Valid ✅
Time: 00:30 → User request → Use cache (30s old) → Valid ✅
Time: 01:00 → User request → Use cache (60s old) → Valid ✅
Time: 01:01 → User request → Check license again → Cache updated
Time: 01:30 → User request → Use cache (29s old)
...
```

## Notification Flow

### First Suspension

```
License becomes suspended
  ↓
Admin tries to use bot
  ↓
startup_check() detects suspension
  ↓
Send notification to admin (ONCE)
  ↓
Save flag: license_notif_sent.json
  ↓
Admin receives:
  "🚫 Bot Suspended
   📥 Deposit to: 0xff680baa...
   Bot will auto-activate in 5-10 min"
```

### Subsequent Checks (No Spam)

```
License still suspended
  ↓
Periodic check runs
  ↓
Check notification flag
  ↓
Flag exists → Skip notification
  ↓
No spam to admin ✅
```

### Reactivation

```
Admin deposits $20
  ↓
Deposit monitor detects deposit
  ↓
Trigger billing
  ↓
License becomes active
  ↓
Clear notification flag
  ↓
Admin receives:
  "✅ License Activated!
   Balance: $10
   Expires: 2026-04-25"
```

## Performance Optimization

### Without Cache (Bad)

```
User 1 → /start → API call (200ms)
User 2 → /help → API call (200ms)
User 3 → /autotrade → API call (200ms)
...
100 users/min → 100 API calls → 20 seconds total
```

### With Cache (Good)

```
User 1 → /start → API call (200ms) → Cache updated
User 2 → /help → Use cache (<1ms)
User 3 → /autotrade → Use cache (<1ms)
...
100 users/min → 1 API call → 200ms total
```

## Security Flow

### Bypass Attempt (Fails)

```
Malicious user tries to bypass middleware
  ↓
Middleware runs at group=-1 (highest priority)
  ↓
Blocks request before ANY handler
  ↓
No way to reach handlers
  ↓
Bypass fails ❌
```

### Admin Emergency Access

```
License suspended + API down
  ↓
Admin needs to troubleshoot
  ↓
Middleware: Is admin? YES ✅
  ↓
Skip license check
  ↓
Admin can access bot
  ↓
Can check status, restart services, etc.
```

## Summary

The middleware provides:

✅ **Effective Blocking**: Users cannot access bot when suspended
✅ **Performance**: 60-second cache prevents API spam
✅ **Security**: No bypass possible (runs at highest priority)
✅ **Admin Access**: Preserved for troubleshooting
✅ **User-Friendly**: Clear error messages
✅ **No Spam**: Notifications sent only once
✅ **Auto-Reactivation**: Works automatically when license restored

The flow ensures that:
1. License is checked efficiently (cached)
2. Users are blocked immediately when suspended
3. Admin can always access for troubleshooting
4. Performance is not impacted
5. Security is maintained
