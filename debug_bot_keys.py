"""Run inside bot's working directory to simulate exact same environment."""
import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

# Load env exactly like systemd service does
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')

# Check what supabase_repo sees
import importlib
import app.supabase_repo as repo
importlib.reload(repo)

print(f"SUPABASE_URL: {repo.SUPABASE_URL[:30]}...")
print(f"SUPABASE_SERVICE_KEY set: {bool(repo.SUPABASE_SERVICE_KEY)}")
print(f"SUPABASE_SERVICE_KEY: {str(repo.SUPABASE_SERVICE_KEY or '')[:20]}...")

# Test query
s = repo._client()
res = s.table('user_api_keys').select('telegram_id').eq('telegram_id', 1234500009).limit(1).execute()
print(f"\nQuery result for UID 1234500009: {res.data}")
print(f"Row count: {len(res.data or [])}")
