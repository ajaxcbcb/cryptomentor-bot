# Onboarding Flow Fix - Remove Capital/Leverage Input

## Problem

User masih diminta input "Capital" dan "Leverage" padahal menggunakan mode "Rekomendasi" (risk-based). Ini membingungkan karena:

1. Sistem sudah baca balance dari API
2. Leverage sudah fixed 10x (otomatis)
3. Position size dihitung dari risk % dan SL distance
4. User seharusnya hanya perlu pilih Risk % (1%, 2%, 3%)

## Root Cause

Ada 2 flow yang conflict:

### Flow Lama (Masih Aktif):
```
API Key Setup → Capital Input → Leverage Input → Start Trading
```

### Flow Baru (Sudah Ada tapi Tidak Konsisten):
```
API Key Setup → Risk Mode Selection → Risk % Selection → Start Trading
```

User existing yang punya data lama masih bisa trigger flow lama.

## Solution

### 1. Remove Capital/Leverage Input for Risk-Based Mode

**For New Users:**
- ✅ Already correct: API Key → Risk Mode → Risk % → Start
- ❌ Remove old flow completely

**For Existing Users:**
- ✅ If mode = "risk_based" → Skip capital/leverage, go to risk %
- ❌ Never show capital/leverage input for risk-based mode

### 2. Update Settings Flow

**Current (Confusing):**
- Settings → Change Margin → Input new capital
- Settings → Change Leverage → Input new leverage

**New (Clear):**
- Settings → Change Risk % → Select 1%/2%/3%
- No capital/leverage options for risk-based mode

### 3. Migration for Existing Users

Users with old data (`trade_amount`, `trade_leverage`) should:
1. Keep their data for backward compatibility
2. But when they open settings, show risk-based UI
3. If they change anything, migrate to new system

## Implementation Plan

### Phase 1: Remove Old Flow (CRITICAL)

**Files to Update:**
1. `handlers_autotrade.py`:
   - Remove `WAITING_TRADE_AMOUNT` state
   - Remove `WAITING_LEVERAGE` state (for new users)
   - Remove capital/leverage input handlers
   - Keep only for manual mode

2. `handlers_risk_mode.py`:
   - Already correct, no changes needed

### Phase 2: Update Settings

**Files to Update:**
1. `handlers_autotrade.py`:
   - `callback_settings()` - Already updated ✅
   - `callback_set_amount()` - Should check risk_mode first
   - `callback_set_leverage()` - Should check risk_mode first

### Phase 3: Add Migration Logic

**For existing users with old data:**
```python
if risk_mode == "risk_based":
    # Use balance from API, not stored trade_amount
    # Use fixed 10x leverage, not stored trade_leverage
    # Calculate position size from risk %
```

## Detailed Changes

### Change 1: Remove Capital Input for Risk-Based

**File:** `handlers_autotrade.py`

**Current Flow:**
```python
# After API key setup
→ Ask for capital (WAITING_TRADE_AMOUNT)
→ Ask for leverage (WAITING_LEVERAGE)
→ Start trading
```

**New Flow:**
```python
# After API key setup
→ Choose Risk Mode (at_choose_risk_mode)
→ If risk_based: Select Risk % (at_risk_1/2/3)
→ If manual: Input capital → Input leverage
→ Start trading
```

### Change 2: Block Capital/Leverage Changes for Risk-Based

**File:** `handlers_autotrade.py`

**Function:** `callback_set_amount()`

**Add Check:**
```python
async def callback_set_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Check risk mode
    risk_mode = get_risk_mode(user_id)
    
    if risk_mode == "risk_based":
        await query.edit_message_text(
            "❌ <b>Tidak Tersedia untuk Mode Rekomendasi</b>\n\n"
            "Dalam mode Rekomendasi, sistem otomatis menghitung margin dari balance Anda.\n\n"
            "Yang bisa Anda ubah:\n"
            "• Risk per trade (1%, 2%, 3%)\n\n"
            "Jika ingin kontrol manual, switch ke Manual Mode.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="at_settings")]
            ])
        )
        return ConversationHandler.END
    
    # Continue with manual mode flow...
```

**Function:** `callback_set_leverage()`

**Add Same Check:**
```python
async def callback_set_leverage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Check risk mode
    risk_mode = get_risk_mode(user_id)
    
    if risk_mode == "risk_based":
        await query.edit_message_text(
            "❌ <b>Tidak Tersedia untuk Mode Rekomendasi</b>\n\n"
            "Dalam mode Rekomendasi, leverage fixed 10x (optimal untuk risk management).\n\n"
            "Yang bisa Anda ubah:\n"
            "• Risk per trade (1%, 2%, 3%)\n\n"
            "Jika ingin kontrol leverage manual, switch ke Manual Mode.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="at_settings")]
            ])
        )
        return ConversationHandler.END
    
    # Continue with manual mode flow...
```

### Change 3: Update Dashboard Display

**File:** `handlers_autotrade.py`

**Function:** `cmd_autotrade()`

**For Risk-Based Mode:**
```python
if risk_mode == "risk_based":
    # Don't show stored trade_amount/trade_leverage
    # Show balance from API + risk %
    text = (
        f"Mode: 🎯 Rekomendasi\n"
        f"Balance: ${balance:.2f} USDT\n"
        f"Risk per trade: {risk_pct}%\n"
        # Don't show leverage/margin
    )
```

## Testing Plan

### Test Case 1: New User
1. Start /autotrade
2. Select exchange
3. Enter API key
4. Should see: "Choose Risk Mode"
5. Select "Rekomendasi"
6. Should see: "Select Risk %" (1%, 2%, 3%)
7. Select 2%
8. Should see: "Setup Complete" with balance & risk %
9. Start trading
10. ✅ Never asked for capital/leverage

### Test Case 2: Existing User (Risk-Based)
1. Already has session with risk_mode="risk_based"
2. Open /autotrade
3. Go to Settings
4. Should NOT see: "Change Margin" or "Change Leverage"
5. Should see: "Change Risk %"
6. ✅ Cannot change capital/leverage

### Test Case 3: Existing User (Manual)
1. Already has session with risk_mode="manual"
2. Open /autotrade
3. Go to Settings
4. Should see: "Change Margin" and "Change Leverage"
5. Can change both
6. ✅ Manual mode still works

### Test Case 4: Migration
1. User has old data (before risk mode system)
2. Open /autotrade
3. Should be prompted to choose risk mode
4. After choosing, old data ignored
5. ✅ Migrated to new system

## Rollout Plan

### Step 1: Deploy Blocking Logic (IMMEDIATE)
- Add checks to `callback_set_amount()` and `callback_set_leverage()`
- Block these for risk-based mode users
- This prevents confusion immediately

### Step 2: Clean Up Old Flow (NEXT)
- Remove unused states and handlers
- Clean up code
- Add migration logic

### Step 3: User Communication (AFTER)
- Announce in bot: "Risk management system updated"
- Explain: "No need to set capital/leverage anymore"
- Guide: "Just choose your risk %"

## Expected Impact

### Before:
- ❌ User confused about capital/leverage
- ❌ Conflict between stored values and API balance
- ❌ Inconsistent UX

### After:
- ✅ Clear and simple: Just choose risk %
- ✅ System handles everything else
- ✅ Consistent with "Rekomendasi" concept
- ✅ No more support questions about capital/leverage

## Files to Modify

1. ✅ `Bismillah/app/handlers_autotrade.py` - Main changes
2. ❌ `Bismillah/app/handlers_risk_mode.py` - Already correct
3. ✅ `Bismillah/app/supabase_repo.py` - Add get_risk_mode() if not exists

## Priority

🔴 **CRITICAL** - Deploy immediately to stop user confusion

Users are already complaining about this conflict. We need to fix it ASAP.

