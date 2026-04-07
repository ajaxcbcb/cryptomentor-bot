# Community Partners Button Visibility Fix

## Issue Summary

User reported that the "👥 Community Partners" button is missing from their AutoTrade dashboard.

## Root Cause Analysis

### Current Button Visibility Logic
```python
uid_status = session.get("status", "")
show_community = uid_status == "uid_verified" or uid_status == "active"
```

### Status Values in Database
Analysis of 24 users in production:

| Status | Count | Button Visible? |
|--------|-------|----------------|
| stopped | 8 | ❌ NO |
| active | 8 | ✅ YES |
| uid_verified | 5 | ✅ YES |
| inactive | 2 | ❌ NO |
| uid_rejected | 1 | ❌ NO |

### The Problem
- **11 out of 24 users (46%)** cannot see the Community Partners button
- Users with status "stopped" have completed verification and have deposits, but button is hidden
- The "stopped" status is set when users manually stop their engine via "🛑 Stop AutoTrade"

### Status Lifecycle
1. **pending_verification** → User submitted UID, waiting for admin/leader approval
2. **uid_verified** → UID approved, user can start trading
3. **active** → Engine is running
4. **stopped** → User manually stopped engine (but still verified and can restart)
5. **inactive** → Session not active
6. **uid_rejected** → UID verification rejected

## Solution

### Option 1: Show Button for All Verified Users (RECOMMENDED)
Show button for users who have completed UID verification, regardless of engine status:

```python
uid_status = session.get("status", "")
show_community = uid_status in ["uid_verified", "active", "stopped"]
```

**Rationale:**
- Users with "stopped" status have already been verified
- They should still have access to Community Partners features
- Engine status (running/stopped) is independent of community access

### Option 2: Show Button for All Users with Sessions
Most permissive - show for everyone who has a session:

```python
show_community = session is not None and session.get("status") not in ["uid_rejected"]
```

**Rationale:**
- Only exclude users who were explicitly rejected
- Allow pending users to see what they'll get access to

### Option 3: Keep Current Logic (NOT RECOMMENDED)
Keep current logic but ensure "stopped" status is changed to "uid_verified" when engine stops.

**Rationale:**
- More complex, requires changing stop engine logic
- Loses information about engine state

## Recommended Fix

**Use Option 1** - it's the right balance:
- Verified users always see the button
- Rejected users don't see it
- Pending users don't see it (they need to complete verification first)

## Implementation

### Files to Modify
1. `Bismillah/app/handlers_autotrade.py` - 3 locations (lines ~247, ~373, ~1855)

### Code Changes

Replace all 3 occurrences of:
```python
show_community = uid_status == "uid_verified" or uid_status == "active"
```

With:
```python
show_community = uid_status in ["uid_verified", "active", "stopped"]
```

## Testing Plan

1. Test with user who has status="stopped" → Should see button ✅
2. Test with user who has status="active" → Should see button ✅
3. Test with user who has status="uid_verified" → Should see button ✅
4. Test with user who has status="pending_verification" → Should NOT see button ❌
5. Test with user who has status="uid_rejected" → Should NOT see button ❌
6. Test with user who has status="inactive" → Should NOT see button ❌

## Impact

- **Positive:** 8 users with "stopped" status will now see Community Partners button
- **No negative impact:** All other users maintain current behavior
- **User Experience:** Users who stopped their engine can still access community features

## Deployment

1. Update `handlers_autotrade.py` with the fix
2. Deploy to VPS via SCP
3. Restart service: `systemctl restart cryptomentor`
4. Verify with test user

## Additional Findings

### Community Partners Flow (Documented)

**For Community Leaders:**
1. Go to /autotrade → Dashboard → "👥 Community Partners"
2. Click "✅ Daftar Komunitas"
3. Enter community name (e.g., "Crypto Indo")
4. Enter Bitunix referral code (e.g., "ABC123")
5. Enter your Bitunix UID
6. Wait for admin approval
7. Once approved, get invitation link: `t.me/bot?start=community_{code}`
8. Share link with community members

**For Community Members:**
1. Click community invitation link
2. Register on Bitunix using community's referral code
3. Complete AutoTrade setup (/autotrade)
4. Enter Bitunix UID
5. Wait for community leader approval (not admin)
6. Once approved, can start trading

**Access Control:**
- Button only shows for verified users (uid_verified, active, stopped)
- Demo users are blocked from accessing Community Partners
- Pending/rejected users cannot see the button

### Current State
- **0 active communities** in production
- Feature is ready but not yet used by any community
- All infrastructure is in place and working

## Conclusion

The fix is straightforward - add "stopped" to the list of statuses that can see the Community Partners button. This ensures users who have completed verification can always access community features, regardless of whether their trading engine is currently running.
