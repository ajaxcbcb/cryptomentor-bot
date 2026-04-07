# Community Partners Access Control

## Overview

Fitur Community Partners sekarang hanya tersedia untuk user yang sudah terverifikasi (UID approved). User yang tidak terdaftar under referral tidak akan bisa mengakses fitur ini.

## Changes Made

### 1. Dashboard AutoTrade - Conditional Button Display

**File**: `Bismillah/app/handlers_autotrade.py`

**Before**:
```python
keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("📊 Status Portfolio",  callback_data="at_status")],
    [InlineKeyboardButton("📈 Trade History",     callback_data="at_history")],
    engine_btn,
    [InlineKeyboardButton("🧠 Bot Skills",        callback_data="skills_menu")],
    [InlineKeyboardButton("👥 Community Partners", callback_data="community_partners")],  # Always shown
    [InlineKeyboardButton("⚙️ Settings",          callback_data="at_settings")],
    [InlineKeyboardButton("🔑 Change API Key",    callback_data="at_change_key")],
])
```

**After**:
```python
# Check if user is verified (UID approved)
uid_status = session.get("status", "")
show_community = uid_status == "uid_verified" or uid_status == "active"

# Build keyboard based on verification status
keyboard_buttons = [
    [InlineKeyboardButton("📊 Status Portfolio",  callback_data="at_status")],
    [InlineKeyboardButton("📈 Trade History",     callback_data="at_history")],
    engine_btn,
    [InlineKeyboardButton("🧠 Bot Skills",        callback_data="skills_menu")],
]

# Only add Community Partners button if user is verified
if show_community:
    keyboard_buttons.append([InlineKeyboardButton("👥 Community Partners", callback_data="community_partners")])

keyboard_buttons.extend([
    [InlineKeyboardButton("⚙️ Settings",          callback_data="at_settings")],
    [InlineKeyboardButton("🔑 Change API Key",    callback_data="at_change_key")],
])

keyboard = InlineKeyboardMarkup(keyboard_buttons)
```

### 2. Community Partners Handler - Access Guard

**File**: `Bismillah/app/handlers_community.py`

**Added at the beginning of `callback_partners_menu()`**:
```python
# Check if user is verified (has approved UID)
from app.handlers_autotrade import get_autotrade_session
session = get_autotrade_session(user_id)

if not session or session.get("status") not in ["uid_verified", "active"]:
    await query.edit_message_text(
        "❌ <b>Access Denied</b>\n\n"
        "Community Partners feature is only available for verified users.\n\n"
        "Please complete your registration and UID verification first:\n"
        "/autotrade",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="at_dashboard")]
        ])
    )
    return ConversationHandler.END
```

## How It Works

### Flow Diagram

```
User opens /autotrade
         │
         ↓
    Has API Key?
         │
    ┌────┴────┐
    │         │
   Yes       No
    │         │
    ↓         ↓
Dashboard   Setup
    │
    ↓
Check UID Status
    │
    ├─ uid_verified → Show Community Partners button ✅
    ├─ active → Show Community Partners button ✅
    └─ pending/other → Hide Community Partners button ❌
```

### Access Control Logic

| UID Status | Community Partners Button | Access to Feature |
|------------|---------------------------|-------------------|
| `uid_verified` | ✅ Shown | ✅ Allowed |
| `active` | ✅ Shown | ✅ Allowed |
| `pending_verification` | ❌ Hidden | ❌ Blocked |
| `null` / not set | ❌ Hidden | ❌ Blocked |

## User Experience

### Verified User (UID Approved)
1. Opens `/autotrade`
2. Sees dashboard with "👥 Community Partners" button
3. Can click and access Community Partners features
4. Can register as community leader
5. Can get referral link

### Non-Verified User (No UID or Pending)
1. Opens `/autotrade`
2. Sees dashboard WITHOUT "👥 Community Partners" button
3. If somehow tries to access (via direct callback):
   - Gets "Access Denied" message
   - Prompted to complete registration
   - Redirected back to dashboard

## Specific Case: User ID 7972497694

**Status**: Not under referral  
**UID Status**: Not verified / Pending  
**Access**: ❌ BLOCKED

This user will:
- NOT see Community Partners button in dashboard
- Get "Access Denied" if tries to access directly
- Need to complete UID verification to access feature

## Testing

### Test 1: Verified User
```
1. Login as verified user
2. Send /autotrade
3. Should see "👥 Community Partners" button
4. Click button
5. Should access Community Partners menu
```

### Test 2: Non-Verified User (ID: 7972497694)
```
1. Login as user 7972497694
2. Send /autotrade
3. Should NOT see "👥 Community Partners" button
4. Dashboard shows other buttons normally
```

### Test 3: Direct Access Attempt
```
1. User somehow triggers community_partners callback
2. Should get "Access Denied" message
3. Should be redirected to dashboard
```

## Deployment

### Files Updated
- ✅ `Bismillah/app/handlers_autotrade.py`
- ✅ `Bismillah/app/handlers_community.py`

### Deployment Status
- ✅ Uploaded to VPS
- ✅ Bot service restarted
- ✅ Changes live in production

### Verification
```bash
ssh root@147.93.156.165
systemctl status cryptomentor.service
# Should show: active (running)
```

## Security Benefits

1. **Prevents Unauthorized Access**: Only verified users can access Community Partners
2. **Protects Referral System**: Ensures only legitimate referrals can become partners
3. **Clean UI**: Non-verified users don't see features they can't use
4. **Double Protection**: Both UI hiding + backend check

## Future Enhancements

Possible improvements:
1. Add notification when user becomes verified
2. Show "🔒 Locked" button with explanation
3. Track access attempts for security monitoring
4. Add admin panel to manage access

## Rollback

If needed to rollback:
```bash
ssh root@147.93.156.165
cd /root/cryptomentor-bot/backups
# Find latest backup before this change
# Restore files
systemctl restart cryptomentor.service
```

---

**Status**: ✅ DEPLOYED  
**Date**: 2026-03-31  
**Affected User**: 7972497694 (and all non-verified users)  
**Impact**: Community Partners feature now restricted to verified users only
