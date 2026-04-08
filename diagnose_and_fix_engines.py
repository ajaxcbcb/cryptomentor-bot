#!/usr/bin/env python3
"""
Diagnose & Fix All User AutoTrade Engines
Run on VPS: python3 diagnose_and_fix_engines.py [--fix]

Flags:
  --fix       Auto-restart engines yang inactive tapi seharusnya running
  --fix-all   Fix + kirim notifikasi ke user
"""
import sys, os, asyncio, argparse
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')
os.chdir('/root/cryptomentor-bot/Bismillah')

from dotenv import load_dotenv
load_dotenv()

# ── Parse args ────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--fix', action='store_true', help='Auto-restart inactive engines')
parser.add_argument('--fix-all', action='store_true', help='Fix + notify users')
args = parser.parse_args()

DO_FIX    = args.fix or args.fix_all
DO_NOTIFY = args.fix_all

# ── Imports ───────────────────────────────────────────────────────────────────
from app.supabase_repo import _client
from app.autotrade_engine import is_running

s = _client()

# ── Fetch all sessions ────────────────────────────────────────────────────────
res = s.table("autotrade_sessions").select(
    "telegram_id,status,engine_active,trading_mode,initial_deposit,leverage,risk_mode,risk_per_trade,updated_at"
).execute()
sessions = res.data or []

# ── Fetch all API keys ────────────────────────────────────────────────────────
keys_res = s.table("user_api_keys").select(
    "telegram_id,exchange,api_key,api_secret_enc,key_hint"
).execute()
keys_map = {int(k['telegram_id']): k for k in (keys_res.data or [])}

print(f"\n{'='*70}")
print(f"  AUTOTRADE ENGINE DIAGNOSTIC REPORT")
print(f"{'='*70}")
print(f"  Total sessions: {len(sessions)}")
print(f"  Mode: {'FIX + NOTIFY' if DO_NOTIFY else 'FIX' if DO_FIX else 'DIAGNOSE ONLY'}")
print(f"{'='*70}\n")

# ── Categorize ────────────────────────────────────────────────────────────────
ok          = []   # active & running
broken      = []   # active status but engine NOT running
no_key      = []   # active but no API key
stopped     = []   # stopped by user (intentional)
pending     = []   # pending/rejected
zero_bal    = []   # active but deposit=0
other       = []

ACTIVE_STATUSES = ('active', 'uid_verified')

for row in sessions:
    uid        = int(row['telegram_id'])
    status     = row.get('status', 'unknown')
    deposit    = float(row.get('initial_deposit') or 0)
    mode       = row.get('trading_mode', 'swing')
    leverage   = int(row.get('leverage') or 10)
    risk_mode  = row.get('risk_mode', 'risk_based')
    risk_pct   = float(row.get('risk_per_trade') or 2.0)
    running    = is_running(uid)
    has_key    = uid in keys_map and bool(keys_map[uid].get('api_key'))
    exchange   = keys_map[uid].get('exchange', 'bitunix') if has_key else 'N/A'
    key_hint   = keys_map[uid].get('key_hint', '????') if has_key else 'MISSING'

    entry = {
        'uid': uid, 'status': status, 'deposit': deposit,
        'mode': mode, 'leverage': leverage, 'running': running,
        'has_key': has_key, 'exchange': exchange, 'key_hint': key_hint,
        'risk_mode': risk_mode, 'risk_pct': risk_pct,
        'updated_at': row.get('updated_at', '-'),
    }

    if status == 'stopped':
        stopped.append(entry)
    elif status in ('pending_verification', 'pending', 'uid_rejected'):
        pending.append(entry)
    elif status in ACTIVE_STATUSES:
        if deposit <= 0:
            zero_bal.append(entry)
        elif not has_key:
            no_key.append(entry)
        elif running:
            ok.append(entry)
        else:
            broken.append(entry)
    else:
        other.append(entry)

# ── Print summary ─────────────────────────────────────────────────────────────
print(f"✅  RUNNING OK:              {len(ok)}")
print(f"🔴  BROKEN (should run):     {len(broken)}")
print(f"🔑  NO API KEY:              {len(no_key)}")
print(f"💸  ZERO BALANCE:            {len(zero_bal)}")
print(f"🛑  STOPPED BY USER:         {len(stopped)}")
print(f"⏳  PENDING/REJECTED:        {len(pending)}")
print(f"❓  OTHER:                   {len(other)}")
print()

# ── Detail: Running OK ────────────────────────────────────────────────────────
if ok:
    print(f"{'─'*70}")
    print(f"✅  RUNNING ENGINES ({len(ok)}):")
    for e in ok:
        print(f"  uid={e['uid']} | {e['exchange']} | mode={e['mode']} | "
              f"deposit=${e['deposit']:.0f} | {e['leverage']}x | "
              f"risk={e['risk_mode']}({e['risk_pct']}%)")

# ── Detail: Broken ────────────────────────────────────────────────────────────
if broken:
    print(f"\n{'─'*70}")
    print(f"🔴  BROKEN ENGINES — ACTIVE BUT NOT RUNNING ({len(broken)}):")
    for e in broken:
        print(f"  uid={e['uid']} | {e['exchange']} | mode={e['mode']} | "
              f"deposit=${e['deposit']:.0f} | {e['leverage']}x | key=...{e['key_hint']} | "
              f"last_update={e['updated_at'][:19] if e['updated_at'] else '-'}")

# ── Detail: No API Key ────────────────────────────────────────────────────────
if no_key:
    print(f"\n{'─'*70}")
    print(f"🔑  NO API KEY ({len(no_key)}):")
    for e in no_key:
        print(f"  uid={e['uid']} | status={e['status']} | deposit=${e['deposit']:.0f}")

# ── Detail: Zero Balance ──────────────────────────────────────────────────────
if zero_bal:
    print(f"\n{'─'*70}")
    print(f"💸  ZERO/INVALID BALANCE ({len(zero_bal)}):")
    for e in zero_bal:
        print(f"  uid={e['uid']} | status={e['status']} | deposit=${e['deposit']:.0f}")

# ── Detail: Stopped ───────────────────────────────────────────────────────────
if stopped:
    print(f"\n{'─'*70}")
    print(f"🛑  STOPPED BY USER ({len(stopped)}):")
    for e in stopped:
        print(f"  uid={e['uid']} | {e['exchange']} | deposit=${e['deposit']:.0f}")

# ── Detail: Other ─────────────────────────────────────────────────────────────
if other:
    print(f"\n{'─'*70}")
    print(f"❓  OTHER STATUS ({len(other)}):")
    for e in other:
        print(f"  uid={e['uid']} | status={e['status']} | running={e['running']}")

# ── FIX: Restart broken engines ───────────────────────────────────────────────
if not broken:
    print(f"\n{'='*70}")
    print("✅  All active engines are running. No fix needed.")
    print(f"{'='*70}\n")
    sys.exit(0)

if not DO_FIX:
    print(f"\n{'='*70}")
    print(f"⚠️   {len(broken)} engine(s) need restart.")
    print(f"    Run with --fix to auto-restart, or --fix-all to also notify users.")
    print(f"{'='*70}\n")
    sys.exit(0)

# ── Auto-fix via engine_restore ───────────────────────────────────────────────
print(f"\n{'='*70}")
print(f"🔧  AUTO-FIX: Restarting {len(broken)} broken engine(s)...")
print(f"{'='*70}\n")

async def fix_engines():
    from telegram import Bot
    from app.engine_restore import restore_user_engine
    from app.lib.crypto import decrypt

    bot_token = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("❌  BOT_TOKEN not found in environment. Cannot restart engines.")
        return

    bot = Bot(token=bot_token)

    fixed   = []
    failed  = []

    for e in broken:
        uid = e['uid']
        raw_key = keys_map.get(uid)
        if not raw_key:
            print(f"  ❌ uid={uid} — no API key row, skip")
            failed.append(uid)
            continue

        try:
            api_secret = decrypt(raw_key['api_secret_enc'])
        except Exception as dec_err:
            print(f"  ❌ uid={uid} — decrypt failed: {dec_err}")
            failed.append(uid)
            continue

        keys = {
            'api_key':    raw_key['api_key'],
            'api_secret': api_secret,
            'exchange':   raw_key.get('exchange', 'bitunix'),
        }

        # Build session dict as expected by restore_user_engine
        session = {
            'telegram_id':    uid,
            'initial_deposit': e['deposit'],
            'leverage':        e['leverage'],
        }

        print(f"  🔄 Restarting uid={uid} ({e['exchange']}, ${e['deposit']:.0f}, {e['leverage']}x)...")
        try:
            success = restore_user_engine(bot, session, keys)
            if success:
                print(f"  ✅ uid={uid} — engine restarted")
                fixed.append(uid)

                if DO_NOTIFY:
                    try:
                        await bot.send_message(
                            chat_id=uid,
                            text=(
                                "🔄 <b>AutoTrade Engine Restarted</b>\n\n"
                                "✅ Engine kamu sempat berhenti dan sudah di-restart otomatis.\n\n"
                                "Bot kamu sekarang aktif kembali dan siap trading.\n"
                                "Gunakan /autotrade untuk cek status."
                            ),
                            parse_mode='HTML'
                        )
                    except Exception as notify_err:
                        print(f"     ⚠️  Notify failed: {notify_err}")
            else:
                print(f"  ❌ uid={uid} — restore_user_engine returned False")
                failed.append(uid)
        except Exception as ex:
            print(f"  ❌ uid={uid} — exception: {ex}")
            failed.append(uid)

    print(f"\n{'='*70}")
    print(f"  FIX SUMMARY:")
    print(f"  ✅ Fixed:  {len(fixed)} — {fixed}")
    print(f"  ❌ Failed: {len(failed)} — {failed}")
    print(f"{'='*70}\n")

asyncio.run(fix_engines())
