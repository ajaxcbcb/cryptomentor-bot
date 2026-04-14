"""Notify users with issues."""
import os, asyncio, sys
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
DASH_URL = os.getenv('WEB_DASHBOARD_URL', 'https://cryptomentor.id')

LOW_BALANCE = [1156155004, 6004753307, 5366384434, 1969755249, 1265990951]
INVALID_KEY = [7338184122, 7972497694]

async def main():
    from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
    bot = Bot(token=BOT_TOKEN)

    # Notify low balance users
    for uid in LOW_BALANCE:
        try:
            await bot.send_message(
                chat_id=uid,
                text=(
                    "⚠️ <b>AutoTrade Paused — Zero Balance</b>\n\n"
                    "Your Bitunix account balance is <b>$0.00</b>. "
                    "Your AutoTrade engine cannot open trades without funds.\n\n"
                    "<b>To resume trading:</b>\n"
                    "1. Deposit USDT to your Bitunix account\n"
                    "2. Your engine will automatically start trading once funds are detected\n\n"
                    "Need help? Contact admin: @BillFarr"
                ),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📊 Dashboard", url=DASH_URL),
                    InlineKeyboardButton("💬 @BillFarr", url="https://t.me/BillFarr"),
                ]])
            )
            print(f"  ✅ Notified UID {uid} (low balance)")
        except Exception as e:
            print(f"  ❌ Failed UID {uid}: {e}")
        await asyncio.sleep(0.3)

    # Notify invalid API key users
    for uid in INVALID_KEY:
        try:
            await bot.send_message(
                chat_id=uid,
                text=(
                    "⚠️ <b>API Key Invalid</b>\n\n"
                    "Your Bitunix API key is invalid or your server IP is not whitelisted. "
                    "Your AutoTrade engine cannot run.\n\n"
                    "<b>How to fix:</b>\n"
                    "1. Go to Bitunix → Profile → API Management\n"
                    "2. Delete the old API key\n"
                    "3. Create a new one with <b>Trade</b> permission\n"
                    "4. Make sure <b>IP restriction is disabled</b> or whitelist our server IP\n"
                    "5. Update via: /autotrade → Settings → Change API Key\n\n"
                    "Need help? Contact admin: @BillFarr"
                ),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📊 Dashboard", url=DASH_URL),
                    InlineKeyboardButton("💬 @BillFarr", url="https://t.me/BillFarr"),
                ]])
            )
            print(f"  ✅ Notified UID {uid} (invalid API key)")
        except Exception as e:
            print(f"  ❌ Failed UID {uid}: {e}")
        await asyncio.sleep(0.3)

    print("Done.")

asyncio.run(main())
