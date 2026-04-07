"""
AutoTrade Daily Reminder
Kirim pesan harian ke user yang belum mendaftar autotrade.
"""

import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Pesan reminder dalam Bahasa Indonesia
REMINDER_MESSAGES = [
    # Hari 1 - Perkenalan
    (
        "🤖 <b>Tau nggak? Bot ini bisa trading otomatis buat kamu!</b>\n\n"
        "Selama ini kamu mungkin cuma pakai sinyal manual — tapi ada fitur yang lebih powerful:\n\n"
        "⚡ <b>AutoTrade</b> — bot yang kelola akun exchange kamu secara real-time.\n\n"
        "Cara kerjanya:\n"
        "• Kamu hubungkan API key exchange (Binance/Bybit/Bitunix)\n"
        "• Bot analisa market 24/7 pakai AI + indikator SMC\n"
        "• Kalau ada setup bagus, bot langsung buka posisi otomatis\n"
        "• SL/TP dikelola otomatis, kamu tinggal pantau profit\n\n"
        "💰 Modal minimal bisa mulai dari <b>10 USDT</b>\n"
        "🔒 Dana tetap di exchange kamu, bot hanya punya izin Trade\n\n"
        "Mau coba? Ketik /autotrade"
    ),
    # Hari 2 - Bukti & cara kerja
    (
        "📊 <b>Gimana cara AutoTrade bekerja?</b>\n\n"
        "Bot kamu terhubung langsung ke exchange via API Key.\n\n"
        "Setiap detik, bot:\n"
        "1️⃣ Scan 20+ pair crypto secara real-time\n"
        "2️⃣ Analisa struktur market (CHoCH, BOS, S&D Zone)\n"
        "3️⃣ Kalau confidence ≥75%, buka posisi otomatis\n"
        "4️⃣ Kelola SL/TP dan trailing stop\n"
        "5️⃣ Kirim notifikasi ke kamu setiap ada trade\n\n"
        "Kamu nggak perlu duduk depan chart seharian.\n"
        "Bot yang kerja, kamu yang terima hasilnya. 🎯\n\n"
        "Daftar sekarang: /autotrade"
    ),
    # Hari 3 - Keamanan
    (
        "🔒 <b>Aman nggak sih AutoTrade?</b>\n\n"
        "Pertanyaan yang wajar. Ini jawabannya:\n\n"
        "✅ Dana kamu <b>tetap di exchange</b> (Binance/Bybit/Bitunix)\n"
        "✅ API Key hanya punya izin <b>Trade</b> — tidak bisa withdraw\n"
        "✅ Kamu bisa <b>stop kapan saja</b> dengan satu klik\n"
        "✅ API Key dienkripsi AES-256 di server kami\n"
        "✅ Kamu tetap full control atas akun exchange kamu\n\n"
        "Sudah ada <b>15+ user aktif</b> yang pakai AutoTrade sekarang.\n\n"
        "Mau bergabung? /autotrade"
    ),
    # Hari 4 - CTA kuat
    (
        "🚀 <b>1.200+ user, tapi baru 15 yang pakai AutoTrade</b>\n\n"
        "Kamu salah satu dari mayoritas yang belum coba.\n\n"
        "Padahal setup-nya cuma 3 langkah:\n"
        "1. Daftar exchange via referral kami\n"
        "2. Buat API Key (Trade only)\n"
        "3. Masukkan ke bot → pilih modal → mulai!\n\n"
        "⏱ Total waktu setup: <b>~5 menit</b>\n\n"
        "Setelah itu bot yang kerja 24/7 buat kamu.\n\n"
        "Mulai sekarang: /autotrade"
    ),
]


def _get_reminder_index(telegram_id: int, sent_count: int) -> int:
    """Pilih pesan berdasarkan berapa kali sudah dikirim (cycling)."""
    return sent_count % len(REMINDER_MESSAGES)


async def send_autotrade_reminders(bot):
    """
    Kirim reminder ke semua user yang belum daftar autotrade.
    Dipanggil sekali sehari dari scheduler.
    """
    try:
        from app.supabase_repo import _client
        s = _client()

        # Ambil semua user yang BELUM punya autotrade session aktif
        # Pakai pagination untuk bypass limit 1000 Supabase
        all_users = []
        page_size = 1000
        offset = 0
        while True:
            res = s.table("users").select("telegram_id, first_name").range(offset, offset + page_size - 1).execute()
            batch = res.data or []
            all_users.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size

        if not all_users:
            logger.info("[Reminder] No users found")
            return

        # Ambil user yang sudah punya autotrade session (exclude mereka)
        at_res = s.table("autotrade_sessions").select("telegram_id").execute()
        at_user_ids = {row["telegram_id"] for row in (at_res.data or [])}

        # Filter: hanya user yang belum punya session sama sekali
        target_users = [u for u in all_users if u["telegram_id"] not in at_user_ids]

        logger.info(f"[Reminder] Total users: {len(all_users)}, AT users: {len(at_user_ids)}, Targets: {len(target_users)}")
        print(f"[Reminder] Total users: {len(all_users)}, AT users: {len(at_user_ids)}, Targets: {len(target_users)}")

        # Ambil log reminder hari ini untuk avoid duplikat (dengan pagination)
        today = datetime.utcnow().date().isoformat()
        sent_today_ids = set()
        offset2 = 0
        while True:
            res2 = s.table("autotrade_reminder_log").select("telegram_id").eq("sent_date", today).range(offset2, offset2 + 999).execute()
            batch2 = res2.data or []
            sent_today_ids.update(row["telegram_id"] for row in batch2)
            if len(batch2) < 1000:
                break
            offset2 += 1000

        # Ambil total count per user untuk pilih pesan yang tepat (dengan pagination)
        count_map = {}
        offset3 = 0
        while True:
            res3 = s.table("autotrade_reminder_log").select("telegram_id, count").range(offset3, offset3 + 999).execute()
            batch3 = res3.data or []
            for row in batch3:
                count_map[row["telegram_id"]] = row.get("count", 0)
            if len(batch3) < 1000:
                break
            offset3 += 1000

        sent = 0
        failed = 0
        skipped = 0

        for user in target_users:
            uid = user["telegram_id"]

            # Skip kalau sudah dapat reminder hari ini
            if uid in sent_today_ids:
                skipped += 1
                continue

            sent_count = count_map.get(uid, 0)
            msg_index = _get_reminder_index(uid, sent_count)
            message = REMINDER_MESSAGES[msg_index]

            try:
                await bot.send_message(
                    chat_id=uid,
                    text=message,
                    parse_mode='HTML',
                    reply_markup=_autotrade_keyboard()
                )

                # Log pengiriman
                _log_reminder_sent(s, uid, today)
                sent += 1

                # Rate limit: jangan spam Telegram API
                await asyncio.sleep(0.05)

            except Exception as e:
                err_str = str(e)
                # User block bot atau tidak valid — skip saja
                if any(x in err_str for x in ["blocked", "deactivated", "not found", "chat not found", "Forbidden"]):
                    failed += 1
                else:
                    logger.warning(f"[Reminder] Failed to send to {uid}: {e}")
                    print(f"[Reminder] ❌ Failed uid={uid}: {e}")
                    failed += 1

        logger.info(f"[Reminder] Done: {sent} sent, {skipped} skipped (already sent today), {failed} failed")
        print(f"[Reminder] Done: {sent} sent, {skipped} skipped (already sent today), {failed} failed")

    except Exception as e:
        logger.error(f"[Reminder] Task failed: {e}")
        print(f"[Reminder] ❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()


def _autotrade_keyboard():
    """Keyboard inline untuk reminder."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Daftar AutoTrade Sekarang", callback_data="at_start_onboarding")],
        [InlineKeyboardButton("ℹ️ Pelajari Lebih Lanjut", callback_data="at_learn_more")],
    ])


def _log_reminder_sent(s, telegram_id: int, today: str):
    """Catat bahwa reminder sudah dikirim ke user hari ini."""
    try:
        # Cek apakah sudah ada record untuk user ini
        existing = s.table("autotrade_reminder_log").select("id, count").eq("telegram_id", telegram_id).limit(1).execute()
        if existing.data:
            row = existing.data[0]
            s.table("autotrade_reminder_log").update({
                "sent_date": today,
                "count": row.get("count", 0) + 1,
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", row["id"]).execute()
        else:
            s.table("autotrade_reminder_log").insert({
                "telegram_id": telegram_id,
                "sent_date": today,
                "count": 1,
                "updated_at": datetime.utcnow().isoformat(),
            }).execute()
    except Exception as e:
        logger.warning(f"[Reminder] Failed to log for {telegram_id}: {e}")
