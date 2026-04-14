"""
Force restart all stopped autotrade engines.
Updates status to 'active' and starts engine in bot memory.
Notifies each user that their engine has been restarted.
"""
import asyncio, sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

env_path = '/root/cryptomentor-bot/.env'
for line in open(env_path):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

from datetime import datetime

async def main():
    from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
    from app.supabase_repo import _client
    from app.lib.crypto import decrypt

    def get_user_api_keys(telegram_id):
        s2 = _client()
        res = s2.table('user_api_keys').select('*').eq('telegram_id', int(telegram_id)).limit(1).execute()
        if not res.data:
            return None
        row = res.data[0]
        try:
            secret = decrypt(row['api_secret_enc'])
        except Exception:
            return None
        return {
            'api_key': row['api_key'],
            'api_secret': secret,
            'exchange': row.get('exchange', 'bitunix'),
            'key_hint': row.get('key_hint', ''),
        }

    from app.autotrade_engine import start_engine, is_running
    from app.skills_repo import has_skill

    bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
    s = _client()

    # Get all stopped sessions that have API keys (verified users only)
    res = s.table('autotrade_sessions').select('*').eq('status', 'stopped').execute()
    stopped = [
        sess for sess in (res.data or [])
        if sess.get('telegram_id') and int(sess.get('telegram_id', 0)) < 999999990
    ]

    print(f"Found {len(stopped)} stopped sessions")

    restarted = 0
    no_keys = 0
    failed = 0

    for sess in stopped:
        uid = int(sess['telegram_id'])
        amount = float(sess.get('initial_deposit') or sess.get('current_balance') or 10)
        leverage = int(sess.get('leverage') or 10)
        trading_mode = sess.get('trading_mode', 'scalping')
        exchange_id = 'bitunix'

        # Check API keys
        keys = get_user_api_keys(uid)
        if not keys:
            print(f"  ⏭️  UID {uid} — no API keys, skipping")
            no_keys += 1
            continue

        # Skip if already running
        if is_running(uid):
            print(f"  ✅ UID {uid} — already running, just update DB status")
            s.table('autotrade_sessions').update({
                'status': 'active',
                'engine_active': True,
                'updated_at': datetime.utcnow().isoformat(),
            }).eq('telegram_id', uid).execute()
            restarted += 1
            continue

        try:
            # Update DB status to active first
            s.table('autotrade_sessions').update({
                'status': 'active',
                'engine_active': True,
                'updated_at': datetime.utcnow().isoformat(),
            }).eq('telegram_id', uid).execute()

            # Start engine in memory
            is_premium = has_skill(uid, 'dual_tp_rr3')
            start_engine(
                bot=bot,
                user_id=uid,
                api_key=keys['api_key'],
                api_secret=keys['api_secret'],
                amount=amount,
                leverage=leverage,
                notify_chat_id=uid,
                is_premium=is_premium,
                silent=True,
                exchange_id=exchange_id,
            )

            # Notify user
            dash_url = os.getenv('WEB_DASHBOARD_URL', 'https://cryptomentor.id')
            await bot.send_message(
                chat_id=uid,
                text=(
                    "🔄 <b>AutoTrade Engine Restarted</b>\n\n"
                    "Your engine was found inactive and has been automatically restarted by the system.\n\n"
                    f"📊 Mode: <b>{trading_mode.title()}</b>\n"
                    f"💰 Capital: <b>{amount} USDT</b>\n"
                    f"⚡ Leverage: <b>{leverage}x</b>\n\n"
                    "Your engine is now active and trading. "
                    "Use the dashboard or /autotrade to check status."
                ),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📊 Dashboard", url=dash_url)
                ]])
            )

            print(f"  ✅ UID {uid} — engine restarted ({trading_mode}, {amount} USDT, {leverage}x)")
            restarted += 1
            await asyncio.sleep(0.5)  # small delay between restarts

        except Exception as e:
            print(f"  ❌ UID {uid} — failed: {e}")
            # Revert status back to stopped on failure
            s.table('autotrade_sessions').update({
                'status': 'stopped',
                'engine_active': False,
                'updated_at': datetime.utcnow().isoformat(),
            }).eq('telegram_id', uid).execute()
            failed += 1

    print(f"\n=== DONE ===")
    print(f"  ✅ Restarted: {restarted}")
    print(f"  ⏭️  No API keys: {no_keys}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📊 Total processed: {len(stopped)}")

asyncio.run(main())
