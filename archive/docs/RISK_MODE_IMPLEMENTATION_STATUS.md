# Risk Mode Selection - Implementation Status

**Date:** April 2, 2026  
**Status:** IN PROGRESS

---

## Completed ✅

### 1. Database Migration
- ✅ Created `db/add_risk_mode.sql`
- ✅ Add column `risk_mode` (VARCHAR(20), default 'risk_based')
- ✅ Set existing users to 'manual' (backward compatible)
- ✅ Create index for performance

### 2. Repository Functions
- ✅ `get_risk_mode(telegram_id)` - Get user's mode
- ✅ `set_risk_mode(telegram_id, mode)` - Update mode
- ✅ Validation (only 'risk_based' or 'manual')
- ✅ Error handling

---

## Next Steps 🔄

### 3. Registration Flow (handlers_autotrade.py)
Need to add new callbacks:
- `callback_choose_risk_mode` - Mode selection
- `callback_mode_risk_based` - Choose risk-based mode
- `callback_mode_manual` - Choose manual mode
- `callback_select_risk_pct` - Select risk % (1%, 2%, 3%, 5%)
- Update existing `callback_set_leverage` to handle both modes
- Update existing `callback_set_amount` for manual mode only
- Update `callback_confirm_trade` to show mode-specific info

### 4. Settings Dashboard
Need to update:
- `callback_settings` - Show current mode
- Add `callback_change_risk_mode` - Switch between modes
- Update `callback_risk_settings` - Mode-specific options
- Update display to hide margin if risk_based mode

### 5. Engine Integration
- ✅ Already done in Phase 2!
- Engine checks `risk_mode` and uses appropriate calculation
- No additional changes needed

---

## Implementation Plan

### Registration Flow Changes:

**Current Flow:**
```
/autotrade
→ Select Exchange
→ Enter API Key
→ Enter API Secret  
→ Set Amount (margin)
→ Set Leverage
→ Confirm
```

**New Flow:**
```
/autotrade
→ Select Exchange
→ Enter API Key
→ Enter API Secret
→ [NEW] Choose Risk Mode (Rekomendasi / Manual)
    ├─ If Rekomendasi:
    │   → Select Risk % (1% / 2% / 3% / 5%)
    │   → Select Leverage (5x / 10x / 20x / 50x)
    │   → Confirm (no margin input needed)
    │
    └─ If Manual:
        → Set Amount (margin)
        → Set Leverage
        → Confirm
```

### Settings Flow Changes:

**Current:**
```
Settings
→ Change Margin
→ Change Leverage
→ Risk Management (separate)
```

**New:**
```
Settings
→ Current Mode: [Rekomendasi / Manual]
→ If Rekomendasi:
    - Change Risk %
    - Change Leverage
    - Switch to Manual Mode
→ If Manual:
    - Change Margin
    - Change Leverage
    - Switch to Rekomendasi Mode
```

---

## Key Design Decisions

### 1. Default Mode
- **New users:** `risk_based` (recommended)
- **Existing users:** `manual` (backward compatible)

### 2. Mode Switching
- Users can switch anytime in Settings
- When switching to risk_based: keep leverage, ignore margin
- When switching to manual: need to set margin

### 3. Display Logic
- Risk_based mode: Show risk %, hide margin
- Manual mode: Show margin, hide risk %
- Both modes: Show leverage

### 4. Engine Behavior
- Risk_based: Calculate from balance + risk % + SL distance
- Manual: Use fixed margin (legacy behavior)
- Fallback: If risk calculation fails, use manual mode

---

## Token Budget Check

Current usage: ~118K / 200K tokens
Remaining: ~82K tokens

Estimated for handlers:
- Registration flow: ~20K tokens
- Settings flow: ~15K tokens
- Testing: ~10K tokens
- Documentation: ~5K tokens

Total estimated: ~50K tokens
**Status:** ✅ Sufficient tokens remaining

---

## Next Action

Implement registration flow in `handlers_autotrade.py`:
1. Add mode selection callback
2. Branch flow based on mode
3. Update confirmation message
4. Test flow

Ready to proceed? 🚀
