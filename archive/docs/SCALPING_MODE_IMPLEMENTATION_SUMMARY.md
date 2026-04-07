# Scalping Mode Implementation Summary

## ✅ Completed Tasks

### Phase 1: Core Infrastructure (COMPLETE)
- ✅ Task 1.1: Database Migration Script (`db/add_trading_mode.sql`)
- ✅ Task 1.2: TradingMode Enum and Data Models (`Bismillah/app/trading_mode.py`)
- ✅ Task 1.3: TradingModeManager Module (`Bismillah/app/trading_mode_manager.py`)

### Phase 2: Scalping Engine (COMPLETE)
- ✅ Task 2.1-2.8: Complete ScalpingEngine Implementation (`Bismillah/app/scalping_engine.py`)
  - Core structure with run loop
  - Signal generation with 15M trend validation
  - TP/SL calculation (1.5R)
  - Signal validation (80% confidence, R:R checks)
  - Order placement with retry logic
  - Position monitoring (TP/SL/max hold time)
  - Max hold time enforcement (30 minutes)
  - Cooldown management (5 minutes)
- ✅ Task 4.2: Extended autosignal_fast.py with `compute_signal_scalping()` function

## 📋 Remaining Tasks (Manual Implementation Required)

### Phase 3: Dashboard Integration
**Files to Modify:** `Bismillah/app/handlers_autotrade.py`, `Bismillah/bot.py`

#### Task 3.1: Add Trading Mode Menu Handler
Add to `handlers_autotrade.py`:

```python
async def callback_trading_mode_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display trading mode selection menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    from app.trading_mode_manager import TradingModeManager, TradingMode
    current_mode = TradingModeManager.get_mode(user_id)
    
    scalping_check = "✅ " if current_mode == TradingMode.SCALPING else ""
    swing_check = "✅ " if current_mode == TradingMode.SWING else ""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{scalping_check}⚡ Scalping Mode (5M)",
            callback_data="mode_select_scalping"
        )],
        [InlineKeyboardButton(
            f"{swing_check}📊 Swing Mode (15M)",
            callback_data="mode_select_swing"
        )],
        [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="at_dashboard")],
    ])
    
    await query.edit_message_text(
        "⚙️ <b>Select Trading Mode</b>\n\n"
        "⚡ <b>Scalping Mode (5M):</b>\n"
        "• Fast trades on 5-minute chart\n"
        "• 10-20 trades per day\n"
        "• Single TP at 1.5R\n"
        "• 30-minute max hold time\n"
        "• Pairs: BTC, ETH\n\n"
        "📊 <b>Swing Mode (15M):</b>\n"
        "• Swing trades on 15-minute chart\n"
        "• 2-3 trades per day\n"
        "• 3-tier TP (StackMentor)\n"
        "• No max hold time\n"
        "• Pairs: BTC, ETH, SOL, BNB\n\n"
        f"Current mode: <b>{current_mode.value.upper()}</b>",
        parse_mode='HTML',
        reply_markup=keyboard
    )
```

#### Task 3.2: Add Mode Selection Handlers
Add to `handlers_autotrade.py`:

```python
async def callback_select_scalping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle scalping mode selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    from app.trading_mode_manager import TradingModeManager, TradingMode
    current_mode = TradingModeManager.get_mode(user_id)
    
    if current_mode == TradingMode.SCALPING:
        await query.edit_message_text(
            "⚡ You're already in Scalping Mode!",
            parse_mode='HTML'
        )
        return
    
    # Switch mode
    result = await TradingModeManager.switch_mode(
        user_id, TradingMode.SCALPING, context.application.bot, context
    )
    
    if result["success"]:
        await query.edit_message_text(
            "✅ <b>Trading Mode Changed</b>\n\n"
            "⚡ <b>Scalping Mode Activated</b>\n\n"
            "📊 Configuration:\n"
            "• Timeframe: 5 minutes\n"
            "• Scan interval: 15 seconds\n"
            "• Profit target: 1.5R (single TP)\n"
            "• Max hold time: 30 minutes\n"
            "• Trading pairs: BTCUSDT, ETHUSDT\n"
            "• Min confidence: 80%\n\n"
            "🚀 Engine restarted with scalping parameters.\n"
            "You'll receive signals when high-probability setups appear.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 View Dashboard", callback_data="at_dashboard")]
            ])
        )
    else:
        await query.edit_message_text(
            f"❌ Failed to switch mode: {result['message']}",
            parse_mode='HTML'
        )

async def callback_select_swing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle swing mode selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    from app.trading_mode_manager import TradingModeManager, TradingMode
    current_mode = TradingModeManager.get_mode(user_id)
    
    if current_mode == TradingMode.SWING:
        await query.edit_message_text(
            "📊 You're already in Swing Mode!",
            parse_mode='HTML'
        )
        return
    
    # Switch mode
    result = await TradingModeManager.switch_mode(
        user_id, TradingMode.SWING, context.application.bot, context
    )
    
    if result["success"]:
        await query.edit_message_text(
            "✅ <b>Trading Mode Changed</b>\n\n"
            "📊 <b>Swing Mode Activated</b>\n\n"
            "📊 Configuration:\n"
            "• Timeframe: 15 minutes\n"
            "• Scan interval: 45 seconds\n"
            "• Profit targets: 3-tier (StackMentor)\n"
            "• No max hold time\n"
            "• Trading pairs: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT\n"
            "• Min confidence: 68%\n\n"
            "🚀 Engine restarted with swing parameters.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 View Dashboard", callback_data="at_dashboard")]
            ])
        )
    else:
        await query.edit_message_text(
            f"❌ Failed to switch mode: {result['message']}",
            parse_mode='HTML'
        )
```

#### Task 3.3: Update Dashboard Display
Modify `cmd_autotrade()` in `handlers_autotrade.py`:

```python
# Add after line where you check if keys and is_active:
from app.trading_mode_manager import TradingModeManager, TradingMode

# Load trading mode
trading_mode = TradingModeManager.get_mode(user_id)
mode_emoji = "⚡" if trading_mode == TradingMode.SCALPING else "📊"
mode_label = "Scalping (5M)" if trading_mode == TradingMode.SCALPING else "Swing (15M)"

# Update dashboard text to include mode:
# Change this line:
# "✅ Status: <b>ACTIVE</b>\n\n"
# To:
# f"✅ Status: <b>ACTIVE</b>\n"
# f"{mode_emoji} Mode: <b>{mode_label}</b>\n\n"

# Add Trading Mode button to keyboard:
keyboard_buttons = [
    [InlineKeyboardButton("📊 Status Portfolio",  callback_data="at_status")],
    [InlineKeyboardButton("📈 Trade History",     callback_data="at_history")],
    [InlineKeyboardButton("⚙️ Trading Mode",      callback_data="trading_mode_menu")],  # NEW
    engine_btn,
    # ... rest of buttons
]
```

#### Task 3.4: Register Handlers
Add to `bot.py` (in the handler registration section):

```python
from app.handlers_autotrade import (
    callback_trading_mode_menu,
    callback_select_scalping,
    callback_select_swing,
)

application.add_handler(CallbackQueryHandler(
    callback_trading_mode_menu, 
    pattern="^trading_mode_menu$"
))

application.add_handler(CallbackQueryHandler(
    callback_select_scalping, 
    pattern="^mode_select_scalping$"
))

application.add_handler(CallbackQueryHandler(
    callback_select_swing, 
    pattern="^mode_select_swing$"
))
```

### Phase 4: Engine Integration

#### Task 4.1: Integrate with autotrade_engine.py
Modify `start_engine()` function in `Bismillah/app/autotrade_engine.py`:

```python
def start_engine(bot, user_id: int, api_key: str, api_secret: str,
                 amount: float, leverage: int, notify_chat_id: int,
                 is_premium: bool = False, silent: bool = False, 
                 exchange_id: str = "bitunix"):
    
    stop_engine(user_id)
    
    # Load trading mode
    from app.trading_mode_manager import TradingModeManager, TradingMode
    trading_mode = TradingModeManager.get_mode(user_id)
    
    # Get exchange client
    from app.exchange_registry import get_client
    client = get_client(exchange_id, api_key, api_secret)
    
    # Start appropriate engine based on mode
    if trading_mode == TradingMode.SCALPING:
        from app.scalping_engine import ScalpingEngine
        engine = ScalpingEngine(
            user_id=user_id,
            client=client,
            bot=bot,
            notify_chat_id=notify_chat_id
        )
        task = asyncio.create_task(engine.run())
        logger.info(f"[AutoTrade:{user_id}] Started SCALPING engine")
    else:
        # Existing swing trading logic
        task = asyncio.create_task(_trade_loop(
            bot, user_id, client, amount, leverage, 
            notify_chat_id, is_premium, exchange_id
        ))
        logger.info(f"[AutoTrade:{user_id}] Started SWING engine")
    
    _running_tasks[user_id] = task
    
    def _done_cb(t):
        if t.cancelled():
            logger.info(f"[AutoTrade:{user_id}] Engine cancelled")
        elif t.exception():
            logger.error(f"[AutoTrade:{user_id}] Engine error: {t.exception()}")
    
    task.add_done_callback(_done_cb)
```

## 🚀 Deployment Steps

### Step 1: Database Migration
```bash
# On VPS, backup database first
pg_dump cryptomentor > backup_$(date +%Y%m%d).sql

# Run migration
psql cryptomentor < db/add_trading_mode.sql

# Verify
psql cryptomentor -c "SELECT column_name FROM information_schema.columns WHERE table_name='autotrade_sessions' AND column_name='trading_mode';"
```

### Step 2: Deploy Code Files
```bash
# Upload new files
scp Bismillah/app/trading_mode.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/trading_mode_manager.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/scalping_engine.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/

# Update existing files (after manual modifications)
scp Bismillah/app/autosignal_fast.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/handlers_autotrade.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/app/autotrade_engine.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/app/
scp Bismillah/bot.py root@147.93.156.165:/root/cryptomentor-bot/Bismillah/
```

### Step 3: Restart Service
```bash
ssh root@147.93.156.165
cd /root/cryptomentor-bot
systemctl restart cryptomentor.service
systemctl status cryptomentor.service
journalctl -u cryptomentor.service -f
```

### Step 4: Test
1. Open bot and run `/autotrade`
2. Click "⚙️ Trading Mode" button
3. Select "⚡ Scalping Mode (5M)"
4. Verify confirmation message
5. Check dashboard shows "⚡ Mode: Scalping (5M)"
6. Monitor logs for signal generation

## 📊 Implementation Status

| Phase | Tasks | Status | Files Created |
|-------|-------|--------|---------------|
| Phase 1 | 3/3 | ✅ COMPLETE | 3 files |
| Phase 2 | 8/8 | ✅ COMPLETE | 1 file + 1 modified |
| Phase 3 | 0/4 | ⏳ PENDING | Manual edits needed |
| Phase 4 | 1/3 | ⏳ PARTIAL | Manual edits needed |
| Phase 5 | 0/3 | ⏳ PENDING | Testing |
| Phase 6 | 0/4 | ⏳ PENDING | Deployment |
| Phase 7 | 0/2 | ⏳ PENDING | Documentation |

## 🎯 Next Steps

1. **Manual Code Integration** (Phase 3 & 4):
   - Add dashboard handlers to `handlers_autotrade.py`
   - Register handlers in `bot.py`
   - Integrate mode switching in `autotrade_engine.py`

2. **Testing** (Phase 5):
   - Unit tests for TradingModeManager
   - Unit tests for ScalpingEngine
   - Integration tests for full flow
   - Demo user testing (24 hours)

3. **Deployment** (Phase 6):
   - Run database migration on VPS
   - Deploy code files
   - Restart service
   - Monitor for errors

4. **Documentation** (Phase 7):
   - User documentation (`/scalping_help` command)
   - Developer documentation
   - Update README

## 📝 Notes

- All core modules (Phase 1 & 2) are complete and ready
- Dashboard integration requires manual code edits to existing files
- Engine integration is straightforward - just add mode check in `start_engine()`
- Database migration is safe - adds column with default value
- Rollback is possible - migration script includes rollback commands

## ⚠️ Important

- Test on local/staging environment first
- Backup database before migration
- Monitor logs after deployment
- Start with demo users for beta testing
- Keep rollback script ready

---

**Implementation Date:** 2024  
**Status:** Core modules complete, integration pending  
**Estimated Completion:** Phase 3-4 manual edits (~2-3 hours)
