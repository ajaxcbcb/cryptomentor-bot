
from telegram import Update
from telegram.ext import ContextTypes
from app.lib.guards import admin_guard
from app.autosignal import set_autosignal_enabled, autosignal_enabled, run_scan_once, SCAN_INTERVAL_SEC, TOP_N, MIN_CONFIDENCE, TIMEFRAME
from app.safe_send import safe_reply

@admin_guard
async def cmd_signal_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_autosignal_enabled(True)
    await safe_reply(update.effective_message, "✅ AutoSignal ON")

@admin_guard
async def cmd_signal_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_autosignal_enabled(False)
    await safe_reply(update.effective_message, "⏸️ AutoSignal OFF")

@admin_guard
async def cmd_signal_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(
        update.effective_message,
        f"🛰️ AutoSignal: {'ON' if autosignal_enabled() else 'OFF'}\n"
        f"Interval: {SCAN_INTERVAL_SEC//60}m (min 30m)\n"
        f"Top: {TOP_N} | TF: {TIMEFRAME} | MinConf: {MIN_CONFIDENCE}%"
    )

@admin_guard
async def cmd_signal_tick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = await run_scan_once(context.bot)
        await safe_reply(update.effective_message, f"⏱️ Manual scan completed: {res}")
    except Exception as e:
        await safe_reply(update.effective_message, f"❌ Manual scan failed: {str(e)}")️ Tick: {res}")
