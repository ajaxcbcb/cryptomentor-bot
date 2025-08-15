
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from app.lib.guards import admin_guard
from app.safe_send import safe_reply
from app.sb_client import get_view, health_users, project_url, upsert_users
import json, os
from datetime import datetime, timezone, timedelta

def _fmt_stats(d: dict) -> str:
    return (
        "📊 *Bot Statistics (Supabase)*\n"
        f"• Total Users: *{d.get('total_users',0)}*\n"
        f"• Premium Users: *{d.get('premium_users',0)}*\n"
        f"• Banned Users: *{d.get('banned_users',0)}*\n"
        f"• Active Today: *{d.get('active_today',0)}*\n"
        f"• Total Credits: *{d.get('total_credits',0)}*"
    )

@admin_guard
async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rows = get_view("v_bot_stats")
        stats = rows[0] if rows else {}
        await safe_reply(update.effective_message, _fmt_stats(stats), parse_mode="Markdown")
    except Exception as e:
        await safe_reply(update.effective_message, f"❌ /admin gagal baca v_bot_stats: {e}")

@admin_guard
async def cmd_sb_whereami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = project_url()
        ok, total, detail = health_users()
        await safe_reply(update.effective_message,
            f"🛰️ Supabase Project: {url}\n🗄️ Users table: {'OK' if ok else 'FAIL'} ({detail})\n📦 Rows: {total}")
    except Exception as e:
        await safe_reply(update.effective_message, f"❌ whereami: {e}")

@admin_guard
async def cmd_sb_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        rows = get_view("v_bot_stats")
        stats = rows[0] if rows else {}
        ok, total, detail = health_users()
        await safe_reply(update.effective_message,
            f"✅ Count: users_table_rows={total}\n" +
            _fmt_stats(stats), parse_mode="Markdown")
    except Exception as e:
        await safe_reply(update.effective_message, f"❌ sb_count: {e}")

def _parse_backup_rows(obj):
    """
    Terima format JSON berisi list user lama dan mapping ke kolom Supabase.
    Dukungan field umum: telegram_id, is_premium, lifetime, premium_until, credits, banned
    Jika lifetime=true → premium_until=None
    Jika premium_until angka (epoch) → konversi ke ISO UTC
    """
    out = []
    now = datetime.now(timezone.utc).isoformat()
    for it in obj:
        tid = int(it.get("telegram_id") or it.get("user_id") or it.get("id"))
        if not tid: continue
        is_p = bool(it.get("is_premium") or it.get("premium") or it.get("lifetime"))
        banned = bool(it.get("banned", False))
        credits = int(it.get("credits", 0))
        lifetime = bool(it.get("lifetime", False))
        until = it.get("premium_until")
        iso_until = None
        if lifetime:
            iso_until = None
        else:
            if until in (None, "", 0, "0"):
                iso_until = None
            else:
                try:
                    # mendukung ISO string langsung
                    if isinstance(until, str) and "T" in until:
                        iso_until = until
                    else:
                        # epoch (detik)
                        iso_until = datetime.fromtimestamp(int(until), tz=timezone.utc).isoformat()
                except Exception:
                    iso_until = None
        out.append({
            "telegram_id": tid,
            "is_premium": is_p,
            "premium_until": iso_until,
            "banned": banned,
            "credits": credits,
            "is_registered": True,
            "first_seen_at": now,
            "last_seen_at": now,
        })
    return out

@admin_guard
async def cmd_sb_restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /sb_restore <path.json>
    Contoh: /sb_restore premium_users_backup_20250802_130229.json
    """
    if not context.args:
        return await safe_reply(update.effective_message, "Format: /sb_restore <path.json>")
    path = " ".join(context.args).strip()
    if not os.path.exists(path):
        return await safe_reply(update.effective_message, f"❌ File tidak ditemukan: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        rows = _parse_backup_rows(data if isinstance(data, list) else data.get("users", []))
        if not rows:
            return await safe_reply(update.effective_message, "⚠️ Tidak ada row valid di file.")
        # batch kirim (idempoten) 500-an per chunk
        BATCH = 500
        total = 0
        for i in range(0, len(rows), BATCH):
            chunk = rows[i:i+BATCH]
            upsert_users(chunk)
            total += len(chunk)
        ok, after, detail = health_users()
        await safe_reply(update.effective_message,
            f"✅ Restore selesai. Upsert: {total} row.\nUsers table now: {after} rows ({'OK' if ok else 'WARN'}: {detail})")
    except Exception as e:
        await safe_reply(update.effective_message, f"❌ Restore gagal: {e}")

def register_admin_panel_handlers(application):
    application.add_handler(CommandHandler("admin", cmd_admin))
    application.add_handler(CommandHandler("sb_whereami", cmd_sb_whereami))
    application.add_handler(CommandHandler("sb_count", cmd_sb_count))
    return application.add_handler(CommandHandler("sb_restore", cmd_sb_restore))
