#!/usr/bin/env python3
"""Quick DB health check for website-backend"""
import os, sys
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
os.chdir('/root/cryptomentor-bot/website-backend')

# Load env
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/website-backend/.env')

from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')

print(f"SUPABASE_URL: {url}")
print(f"SERVICE_KEY: {'SET' if key else 'MISSING'}")

if not url or not key:
    print("ERROR: Missing env vars!")
    sys.exit(1)

try:
    c = create_client(url, key)
    r = c.table('users').select('telegram_id, username, credits').limit(3).execute()
    print(f"DB OK - users table has data: {len(r.data)} rows returned")
    for u in r.data:
        print(f"  - {u.get('username','?')} | credits: {u.get('credits','?')}")
except Exception as e:
    print(f"DB ERROR: {e}")
