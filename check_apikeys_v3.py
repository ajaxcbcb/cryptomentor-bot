"""Minimal test - no app imports, direct supabase."""
import os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')

import asyncio, sys
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

from supabase import create_client
from app.lib.crypto import decrypt
from app.bitunix_autotrade_client import BitunixAutoTradeClient

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
s = create_client(url, key)

keys_res = s.table('user_api_keys').select('*').execute()
print(f"Found {len(keys_res.data or [])} users with API keys")

async def main():
    from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
    bot = Bot(token=BOT_TOKEN)

    invalid_users = []
    valid_users = []

    for row in (keys_res.data or []):
        uid = row.get('telegram_id')
        if not uid:
            continue
        uid = int(uid)
        if uid >= 999999990:
            continue
        api_key = row.get('api_key', '')
        enc = row.get('api_secret_enc', '')
        hint = row.get('key_hint', '???')

        try:
            api_secret = decrypt(enc)
        except Exception as e:
            print(f"  UID {uid} | ...{hint} | ❌ DECRYPT FAILED: {e}")
            invalid_users.append({'uid': uid, 'reason': 'Decrypt failed'})
            continue

        try:
            client = BitunixAutoTradeClient(api_key=api_key, api_secret=api_secret)
            # Run in thread with timeout to prevent hanging
            loop = asyncio.get_event_loop()
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, client.check_connection),
                    timeout=15.0
                )
            except asyncio.TimeoutError:
                print(f"  UID {uid} | ...{hint} | ❌ TIMEOUT (connection hung)")
                invalid_users.append({'uid': uid, 'reason': 'Connection timeout — API key may be invalid'})
                continue
            if result.get('online'):
                print(f"  UID {uid} | ...{hint} | ✅ VALID")
                valid_users.append(uid)
            else:
                error = result.get('error', 'Connection failed')
                print(f"  UID {uid} | ...{hint} | ❌ INVALID: {error}")
                invalid_users.append({'uid': uid, 'reason': error})
        except Exception as e:
            print(f"  UID {uid} | ...{hint} | ❌ ERROR: {str(e)[:60]}")
            invalid_users.append({'uid': uid, 'reason': str(e)[:60]})

    print(f"\n✅ Valid: {len(valid_users)} | ❌ Invalid: {len(invalid_users)}")

    if not invalid_users:
        print("All API keys are valid!")
        return

    dash_url = os.getenv('WEB_DASHBOARD_URL', 'https://cryptomentor.id')
    print(f"\nNotifying {len(invalid_users)} users...")
    for u in invalid_users:
        uid = u['uid']
        try:
            await bot.send_message(
                chat_id=uid,
                text=(
                    "⚠️ <b>API Key Issue Detected</b>\n\n"
                    "Your Bitunix API key appears to be invalid or has expired. "
                    "Your AutoTrade engine cannot run until this is fixed.\n\n"
                    "<b>How to fix:</b>\n"
                    "1. Go to Bitunix → Profile → API Management\n"
                    "2. Create a new API key with <b>Trade</b> permission enabled\n"
                    "3. Update it via: /autotrade → Settings → Change API Key\n"
                    "   or via the web dashboard\n\n"
                    "Need help? Contact admin: @BillFarr"
                ),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📊 Dashboard", url=dash_url),
                    InlineKeyboardButton("💬 @BillFarr", url="https://t.me/BillFarr"),
                ]])
            )
            print(f"  ✅ Notified UID {uid}")
        except Exception as e:
            print(f"  ❌ Failed UID {uid}: {e}")
        await asyncio.sleep(0.3)

asyncio.run(main())
