"""
Bot Skills Handler
Menu untuk melihat dan membeli skill premium per-item.
Diakses dari dashboard AutoTrade via tombol "🧠 Bot Skills".
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from app.skills_repo import SKILL_CATALOG, get_user_skills, has_skill, purchase_skill
from app.supabase_repo import get_user_by_tid


# ─────────────────────────────────────────────
#  Menu utama skill
# ─────────────────────────────────────────────

async def callback_skills_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    await _show_skills_menu(query, user_id)


async def _show_skills_menu(query, user_id: int):
    from app.skills_repo import _is_privileged
    owned = get_user_skills(user_id)
    privileged = _is_privileged(user_id)

    # Ambil credits user
    try:
        user = get_user_by_tid(user_id)
        credits = user.get("credits", 0) if user else 0
    except Exception:
        credits = 0

    if privileged:
        lines = ["🧠 <b>Bot Skills</b>\n",
                 "👑 <b>Semua skill aktif</b> — kamu adalah admin atau user premium.\n"]
    else:
        lines = ["🧠 <b>Bot Skills</b>\n",
                 f"💳 Credits kamu: <b>{credits}</b>\n",
                 "Beli skill untuk upgrade kemampuan AutoTrade bot kamu secara permanen.\n"]

    buttons = []
    for skill_id, skill in SKILL_CATALOG.items():
        owned_tag = " ✅" if skill_id in owned else ""
        price_tag = "Owned" if skill_id in owned else f"{skill['price_credits']} Credits"
        lines.append(
            f"{skill['emoji']} <b>{skill['name']}</b>{owned_tag}\n"
            f"   {skill['description'].splitlines()[0]}\n"
            f"   💰 {price_tag}\n"
        )
        if skill_id not in owned:
            buttons.append([InlineKeyboardButton(
                f"{skill['emoji']} Beli {skill['name']} — {skill['price_credits']} Credits",
                callback_data=f"skill_buy:{skill_id}"
            )])

    if not buttons:
        lines.append("\n🎉 Kamu sudah memiliki semua skill yang tersedia!")

    buttons.append([InlineKeyboardButton("🔙 Kembali ke AutoTrade", callback_data="at_back_dashboard")])

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ─────────────────────────────────────────────
#  Detail skill sebelum beli
# ─────────────────────────────────────────────

async def callback_skill_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    skill_id = query.data.split(":", 1)[1]

    if skill_id not in SKILL_CATALOG:
        await query.answer("Skill tidak ditemukan.", show_alert=True)
        return

    skill = SKILL_CATALOG[skill_id]

    if has_skill(user_id, skill_id):
        await query.answer("Kamu sudah memiliki skill ini! ✅", show_alert=True)
        return

    try:
        user = get_user_by_tid(user_id)
        credits = user.get("credits", 0) if user else 0
    except Exception:
        credits = 0

    enough = credits >= skill["price_credits"]
    confirm_btn = (
        InlineKeyboardButton(
            f"✅ Konfirmasi Beli — {skill['price_credits']} Credits",
            callback_data=f"skill_confirm:{skill_id}"
        ) if enough else
        InlineKeyboardButton("❌ Credits tidak cukup", callback_data="skill_nocredits")
    )

    await query.edit_message_text(
        f"{skill['emoji']} <b>{skill['name']}</b>\n\n"
        f"{skill['description']}\n\n"
        f"💰 Harga: <b>{skill['price_credits']} Credits</b>\n"
        f"💳 Credits kamu: <b>{credits}</b>\n"
        f"{'✅ Cukup untuk membeli' if enough else '❌ Credits tidak cukup — top up dulu'}\n\n"
        f"⚠️ Pembelian bersifat <b>permanen</b> dan tidak dapat dikembalikan.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [confirm_btn],
            [InlineKeyboardButton("🔙 Kembali", callback_data="skills_menu")],
        ])
    )


async def callback_skill_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    skill_id = query.data.split(":", 1)[1]

    result = purchase_skill(user_id, skill_id)

    if result["success"]:
        skill = SKILL_CATALOG.get(skill_id, {})
        await query.edit_message_text(
            f"🎉 <b>Skill Aktif!</b>\n\n"
            f"{skill.get('emoji','🧠')} <b>{skill.get('name', skill_id)}</b> berhasil diaktifkan.\n\n"
            f"{result['message']}\n\n"
            f"Skill ini akan aktif otomatis saat kamu menjalankan AutoTrade berikutnya.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali ke Skills", callback_data="skills_menu")],
                [InlineKeyboardButton("🤖 Ke AutoTrade",      callback_data="at_back_dashboard")],
            ])
        )
    else:
        await query.edit_message_text(
            f"❌ <b>Gagal membeli skill</b>\n\n{result['message']}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="skills_menu")],
            ])
        )


async def callback_skill_nocredits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(
        "Credits tidak cukup. Top up credits dulu melalui menu Portfolio & Credits.",
        show_alert=True
    )


# ─────────────────────────────────────────────
#  Register handlers
# ─────────────────────────────────────────────

def register_skills_handlers(application):
    application.add_handler(CallbackQueryHandler(callback_skills_menu,   pattern=r"^skills_menu$"))
    application.add_handler(CallbackQueryHandler(callback_skill_buy,     pattern=r"^skill_buy:"))
    application.add_handler(CallbackQueryHandler(callback_skill_confirm, pattern=r"^skill_confirm:"))
    application.add_handler(CallbackQueryHandler(callback_skill_nocredits, pattern=r"^skill_nocredits$"))
