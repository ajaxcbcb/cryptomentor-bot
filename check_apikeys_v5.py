"""No app imports at all - pure supabase + crypto."""
import os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')

import sys
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

# Import supabase BEFORE any app imports
from supabase import create_client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
s = create_client(url, key)

r = s.table('user_api_keys').select('telegram_id, key_hint').execute()
print(f"BEFORE app import: {len(r.data)} rows")

# Now import app
from app.lib.crypto import decrypt

r2 = s.table('user_api_keys').select('telegram_id, key_hint').execute()
print(f"AFTER app.lib.crypto import: {len(r2.data)} rows")

# Create new client
s2 = create_client(url, key)
r3 = s2.table('user_api_keys').select('telegram_id, key_hint').execute()
print(f"NEW client after app import: {len(r3.data)} rows")
