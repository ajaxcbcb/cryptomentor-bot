# Button-Based Menu System - Integration Guide

## Overview
A complete InlineKeyboard menu system that makes all bot commands accessible via buttons instead of typing. **Fully backward compatible** with existing slash commands.

---

## Quick Integration (3 Steps)

### Step 1: Import the menu handler in `bot.py`
```python
from menu_handler import register_menu_handlers, build_main_menu
```

### Step 2: Register handlers in bot setup
```python
async def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register menu handlers
    register_menu_handlers(application)
    
    # ... rest of your handlers ...
    application.run_polling()
```

### Step 3: Add /menu command to show main menu
```python
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    await update.message.reply_text(
        "🎯 **CryptoMentor AI - Main Menu**\n\nChoose a category:",
        reply_markup=build_main_menu(),
        parse_mode='Markdown'
    )

# Register the command
application.add_handler(CommandHandler("menu", handle_menu))
```

---

## Menu Structure

```
📱 MAIN MENU
├── 📈 Price & Market
│   ├── 🔹 Check Price → /price
│   ├── 🌍 Market Overview → /market
│   └── 🔙 Back
│
├── 🧠 Trading Analysis
│   ├── 📊 Spot Analysis (SnD) → /analyze
│   ├── 📉 Futures Analysis (SnD) → /futures
│   └── 🔙 Back
│
├── 🚀 Futures Signals
│   ├── 🔥 Multi-Coin Signals → /futures_signals
│   ├── 👑 Auto Signal Info (Lifetime)
│   └── 🔙 Back
│
├── 💼 Portfolio & Credits
│   ├── 📂 My Portfolio → /portfolio
│   ├── ➕ Add Coin → /add_coin (step-by-step)
│   ├── 💳 Check Credits → /credits
│   ├── ⭐ Upgrade Premium → /subscribe
│   └── 🔙 Back
│
├── 👑 Premium & Referral
│   ├── 🎁 Referral Program → /referral
│   ├── 💰 Premium Earnings → /premium_earnings
│   └── 🔙 Back
│
├── 🤖 Ask AI
│   ├── 💬 Ask CryptoMentor AI → /ask_ai
│   └── 🔙 Back
│
└── ⚙️ Settings
    ├── 🌐 Change Language
    └── 🔙 Back
```

---

## How It Works

### Flow Example: /price via buttons

1. User presses **📈 Price & Market**
2. Sees submenu with options
3. Presses **🔹 Check Price**
4. System shows quick symbol buttons (BTC, ETH, SOL, etc)
5. User selects symbol → Calls `/price BTCUSDT` internally
6. Returns to main menu on finish

### Multi-step Example: /add_coin

1. User presses **💼 Portfolio**
2. User presses **➕ Add Coin**
3. Prompted for symbol (button grid)
4. User selects (e.g., BTC)
5. Prompted for amount (text input)
6. User types amount
7. Coin added to portfolio

---

## Mapping to Existing Commands

| Button | Triggers | Command | Credits |
|--------|----------|---------|---------|
| Check Price | `check_price_callback()` | `/price SYMBOL` | FREE |
| Market Overview | `market_overview_callback()` | `/market` | FREE |
| Spot Analysis | `spot_analysis_callback()` | `/analyze SYMBOL` | 20 |
| Futures Analysis | `futures_analysis_callback()` | `/futures SYMBOL` | 20 |
| Multi-Coin Signals | `multi_coin_signals_callback()` | `/futures_signals` | 20 |
| My Portfolio | `my_portfolio_callback()` | `/portfolio` | FREE |
| Add Coin | `add_coin_callback()` | `/add_coin SYMBOL AMOUNT` | FREE |
| Check Credits | `check_credits_callback()` | `/credits` | FREE |
| Upgrade Premium | `upgrade_premium_callback()` | `/subscribe` | — |
| Referral Program | `referral_program_callback()` | `/referral` | FREE |
| Premium Earnings | `premium_earnings_callback()` | `/premium_earnings` | FREE |
| Ask AI | `ask_cryptomentor_callback()` | `/ask_ai QUESTION` | 10 |
| Change Language | `change_language_callback()` | `/language LANG` | FREE |

---

## Implementation Pattern

Each button callback follows this pattern:

```python
async def your_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Remove loading animation
    
    # Option 1: Show submenu
    await query.edit_message_text(
        text="Submenu title",
        reply_markup=build_your_submenu(),
        parse_mode='Markdown'
    )
    
    # Option 2: Call existing command handler
    context.user_data['action'] = 'your_action'
    # Then your command handler uses context.user_data['action']
    
    # Option 3: For multi-step input
    context.user_data['step'] = 'symbol'
    context.user_data['awaiting_input'] = True
```

---

## Handling Command Integration

### Pattern 1: Callback → Command Handler
```python
async def check_price_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['action'] = 'price'
    # Show symbol buttons...

# In your command handler:
async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get('action')
    symbol = context.user_data.get('symbol')
    
    if action == 'price' and symbol:
        # Process button-triggered price check
    elif update.message:
        # Process /price command
```

### Pattern 2: Direct Callback Execution
```python
async def my_portfolio_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Call your portfolio function directly
    await show_portfolio(update, context)
```

---

## UX Best Practices

✅ **DO**
- Show quick buttons for common symbols (BTC, ETH, SOL)
- Use emoji for visual clarity
- Step-by-step input for complex actions
- Always provide "Back" buttons
- Show loading message during processing
- Validate input before processing

❌ **DON'T**
- Remove slash commands (keep backward compatibility)
- Too many buttons in one menu (max 3 rows = 6 buttons)
- Confusing navigation (always show path back to main menu)
- Technical error messages (use friendly language)
- Long waits without feedback

---

## Code Structure

### Constants (callback routing)
```python
MAIN_MENU = "main_menu"
PRICE_MARKET = "price_market"
CHECK_PRICE = "check_price"
# etc...
```

### Menu Builders
```python
def build_main_menu() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(...)]]
    return InlineKeyboardMarkup(keyboard)
```

### Callbacks
```python
async def price_market_callback(...):
    # Show submenu or trigger action
```

### Registration
```python
def register_menu_handlers(application):
    application.add_handler(
        CallbackQueryHandler(callback_func, pattern=PATTERN)
    )
```

---

## Handling User Input States

The menu system uses `context.user_data` to track state:

```python
# Symbol input waiting
context.user_data['awaiting_symbol'] = True
context.user_data['symbol'] = 'BTCUSDT'

# Amount input waiting  
context.user_data['awaiting_amount'] = True
context.user_data['amount'] = '1.5'

# Action tracking
context.user_data['action'] = 'add_coin'
context.user_data['step'] = 'amount'
```

In your message handler:
```python
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_symbol'):
        symbol = update.message.text.upper()
        context.user_data['symbol'] = symbol
        # Next step...
    
    elif context.user_data.get('awaiting_amount'):
        amount = update.message.text
        symbol = context.user_data['symbol']
        # Process /add_coin symbol amount
```

---

## Scalability Notes

✅ **This design scales because:**
1. Callback data is string-based (no data size limits)
2. Modular menu builders (easy to add new submenus)
3. Clear separation of concerns (menus ≠ logic)
4. Symbol buttons can be dynamic (fetch from API)
5. Easy to add new categories/commands

🔧 **To add a new command:**
1. Create callback function
2. Add button to appropriate menu
3. Register callback in `register_menu_handlers()`
4. Call existing command handler or implement logic

---

## Example: Add New "Alert" Feature

```python
# 1. Add constant
PRICE_ALERTS = "price_alerts"

# 2. Add to menu builder
def build_portfolio_menu():
    keyboard = [
        [InlineKeyboardButton("🔔 Price Alerts", callback_data=PRICE_ALERTS)],
        # ... others
    ]

# 3. Create callback
async def price_alerts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Show alerts menu

# 4. Register
application.add_handler(
    CallbackQueryHandler(price_alerts_callback, pattern=f"^{PRICE_ALERTS}$")
)
```

---

## Testing

```python
# Test each menu opens correctly
# Test buttons navigate to submenus
# Test back buttons work
# Test command execution works
# Test fallback to slash commands
# Test mobile responsiveness
```

---

## Files

- `menu_handler.py` - All menu logic
- `MENU_INTEGRATION_GUIDE.md` - This file
- `bot.py` - Add `register_menu_handlers()` call here

---

**Status**: Ready to integrate. Fully backward compatible with existing commands.
