#!/usr/bin/env python3
"""Check auto mode status for all active users"""
import os, sys
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')
os.chdir('/root/cryptomentor-bot/Bismillah')

from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env', override=True)

# Fallback: read manually if dotenv fails
if not os.getenv('SUPABASE_URL'):
    with open('/root/cryptomentor-bot/.env') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()

from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
c = create_client(url, key)

print("=" * 60)
print("AUTOTRADE SESSIONS STATUS")
print("=" * 60)

sessions = c.table('autotrade_sessions').select(
    'telegram_id, status, engine_active, auto_mode_enabled, trading_mode'
).execute()

if not sessions.data:
    print("No sessions found!")
else:
    for s in sessions.data:
        print(f"  tg_id={s['telegram_id']} | status={s.get('status')} | "
              f"engine_active={s.get('engine_active')} | "
              f"auto_mode={s.get('auto_mode_enabled')} | "
              f"mode={s.get('trading_mode')}")

print()
print("=" * 60)
print("ACTIVE ENGINES (engine_active=True)")
print("=" * 60)

active = c.table('autotrade_sessions').select(
    'telegram_id, status, engine_active, auto_mode_enabled, trading_mode'
).eq('engine_active', True).execute()

print(f"Total active engines: {len(active.data) if active.data else 0}")
for s in (active.data or []):
    auto = s.get('auto_mode_enabled')
    mode = s.get('trading_mode', 'unknown')
    print(f"  tg_id={s['telegram_id']} | mode={mode} | auto_mode={auto}")

print()
print("=" * 60)
print("USERS WITH auto_mode_enabled=True")
print("=" * 60)

auto_users = c.table('autotrade_sessions').select(
    'telegram_id, engine_active, trading_mode'
).eq('auto_mode_enabled', True).execute()

print(f"Total: {len(auto_users.data) if auto_users.data else 0}")
for s in (auto_users.data or []):
    print(f"  tg_id={s['telegram_id']} | engine_active={s.get('engine_active')} | mode={s.get('trading_mode')}")
