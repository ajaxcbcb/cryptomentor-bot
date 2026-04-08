#!/usr/bin/env python3
"""Test engine stop endpoint and diagnose stop issue"""
import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
os.chdir('/root/cryptomentor-bot/website-backend')
from dotenv import load_dotenv
load_dotenv('.env')

from app.auth.jwt import create_token
import subprocess, json

# Test user - admin
tg_id = 1234500009
tok = create_token(tg_id)
print(f"Token generated for uid={tg_id}")

# Test /state
r = subprocess.run(
    ['curl', '-s', f'http://localhost:8000/dashboard/engine/state',
     '-H', f'Authorization: Bearer {tok}'],
    capture_output=True, text=True
)
print(f"\n/state response: {r.stdout}")

# Check Supabase directly
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')
from app.supabase_repo import _client
s = _client()
res = s.table("autotrade_sessions").select("telegram_id,status,engine_active").eq("telegram_id", tg_id).execute()
print(f"\nSupabase session: {res.data}")

# Test stop
print("\nTesting POST /stop...")
r2 = subprocess.run(
    ['curl', '-s', '-X', 'POST', f'http://localhost:8000/dashboard/engine/stop',
     '-H', f'Authorization: Bearer {tok}'],
    capture_output=True, text=True
)
print(f"/stop response: {r2.stdout}")

# Check Supabase after stop
res2 = s.table("autotrade_sessions").select("telegram_id,status,engine_active").eq("telegram_id", tg_id).execute()
print(f"\nSupabase after stop: {res2.data}")
