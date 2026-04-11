import os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')
from supabase import create_client
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
r = s.table('user_api_keys').select('telegram_id, key_hint').execute()
print(f"Total: {len(r.data)}")
for row in r.data:
    uid = row.get('telegram_id')
    print(f"  uid={uid} type={type(uid).__name__} hint={row.get('key_hint')}")
