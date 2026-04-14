"""Final test - import BitunixAutoTradeClient AFTER getting data."""
import os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')

import sys, asyncio
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

# Get all data FIRST before any heavy imports
from supabase import create_client
from app.lib.crypto import decrypt

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
s = create_client(url, key)

keys_res = s.table('user_api_keys').select('*').execute()
all_rows = [r for r in (keys_res.data or []) if r.get('telegram_id') and int(r.get('telegram_id',0)) < 999999990]
print(f"Loaded {len(all_rows)} users")

# Decrypt all first
users_to_test = []
decrypt_fail = []
for row in all_rows:
    uid = int(row['telegram_id'])
    hint = row.get('key_hint', '???')
    try:
        secret = decrypt(row.get('api_secret_enc', ''))
        users_to_test.append({'uid': uid, 'api_key': row['api_key'], 'api_secret': secret, 'hint': hint})
    except Exception as e:
        print(f"  UID {uid} | DECRYPT FAIL: {e}")
        decrypt_fail.append({'uid': uid, 'hint': hint, 'reason': 'Decrypt failed'})

print(f"Decrypt OK: {len(users_to_test)} | Fail: {len(decrypt_fail)}")

# NOW import BitunixAutoTradeClient
from app.bitunix_autotrade_client import BitunixAutoTradeClient

print("\n=== TESTING CONNECTIONS ===")
invalid_users = list(decrypt_fail)
valid_users = []

for u in users_to_test:
    uid = u['uid']
    hint = u['hint']
    try:
        client = BitunixAutoTradeClient(api_key=u['api_key'], api_secret=u['api_secret'])
        result = client.check_connection()
        if result.get('online'):
            print(f"  UID {uid} | ...{hint} | ✅ VALID")
            valid_users.append(uid)
        else:
            error = result.get('error', 'Connection failed')
            print(f"  UID {uid} | ...{hint} | ❌ INVALID: {error}")
            invalid_users.append({'uid': uid, 'hint': hint, 'reason': error})
    except Exception as e:
        print(f"  UID {uid} | ...{hint} | ❌ ERROR: {str(e)[:80]}")
        invalid_users.append({'uid': uid, 'hint': hint, 'reason': str(e)[:80]})

print(f"\n=== SUMMARY ===")
print(f"✅ Valid: {len(valid_users)}")
print(f"❌ Invalid: {len(invalid_users)}")

if not invalid_users:
    print("All API keys are valid!")
    sys.exit(0)

print("\nInvalid users:")
for u in invalid_users:
    print(f"  UID {u['uid']} | ...{u.get('hint','?')} | {u.get('reason','?')}")

# Send notifications
async def notify():
    from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
    bot = Bot(token=BOT_TOKEN)
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
            print(f"  ❌ Failed UID {uid}: {e}")
        await asyncio.sleep(0.3)

asyncio.run(notify())
