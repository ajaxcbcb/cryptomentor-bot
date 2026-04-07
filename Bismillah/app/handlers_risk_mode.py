"""
Risk Mode Selection Handlers
Handles dual mode risk management (Recommended vs Manual)
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.supabase_repo import (
    get_risk_mode, set_risk_mode, 
    get_risk_per_trade, set_risk_per_trade
)
from app.ui_components import (
    progress_indicator,
    comparison_card,
    loading_message,
    success_message,
)


async def callback_choose_risk_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show risk mode selection after API key setup.
    User chooses between Rekomendasi (risk-based) or Manual (fixed margin).
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Add progress indicator
    progress = progress_indicator(3, 4, "Risk Management")
    
    # Get current balance if available
    try:
        from app.handlers_autotrade import get_autotrade_session
        session = get_autotrade_session(user_id)
        balance = session.get("initial_deposit", 0) if session else 0
        balance_text = f"\n💰 Your Balance: ${balance:.2f}\n" if balance > 0 else ""
    except:
        balance_text = ""
    
    # Build comparison cards
    recommended_card = comparison_card(
        title="RECOMMENDED",
        emoji="🌟",
        pros=[
            "Auto margin calculation",
            "Safe compounding",
            "Account protection",
            "Great for beginners"
        ],
        badge="✨ 95% user pilih ini"
    )
    
    manual_card = comparison_card(
        title="MANUAL",
        emoji="⚙️",
        pros=[
            "Full control",
            "Fixed position size"
        ],
        cons=[
            "Requires experience",
            "Higher risk"
        ]
    )
    
    text = f"{progress}\n\n"
    text += "🎯 <b>Select Trading Mode</b>\n"
    text += f"{balance_text}\n"
    text += recommended_card + "\n"
    text += manual_card + "\n"
    text += "💡 <b>Our Recommendation:</b> Choose Recommended for best results!\n"
    
    keyboard = [
        [InlineKeyboardButton("🌟 Choose Recommended", callback_data="at_mode_risk_based")],
        [InlineKeyboardButton("⚙️ Choose Manual", callback_data="at_mode_manual")],
        [InlineKeyboardButton("« Back", callback_data="at_start")],
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def callback_mode_risk_based(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    User selected risk-based mode.
    Save mode and show risk % selection.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Save risk mode
    set_risk_mode(user_id, "risk_based")
    
    # Get balance for display
    try:
        from app.handlers_autotrade import get_autotrade_session
        session = get_autotrade_session(user_id)
        balance = session.get("initial_deposit", 0) if session else 100
    except:
        balance = 100
    
    # Calculate risk amounts for each option
    risk_1 = balance * 0.01
    risk_2 = balance * 0.02
    risk_3 = balance * 0.03
    risk_5 = balance * 0.05
    
    text = (
        "🎯 <b>Select Risk Per Trade</b>\n\n"
        f"💰 Your Balance: ${balance:.2f}\n\n"
        "What % of your balance do you want to risk per trade?\n\n"
        
        f"🛡️ <b>1%</b> - Very Conservative\n"
        f"   Risk: ${risk_1:.2f} per trade\n"
        f"   Can survive 100+ losing trades\n\n"
        
        f"⚖️ <b>2%</b> - Moderate (RECOMMENDED)\n"
        f"   Risk: ${risk_2:.2f} per trade\n"
        f"   Can survive 50+ losing trades\n\n"
        
        f"⚡ <b>3%</b> - Aggressive\n"
        f"   Risk: ${risk_3:.2f} per trade\n"
        f"   Can survive 33+ losing trades\n\n"
        
        f"🔥 <b>5%</b> - Sangat Aggressive\n"
        f"   Risk: ${risk_5:.2f} per trade\n"
        f"   Can survive 20+ losing trades\n\n"
        
        "💡 <b>Recommendation:</b> Pilih 2% for balanced risk & reward yang optimal!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛡️ 1% (Conservative)", callback_data="at_risk_1")],
        [InlineKeyboardButton("⚖️ 2% (Recommended)", callback_data="at_risk_2")],
        [InlineKeyboardButton("⚡ 3% (Aggressive)", callback_data="at_risk_3")],
        [InlineKeyboardButton("🔥 5% (Sangat Aggressive)", callback_data="at_risk_5")],
        [InlineKeyboardButton("« Back", callback_data="at_choose_risk_mode")],
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def callback_select_risk_pct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    User selected risk percentage.
    Save it, set default leverage (10x), fetch balance, calculate margin, and save to DB.
    NO manual leverage or margin selection needed - system handles everything automatically.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Extract risk % from callback data
    risk_map = {
        "at_risk_1": 1.0,
        "at_risk_2": 2.0,
        "at_risk_3": 3.0,
        "at_risk_5": 5.0,
    }
    
    risk_pct = risk_map.get(query.data, 2.0)
    
    # Save risk percentage
    set_risk_per_trade(user_id, risk_pct)
    
    # Set default leverage automatically (10x recommended)
    DEFAULT_LEVERAGE = 10
    
    # Get real balance from exchange
    loading_text = loading_message(
        action="Fetching balance from exchange",
        tip="Risk-based mode helps you survive 50+ losing trades!"
    )
    loading = await query.edit_message_text(loading_text, parse_mode='HTML')
    
    try:
        from app.handlers_autotrade import get_user_api_keys
        import asyncio
        from app.exchange_registry import get_client as _get_client
        
        keys = get_user_api_keys(user_id)
        if not keys:
            await loading.edit_text("❌ API Key not found. Please setup API key first.")
            return
        
        exchange_id = keys.get("exchange", "bitunix")
        client = _get_client(exchange_id, keys['api_key'], keys['api_secret'])
        
        acc = await asyncio.wait_for(
            asyncio.to_thread(client.get_account_info),
            timeout=8.0
        )
        
        if not acc.get('success'):
            await loading.edit_text(
                f"❌ <b>Failed to fetch balance:</b> {acc.get('error', 'Unknown error')}\n\n"
                "Make sure your API Key is valid and try again.",
                parse_mode='HTML'
            )
            return
        
        balance = acc.get('available', 0)
        
        if balance < 10:
            await loading.edit_text(
                f"❌ <b>Insufficient balance</b>\n\n"
                f"Your Balance: ${balance:.2f} USDT\n"
                f"Minimum: $10 USDT\n\n"
                "Please top up your balance on the exchange.",
                parse_mode='HTML'
            )
            return
        
    except asyncio.TimeoutError:
        await loading.edit_text("❌ Timeout fetching balance. Try again.")
        return
    except Exception as e:
        await loading.edit_text(f"❌ Error: {str(e)[:150]}")
        return
    
    # Calculate risk amount
    risk_amount = balance * (risk_pct / 100)
    
    # Save to database (balance as initial_deposit, leverage, risk mode)
    from app.supabase_repo import _client
    from datetime import datetime, timezone
    
    try:
        s = _client()
        s.table("autotrade_sessions").upsert({
            "telegram_id": int(user_id),
            "initial_deposit": float(balance),  # Save full balance
            "leverage": DEFAULT_LEVERAGE,
            "risk_mode": "risk_based",
            "risk_per_trade": float(risk_pct),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }, on_conflict="telegram_id").execute()
    except Exception as e:
        print(f"Error saving to database: {e}")
        await loading.edit_text(f"❌ Error saving settings: {e}")
        return
    
    # Show confirmation with option to start trading
    success_text = success_message(
        "Setup Complete!",
        {
            "Mode": "🎯 Rekomendasi",
            "Balance": f"${balance:.2f} USDT",
            "Risk per trade": f"{risk_pct}% (${risk_amount:.2f})",
            "Leverage": f"{DEFAULT_LEVERAGE}x (auto)"
        }
    )
    
    text = (
        success_text + "\n"
        "💡 <b>How it works:</b>\n"
        "✅ System automatically calculates margin from balance\n"
        "✅ Position size adjusts automatically per trade\n"
        "✅ Safe compounding as balance grows\n"
        f"✅ Leverage {DEFAULT_LEVERAGE}x for balanced risk & reward\n\n"
        
        "📈 <b>Trade Example:</b>\n"
        "Entry: $50,000\n"
        "SL: $49,000 (2% away)\n"
        f"→ Risk: ${risk_amount:.2f} ({risk_pct}% dari balance)\n"
        "→ Position: Calculated automatically per trade\n"
        "→ Margin: Calculated automatically per trade\n\n"
        
        f"If SL hits: Loss ${risk_amount:.2f} ({risk_pct}% dari balance) ✅\n"
        "If TP hits: Profit varies by R:R\n\n"
        
        "💡 You can change risk % or leverage later in Settings"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Start AutoTrade", callback_data="at_start_engine_now")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="at_settings")],
        [InlineKeyboardButton("« Back", callback_data="at_mode_risk_based")],
    ]
    
    await loading.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def callback_mode_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    User selected manual mode.
    Save mode and show margin input instruction.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Save risk mode
    set_risk_mode(user_id, "manual")
    
    # Get balance
    try:
        from app.handlers_autotrade import get_autotrade_session
        session = get_autotrade_session(user_id)
        balance = session.get("initial_deposit", 0) if session else 100
    except:
        balance = 100
    
    # Calculate recommendations
    rec_min = balance * 0.05  # 5% of balance
    rec_max = balance * 0.10  # 10% of balance
    
    text = (
        "⚙️ <b>Set Margin Per Trade</b>\n\n"
        f"Mode: Manual (Fixed Margin)\n"
        f"Your Balance: ${balance:.2f}\n\n"
        
        "How much USDT do you want to use per trade?\n\n"
        
        "<b>Example:</b>\n"
        "• $5 - For balance $50-100\n"
        "• $10 - For balance $100-200\n"
        "• $20 - For balance $200-500\n\n"
        
        f"💡 <b>Recommended for your balance:</b>\n"
        f"   ${rec_min:.0f} - ${rec_max:.0f}\n\n"
        
        "⚠️ Do not use more than 10% of your balance\n\n"
        
        "Type margin amount in USDT (example: 10)"
    )
    
    keyboard = [
        [InlineKeyboardButton("« Back", callback_data="at_choose_risk_mode")],
    ]
    
    # Set state for text input
    context.user_data['awaiting_manual_margin'] = True
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    
    # Import conversation state from handlers_autotrade
    from app.handlers_autotrade import WAITING_MANUAL_MARGIN
    return WAITING_MANUAL_MARGIN


async def callback_switch_risk_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Switch between risk_based and manual mode from settings.
    Saves and restores margin and leverage to prevent inheritance conflicts.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get current mode
    current_mode = get_risk_mode(user_id)
    new_mode = "manual" if current_mode == "risk_based" else "risk_based"
    
    try:
        from app.handlers_autotrade import get_autotrade_session
        from app.supabase_repo import _client
        from app.risk_mode_manager import get_manual_settings, set_manual_settings
        import asyncio
        from app.handlers_autotrade import get_user_api_keys
        from app.exchange_registry import get_client as _get_client
        
        session = get_autotrade_session(user_id)
        s = _client()
        
        if session:
            current_amount = float(session.get("initial_deposit", 10))
            current_leverage = int(session.get("leverage", 10))
            
            if new_mode == "risk_based":
                # SWAPPING FROM MANUAL TO RISK_BASED
                # 1. Save current amount and leverage as manual preferences
                set_manual_settings(user_id, current_amount, current_leverage)
                
                # 2. Fetch live balance for risk_based
                balance = current_amount
                keys = get_user_api_keys(user_id)
                if keys:
                    try:
                        exchange_id = keys.get("exchange", "bitunix")
                        client = _get_client(exchange_id, keys['api_key'], keys['api_secret'])
                        acc = await asyncio.wait_for(asyncio.to_thread(client.get_account_info), timeout=5.0)
                        if acc.get('success'):
                            balance = float(acc.get('available', balance))
                    except Exception as e:
                        print(f"Warning catching balance: {e}")
                
                # 3. Update active session with full balance and default 10x
                s.table("autotrade_sessions").upsert({
                    "telegram_id": int(user_id),
                    "initial_deposit": float(balance),
                    "leverage": 10,
                    "risk_mode": "risk_based"
                }, on_conflict="telegram_id").execute()
                
            else:
                # SWAPPING FROM RISK_BASED TO MANUAL
                # 1. Load manual preferences
                man_margin, man_leverage = get_manual_settings(user_id)
                
                # 2. Update active session with manual preferences
                s.table("autotrade_sessions").upsert({
                    "telegram_id": int(user_id),
                    "initial_deposit": float(man_margin),
                    "leverage": int(man_leverage),
                    "risk_mode": "manual"
                }, on_conflict="telegram_id").execute()
        else:
            # Fallback if no session
            set_risk_mode(user_id, new_mode)
            
    except Exception as e:
        print(f"Mode switch error: {e}")
        set_risk_mode(user_id, new_mode)
    
    if new_mode == "risk_based":
        text = (
            "✅ <b>Mode Successfully Changed</b>\n\n"
            "New mode: 🎯 Recommended (Risk Per Trade)\n\n"
            "The system will automatically calculate margin from your balance.\n"
            "Position size will adjust automatically as balance increases.\n\n"
            "Please set your risk % in Settings → Risk Management"
        )
    else:
        text = (
            "✅ <b>Mode Successfully Changed</b>\n\n"
            "New mode: ⚙️ Manual (Fixed Margin)\n\n"
            "You need to manually set margin per trade.\n"
            "Position size will remain fixed.\n\n"
            "Please set your margin in Settings → Change Margin"
        )
    
    keyboard = [
        [InlineKeyboardButton("« Back to Settings", callback_data="at_settings")],
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

