from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
import html
from supabase_conn import health, env_ok
from app.middlewares.ensure_weekly_sb import EnsureWeeklySBMiddleware
from app.routers.admin_set_credit_all import router as set_credit_all_router
from app.routers.admin_set_premium import router as set_premium_router

def _format_md_v2(text: str) -> str:
    """Escape all special characters for MarkdownV2"""
    return escape_markdown(text, version=2)

async def _safe_reply_status(message, raw_text: str):
    """
    Try to send as MarkdownV2 (escaped).
    If fails, fallback to HTML <pre> (escaped).
    If still fails, send plain text without parse mode.
    """
    # 1) MarkdownV2 (escaped)
    try:
        md2 = _format_md_v2(raw_text)
        await message.reply_text(md2, parse_mode=ParseMode.MARKDOWN_V2)
        return
    except Exception as e_md2:
        pass

    # 2) HTML <pre> (escaped)
    try:
        html_text = f"<pre>{html.escape(raw_text)}</pre>"
        await message.reply_text(html_text, parse_mode=ParseMode.HTML)
        return
    except Exception as e_html:
        pass

    # 3) Plain text fallback
    await message.reply_text(raw_text)

async def cmd_sb_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only command to check Supabase connection status"""
    uid = update.effective_user.id if update and update.effective_user else None

    # Dynamic admin check with environment variable fallback
    import os
    admin_ids = set()

    # Check ADMIN1, ADMIN2, etc.
    for i in range(1, 10):
        env_key = f'ADMIN{i}'
        admin_id_str = (os.getenv(env_key) or "").strip()

        # Fallback to old naming format
        if not admin_id_str and i <= 2:
            fallback_key = f'ADMIN{i}_USER_ID' if i > 1 else 'ADMIN_USER_ID'
            admin_id_str = (os.getenv(fallback_key) or "").strip()

        # Add to set if valid
        if admin_id_str and admin_id_str.lower() != "none":
            admin_ids.add(str(admin_id_str))

    # Check if user is admin (string comparison)
    is_admin = str(uid) in admin_ids

    if not is_admin:
        await update.effective_message.reply_text(
            f"❌ **Admin Access Required**\n\n"
            f"**Your ID**: {uid}\n"
            f"**Admin IDs**: {sorted(list(admin_ids)) if admin_ids else 'NONE CONFIGURED'}\n\n"
            f"⚙️ **Setup Instructions:**\n"
            f"1. Buka Secrets tab di Replit\n"
            f"2. Tambahkan `ADMIN1` = {uid}\n"
            f"3. Restart bot untuk apply changes\n\n"
            f"💡 Atau contact owner untuk menambahkan ID Anda ke admin list.",
            parse_mode='Markdown'
        )
        return

    # Use new admin panel builder
    from app.admin_status import build_admin_panel, build_supabase_diagnostics

    # Check if this is a diagnostic request
    if context.args and context.args[0] == 'diag':
        status_msg = build_supabase_diagnostics()
    else:
        # Get autosignal status (you can implement this based on your autosignal system)
        autosignals_running = False  # Replace with actual status check
        status_msg = build_admin_panel(autosignals_running=autosignals_running)

    await _safe_reply_status(update.effective_message, status_msg)

def register_handlers(dp):
    # Register middleware
    dp.message.middleware(EnsureWeeklySBMiddleware())
    dp.callback_query.middleware(EnsureWeeklySBMiddleware())

    # Register routers
    dp.include_router(set_credit_all_router)
    dp.include_router(set_premium_router)