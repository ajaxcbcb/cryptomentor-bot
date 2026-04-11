import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

env_path = '/root/cryptomentor-bot/.env'
for line in open(env_path):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

from app.supabase_repo import _client
from app.autotrade_engine import is_running, _running_tasks

s = _client()

# In-memory running engines
running_in_memory = [uid for uid, task in _running_tasks.items() if not task.done()]
print(f"=== ENGINES RUNNING IN MEMORY: {len(running_in_memory)} ===")
for uid in sorted(running_in_memory):
    print(f"  UID {uid}")

# DB sessions with status active
db_active = s.table('autotrade_sessions').select('telegram_id, status, engine_active').not_.in_(
    'status', ['stopped', 'pending_verification', 'uid_rejected', 'pending']
).execute()
db_rows = [r for r in (db_active.data or []) if r.get('telegram_id') and int(r.get('telegram_id',0)) < 999999990]
print(f"\n=== DB SESSIONS STATUS ACTIVE: {len(db_rows)} ===")
for r in db_rows:
    in_mem = is_running(r['telegram_id'])
    print(f"  UID {r['telegram_id']} | db_status={r.get('status')} | engine_active={r.get('engine_active')} | in_memory={'✅' if in_mem else '❌'}")

print(f"\n=== SUMMARY ===")
print(f"  Running in memory: {len(running_in_memory)}")
print(f"  Active in DB: {len(db_rows)}")
