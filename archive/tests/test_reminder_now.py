"""
Test: kirim reminder autotrade sekarang juga (tanpa tunggu scheduler).
Jalankan di VPS: python3 test_reminder_now.py
"""
import asyncio
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Load .env dari folder Bismillah
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BISMILLAH_DIR = os.path.join(SCRIPT_DIR, 'Bismillah')
sys.path.insert(0, BISMILLAH_DIR)

from dotenv import load_dotenv
# Coba beberapa lokasi .env
for env_candidate in [
    os.path.join(BISMILLAH_DIR, '.env'),
    os.path.join(SCRIPT_DIR, '.env'),
]:
    if os.path.exists(env_candidate):
        print(f"Loading .env from: {env_candidate}")
        load_dotenv(env_candidate, override=True)
        break
else:
    print("WARNING: .env tidak ditemukan, pakai environment variables yang ada")

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN tidak ditemukan di .env")
        return

    print(f"🤖 Bot token: ...{token[-10:]}")

    # --- 1. Cek koneksi Supabase & hitung user ---
    print("\n🔍 Mengecek Supabase...")
    try:
        from app.supabase_repo import _client
        s = _client()

        total_users = s.table("users").select("telegram_id", count="exact").execute()
        print(f"✅ Total user di DB: {total_users.count}")

        at_sessions = s.table("autotrade_sessions").select("telegram_id", count="exact").execute()
        print(f"✅ User dengan autotrade session: {at_sessions.count}")

        # Cek tabel reminder log
        try:
            log_check = s.table("autotrade_reminder_log").select("id", count="exact").execute()
            print(f"✅ Tabel autotrade_reminder_log ada, records: {log_check.count}")
        except Exception as e:
            print(f"❌ Tabel autotrade_reminder_log BELUM ADA atau error: {e}")
            print("   → Jalankan SQL di Supabase dulu!")
            return

    except Exception as e:
        print(f"❌ Supabase error: {e}")
        return

    # --- 2. Kirim reminder ---
    print("\n📤 Mengirim reminder sekarang...\n")
    from telegram import Bot
    from app.autotrade_reminder import send_autotrade_reminders

    bot = Bot(token=token)
    await send_autotrade_reminders(bot)
    print("\n✅ Selesai!")

if __name__ == "__main__":
    asyncio.run(main())
