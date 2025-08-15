
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from supabase_client import supabase_service
from app.lib.guards import admin_guard
from app.safe_send import safe_reply

@admin_guard
async def cmd_whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    rec = supabase_service.get_user(u.id)
    is_p = supabase_service.is_premium(u.id)
    await safe_reply(update.effective_message,
        f"👤 You: {u.id}\n"
        f"Premium: {is_p}\n"
        f"Record: {rec}")

@admin_guard
async def cmd_refresh_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        return await safe_reply(update.effective_message, "Format: /refresh_access <user_id>")
    tid = int(context.args[0])
    ok, detail = supabase_service.health()
    rec = supabase_service.get_user(tid)
    is_p = supabase_service.is_premium(tid)
    await safe_reply(update.effective_message,
        f"🩺 Health: {'OK' if ok else 'FAIL'} ({detail})\n"
        f"👤 User: {tid}\n"
        f"Premium: {is_p}\n"
        f"Record: {rec}")

def register_access_tools(application):
    application.add_handler(CommandHandler("whoami", cmd_whoami))
    application.add_handler(CommandHandler("refresh_access", cmd_refresh_access))
