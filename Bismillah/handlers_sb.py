#!/usr/bin/env python3
"""
Supabase handlers untuk CryptoMentor AI Bot
Updated dengan RPC integration dan diagnostik lengkap
"""

import os
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes

# Import Supabase modules
from app.supabase_conn import get_supabase_client, health
from app.sb_repo import (
    upsert_user_with_ref_optional, 
    set_premium_rpc, 
    stats_totals,
    user_exists
)

# Admin configuration
ADMIN_IDS = {int(x.strip()) for x in (os.getenv("ADMIN_IDS", "").split(",") if os.getenv("ADMIN_IDS") else [])}

async def handle_start_supabase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start with Supabase integration"""
    user = update.effective_user
    if not user:
        return

    # Parse referral from /start command
    ref_id = None
    if context.args and len(context.args) > 0:
        try:
            ref_id = int(context.args[0])
        except (ValueError, IndexError):
            ref_id = None

    try:
        # Upsert user to Supabase
        result = upsert_user_with_ref_optional(
            tg_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            referred_by=ref_id
        )

        welcome_msg = f"""👋 **Welcome to CryptoMentor AI!**

🆔 **User ID**: {user.id}
👤 **Username**: @{(user.username or '').lower()}
💰 **Credits**: {result.get('credits', 100)}
🔗 **Referred by**: {result.get('referred_by', 'None')}

**Available Commands:**
• `/price btc` - Get real-time price (FREE)
• `/analyze btc` - Technical analysis (20 credits)
• `/futures btc` - Futures signals (20 credits)
• `/help` - Show all commands

**Start trading with real-time data! 📈**"""

        await update.effective_message.reply_text(welcome_msg, parse_mode='Markdown')

    except Exception as e:
        error_msg = f"⚠️ **Registration Error**\n\n{str(e)}"
        if "Referral required" in str(e):
            error_msg += "\n\n💡 **Tip**: Use a referral link from existing user to register."

        await update.effective_message.reply_text(error_msg, parse_mode='Markdown')

async def handle_supabase_diag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /diag_supabase command"""
    user_id = update.effective_user.id if update.effective_user else 0

    # Check Supabase health
    ok, detail = health()

    # Get stats if connection is healthy
    total_users = premium_users = 0
    if ok:
        try:
            total_users, premium_users = stats_totals()
        except Exception as e:
            detail = f"stats_totals error: {e}"

    status_msg = f"""🔧 **Supabase Diagnostics**

**Connection Status**: {'✅ Healthy' if ok else '❌ Failed'}
**Details**: {detail}

**Database Stats**:
• Total Users: {total_users:,}
• Premium Users: {premium_users:,}
• Free Users: {total_users - premium_users:,}

**Environment**:
• SUPABASE_URL: {'✅ Set' if os.getenv('SUPABASE_URL') else '❌ Missing'}
• SUPABASE_SERVICE_KEY: {'✅ Set' if os.getenv('SUPABASE_SERVICE_KEY') else '❌ Missing'}
• REFERRAL_REQUIRED: {os.getenv('REFERRAL_REQUIRED', 'false')}
• WELCOME_CREDITS: {os.getenv('WELCOME_CREDITS', '100')}

**Your Access**: {'👑 Admin' if user_id in ADMIN_IDS else '👤 User'}"""

    await update.effective_message.reply_text(status_msg, parse_mode='Markdown')

async def cmd_sb_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sb_status command for Supabase diagnostics"""
    user_id = update.effective_user.id if update.effective_user else 0

    # Check if user is admin
    if user_id not in ADMIN_IDS:
        await update.effective_message.reply_text(f"❌ Admin only. Your ID: {user_id}")
        return

    # Check Supabase health
    ok, detail = health()

    # Get stats if connection is healthy
    total_users = premium_users = 0
    if ok:
        try:
            total_users, premium_users = stats_totals()
        except Exception as e:
            detail = f"stats_totals error: {e}"

    status_msg = f"""🔧 **Supabase Status**

**Connection**: {'✅ Healthy' if ok else '❌ Failed'}
**Details**: {detail}

**Stats**:
• Total Users: {total_users:,}
• Premium Users: {premium_users:,}

**Environment**:
• SUPABASE_URL: {'✅ Set' if os.getenv('SUPABASE_URL') else '❌ Missing'}
• SERVICE_KEY: {'✅ Set' if os.getenv('SUPABASE_SERVICE_KEY') else '❌ Missing'}"""

    await update.effective_message.reply_text(status_msg, parse_mode='Markdown')

async def handle_admin_set_premium_sb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /set_premium command with Supabase"""
    user_id = update.effective_user.id if update.effective_user else 0

    if user_id not in ADMIN_IDS:
        await update.effective_message.reply_text(f"❌ Admin only. Your ID: {user_id}")
        return

    if not context.args or len(context.args) < 2:
        await update.effective_message.reply_text(
            "**Usage**: `/set_premium <telegram_id> <lifetime|days|months> [value]`\n\n"
            "**Examples**:\n"
            "• `/set_premium 123456789 lifetime`\n"
            "• `/set_premium 123456789 days 30`\n"
            "• `/set_premium 123456789 months 3`",
            parse_mode='Markdown'
        )
        return

    try:
        target_id = int(context.args[0])
        duration_type = context.args[1].lower()
        duration_value = int(context.args[2]) if len(context.args) >= 3 and duration_type in ("days", "months") else 0

        # Validate duration type
        if duration_type not in ("lifetime", "days", "months"):
            await update.effective_message.reply_text("❌ Duration type must be: lifetime, days, or months")
            return

        # Check if user exists
        if not user_exists(target_id):
            await update.effective_message.reply_text(f"❌ User {target_id} not found in database")
            return

        # Set premium
        set_premium_rpc(target_id, duration_type, duration_value)

        success_msg = f"✅ **Premium Updated**\n\n"
        success_msg += f"**User**: {target_id}\n"
        success_msg += f"**Type**: {duration_type}\n"
        if duration_value > 0:
            success_msg += f"**Duration**: {duration_value} {duration_type}\n"

        await update.effective_message.reply_text(success_msg, parse_mode='Markdown')

    except ValueError as e:
        await update.effective_message.reply_text(f"❌ Invalid input: {e}")
    except Exception as e:
        await update.effective_message.reply_text(f"⚠️ Failed to set premium: {e}")