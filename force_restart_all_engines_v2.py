"""
Force restart ALL engines — including users with API keys but no session row.
Creates session if missing, updates stopped sessions to active, starts engines.
"""
import asyncio, sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

env_path = '/root/cryptomentor-bot/.env'
for line in open(env_path):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

from datetime import datetime, timezone

SKIP_UIDS = {999999999, 999999998, 999999997, 500000025, 500000026}

async def main():
    from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
    from app.supabase_repo import _client
    from app.lib.crypto import decrypt
    from app.autotrade_engine import start_engine, is_running
    from app.skills_repo import has_skill

    bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
    s = _client()
    now_iso = datetime.now(timezone.utc).isoformat()
    dash_url = os.getenv('WEB_DASHBOARD_URL', 'https://cryptomentor.id')

    # ── 1. Get all users with API keys ────────────────────────────────
    keys_res = s.table('user_api_keys').select('telegram_id, api_key, api_secret_enc, key_hint, exchange').execute()
    all_keys = {
        r['telegram_id']: r for r in (keys_res.data or [])
        if r.get('telegram_id') and int(r.get('telegram_id', 0)) not in SKIP_UIDS
    }
    print(f"Found {len(all_keys)} users with API keys")

    # ── 2. Get existing sessions ──────────────────────────────────────
    sess_res = s.table('autotrade_sessions').select('*').execute()
    sessions_by_uid = {
        r['telegram_id']: r for r in (sess_res.data or [])
        if r.get('telegram_id') and int(r.get('telegram_id', 0)) not in SKIP_UIDS
    }
    print(f"Found {len(sessions_by_uid)} existing sessions")

    # ── 3. Get verified users (approved in user_verifications) ────────
    ver_res = s.table('user_verifications').select('telegram_id, status, bitunix_uid').execute()
    verified_uids = {
        r['telegram_id'] for r in (ver_res.data or [])
        if r.get('status') in ('approved', 'uid_verified', 'active', 'verified')
    }
    print(f"Found {len(verified_uids)} verified users")

    restarted = 0
    created = 0
    skipped_unverified = 0
    failed = 0

    for uid, key_row in all_keys.items():
        uid = int(uid)

        # Only restart verified users
        if uid not in verified_uids:
            print(f"  ⏭️  UID {uid} — not verified, skipping")
            skipped_unverified += 1
            continue

        # Decrypt API keys
        try:
            secret = decrypt(key_row['api_secret_enc'])
        except Exception as e:
            print(f"  ❌ UID {uid} — decrypt failed: {e}")
            failed += 1
            continue

        api_key = key_row['api_key']
        exchange_id = key_row.get('exchange', 'bitunix')

        # Get or create session
        sess = sessions_by_uid.get(uid)
        if sess:
            amount = float(sess.get('initial_deposit') or sess.get('current_balance') or 10)
            leverage = int(sess.get('leverage') or 10)
            trading_mode = sess.get('trading_mode', 'scalping')
        else:
            # No session — create with defaults
            amount = 10.0
            leverage = 10
            trading_mode = 'scalping'

        # Skip if already running
        if is_running(uid):
            print(f"  ✅ UID {uid} — already running")
            restarted += 1
            continue

        try:
            # Upsert session as active
            s.table('autotrade_sessions').upsert({
                'telegram_id': uid,
                'status': 'active',
                'engine_active': True,
                'initial_deposit': amount,
                'current_balance': amount,
                'leverage': leverage,
                'trading_mode': trading_mode,
                'updated_at': now_iso,
            }, on_conflict='telegram_id').execute()

            # Start engine
            is_premium = has_skill(uid, 'dual_tp_rr3')
            start_engine(
                bot=bot,
                user_id=uid,
                api_key=api_key,
                api_secret=secret,
                amount=amount,
                leverage=leverage,
                notify_chat_id=uid,
                is_premium=is_premium,
                silent=True,
                exchange_id=exchange_id,
            )

            action = "created & started" if not sess else "restarted"
            print(f"  ✅ UID {uid} — engine {action} ({trading_mode}, {amount} USDT, {leverage}x)")

            # Notify user
            await bot.send_message(
                chat_id=uid,
                text=(
                    "🔄 <b>AutoTrade Engine Restarted</b>\n\n"
                    "Your engine was found inactive and has been automatically restarted.\n\n"
                    f"📊 Mode: <b>{trading_mode.title()}</b>\n"
                    f"💰 Capital: <b>{amount} USDT</b>\n"
                    f"⚡ Leverage: <b>{leverage}x</b>\n\n"
                    "Your engine is now active. Use the dashboard or /autotrade to check status."
                ),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📊 Dashboard", url=dash_url)
                ]])
            )

            if not sess:
                created += 1
            else:
                restarted += 1

            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"  ❌ UID {uid} — failed: {e}")
            failed += 1

    print(f"\n=== DONE ===")
    print(f"  ✅ Restarted (existing session): {restarted}")
    print(f"  🆕 Created & started (new session): {created}")
    print(f"  ⏭️  Skipped (not verified): {skipped_unverified}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📊 Total API key users: {len(all_keys)}")

asyncio.run(main())
