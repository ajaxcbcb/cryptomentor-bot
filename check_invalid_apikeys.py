"""
Test API key validity for all users by calling Bitunix API.
Notify users with invalid/failed keys to re-enter them.
"""
import asyncio, sys, os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

async def main():
    from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
    from app.supabase_repo import _client
    from app.lib.crypto import decrypt
    from app.bitunix_autotrade_client import BitunixAutoTradeClient

    bot = Bot(token=BOT_TOKEN)
    s = _client()

    # Get all users with API keys
    keys_res = s.table('user_api_keys').select('*').execute()
    all_keys = [
        r for r in (keys_res.data or [])
        if r.get('telegram_id') and int(r.get('telegram_id', 0)) < 999999990
    ]
    print(f"Testing {len(all_keys)} users' API keys...\n")

    invalid_users = []
    valid_users = []

    for row in all_keys:
        uid = row['telegram_id']
        api_key = row.get('api_key', '')
        enc = row.get('api_secret_enc', '')
        hint = row.get('key_hint', '???')

        # Decrypt secret
        try:
            api_secret = decrypt(enc)
        except Exception as e:
            print(f"  UID {uid} | hint=...{hint} | ❌ DECRYPT FAILED: {e}")
            invalid_users.append({'uid': uid, 'reason': 'decrypt_failed'})
            continue

        # Test connection to Bitunix
        try:
            client = BitunixAutoTradeClient(api_key=api_key, api_secret=api_secret)
            result = client.check_connection()
            if result.get('online'):
                print(f"  UID {uid} | hint=...{hint} | ✅ VALID")
                valid_users.append(uid)
            else:
                error = result.get('error', 'Connection failed')
                print(f"  UID {uid} | hint=...{hint} | ❌ INVALID: {error}")
                invalid_users.append({'uid': uid, 'reason': error})
        except Exception as e:
            print(f"  UID {uid} | hint=...{hint} | ❌ ERROR: {e}")
            invalid_users.append({'uid': uid, 'reason': str(e)})

    print(f"\n=== SUMMARY ===")
    print(f"  ✅ Valid: {len(valid_users)}")
    print(f"  ❌ Invalid/Failed: {len(invalid_users)}")

    if not invalid_users:
        print("  All API keys are valid!")
        return

    print(f"\n=== NOTIFYING {len(invalid_users)} USERS ===")
    dash_url = os.getenv('WEB_DASHBOARD_URL', 'https://cryptomentor.id')

    for u in invalid_users:
        uid = u['uid']
        reason = u['reason']
        try:
            await bot.send_message(
                chat_id=uid,
                text=(
                    "⚠️ <b>API Key Issue Detected</b>\n\n"
                    "Your Bitunix API key appears to be invalid or has expired. "
                    "Your AutoTrade engine cannot run until this is fixed.\n\n"
                    "<b>Please re-enter your API key:</b>\n"
                    "1. Go to Bitunix → Profile → API Management\n"
                    "2. Create a new API key with <b>Trade</b> permission\n"
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
            print(f"  ❌ Failed to notify UID {uid}: {e}")
        await asyncio.sleep(0.3)

asyncio.run(main())
