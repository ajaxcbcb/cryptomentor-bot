#!/usr/bin/env python3
"""
Script to check all engine statuses and diagnose inactive engines.
Run on VPS: python3 check_engine_status.py
"""
import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')
os.chdir('/root/cryptomentor-bot/Bismillah')

from dotenv import load_dotenv
load_dotenv()

# Load env from systemd environment
import subprocess
result = subprocess.run(['systemctl', 'show-environment'], capture_output=True, text=True)
for line in result.stdout.splitlines():
    if '=' in line:
        k, v = line.split('=', 1)
        os.environ.setdefault(k, v)

from app.supabase_repo import _client
from app.autotrade_engine import is_running

s = _client()

# Get ALL sessions
res = s.table("autotrade_sessions").select(
    "telegram_id,status,engine_active,trading_mode,initial_deposit,leverage,updated_at"
).execute()

sessions = res.data or []

print(f"\n{'='*70}")
print(f"TOTAL SESSIONS IN DATABASE: {len(sessions)}")
print(f"{'='*70}\n")

# Categorize
active_running = []
active_not_running = []
stopped_by_user = []
pending = []
other = []

for s_data in sessions:
    uid = s_data.get('telegram_id')
    status = s_data.get('status', 'unknown')
    engine_active = s_data.get('engine_active', False)
    deposit = s_data.get('initial_deposit', 0)
    mode = s_data.get('trading_mode', 'swing')
    running = is_running(uid)

    entry = {
        'uid': uid,
        'status': status,
        'engine_active': engine_active,
        'deposit': deposit,
        'mode': mode,
        'running': running,
    }

    if status == 'stopped':
        stopped_by_user.append(entry)
    elif status in ('pending_verification', 'pending', 'uid_rejected'):
        pending.append(entry)
    elif running:
        active_running.append(entry)
    elif status == 'active' or status == 'uid_verified':
        active_not_running.append(entry)
    else:
        other.append(entry)

print(f"✅ ACTIVE & RUNNING:        {len(active_running)}")
print(f"❌ ACTIVE BUT NOT RUNNING:  {len(active_not_running)}")
print(f"🛑 STOPPED BY USER:         {len(stopped_by_user)}")
print(f"⏳ PENDING/REJECTED:        {len(pending)}")
print(f"❓ OTHER STATUS:            {len(other)}")
print(f"\n{'='*70}")

if active_running:
    print(f"\n✅ RUNNING ENGINES ({len(active_running)}):")
    for e in active_running:
        print(f"  uid={e['uid']} | mode={e['mode']} | deposit=${e['deposit']}")

if active_not_running:
    print(f"\n❌ SHOULD BE RUNNING BUT INACTIVE ({len(active_not_running)}):")
    print(f"  (These are sessions with status=active but engine not running)")
    for e in active_not_running:
        deposit = float(e['deposit'] or 0)
        reason = "⚠️ balance=0" if deposit <= 0 else "🔴 engine crashed/stopped"
        print(f"  uid={e['uid']} | mode={e['mode']} | deposit=${deposit:.2f} | {reason}")

if stopped_by_user:
    print(f"\n🛑 STOPPED BY USER ({len(stopped_by_user)}):")
    for e in stopped_by_user:
        deposit = float(e['deposit'] or 0)
        print(f"  uid={e['uid']} | mode={e['mode']} | deposit=${deposit:.2f}")

if pending:
    print(f"\n⏳ PENDING/REJECTED ({len(pending)}):")
    for e in pending:
        print(f"  uid={e['uid']} | status={e['status']}")

if other:
    print(f"\n❓ OTHER ({len(other)}):")
    for e in other:
        print(f"  uid={e['uid']} | status={e['status']} | running={e['running']}")

print(f"\n{'='*70}")
print("SUMMARY:")
print(f"  Total sessions:     {len(sessions)}")
print(f"  Running engines:    {len(active_running)}")
print(f"  Inactive (crashed): {len(active_not_running)}")
print(f"  Stopped by user:    {len(stopped_by_user)}")
print(f"  Pending:            {len(pending)}")
print(f"{'='*70}\n")
