# Business Requirements - NON-NEGOTIABLE

**Date:** April 3, 2026  
**Status:** ✅ CONFIRMED - MUST NOT BE CHANGED

---

## Critical Business Rules

### 1. REFERRAL REQUIREMENT - MANDATORY ✅

**Rule:** ALL users MUST register through our referral link

**Why:** This is our revenue source - we earn from trading volume

**Implementation:**
- ✅ User MUST click referral link
- ✅ User MUST register on exchange via our link
- ✅ User MUST confirm registration before proceeding
- ❌ NO bypass allowed
- ❌ NO skip button
- ❌ NO "I'll do it later"

**Current Flow (CORRECT - DO NOT CHANGE):**
```
/autotrade
→ Select Exchange
→ Show referral link
→ User clicks "Register via Referral"
→ User registers on exchange
→ User returns and clicks "Already Registered"
→ Continue to API Key setup
```

**What UX Improvements CAN Do:**
- ✅ Make explanation clearer
- ✅ Add visual guide/tutorial
- ✅ Show benefits of registration
- ✅ Add progress indicator
- ❌ Remove referral requirement
- ❌ Add skip option
- ❌ Make it optional

---

### 2. ADMIN VERIFICATION - MANDATORY (for Bitunix) ✅

**Rule:** Bitunix users MUST have UID verified by admin

**Why:** 
- Ensures user registered via our referral
- Prevents fraud
- Confirms we get commission

**Implementation:**
- ✅ User enters UID after API key setup
- ✅ UID sent to admin for verification
- ✅ Admin checks if UID is under our referral
- ✅ Admin approves or rejects
- ✅ User notified of result
- ❌ NO auto-approval
- ❌ NO bypass
- ❌ NO skip

**Current Flow (CORRECT - DO NOT CHANGE):**
```
API Key Setup Complete
→ Enter UID
→ UID sent to admin
→ Admin verifies UID is under our referral
→ Admin clicks Approve/Reject
→ User notified
→ If approved: Continue to risk mode
→ If rejected: Must re-register via correct referral
```

**What UX Improvements CAN Do:**
- ✅ Show estimated verification time
- ✅ Add "What happens next?" explanation
- ✅ Send notification when verified
- ✅ Show verification status
- ❌ Remove admin verification
- ❌ Auto-approve
- ❌ Skip verification

---

### 3. API KEY REQUIREMENT - MANDATORY ✅

**Rule:** Users MUST provide API Key & Secret

**Why:** Bot needs access to execute trades

**Implementation:**
- ✅ User must create API key on exchange
- ✅ User must enter API key in bot
- ✅ User must enter API secret in bot
- ✅ Bot verifies connection
- ❌ NO demo mode without API
- ❌ NO skip
- ❌ NO "try without API"

**Current Flow (CORRECT - DO NOT CHANGE):**
```
Referral Confirmed
→ Enter API Key
→ Enter API Secret
→ Bot verifies connection
→ If success: Continue
→ If fail: Show error with fix instructions
```

**What UX Improvements CAN Do:**
- ✅ Combine API Key & Secret input (single screen)
- ✅ Add inline tutorial
- ✅ Better error messages
- ✅ Show verification progress
- ❌ Remove API requirement
- ❌ Add demo mode
- ❌ Skip verification

---

## UX Improvements - ALLOWED ✅

### What We CAN Improve:

#### 1. Progress Indicators
```
✅ Show "Step 1 of 4"
✅ Show progress bar
✅ Show estimated time
✅ Show "Almost done!"
```

#### 2. Better Explanations
```
✅ Clearer text
✅ Visual guides
✅ Video tutorials
✅ FAQ links
```

#### 3. Error Messages
```
✅ Actionable steps
✅ Quick fix buttons
✅ Visual hierarchy
✅ Help options
```

#### 4. Loading States
```
✅ Progress indicators
✅ Tips while waiting
✅ Estimated time
✅ Cancel option (if appropriate)
```

#### 5. Settings Organization
```
✅ Group by category
✅ Visual status
✅ Quick actions
✅ Better layout
```

---

## UX Improvements - NOT ALLOWED ❌

### What We CANNOT Change:

#### 1. Referral Flow
```
❌ Remove referral link
❌ Add skip button
❌ Make it optional
❌ Add "I'll do it later"
❌ Auto-approve without registration
```

#### 2. Admin Verification
```
❌ Remove admin approval
❌ Auto-approve UIDs
❌ Skip verification
❌ Add bypass
❌ Make it optional
```

#### 3. API Key Requirement
```
❌ Remove API key requirement
❌ Add demo mode without API
❌ Skip API verification
❌ Allow trading without API
```

---

## Current Implementation Status

### ✅ CORRECT - Business Requirements Protected

1. **Referral Flow** - ✅ Mandatory, no bypass
2. **Admin Verification** - ✅ Mandatory for Bitunix
3. **API Key Setup** - ✅ Mandatory, verified

### ✅ SAFE - UX Improvements Applied

1. **Progress Indicators** - ✅ Added (doesn't bypass requirements)
2. **Better Error Messages** - ✅ Improved (still enforces requirements)
3. **Settings Menu** - ✅ Reorganized (doesn't change requirements)
4. **Loading States** - ✅ Enhanced (doesn't skip verification)

---

## Exchange-Specific Rules

### Bitunix (UID Verification Required)
```
Flow:
1. Register via referral ✅ MANDATORY
2. Enter API Key ✅ MANDATORY
3. Enter UID ✅ MANDATORY
4. Admin verifies UID ✅ MANDATORY
5. Continue to risk mode ✅ After approval only
```

### BingX, Binance, Bybit (No UID Verification)
```
Flow:
1. Register via referral ✅ MANDATORY (honor system)
2. Enter API Key ✅ MANDATORY
3. Continue to risk mode ✅ After API verified
```

**Note:** For non-Bitunix exchanges, we trust user registered via referral (no UID to verify). But referral link is still shown and required.

---

## Testing Checklist

### Business Requirements Testing

- [ ] User CANNOT skip referral registration
- [ ] User CANNOT proceed without API key
- [ ] Bitunix user CANNOT trade without UID approval
- [ ] Admin verification is required for Bitunix
- [ ] Rejected UID blocks trading
- [ ] No bypass options exist

### UX Improvements Testing

- [ ] Progress indicators show correctly
- [ ] Error messages are helpful
- [ ] Settings menu is organized
- [ ] Loading states are informative
- [ ] All improvements respect business rules

---

## Summary

### What Changed (UX Improvements):
- ✅ Added progress indicators
- ✅ Improved error messages
- ✅ Better settings organization
- ✅ Enhanced loading states
- ✅ Clearer explanations

### What Did NOT Change (Business Requirements):
- ✅ Referral requirement - STILL MANDATORY
- ✅ Admin verification - STILL MANDATORY (Bitunix)
- ✅ API key requirement - STILL MANDATORY
- ✅ No bypass options - STILL NONE
- ✅ No skip buttons - STILL NONE

---

## Conclusion

**UX improvements make the experience better WITHOUT compromising business requirements.**

- User still MUST register via referral
- User still MUST provide API key
- Bitunix user still MUST get admin approval
- But now the process is:
  - Clearer (progress indicators)
  - Less frustrating (better errors)
  - More organized (better settings)
  - More informative (loading tips)

**Result:** Better UX + Same business protection = Win-win! 🎉

---

**Confirmed by:** Senior Developer Review  
**Status:** ✅ APPROVED - Safe to implement  
**Risk:** LOW - No business impact
