"""
Admin handlers for Whitelabel bot.
/admin — dashboard + manual deposit balance via License API.
"""

import logging
import os
from datetime import datetime, timezone

import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, ConversationHandler,
    CallbackQueryHandler, filters,
)

logger = logging.getLogger(__name__)

WAITING_DEPOSIT_AMOUNT = 10  # kept for backward compat, no longer used

# ── helpers ────────────────────────────────────────────────────────

def _get_admin_ids() -> list[int]:
    from config import ADMIN_IDS
    return ADMIN_IDS


def _is_admin(user_id: int) -> bool:
    return user_id in _get_admin_ids()


def _license_api_url() -> str:
    return os.getenv("LICENSE_API_URL", "").rstrip("/")


def _wl_credentials() -> tuple[str, str]:
    return os.getenv("WL_ID", ""), os.getenv("WL_SECRET_KEY", "")


async def _fetch_license_info() -> dict | None:
    """Call License API /api/license/info to get deposit address and full info."""
    url = _license_api_url()
    wl_id, secret_key = _wl_credentials()
    if not url or not wl_id or not secret_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{url}/api/license/info",
                json={"wl_id": wl_id, "secret_key": secret_key},
            )
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logger.warning("_fetch_license_info error: %s", e)
    return None


async def _fetch_license_status() -> dict | None:
    """Call License API /api/license/check and return response dict."""
    url = _license_api_url()
    wl_id, secret_key = _wl_credentials()
    if not url or not wl_id or not secret_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{url}/api/license/check",
                json={"wl_id": wl_id, "secret_key": secret_key},
            )
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logger.warning("_fetch_license_status error: %s", e)
    return None


async def _deposit_balance(amount: float) -> dict:
    """
    Call License API /api/license/deposit to credit balance manually.
    Returns {"success": bool, "balance": float, "message": str}
    """
    url = _license_api_url()
    wl_id, secret_key = _wl_credentials()
    if not url or not wl_id or not secret_key:
        return {"success": False, "message": "License API not configured"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{url}/api/license/deposit",
                json={"wl_id": wl_id, "secret_key": secret_key, "amount": amount},
            )
            data = r.json()
            if r.status_code == 200:
                return {"success": True, "balance": data.get("balance", 0), "message": "OK"}
            return {"success": False, "message": data.get("error", f"HTTP {r.status_code}")}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ── /admin command ─────────────────────────────────────────────────

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not _is_admin(user_id):
        await update.message.reply_text("⛔ Access denied.")
        return ConversationHandler.END

    await update.message.reply_text("⏳ Fetching license status...")

    status = await _fetch_license_status()
    wl_id, _ = _wl_credentials()

    if status:
        valid       = status.get("valid", False)
        balance     = float(status.get("balance", 0))
        expires     = status.get("expires_in_days", 0)
        st          = status.get("status", "unknown")
        warning     = status.get("warning", False)

        status_icon = "✅" if valid else ("⚠️" if st == "grace_period" else "🚫")
        warn_line   = "\n⚠️ Low balance or expiring soon — top up recommended!" if warning else ""

        text = (
            f"🔐 <b>Admin Panel — License Status</b>\n\n"
            f"WL ID: <code>{wl_id}</code>\n"
            f"Status: {status_icon} <b>{st.upper()}</b>\n"
            f"Balance: <b>${balance:.2f} USDT</b>\n"
            f"Expires in: <b>{expires} days</b>"
            f"{warn_line}\n\n"
            f"Monthly fee: <b>$10 USDT</b>\n"
            f"Each $10 deposited = 1 month extension."
        )
    else:
        text = (
            f"🔐 <b>Admin Panel</b>\n\n"
            f"WL ID: <code>{wl_id}</code>\n"
            f"⚠️ Could not reach License API.\n"
            f"Balance and status unavailable."
        )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Deposit Balance", callback_data="admin_deposit")],
        [InlineKeyboardButton("🔄 Refresh Status",  callback_data="admin_refresh")],
    ])

    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)
    return ConversationHandler.END


# ── Refresh callback ───────────────────────────────────────────────

async def callback_admin_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Refreshing...")
    user_id = query.from_user.id
    if not _is_admin(user_id):
        await query.answer("⛔ Access denied.", show_alert=True)
        return

    status = await _fetch_license_status()
    wl_id, _ = _wl_credentials()

    if status:
        valid   = status.get("valid", False)
        balance = float(status.get("balance", 0))
        expires = status.get("expires_in_days", 0)
        st      = status.get("status", "unknown")
        warning = status.get("warning", False)

        status_icon = "✅" if valid else ("⚠️" if st == "grace_period" else "🚫")
        warn_line   = "\n⚠️ Low balance or expiring soon — top up recommended!" if warning else ""

        text = (
            f"🔐 <b>Admin Panel — License Status</b>\n\n"
            f"WL ID: <code>{wl_id}</code>\n"
            f"Status: {status_icon} <b>{st.upper()}</b>\n"
            f"Balance: <b>${balance:.2f} USDT</b>\n"
            f"Expires in: <b>{expires} days</b>"
            f"{warn_line}\n\n"
            f"Monthly fee: <b>$10 USDT</b>\n"
            f"Each $10 deposited = 1 month extension."
        )
    else:
        text = (
            f"🔐 <b>Admin Panel</b>\n\n"
            f"WL ID: <code>{wl_id}</code>\n"
            f"⚠️ Could not reach License API."
        )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Deposit Balance", callback_data="admin_deposit")],
        [InlineKeyboardButton("🔄 Refresh Status",  callback_data="admin_refresh")],
    ])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)


# ── Deposit flow ───────────────────────────────────────────────────

async def callback_admin_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not _is_admin(user_id):
        await query.answer("⛔ Access denied.", show_alert=True)
        return ConversationHandler.END

    await query.edit_message_text("⏳ Fetching deposit address...")

    info = await _fetch_license_info()

    if not info or not info.get("deposit_address"):
        await query.edit_message_text(
            "❌ <b>Could not fetch deposit address.</b>\n\n"
            "License API is unreachable. Please try again later.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Retry", callback_data="admin_deposit")],
                [InlineKeyboardButton("🔙 Back",  callback_data="admin_refresh")],
            ])
        )
        return ConversationHandler.END

    deposit_address = info["deposit_address"]
    balance         = float(info.get("balance", 0))
    monthly_fee     = float(info.get("monthly_fee", 10))
    network         = info.get("network", "BSC (BEP20)")
    token           = info.get("token", "USDT")

    months_remaining = int(balance // monthly_fee) if monthly_fee > 0 else 0

    text = (
        f"💰 <b>Deposit Balance</b>\n\n"
        f"Send <b>USDT</b> to the address below to top up your license balance.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 Network: <b>{network}</b>\n"
        f"💎 Token: <b>{token}</b>\n\n"
        f"📍 <b>Deposit Address:</b>\n"
        f"<code>{deposit_address}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💳 Current balance: <b>${balance:.2f} USDT</b>\n"
        f"📅 Monthly fee: <b>${monthly_fee:.0f} USDT/month</b>\n"
        f"⏳ Months remaining: <b>{months_remaining} month(s)</b>\n\n"
        f"⚡ <b>How it works:</b>\n"
        f"1. Copy the address above\n"
        f"2. Send USDT via <b>BSC Network (BEP20)</b>\n"
        f"3. Balance is credited automatically within 5–10 minutes\n"
        f"4. License renews automatically each month\n\n"
        f"⚠️ <b>Important:</b> Only use BSC/BEP20 network.\n"
        f"Do NOT use ETH, TRC20, or other networks."
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Check Balance", callback_data="admin_refresh")],
            [InlineKeyboardButton("🔙 Back",          callback_data="admin_refresh")],
        ])
    )
    return ConversationHandler.END


async def callback_admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Cancelled.")
    return ConversationHandler.END


# ── Register ───────────────────────────────────────────────────────

def register_admin_handlers(application):
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("admin", cmd_admin),
            CallbackQueryHandler(callback_admin_deposit, pattern="^admin_deposit$"),
        ],
        states={},
        fallbacks=[
            CallbackQueryHandler(callback_admin_cancel, pattern="^admin_cancel$"),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    application.add_handler(conv)
    application.add_handler(CallbackQueryHandler(callback_admin_refresh, pattern="^admin_refresh$"))

    logger.info("✅ Admin handlers registered")
