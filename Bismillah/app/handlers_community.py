"""
Community Partners System
Ketua komunitas bisa daftar sebagai partner dan punya link referral khusus.
Anggota yang masuk via link komunitas → verifikasi UID ke ketua komunitas, bukan admin.
"""

import re
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Conversation states
WAITING_COMMUNITY_NAME = 10
WAITING_COMMUNITY_CODE = 11
WAITING_BITUNIX_REF_CODE = 12


# ------------------------------------------------------------------ #
#  Supabase helpers                                                   #
# ------------------------------------------------------------------ #

def _db():
    from app.supabase_repo import _client
    return _client()


def get_community_by_code(code: str) -> Optional[Dict]:
    """Ambil data komunitas berdasarkan code."""
    try:
        res = _db().table("community_partners").select("*").eq("community_code", code.lower()).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"[Community] get_community_by_code error: {e}")
        return None


def get_community_by_leader(telegram_id: int) -> Optional[Dict]:
    """Ambil data komunitas berdasarkan telegram ID ketua."""
    try:
        res = _db().table("community_partners").select("*").eq("telegram_id", int(telegram_id)).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"[Community] get_community_by_leader error: {e}")
        return None


def _slugify(name: str) -> str:
    """Convert nama komunitas ke slug: 'Crypto Indo' → 'cryptoindo'"""
    slug = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
    return slug[:20]  # max 20 karakter


def _get_admin_ids() -> list:
    import os
    admin_ids = []
    for key in ['ADMIN1', 'ADMIN2', 'ADMIN3', 'ADMIN_IDS']:
        val = os.getenv(key, '')
        if not val:
            continue
        for part in val.split(','):
            part = part.strip()
            if part.isdigit():
                admin_ids.append(int(part))
    return list(set(admin_ids))


# ------------------------------------------------------------------ #
#  Entry: tombol Partners di dashboard autotrade                      #
# ------------------------------------------------------------------ #

async def callback_partners_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan menu partners dari dashboard autotrade."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Block demo users from accessing Community Partners
    from app.demo_users import is_demo_user
    if is_demo_user(user_id):
        await query.edit_message_text(
            "❌ <b>Access Denied</b>\n\n"
            "Community Partners feature is not available for demo accounts.\n\n"
            "Demo accounts are for testing purposes only and cannot access partner features.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="at_dashboard")]
            ])
        )
        return ConversationHandler.END

    # Check if user is verified (has approved UID)
    from app.handlers_autotrade import get_autotrade_session
    session = get_autotrade_session(user_id)
    
    if not session or session.get("status") not in ["uid_verified", "active"]:
        await query.edit_message_text(
            "❌ <b>Access Denied</b>\n\n"
            "Community Partners feature is only available for verified users.\n\n"
            "Please complete your registration and UID verification first:\n"
            "/autotrade",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="at_dashboard")]
            ])
        )
        return ConversationHandler.END

    # Cek apakah sudah punya komunitas
    existing = get_community_by_leader(user_id)

    if existing:
        status = existing.get("status", "pending")
        code = existing.get("community_code", "")
        name = existing.get("community_name", "")
        member_count = existing.get("member_count", 0)

        if status == "active":
            bot_username = (await context.bot.get_me()).username
            invite_link = f"https://t.me/{bot_username}?start=community_{code}"
            await query.edit_message_text(
                f"👥 <b>Community Partners — {name}</b>\n\n"
                f"✅ Status: <b>AKTIF</b>\n"
                f"🔑 Kode: <code>{code}</code>\n"
                f"👤 Anggota terdaftar: <b>{member_count}</b>\n\n"
                f"🔗 <b>Link Undangan Komunitas:</b>\n"
                f"<code>{invite_link}</code>\n\n"
                f"Bagikan link ini ke anggota komunitas kamu.\n"
                f"Saat mereka daftar autotrade, verifikasi UID akan dikirim ke kamu.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 Lihat Anggota", callback_data="community_members")],
                    [InlineKeyboardButton("🔙 Kembali", callback_data="at_dashboard")],
                ])
            )
        elif status == "pending":
            await query.edit_message_text(
                f"👥 <b>Community Partners</b>\n\n"
                f"⏳ Pendaftaran komunitas <b>{name}</b> sedang menunggu persetujuan admin.\n\n"
                f"Kamu akan mendapat notifikasi setelah disetujui.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Kembali", callback_data="at_dashboard")],
                ])
            )
        else:  # rejected
            await query.edit_message_text(
                f"👥 <b>Community Partners</b>\n\n"
                f"❌ Pendaftaran komunitas <b>{name}</b> ditolak.\n\n"
                f"Kamu bisa mendaftar ulang dengan nama komunitas yang berbeda.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Daftar Ulang", callback_data="community_register")],
                    [InlineKeyboardButton("🔙 Kembali", callback_data="at_dashboard")],
                ])
            )
    else:
        await query.edit_message_text(
            "👥 <b>Community Partners</b>\n\n"
            "Jadikan komunitas kamu sebagai partner CryptoMentor AI!\n\n"
            "✅ <b>Keuntungan menjadi Partner:</b>\n"
            "• Link referral eksklusif untuk komunitas kamu\n"
            "• Kamu yang approve/reject anggota komunitas\n"
            "• Pantau berapa anggota yang sudah aktif trading\n"
            "• Bantu komunitas kamu push trading volume\n\n"
            "Daftar sekarang — gratis!",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Daftar Komunitas", callback_data="community_register")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="at_dashboard")],
            ])
        )
    return ConversationHandler.END


async def callback_community_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mulai proses pendaftaran komunitas."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "👥 <b>Daftar Community Partners — Step 1/3</b>\n\n"
        "Masukkan <b>nama komunitas</b> kamu:\n\n"
        "Contoh: <code>Crypto Indo</code>, <code>Trader Pemula ID</code>\n\n"
        "⚠️ Nama komunitas akan digunakan sebagai kode link undangan.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Batal", callback_data="at_dashboard")]
        ])
    )
    return WAITING_COMMUNITY_NAME


async def receive_community_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima nama komunitas dari user."""
    name = update.message.text.strip()

    if len(name) < 3:
        await update.message.reply_text("❌ Nama komunitas minimal 3 karakter. Coba lagi:")
        return WAITING_COMMUNITY_NAME

    if len(name) > 50:
        await update.message.reply_text("❌ Nama komunitas maksimal 50 karakter. Coba lagi:")
        return WAITING_COMMUNITY_NAME

    # Generate kode dari nama
    code = _slugify(name)
    existing_code = get_community_by_code(code)
    if existing_code:
        import random
        code = code + str(random.randint(10, 99))

    context.user_data['community_name'] = name
    context.user_data['community_code'] = code

    await update.message.reply_text(
        "🔑 <b>Step 2/3 — Kode Referral Bitunix Komunitas</b>\n\n"
        "Masukkan <b>kode referral Bitunix</b> milik komunitas kamu.\n\n"
        "Ini adalah kode yang akan dipakai anggota komunitas saat daftar di Bitunix.\n"
        "Kamu bisa lihat kode referral kamu di:\n"
        "<b>Bitunix → Profile → Referral Program</b>\n\n"
        "Contoh: <code>ABC123</code>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Batal", callback_data="at_dashboard")]
        ])
    )
    return WAITING_BITUNIX_REF_CODE


async def receive_bitunix_ref_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima kode referral Bitunix komunitas."""
    ref_code = update.message.text.strip()

    if len(ref_code) < 2:
        await update.message.reply_text("❌ Kode referral tidak valid. Coba lagi:")
        return WAITING_BITUNIX_REF_CODE

    ref_url = f"https://www.bitunix.com/register?vipCode={ref_code}"
    context.user_data['bitunix_referral_code'] = ref_code
    context.user_data['bitunix_referral_url'] = ref_url

    await update.message.reply_text(
        "🆔 <b>Step 3/3 — UID Bitunix Kamu</b>\n\n"
        "Masukkan <b>UID Bitunix</b> kamu sebagai ketua komunitas.\n\n"
        "Ini untuk memudahkan admin memverifikasi bahwa kamu terdaftar di Bitunix.\n"
        "Cara cari UID: Login Bitunix → tap foto profil → UID tertera di bawah nama.\n\n"
        "Contoh: <code>123456789</code>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Batal", callback_data="at_dashboard")]
        ])
    )
    return WAITING_COMMUNITY_CODE  # reuse state untuk UID


async def receive_leader_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima UID Bitunix ketua komunitas, lalu tampilkan preview."""
    uid = update.message.text.strip()

    if not uid.isdigit() or len(uid) < 5:
        await update.message.reply_text("❌ UID tidak valid. Masukkan angka UID Bitunix kamu:")
        return WAITING_COMMUNITY_CODE

    context.user_data['leader_uid'] = uid

    name = context.user_data.get('community_name', '')
    code = context.user_data.get('community_code', '')
    ref_code = context.user_data.get('bitunix_referral_code', '')
    ref_url = context.user_data.get('bitunix_referral_url', '')

    bot_username = (await context.bot.get_me()).username
    preview_link = f"https://t.me/{bot_username}?start=community_{code}"

    await update.message.reply_text(
        f"✅ <b>Preview Pendaftaran Komunitas:</b>\n\n"
        f"📛 Nama: <b>{name}</b>\n"
        f"🔑 Kode Bot: <code>{code}</code>\n"
        f"🎟 Referral Bitunix: <code>{ref_code}</code>\n"
        f"🆔 UID Bitunix: <code>{uid}</code>\n"
        f"🔗 Link Undangan: <code>{preview_link}</code>\n\n"
        f"Anggota komunitas akan diarahkan daftar Bitunix via referral kamu.\n\n"
        f"Konfirmasi pendaftaran?",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Konfirmasi", callback_data="community_confirm")],
            [InlineKeyboardButton("🔄 Mulai Ulang", callback_data="community_register")],
            [InlineKeyboardButton("❌ Batal", callback_data="at_dashboard")],
        ])
    )
    return ConversationHandler.END


async def callback_community_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simpan pendaftaran komunitas dan notifikasi admin."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = query.from_user

    name = context.user_data.get('community_name', '')
    code = context.user_data.get('community_code', '')
    ref_code = context.user_data.get('bitunix_referral_code', '')
    ref_url = context.user_data.get('bitunix_referral_url', '')
    leader_uid = context.user_data.get('leader_uid', '')

    if not name or not code:
        await query.edit_message_text("❌ Session expired. Coba lagi dari /autotrade → Partners.")
        return ConversationHandler.END

    # Simpan ke Supabase
    try:
        _db().table("community_partners").upsert({
            "telegram_id": int(user_id),
            "community_name": name,
            "community_code": code,
            "bitunix_referral_code": ref_code,
            "bitunix_referral_url": ref_url,
            "bitunix_uid": leader_uid,
            "status": "pending",
            "member_count": 0,
            "updated_at": datetime.utcnow().isoformat(),
        }, on_conflict="telegram_id").execute()
    except Exception as e:
        await query.edit_message_text(f"❌ Gagal menyimpan: {e}")
        return ConversationHandler.END

    # Notifikasi admin
    username_display = f"@{user.username}" if user.username else f"#{user_id}"
    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ APPROVE", callback_data=f"community_acc_{user_id}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"community_reject_{user_id}"),
        ]
    ])
    admin_text = (
        f"🔔 <b>Pendaftaran Community Partner Baru</b>\n\n"
        f"👤 Ketua: <b>{user.full_name}</b> ({username_display})\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"📛 Nama Komunitas: <b>{name}</b>\n"
        f"🔑 Kode Bot: <code>{code}</code>\n"
        f"🎟 Referral Bitunix: <code>{ref_code}</code>\n"
        f"🆔 UID Bitunix Ketua: <code>{leader_uid}</code>\n\n"
        f"Verifikasi bahwa UID ini terdaftar di Bitunix, lalu approve atau reject:"
    )
    for admin_id in _get_admin_ids():
        try:
            await context.bot.send_message(
                chat_id=admin_id, text=admin_text,
                parse_mode='HTML', reply_markup=admin_keyboard
            )
        except Exception:
            pass

    await query.edit_message_text(
        f"⏳ <b>Pendaftaran Terkirim!</b>\n\n"
        f"📛 Komunitas: <b>{name}</b>\n"
        f"🔑 Kode: <code>{code}</code>\n\n"
        f"Admin akan mereview dan kamu akan mendapat notifikasi setelah disetujui.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Kembali ke Dashboard", callback_data="at_dashboard")]
        ])
    )
    return ConversationHandler.END


# ------------------------------------------------------------------ #
#  Admin: approve/reject komunitas                                    #
# ------------------------------------------------------------------ #

async def callback_community_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin approve komunitas."""
    query = update.callback_query
    await query.answer("✅ Komunitas di-approve")

    target_user_id = int(query.data.split("_")[-1])

    try:
        _db().table("community_partners").update({
            "status": "active",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("telegram_id", target_user_id).execute()
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")
        return

    # Ambil data komunitas
    community = get_community_by_leader(target_user_id)
    code = community.get("community_code", "") if community else ""
    name = community.get("community_name", "") if community else ""

    await query.edit_message_text(
        query.message.text + f"\n\n✅ <b>Approved by admin</b>",
        parse_mode='HTML'
    )

    # Notifikasi ketua komunitas
    try:
        bot_username = (await context.bot.get_me()).username
        invite_link = f"https://t.me/{bot_username}?start=community_{code}"
        ref_code = community.get("bitunix_referral_code", "") if community else ""
        ref_url = community.get("bitunix_referral_url", "") if community else ""
        await context.bot.send_message(
            chat_id=target_user_id,
            text=(
                f"🎉 <b>Komunitas Kamu Disetujui!</b>\n\n"
                f"📛 Nama: <b>{name}</b>\n"
                f"🔑 Kode Bot: <code>{code}</code>\n"
                f"🎟 Referral Bitunix: <code>{ref_code}</code>\n\n"
                f"🔗 <b>Link Undangan Komunitas:</b>\n"
                f"<code>{invite_link}</code>\n\n"
                f"Bagikan link ini ke anggota komunitas kamu.\n"
                f"Anggota akan diarahkan daftar Bitunix via referral kamu (<code>{ref_code}</code>).\n"
                f"Saat mereka submit UID, notifikasi akan dikirim ke kamu untuk di-approve."
            ),
            parse_mode='HTML'
        )
    except Exception:
        pass


async def callback_community_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin reject komunitas."""
    query = update.callback_query
    await query.answer("❌ Komunitas ditolak")

    target_user_id = int(query.data.split("_")[-1])

    try:
        _db().table("community_partners").update({
            "status": "rejected",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("telegram_id", target_user_id).execute()
    except Exception:
        pass

    await query.edit_message_text(
        query.message.text + f"\n\n❌ <b>Rejected by admin</b>",
        parse_mode='HTML'
    )

    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text="❌ <b>Pendaftaran komunitas kamu ditolak.</b>\n\nHubungi admin untuk informasi lebih lanjut.",
            parse_mode='HTML'
        )
    except Exception:
        pass


# ------------------------------------------------------------------ #
#  Community leader: approve/reject anggota                          #
# ------------------------------------------------------------------ #

async def callback_community_member_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ketua komunitas approve UID anggota."""
    query = update.callback_query
    await query.answer("✅ Anggota di-approve")

    target_user_id = int(query.data.split("_")[-1])

    # Update status di autotrade_sessions
    try:
        _db().table("autotrade_sessions").update({
            "status": "uid_verified",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("telegram_id", target_user_id).execute()
    except Exception as e:
        logger.error(f"[Community] approve member error: {e}")

    # Update member count
    leader_id = query.from_user.id
    try:
        community = get_community_by_leader(leader_id)
        if community:
            new_count = (community.get("member_count") or 0) + 1
            _db().table("community_partners").update({
                "member_count": new_count,
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("telegram_id", leader_id).execute()
    except Exception:
        pass

    await query.edit_message_text(
        query.message.text + f"\n\n✅ <b>Approved</b>",
        parse_mode='HTML'
    )

    # Notifikasi anggota
    try:
        from app.handlers_autotrade import get_user_api_keys
        existing_keys = get_user_api_keys(target_user_id)
        if existing_keys:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=(
                    "✅ <b>UID Kamu Sudah Diverifikasi!</b>\n\n"
                    "Akun Bitunix kamu sudah terkonfirmasi.\n\n"
                    "Ketik /autotrade untuk melanjutkan setup trading."
                ),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 Lanjutkan Setup Trading", callback_data="at_start_trade")]
                ])
            )
        else:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=(
                    "✅ <b>UID Kamu Sudah Diverifikasi!</b>\n\n"
                    "Sekarang setup API Key untuk mulai Auto Trade:"
                ),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔑 Setup API Key", callback_data="at_setup_key")]
                ])
            )
    except Exception:
        pass


async def callback_community_member_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ketua komunitas reject UID anggota."""
    query = update.callback_query
    await query.answer("❌ Anggota ditolak")

    target_user_id = int(query.data.split("_")[-1])

    try:
        _db().table("autotrade_sessions").update({
            "status": "uid_rejected",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("telegram_id", target_user_id).execute()
    except Exception:
        pass

    await query.edit_message_text(
        query.message.text + f"\n\n❌ <b>Rejected</b>",
        parse_mode='HTML'
    )

    try:
        from app.exchange_registry import get_exchange
        await context.bot.send_message(
            chat_id=target_user_id,
            text=(
                "❌ <b>UID Verification Rejected</b>\n\n"
                "UID kamu tidak terdeteksi terdaftar di bawah referral komunitas.\n\n"
                "Pastikan kamu mendaftar Bitunix menggunakan link dari komunitas kamu."
            ),
            parse_mode='HTML'
        )
    except Exception:
        pass


# ------------------------------------------------------------------ #
#  Register handlers                                                  #
# ------------------------------------------------------------------ #

def register_community_handlers(application):
    """Register semua community partner handlers."""
    from telegram.ext import ConversationHandler

    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(callback_community_register, pattern="^community_register$"),
        ],
        states={
            WAITING_COMMUNITY_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_community_name),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^at_dashboard$"),
            ],
            WAITING_BITUNIX_REF_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_bitunix_ref_code),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^at_dashboard$"),
            ],
            WAITING_COMMUNITY_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_leader_uid),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^at_dashboard$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^at_dashboard$"),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    application.add_handler(conv)
    application.add_handler(CallbackQueryHandler(callback_partners_menu,         pattern="^community_partners$"))
    application.add_handler(CallbackQueryHandler(callback_community_confirm,     pattern="^community_confirm$"))
    application.add_handler(CallbackQueryHandler(callback_community_acc,         pattern="^community_acc_\\d+$"))
    application.add_handler(CallbackQueryHandler(callback_community_reject,      pattern="^community_reject_\\d+$"))
    application.add_handler(CallbackQueryHandler(callback_community_member_acc,  pattern="^cmember_acc_\\d+$"))
    application.add_handler(CallbackQueryHandler(callback_community_member_reject, pattern="^cmember_reject_\\d+$"))

    print("✅ Community Partners handlers registered")
