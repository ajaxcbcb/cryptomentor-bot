"""Resend pending UID verification notifications to all admins."""
import asyncio, sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

env_path = '/root/cryptomentor-bot/.env'
for line in open(env_path):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

PENDING = [
    {"tg_id": 985106924,  "bitunix_uid": "932385197", "submitted": "2026-04-09"},
    {"tg_id": 5187148337, "bitunix_uid": "629866114", "submitted": "2026-04-09"},
    {"tg_id": 1306878013, "bitunix_uid": "184889197", "submitted": "2026-04-09"},
    {"tg_id": 1087836223, "bitunix_uid": "341862124", "submitted": "2026-04-10"},
]

ADMIN_IDS = [1187119989, 7675185179]

async def main():
    from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
    bot = Bot(token=BOT_TOKEN)

    for p in PENDING:
        tg_id = p['tg_id']
        uid = p['bitunix_uid']
        submitted = p['submitted']
        msg = (
            f"🔔 <b>Pending UID Verification (Resent)</b>\n\n"
            f"User ID: <code>{tg_id}</code>\n"
            f"Bitunix UID: <code>{uid}</code>\n"
            f"Submitted: {submitted}\n\n"
            f"Please approve or reject this user."
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"uid_acc_{tg_id}"),
            InlineKeyboardButton("❌ Reject",  callback_data=f"uid_reject_{tg_id}"),
        ]])
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(chat_id=admin_id, text=msg, parse_mode='HTML', reply_markup=keyboard)
                print(f"  ✅ Sent UID {uid} (user {tg_id}) to admin {admin_id}")
            except Exception as e:
                print(f"  ❌ Failed to send to admin {admin_id}: {e}")
        await asyncio.sleep(0.3)

asyncio.run(main())
