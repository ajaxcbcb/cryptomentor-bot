from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from datetime import datetime, timedelta, timezone
import asyncio

from app.lib.guards import admin_guard
from app.safe_send import safe_reply
from app.supabase_conn import upsert_user_tid, get_user_by_tid, health

_locks = {}
def _lock(uid: int) -> asyncio.Lock:
    if uid not in _locks:
        _locks[uid] = asyncio.Lock()
    return _locks[uid]

def _iso_days_from_now(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=int(days))).isoformat()

@admin_guard
async def cmd_setpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if len(context.args) != 2 or not context.args[0].isdigit():
        return await safe_reply(msg, "Format: /setpremium <userid> <days|lifetime>")

    tid = int(context.args[0])
    dur = context.args[1].lower().strip()

    ok, info = health()
    if not ok:
        await safe_reply(msg, f"⚠️ Supabase not ready: {info}\nTetap mencoba menulis...")

    async with _lock(tid):
        try:
            # 1) Write (UPSERT idempoten)
            if dur == "lifetime":
                upsert_user_tid(tid, is_premium=True, premium_until=None, banned=False)
            else:
                if not dur.isdigit() or int(dur) < 0:
                    return await safe_reply(msg, "days harus angka ≥ 0 atau 'lifetime'")
                until = _iso_days_from_now(int(dur))
                upsert_user_tid(tid, is_premium=True, premium_until=until, banned=False)

            # 2) Read-after-write verify (langsung dipakai fitur lain)
            ref = get_user_by_tid(tid) or {}
            good = bool(ref.get("is_premium")) and not ref.get("banned")
            if dur == "lifetime":
                dur_ok = (ref.get("premium_until") is None)
            else:
                want_date = _iso_days_from_now(int(dur))[:10]
                got = ref.get("premium_until")
                dur_ok = (got is None and int(dur)==0) or (isinstance(got, str) and got[:10] >= want_date)

            if good and dur_ok:
                return await safe_reply(msg, f"✅ Premium set untuk {tid}\n{ref}")
            return await safe_reply(msg, f"❌ Verify gagal. DB terbaca:\n{ref}\nCek index/rls/policy & coba lagi.")
        except Exception as e:
            return await safe_reply(msg, f"❌ Error setting premium: {e}")

@admin_guard
async def cmd_remove_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if len(context.args) != 1 or not context.args[0].isdigit():
        return await safe_reply(msg, "Format: /remove_premium <userid>")

    tid = int(context.args[0])

    async with _lock(tid):
        try:
            update_user_tid(tid, is_premium=False, premium_until=None)
            ref = get_user_by_tid(tid) or {}
            if not ref.get("is_premium"):
                return await safe_reply(msg, f"✅ Premium removed untuk {tid}")
            return await safe_reply(msg, f"❌ Gagal remove premium: {ref}")
        except Exception as e:
            return await safe_reply(msg, f"❌ Error removing premium: {e}")

@admin_guard
async def cmd_grant_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if len(context.args) != 2 or not context.args[0].isdigit() or not context.args[1].isdigit():
        return await safe_reply(msg, "Format: /grant_credits <userid> <amount>")

    tid = int(context.args[0])
    amount = int(context.args[1])

    async with _lock(tid):
        try:
            # Read current credits
            current = get_user_by_tid(tid) or {}
            current_credits = current.get("credits", 0)
            new_total = current_credits + amount

            # Update with new total
            upsert_user_tid(tid, credits=new_total)

            # Verify
            ref = get_user_by_tid(tid) or {}
            if ref.get("credits", 0) >= new_total:
                return await safe_reply(msg, f"✅ Credits granted untuk {tid}: {current_credits} → {new_total}")
            return await safe_reply(msg, f"❌ Gagal grant credits: {ref}")
        except Exception as e:
            return await safe_reply(msg, f"❌ Error granting credits: {e}")