# VPS Cache Cleanup & Community Button Investigation

## Issue Report
User melaporkan tombol Community Partners masih tidak muncul setelah deployment fix.

## Root Cause Analysis

### Problem 1: Python Cache (__pycache__)
**Ditemukan:** Python menyimpan compiled bytecode (.pyc files) di folder `__pycache__`

**Impact:** 
- Code baru sudah di-upload ke VPS
- Tapi Python masih load versi lama dari cache
- Service restart tidak otomatis clear cache

**Lokasi Cache:**
```
/root/cryptomentor-bot/app/providers/__pycache__/
/root/cryptomentor-bot/app/lib/__pycache__/
```

### Problem 2: Demo User Blocking
**Ditemukan:** User 1234500002 adalah DEMO USER

**Logic:**
```python
# From demo_users.py
DEMO_USER_IDS = {1234500001, 1234500002, 1234500003, 1234500004, 1234500005}

# From handlers_community.py
if is_demo_user(user_id):
    # Block access to Community Partners
    return "Access Denied"
```

**Reason:** Demo users are intentionally blocked from Community Partners feature for security.

## Solution Implemented

### Step 1: Clear Python Cache
```bash
cd /root/cryptomentor-bot
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name '*.pyc' -delete 2>/dev/null
```

**Result:** ✅ All cache cleared

### Step 2: Restart Service
```bash
systemctl restart cryptomentor
```

**Result:** ✅ Service restarted with PID 96647 (new process)

### Step 3: Verify Code Deployed
```bash
grep 'show_community = uid_status in' /root/cryptomentor-bot/app/handlers_autotrade.py
```

**Result:** ✅ All 3 occurrences confirmed:
```python
show_community = uid_status in ["uid_verified", "active", "stopped"]
```

## Button Visibility Test Results

### Regular Users (Non-Demo)
| User ID | Status | Button Visible? |
|---------|--------|----------------|
| 1234500008 | stopped | ✅ YES |
| 1234500018 | active | ✅ YES |
| 1234500011 | active | ✅ YES |
| 6954315669 | active | ✅ YES |
| 1265990951 | uid_verified | ✅ YES |

### Demo Users (Blocked)
| User ID | Status | Button Visible? | Reason |
|---------|--------|----------------|--------|
| 1234500002 | stopped | ❌ NO | Demo user blocked |

### Users Without Access
| User ID | Status | Button Visible? | Reason |
|---------|--------|----------------|--------|
| 999999999 | inactive | ❌ NO | Status not verified |
| 899183408 | uid_rejected | ❌ NO | UID rejected |

## Button Visibility Logic (Final)

```python
# Step 1: Check if demo user
if is_demo_user(user_id):
    return False  # Block demo users

# Step 2: Check session exists
session = get_autotrade_session(user_id)
if not session:
    return False  # No session

# Step 3: Check status
uid_status = session.get("status", "")
show_community = uid_status in ["uid_verified", "active", "stopped"]

return show_community
```

## Why Demo Users Are Blocked

**Security Reasons:**
1. Demo accounts are for testing only
2. Community Partners involves real user referrals
3. Demo users have $50 balance cap
4. Prevents abuse of community features
5. Maintains integrity of partner program

**Demo User List:**
- 1234500001
- 1234500002 ← User yang melaporkan issue
- 1234500003
- 1234500004
- 1234500005

## Verification Commands

### Check if user is demo:
```python
from app.demo_users import is_demo_user
is_demo_user(1234500002)  # Returns True
```

### Check user session:
```python
from app.handlers_autotrade import get_autotrade_session
session = get_autotrade_session(1234500002)
print(session.get("status"))  # Returns "stopped"
```

### Test button visibility:
```python
python test_community_button_visibility.py
```

## Deployment Best Practices (Learned)

### Always Clear Cache After Code Update
```bash
# 1. Upload new code
scp file.py root@vps:/path/

# 2. Clear Python cache
ssh root@vps "cd /path && find . -name '*.pyc' -delete && find . -type d -name __pycache__ -exec rm -rf {} +"

# 3. Restart service
ssh root@vps "systemctl restart service"
```

### Why Cache Causes Issues
- Python compiles .py files to .pyc for faster loading
- .pyc files stored in __pycache__ directories
- Service restart doesn't auto-clear cache
- Old .pyc files can persist even after .py update
- Result: New code uploaded but old code still runs

### Prevention Strategy
Add to deployment script:
```bash
#!/bin/bash
# deploy.sh

# Upload files
scp -r app/ root@vps:/root/bot/

# Clear cache (CRITICAL STEP)
ssh root@vps "cd /root/bot && find . -name '*.pyc' -delete && find . -type d -name __pycache__ -exec rm -rf {} +"

# Restart service
ssh root@vps "systemctl restart bot"

# Verify
ssh root@vps "systemctl status bot"
```

## Solution for User

### If You Are Using Demo Account (1234500002)
**Option 1: Use Real Account**
- Create new Telegram account
- Register with real Bitunix account
- Complete UID verification
- Access all features including Community Partners

**Option 2: Request Demo User Removal**
- Contact admin to remove from demo user list
- Complete real UID verification
- Gain full access to all features

### If You Are Using Real Account
**Verify your status:**
```bash
# Check your user ID in bot
/start

# Check if button appears
/autotrade → Should see "👥 Community Partners" button
```

**If button still not visible:**
1. Check your status: Must be "uid_verified", "active", or "stopped"
2. Not "pending_verification", "inactive", or "uid_rejected"
3. Contact admin if status is incorrect

## Files Created

### Analysis Scripts
- `check_community_button_issue.py` - Analyze button visibility
- `check_user_community_access.py` - Check user access
- `test_community_button_visibility.py` - Test visibility logic

### Documentation
- `COMMUNITY_PARTNERS_BUTTON_FIX.md` - Original fix documentation
- `COMMUNITY_BUTTON_FIX_DEPLOYED.md` - Deployment report
- `VPS_CACHE_CLEANUP_COMPLETE.md` - This document

## Summary

✅ **Code Fix:** Successfully deployed (3 locations updated)  
✅ **Cache Cleared:** All __pycache__ and .pyc files removed  
✅ **Service Restarted:** Running with new code (PID 96647)  
✅ **Logic Verified:** Button shows for verified users  
❌ **Demo User Block:** User 1234500002 is demo user (intentional block)

**For Regular Users:** Button now works correctly  
**For Demo Users:** Blocked by design for security

## Next Steps

1. **Confirm User Type:** Is user using demo account or real account?
2. **If Demo:** Explain why blocked and offer alternatives
3. **If Real:** Investigate why user thinks button is missing
4. **Update Deployment Process:** Always clear cache after code updates

---

**Investigation completed:** April 4, 2026, 10:04 CEST  
**Cache cleared:** ✅  
**Service restarted:** ✅  
**Code verified:** ✅  
**Root cause identified:** Demo user blocking (by design)
