# Risk Mode Selection - Implementation Complete

**Date:** April 2, 2026  
**Status:** ✅ FOUNDATION COMPLETE - NEEDS INTEGRATION

---

## ✅ Completed

### 1. Database Layer
- ✅ `db/add_risk_mode.sql` - Migration script
- ✅ Column `risk_mode` added (VARCHAR(20), default 'risk_based')
- ✅ Existing users set to 'manual' (backward compatible)
- ✅ Index created for performance

### 2. Repository Layer
- ✅ `get_risk_mode(telegram_id)` - Get user's mode
- ✅ `set_risk_mode(telegram_id, mode)` - Update mode
- ✅ Validation and error handling
- ✅ Added to `Bismillah/app/supabase_repo.py`

### 3. Handler Layer
- ✅ `Bismillah/app/handlers_risk_mode.py` - New file with all callbacks
- ✅ `callback_choose_risk_mode` - Mode selection screen
- ✅ `callback_mode_risk_based` - Risk-based mode flow
- ✅ `callback_select_risk_pct` - Risk % selection (1%, 2%, 3%, 5%)
- ✅ `callback_mode_manual` - Manual mode flow
- ✅ `callback_switch_risk_mode` - Switch modes in settings

---

## 🔄 Next Steps (Manual Integration Required)

### Step 1: Import New Handlers

Add to `Bismillah/app/handlers_autotrade.py`:

```python
# At the top with other imports
from app.handlers_risk_mode import (
    callback_choose_risk_mode,
    callback_mode_risk_based,
    callback_select_risk_pct,
    callback_mode_manual,
    callback_switch_risk_mode
)
from app.supabase_repo import get_risk_mode, set_risk_mode
```

### Step 2: Register New Callbacks

Add to the handler list in `handlers_autotrade.py` (around line 2537):

```python
CallbackQueryHandler(callback_choose_risk_mode,  pattern="^at_choose_risk_mode$"),
CallbackQueryHandler(callback_mode_risk_based,   pattern="^at_mode_risk_based$"),
CallbackQueryHandler(callback_mode_manual,       pattern="^at_mode_manual$"),
CallbackQueryHandler(callback_select_risk_pct,   pattern="^at_risk_[1235]$"),
CallbackQueryHandler(callback_switch_risk_mode,  pattern="^at_switch_risk_mode$"),
```

### Step 3: Update Registration Flow

Find where API key is saved (after `callback_set_api_secret` or similar), then redirect to mode selection:

**OLD:**
```python
# After API key saved
keyboard = [[InlineKeyboardButton("Set Margin", callback_data="at_set_amount")]]
```

**NEW:**
```python
# After API key saved
keyboard = [[InlineKeyboardButton("Pilih Risk Mode", callback_data="at_choose_risk_mode")]]
```

### Step 4: Update Leverage Callback

Modify `callback_set_leverage` to handle both modes:

```python
async def callback_set_leverage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    risk_mode = get_risk_mode(user_id)
    
    # Extract leverage from callback
    lev_map = {"at_lev_5": 5, "at_lev_10": 10, "at_lev_20": 20, "at_lev_50": 50}
    leverage = lev_map.get(query.data, 10)
    
    # Save leverage
    # ... existing save code ...
    
    if risk_mode == "risk_based":
        # Skip margin input, go directly to confirmation
        await callback_confirm_trade(update, context)
    else:
        # Manual mode: ask for margin
        await callback_set_amount(update, context)
```

### Step 5: Update Confirmation Message

Modify `callback_confirm_trade` to show mode-specific info:

```python
async def callback_confirm_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... existing code ...
    
    risk_mode = get_risk_mode(user_id)
    
    if risk_mode == "risk_based":
        risk_pct = get_risk_per_trade(user_id)
        text = (
            "✅ <b>Konfirmasi Setup AutoTrade</b>\n\n"
            "Mode: 🎯 Rekomendasi (Risk Per Trade)\n\n"
            f"• Exchange: {exchange}\n"
            f"• Risk per trade: {risk_pct}%\n"
            f"• Leverage: {leverage}x\n"
            f"• Balance: ${balance:.2f}\n\n"
            "💡 System akan otomatis hitung margin dari balance\n"
            "💡 Position size adjust otomatis per trade\n"
            # ... rest of message ...
        )
    else:
        text = (
            "✅ <b>Konfirmasi Setup AutoTrade</b>\n\n"
            "Mode: ⚙️ Manual (Fixed Margin)\n\n"
            f"• Exchange: {exchange}\n"
            f"• Margin per trade: ${amount}\n"
            f"• Leverage: {leverage}x\n"
            f"• Balance: ${balance:.2f}\n\n"
            "💡 Setiap trade pakai ${amount} margin (fixed)\n"
            # ... rest of message ...
        )
```

### Step 6: Update Settings Dashboard

Modify `callback_settings` to show mode-specific options:

```python
async def callback_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... existing code ...
    
    risk_mode = get_risk_mode(user_id)
    
    if risk_mode == "risk_based":
        risk_pct = get_risk_per_trade(user_id)
        mode_text = (
            f"Mode: 🎯 Rekomendasi (Risk {risk_pct}%)\n"
            f"Leverage: {leverage}x\n"
            f"Balance: ${balance:.2f}\n"
        )
        keyboard = [
            [InlineKeyboardButton("Change Risk %", callback_data="at_risk_settings")],
            [InlineKeyboardButton("Change Leverage", callback_data="at_set_leverage")],
            [InlineKeyboardButton("Switch to Manual Mode", callback_data="at_switch_risk_mode")],
            # ... other buttons ...
        ]
    else:
        mode_text = (
            f"Mode: ⚙️ Manual (Margin ${amount})\n"
            f"Leverage: {leverage}x\n"
            f"Balance: ${balance:.2f}\n"
        )
        keyboard = [
            [InlineKeyboardButton("Change Margin", callback_data="at_set_amount")],
            [InlineKeyboardButton("Change Leverage", callback_data="at_set_leverage")],
            [InlineKeyboardButton("Switch to Rekomendasi Mode", callback_data="at_switch_risk_mode")],
            # ... other buttons ...
        ]
```

### Step 7: Handle Manual Margin Input

Add message handler for manual margin input:

```python
async def handle_manual_margin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for manual margin"""
    if not context.user_data.get('awaiting_manual_margin'):
        return
    
    try:
        margin = float(update.message.text)
        
        if margin <= 0:
            await update.message.reply_text("❌ Margin harus lebih dari 0")
            return
        
        # Save margin
        user_id = update.effective_user.id
        # ... save to database ...
        
        # Clear state
        context.user_data['awaiting_manual_margin'] = False
        
        # Show leverage selection
        # ... show leverage keyboard ...
        
    except ValueError:
        await update.message.reply_text("❌ Masukkan angka yang valid (contoh: 10)")
```

---

## 📋 Testing Checklist

After integration, test:

### Registration Flow:
- [ ] New user → Choose mode → Risk-based → Select risk % → Select leverage → Confirm
- [ ] New user → Choose mode → Manual → Enter margin → Select leverage → Confirm
- [ ] Existing user → Should see manual mode (backward compatible)

### Settings Flow:
- [ ] Risk-based user → See risk % and leverage options
- [ ] Risk-based user → Can change risk %
- [ ] Risk-based user → Can switch to manual mode
- [ ] Manual user → See margin and leverage options
- [ ] Manual user → Can change margin
- [ ] Manual user → Can switch to risk-based mode

### Engine Behavior:
- [ ] Risk-based mode → Uses risk-based calculation
- [ ] Manual mode → Uses fixed margin calculation
- [ ] Fallback works if calculation fails

---

## 🚀 Deployment Steps

1. **Run Migration:**
```bash
# Connect to Supabase and run
psql $DATABASE_URL < db/add_risk_mode.sql
```

2. **Deploy Files:**
```bash
scp Bismillah/app/supabase_repo.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/handlers_risk_mode.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/handlers_autotrade.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
```

3. **Restart Service:**
```bash
ssh root@147.93.156.165 "systemctl restart cryptomentor.service"
```

4. **Monitor:**
```bash
ssh root@147.93.156.165 "journalctl -u cryptomentor.service -f"
```

---

## 📝 Summary

**What's Done:**
- ✅ Database schema
- ✅ Repository functions
- ✅ Handler callbacks (separate file)
- ✅ Documentation

**What's Needed:**
- 🔄 Integration into handlers_autotrade.py (manual steps above)
- 🔄 Testing
- 🔄 Deployment

**Estimated Time:** 1-2 hours for integration + testing

---

**Foundation is solid! Ready for integration.** 🚀
