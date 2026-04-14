"""Force start 3 approved users by updating their session status to active."""
import os, sys, asyncio
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

from supabase import create_client
from datetime import datetime, timezone

s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
DASH_URL = os.getenv('WEB_DASHBOARD_URL', 'https://cryptomentor.id')

# 3 approved users with stopped sessions
UIDS = [985106924, 5187148337, 1306878013]
now = datetime.now(timezone.utc).isoformat()

print("Updating sessions to active...")
for uid in UIDS:
    s.table('autotrade_sessions').update({
        'status': 'active',
        'engine_active': True,
        'updated_at': now,
    }).eq('telegram_id', uid).execute()
    print(f"  ✅ UID {uid} — session set to active")

async def notify():
    from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
    bot = Bot(token=BOT_TOKEN)
    for uid in UIDS:
        try:
            await bot.send_message(
                chat_id=uid,
                text=(
                    "🚀 <b>AutoTrade Engine Started!</b>\n\n"
                    "Your account has been verified and your AutoTrade engine is now active.\n\n"
                    "📊 Mode: <b>Scalping</b>\n"
                    "⚡ Leverage: <b>10x</b>\n\n"
                    "Your engine will start scanning for trade opportunities automatically.\n"
                    "Use the dashboard or /autotrade to monitor your trades."
                ),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📊 Dashboard", url=DASH_URL)
                ]])
            )
            print(f"  ✅ Notified UID {uid}")
        except Exception as e:
            print(f"  ❌ Failed UID {uid}: {e}")
        await asyncio.sleep(0.3)

asyncio.run(notify())
print("\nDone. Health check will start their engines within 2 minutes.")
