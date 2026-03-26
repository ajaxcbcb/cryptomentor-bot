"""
Whitelabel #1 — Entry Point
"""
import asyncio
import logging
import sys

# Inject crypto API keys WL#1 SEBELUM provider lain diimport
# Ini memastikan WL#1 tidak share rate limit dengan CryptoMentor utama
from app.providers.data_provider import inject_provider_env
inject_provider_env()

from telegram.ext import ApplicationBuilder, CommandHandler
from config import BOT_TOKEN

from app.license_guard import LicenseGuard

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set in .env")

    # ── License check sebelum bot start ──────────────────────────
    license_guard = LicenseGuard()
    ok = await license_guard.startup_check()
    if not ok:
        logger.error("License check failed — bot halted.")
        sys.exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ── Add license middleware to block users when suspended ────
    from app.license_middleware import LicenseMiddleware
    license_middleware = LicenseMiddleware(license_guard)
    app.add_handler(license_middleware, group=-1)  # group=-1 = runs before all other handlers
    logger.info("License middleware registered — will block users if license suspended")

    # Register basic handlers
    from app.handlers_basic import cmd_start, cmd_help, cmd_status, callback_start_autotrade, callback_show_help
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    
    # Register callback handlers for start screen
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(callback_start_autotrade, pattern="^start_autotrade$"))
    app.add_handler(CallbackQueryHandler(callback_show_help, pattern="^show_help$"))

    # Register autotrade handlers
    from app.handlers_autotrade import (
        cmd_autotrade,
        callback_confirm_referral,
        callback_why_referral,
        callback_setup_key,
        callback_change_key,
        callback_start_trade,
        receive_api_key,
        receive_api_secret,
        receive_trade_amount,
        receive_bitunix_uid,
        WAITING_API_KEY,
        WAITING_API_SECRET,
        WAITING_TRADE_AMOUNT,
        WAITING_LEVERAGE,
        WAITING_BITUNIX_UID,
    )
    from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler, filters

    autotrade_conv = ConversationHandler(
        entry_points=[CommandHandler("autotrade", cmd_autotrade)],
        states={
            WAITING_BITUNIX_UID:  [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_bitunix_uid)],
            WAITING_API_KEY:      [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_api_key)],
            WAITING_API_SECRET:   [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_api_secret)],
            WAITING_TRADE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_trade_amount)],
        },
        fallbacks=[CommandHandler("autotrade", cmd_autotrade)],
        allow_reentry=True,
    )

    app.add_handler(autotrade_conv)
    app.add_handler(CallbackQueryHandler(callback_confirm_referral, pattern="^at_confirm_referral$"))
    app.add_handler(CallbackQueryHandler(callback_why_referral,     pattern="^at_why_referral$"))
    app.add_handler(CallbackQueryHandler(callback_setup_key,        pattern="^at_setup_key$"))
    app.add_handler(CallbackQueryHandler(callback_change_key,       pattern="^at_change_key$"))
    app.add_handler(CallbackQueryHandler(callback_start_trade,      pattern="^at_start_trade$"))

    logger.info("Whitelabel #1 bot starting...")

    async with app:
        await app.start()
        # Schedule periodic license check loop
        asyncio.create_task(license_guard.periodic_check_loop())
        await app.updater.start_polling()
        # Run until interrupted
        await asyncio.Event().wait()
        await app.updater.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
