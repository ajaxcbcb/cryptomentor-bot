"""
Broadcast CryptoMentor AI 4.0 announcement to all users.
Run: python3 broadcast_v4.py
"""
import asyncio
import os
import sys

sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

env_path = '/root/cryptomentor-bot/.env'
for line in open(env_path):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

MESSAGE = (
    "🚀 <b>CryptoMentor AI 4.0 Is Live</b>\n\n"
    "Major upgrade complete. We've launched a full <b>Web Dashboard</b> — "
    "now you can manage everything from your browser, anytime.\n\n"
    "<b>What's new in 4.0:</b>\n"
    "<code>"
    "🌐 Full Web Dashboard at cryptomentor.id\n"
    "📊 Live portfolio & position tracking\n"
    "⚙️  Start/Stop engine directly from web\n"
    "📈 Real-time PnL & performance charts\n"
    "🎯 AI Signals with confluence analysis\n"
    "⚡ 1-Click trade execution from signals\n"
    "🤝 Referral Partner program\n"
    "🔒 Secure API key management\n"
    "📱 Mobile-friendly dark dashboard"
    "</code>\n\n"
    "✅ <b>CryptoMentor AI is now faster, smarter, and fully web-powered.</b>\n\n"
    "🌐 Dashboard: <a href=\"https://cryptomentor.id\">cryptomentor.id</a>\n"
    "🤖 Bot: @CryptoMentorAI_bot"
)

async def broadcast():
    from telegram import Bot
    from telegram.error import TelegramError

    from app.supabase_repo import _client
    s = _client()

    res = s.table('users').select('telegram_id').execute()
    users = res.data or []
    print(f"Broadcasting to {len(users)} users...")

    bot = Bot(token=BOT_TOKEN)
    sent = 0
    failed = 0

    for u in users:
        uid = u.get('telegram_id')
        if not uid:
            continue
        try:
            await bot.send_message(
                chat_id=int(uid),
                text=MESSAGE,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            sent += 1
            print(f"  ✅ Sent to {uid}")
            await asyncio.sleep(0.05)  # rate limit
        except TelegramError as e:
            failed += 1
            print(f"  ❌ Failed {uid}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ❌ Error {uid}: {e}")

    print(f"\nDone. Sent: {sent} | Failed: {failed}")

if __name__ == '__main__':
    asyncio.run(broadcast())
