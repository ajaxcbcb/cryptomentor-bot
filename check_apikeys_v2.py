"""Test API keys - loads env properly before any imports."""
import os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')

# Verify env loaded
print(f"SUPABASE_SERVICE_KEY: {bool(os.getenv('SUPABASE_SERVICE_KEY'))}")
print(f"ENCRYPTION_KEY: {bool(os.getenv('ENCRYPTION_KEY'))}")

import asyncio, sys
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

async def main():
    from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
    from supabase import create_client

    # Use service key directly — bypass supabase_repo module-level caching issue
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    s = create_client(url, key)
    print(f"Connected to Supabase, testing API keys...")

    from app.lib.crypto import decrypt
    from app.bitunix_autotrade_client import BitunixAutoTradeClient

    bot = Bot(token=BOT_TOKEN)

    keys_res = s.table('user_api_keys').select('*').execute()
    all_keys = [
        r for r in (keys_res.data or [])
        if r.get('telegram_id') and int(r.get('telegram_id', 0)) < 999999990
    ]
    print(f"\nFound {len(all_keys)} users with API keys\n")

    invalid_users = []
    valid_users = []

    for row in all_keys:
        uid = row['telegram_id']
        api_key = row.get('api_key', '')
        enc = row.get('api_secret_enc', '')
        hint = row.get('key_hint', '???')

        try:
            api_secret = decrypt(enc)
        except Exception as e:
            print(f"  UID {uid} | ...{hint} | ❌ DECRYPT FAILED: {e}")
            invalid_users.append({'uid': uid, 'reason': 'Decrypt failed — key may be corrupted'})
            continue

        try:
            client = BitunixAutoTradeClient(api_key=api_key, api_secret=api_secret)
            result = client.check_connection()
            if result.get('online'):
                print(f"  UID {uid} | ...{hint} | ✅ VALID")
                valid_users.append(uid)
            else:
                error = result.get('error', 'Connection failed')
                print(f"  UID {uid} | ...{hint} | ❌ INVALID: {error}")
                invalid_users.append({'uid': uid, 'reason': error})
        except Exception as e:
            print(f"  UID {uid} | ...{hint} | ❌ ERROR: {e}")
            invalid_users.append({'uid': uid, 'reason': str(e)[:80]})

    print(f"\n=== SUMMARY ===")
    print(f"  ✅ Valid: {len(valid_users)}")
    print(f"  ❌ Invalid: {len(invalid_users)}")

    if not invalid_users:
        print("  All API keys are valid — no notifications needed.")
        return

    dash_url = os.getenv('WEB_DASHBOARD_URL', 'https://cryptomentor.id')
    print(f"\n=== NOTIFYING {len(invalid_users)} USERS ===")

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
            print(f"  ❌ Failed to notify UID {uid}: {e}")
        await asyncio.sleep(0.3)

asyncio.run(main())
